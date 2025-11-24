'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertCircle,
  Database,
  Download,
  Edit3,
  Plus,
  RefreshCw,
  RotateCcw,
  Shield,
  Trash2,
  Upload,
  Eye,
  Key,
  Server,
  Table as TableIcon,
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

interface BackupInfo {
  filename: string;
  size_bytes: number;
  created_at: string;
  label?: string | null;
  created_by?: string | null;
  created_by_email?: string | null;
}

interface SqliteTableInfo {
  name: string;
  row_count: number;
}

interface SqliteColumnInfo {
  cid: number;
  name: string;
  type?: string | null;
  notnull: number;
  dflt_value?: string | null;
  pk: number;
}

type SqliteRow = Record<string, any> & { _rowid_: number };

interface RedisKeyInfo {
  key: string;
  type: string;
  size?: number;
  ttl?: number;
}

interface PostgresTableInfo {
  name: string;
  row_count: number;
  size?: string;
  schema?: string;
}

interface MongoCollectionInfo {
  name: string;
  document_count: number;
  size?: number;
}

interface DatabaseInfo {
  version?: string;
  total_keys?: number;
  used_memory_human?: string;
  table_count?: number;
  database_size?: string;
  collections?: number;
  database_name?: string;
}

// ============================================================================
// Main Component
// ============================================================================

export default function ManageDatabasesPage() {
  const { data: session } = useSession();
  const [activeTab, setActiveTab] = useState('sqlite');
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  // Helper to get headers with user info for audit tracking
  const getUserHeaders = useCallback(() => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (session?.user?.name) {
      headers['x-user-name'] = session.user.name;
    }
    if (session?.user?.email) {
      headers['x-user-email'] = session.user.email;
    }
    return headers;
  }, [session]);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-fg-1">Database Management</h1>
          <p className="text-fg-3 mt-1">Manage all databases: SQLite, Redis, PostgreSQL, MongoDB</p>
        </div>
        <Shield className="h-8 w-8 text-accent-3" />
      </div>

      {message && (
        <Card
          className={`p-4 border ${message.type === 'error' ? 'border-red-500/50 bg-red-950/20' : 'border-green-500/50 bg-green-950/20'}`}
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm">{message.text}</span>
          </div>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-bg-1 border border-white/10">
          <TabsTrigger value="sqlite" className="data-[state=active]:bg-accent-3/20">
            <Database className="h-4 w-4 mr-2" />
            SQLite
          </TabsTrigger>
          <TabsTrigger value="redis" className="data-[state=active]:bg-accent-3/20">
            <Key className="h-4 w-4 mr-2" />
            Redis
          </TabsTrigger>
          <TabsTrigger value="postgres" className="data-[state=active]:bg-accent-3/20">
            <Server className="h-4 w-4 mr-2" />
            PostgreSQL
          </TabsTrigger>
          <TabsTrigger value="mongodb" className="data-[state=active]:bg-accent-3/20">
            <TableIcon className="h-4 w-4 mr-2" />
            MongoDB
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sqlite" className="space-y-4 mt-6">
          <SqliteTab setMessage={setMessage} getUserHeaders={getUserHeaders} />
        </TabsContent>

        <TabsContent value="redis" className="space-y-4 mt-6">
          <RedisTab setMessage={setMessage} getUserHeaders={getUserHeaders} />
        </TabsContent>

        <TabsContent value="postgres" className="space-y-4 mt-6">
          <PostgresTab setMessage={setMessage} getUserHeaders={getUserHeaders} />
        </TabsContent>

        <TabsContent value="mongodb" className="space-y-4 mt-6">
          <MongoDBTab setMessage={setMessage} getUserHeaders={getUserHeaders} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ============================================================================
// SQLite Tab Component
// ============================================================================

function SqliteTab({
  setMessage,
  getUserHeaders,
}: {
  setMessage: (msg: { type: 'error' | 'success'; text: string } | null) => void;
  getUserHeaders: () => Record<string, string>;
}) {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [label, setLabel] = useState('');
  const [tables, setTables] = useState<SqliteTableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableSchema, setTableSchema] = useState<SqliteColumnInfo[]>([]);
  const [tableRows, setTableRows] = useState<SqliteRow[]>([]);
  const [isTableLoading, setIsTableLoading] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editJson, setEditJson] = useState('');
  const [dialogMode, setDialogMode] = useState<'edit' | 'create'>('edit');
  const [editRowId, setEditRowId] = useState<number | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchBackups = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/sqlite/backups`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();
      setBackups(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch backups', error);
      setMessage({ type: 'error', text: 'Unable to load backups' });
    } finally {
      setIsLoading(false);
    }
  }, [setMessage]);

  const fetchTables = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/sqlite/tables`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();
      setTables(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch tables', error);
      setMessage({ type: 'error', text: 'Unable to load tables' });
    }
  }, [setMessage]);

  const loadTableData = useCallback(
    async (tableName: string) => {
      setIsTableLoading(true);
      try {
        const [schemaRes, rowsRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/sqlite/tables/${encodeURIComponent(tableName)}/schema`, {
            cache: 'no-store',
          }),
          fetch(
            `${API_BASE}/api/admin/sqlite/tables/${encodeURIComponent(tableName)}/rows?limit=50`,
            { cache: 'no-store' }
          ),
        ]);
        if (!schemaRes.ok || !rowsRes.ok) throw new Error('Failed to load table data');
        const schema = await schemaRes.json();
        const rows = await rowsRes.json();
        setTableSchema(schema.items ?? []);
        setTableRows(rows.items ?? []);
      } catch (error) {
        console.error('Failed to load table data', error);
        setMessage({ type: 'error', text: 'Unable to load table data' });
      } finally {
        setIsTableLoading(false);
      }
    },
    [setMessage]
  );

  useEffect(() => {
    fetchBackups();
    fetchTables();
  }, [fetchBackups, fetchTables]);

  useEffect(() => {
    if (selectedTable) {
      loadTableData(selectedTable);
    }
  }, [selectedTable, loadTableData]);

  const createBackup = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/sqlite/backups`, {
        method: 'POST',
        headers: getUserHeaders(),
        body: JSON.stringify({ label: label.trim() || undefined }),
      });
      if (!res.ok) throw new Error('Failed to create backup');
      setMessage({ type: 'success', text: 'Backup created successfully' });
      setLabel('');
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create backup' });
    } finally {
      setIsLoading(false);
    }
  };

  const downloadBackup = (filename: string) => {
    window.open(
      `${API_BASE}/api/admin/sqlite/backups/download?filename=${encodeURIComponent(filename)}`,
      '_blank'
    );
  };

  const restoreBackup = async (filename: string) => {
    if (!confirm(`Restore from backup "${filename}"? This will overwrite the current database.`))
      return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/sqlite/backups/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      if (!res.ok) throw new Error('Failed to restore backup');
      setMessage({
        type: 'success',
        text: 'Backup restored successfully. Restart backend to apply.',
      });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to restore backup' });
    } finally {
      setIsLoading(false);
    }
  };

  const importBackup = async (file: File) => {
    if (!confirm(`Import backup "${file.name}"? This will overwrite the current database.`)) return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/api/admin/sqlite/import`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to import backup');
      setMessage({
        type: 'success',
        text: 'Backup imported successfully. Restart backend to apply.',
      });
      fetchBackups();
      fetchTables();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to import backup' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importBackup(file);
      // Reset the input so the same file can be selected again
      e.target.value = '';
    }
  };

  const deleteRow = async (rowId: number) => {
    if (!selectedTable || !confirm('Delete this row?')) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/admin/sqlite/tables/${encodeURIComponent(selectedTable)}/rows/${rowId}`,
        {
          method: 'DELETE',
        }
      );
      if (!res.ok) throw new Error('Failed to delete row');
      setMessage({ type: 'success', text: 'Row deleted' });
      loadTableData(selectedTable);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete row' });
    }
  };

  const openEditDialog = (row: SqliteRow) => {
    setDialogMode('edit');
    setEditRowId(row._rowid_);
    const { _rowid_, ...editableFields } = row;
    setEditJson(JSON.stringify(editableFields, null, 2));
    setEditDialogOpen(true);
  };

  const openCreateDialog = () => {
    setDialogMode('create');
    setEditRowId(null);
    const emptyRow: Record<string, any> = {};
    tableSchema.forEach((col) => {
      emptyRow[col.name] = null;
    });
    setEditJson(JSON.stringify(emptyRow, null, 2));
    setEditDialogOpen(true);
  };

  const saveRowChanges = async () => {
    if (!selectedTable) return;
    try {
      const parsed = JSON.parse(editJson);
      setJsonError(null);
      const endpoint =
        dialogMode === 'edit'
          ? `${API_BASE}/api/admin/sqlite/tables/${encodeURIComponent(selectedTable)}/rows/${editRowId}`
          : `${API_BASE}/api/admin/sqlite/tables/${encodeURIComponent(selectedTable)}/rows`;
      const res = await fetch(endpoint, {
        method: dialogMode === 'edit' ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed),
      });
      if (!res.ok) throw new Error('Failed to save row');
      setMessage({ type: 'success', text: dialogMode === 'edit' ? 'Row updated' : 'Row inserted' });
      setEditDialogOpen(false);
      loadTableData(selectedTable);
    } catch (error: any) {
      if (error instanceof SyntaxError) {
        setJsonError('Invalid JSON');
      } else {
        setMessage({ type: 'error', text: error.message || 'Failed to save row' });
      }
    }
  };

  const filteredTables = useMemo(() => tables, [tables]);

  return (
    <>
      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">SQLite Backups</h2>
          <Database className="h-5 w-5 text-accent-3" />
        </div>
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="Optional backup label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="flex-1"
          />
          <Button onClick={createBackup} disabled={isLoading}>
            <Plus className="h-4 w-4 mr-2" />
            Create Backup
          </Button>
          <Button variant="outline" onClick={handleFileSelect} disabled={isLoading}>
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" onClick={fetchBackups} disabled={isLoading}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".db"
          className="hidden"
          onChange={handleFileChange}
        />
        <ScrollArea className="h-[300px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Created By</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backups.map((backup) => (
                <TableRow key={backup.filename}>
                  <TableCell className="font-mono text-xs">{backup.filename}</TableCell>
                  <TableCell>{(backup.size_bytes / 1024 / 1024).toFixed(2)} MB</TableCell>
                  <TableCell>{new Date(backup.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {backup.created_by || '-'}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadBackup(backup.filename)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => restoreBackup(backup.filename)}
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">Table Browser</h2>
          <Badge variant="outline">{filteredTables.length} tables</Badge>
        </div>
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-3">
            <ScrollArea className="h-[400px] border border-white/10 rounded-md p-2">
              {filteredTables.map((table) => (
                <div
                  key={table.name}
                  className={`p-2 rounded cursor-pointer hover:bg-white/5 ${selectedTable === table.name ? 'bg-accent-3/20' : ''}`}
                  onClick={() => setSelectedTable(table.name)}
                >
                  <div className="text-sm font-medium text-fg-1">{table.name}</div>
                  <div className="text-xs text-fg-3">{table.row_count} rows</div>
                </div>
              ))}
            </ScrollArea>
          </div>
          <div className="col-span-9">
            {selectedTable ? (
              <>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-fg-1">{selectedTable}</h3>
                  <Button size="sm" onClick={openCreateDialog}>
                    <Plus className="h-4 w-4 mr-2" />
                    Insert Row
                  </Button>
                </div>
                <div className="text-xs text-fg-3 mb-2">
                  Schema: {tableSchema.map((c) => c.name).join(', ')}
                </div>
                <ScrollArea className="h-[350px] border border-white/10 rounded-md">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {tableSchema.map((col) => (
                          <TableHead key={col.cid}>{col.name}</TableHead>
                        ))}
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tableRows.map((row) => (
                        <TableRow key={row._rowid_}>
                          {tableSchema.map((col) => (
                            <TableCell key={col.cid} className="max-w-xs truncate text-xs">
                              {row[col.name] != null ? (
                                String(row[col.name])
                              ) : (
                                <span className="text-fg-4">null</span>
                              )}
                            </TableCell>
                          ))}
                          <TableCell className="text-right space-x-1">
                            <Button size="sm" variant="ghost" onClick={() => openEditDialog(row)}>
                              <Edit3 className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteRow(row._rowid_)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              </>
            ) : (
              <div className="text-sm text-fg-3">Select a table to view rows.</div>
            )}
          </div>
        </div>
      </Card>

      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-xl bg-bg-0">
          <DialogHeader>
            <DialogTitle>{dialogMode === 'edit' ? 'Edit Row' : 'Insert Row'}</DialogTitle>
            <DialogDescription>
              {dialogMode === 'edit'
                ? 'Modify the JSON payload for this row.'
                : 'Provide values for the new row as JSON.'}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={editJson}
            onChange={(e) => {
              setEditJson(e.target.value);
              setJsonError(null);
            }}
            className="min-h-[240px] font-mono text-xs"
          />
          {jsonError && <div className="text-xs text-red-400">{jsonError}</div>}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveRowChanges}>{dialogMode === 'edit' ? 'Save' : 'Insert'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ============================================================================
// Redis Tab Component
// ============================================================================

function RedisTab({
  setMessage,
  getUserHeaders,
}: {
  setMessage: (msg: { type: 'error' | 'success'; text: string } | null) => void;
  getUserHeaders: () => Record<string, string>;
}) {
  const [info, setInfo] = useState<DatabaseInfo | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [keys, setKeys] = useState<RedisKeyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [label, setLabel] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInfo = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/redis/info`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch Redis info');
      const data = await res.json();
      setInfo(data);
    } catch (error) {
      console.error('Failed to fetch Redis info', error);
      setMessage({ type: 'error', text: 'Unable to load Redis info' });
    }
  }, [setMessage]);

  const fetchBackups = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/redis/backups`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch backups');
      const data = await res.json();
      setBackups(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch backups', error);
      setMessage({ type: 'error', text: 'Unable to load backups' });
    } finally {
      setIsLoading(false);
    }
  }, [setMessage]);

  const fetchKeys = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/redis/keys?limit=100`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch keys');
      const data = await res.json();
      setKeys(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch keys', error);
      setMessage({ type: 'error', text: 'Unable to load keys' });
    }
  }, [setMessage]);

  useEffect(() => {
    fetchInfo();
    fetchBackups();
    fetchKeys();
  }, [fetchInfo, fetchBackups, fetchKeys]);

  const createBackup = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/redis/backups`, {
        method: 'POST',
        headers: getUserHeaders(),
        body: JSON.stringify({ label: label.trim() || undefined }),
      });
      if (!res.ok) throw new Error('Failed to create backup');
      setMessage({ type: 'success', text: 'Redis backup created successfully' });
      setLabel('');
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create backup' });
    } finally {
      setIsLoading(false);
    }
  };

  const downloadBackup = (filename: string) => {
    window.open(
      `${API_BASE}/api/admin/redis/backups/download?filename=${encodeURIComponent(filename)}`,
      '_blank'
    );
  };

  const importBackup = async (file: File) => {
    if (!confirm(`Import Redis data from "${file.name}"? This will overwrite existing keys.`))
      return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/api/admin/redis/import`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to import data');
      setMessage({ type: 'success', text: 'Redis data imported successfully' });
      fetchInfo();
      fetchKeys();
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to import data' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importBackup(file);
      e.target.value = '';
    }
  };

  const viewKeyValue = async (key: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/redis/keys/${encodeURIComponent(key)}`, {
        cache: 'no-store',
      });
      if (!res.ok) throw new Error('Failed to fetch key value');
      const data = await res.json();
      setSelectedKey(key);
      setKeyValue(data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load key value' });
    }
  };

  return (
    <>
      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">Redis Server Info</h2>
          <Key className="h-5 w-5 text-accent-3" />
        </div>
        {info && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-fg-3">Version</div>
              <div className="text-fg-1 font-medium">{info.version}</div>
            </div>
            <div>
              <div className="text-fg-3">Total Keys</div>
              <div className="text-fg-1 font-medium">{info.total_keys}</div>
            </div>
            <div>
              <div className="text-fg-3">Memory Used</div>
              <div className="text-fg-1 font-medium">{info.used_memory_human}</div>
            </div>
          </div>
        )}
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">Redis Backups</h2>
        </div>
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="Optional backup label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="flex-1"
          />
          <Button onClick={createBackup} disabled={isLoading}>
            <Plus className="h-4 w-4 mr-2" />
            Create Backup
          </Button>
          <Button variant="outline" onClick={handleFileSelect} disabled={isLoading}>
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" onClick={fetchBackups} disabled={isLoading}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={handleFileChange}
        />
        <ScrollArea className="h-[250px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Created By</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backups.map((backup) => (
                <TableRow key={backup.filename}>
                  <TableCell className="font-mono text-xs">{backup.filename}</TableCell>
                  <TableCell>{(backup.size_bytes / 1024).toFixed(2)} KB</TableCell>
                  <TableCell>{new Date(backup.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {backup.created_by || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadBackup(backup.filename)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">Key Browser</h2>
          <Badge variant="outline">{keys.length} keys</Badge>
        </div>
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-4">
            <ScrollArea className="h-[350px] border border-white/10 rounded-md p-2">
              {keys.map((key) => (
                <div
                  key={key.key}
                  className={`p-2 rounded cursor-pointer hover:bg-white/5 ${selectedKey === key.key ? 'bg-accent-3/20' : ''}`}
                  onClick={() => viewKeyValue(key.key)}
                >
                  <div className="text-sm font-mono text-fg-1 truncate">{key.key}</div>
                  <div className="text-xs text-fg-3">{key.type}</div>
                </div>
              ))}
            </ScrollArea>
          </div>
          <div className="col-span-8">
            {selectedKey && keyValue ? (
              <div>
                <h3 className="text-lg font-medium text-fg-1 mb-2">{selectedKey}</h3>
                <div className="text-xs text-fg-3 mb-2">Type: {keyValue.type}</div>
                <ScrollArea className="h-[300px] border border-white/10 rounded-md p-4">
                  <pre className="text-xs font-mono text-fg-1">
                    {JSON.stringify(keyValue.value, null, 2)}
                  </pre>
                </ScrollArea>
              </div>
            ) : (
              <div className="text-sm text-fg-3">Select a key to view its value.</div>
            )}
          </div>
        </div>
      </Card>
    </>
  );
}

// ============================================================================
// PostgreSQL Tab Component
// ============================================================================

function PostgresTab({
  setMessage,
  getUserHeaders,
}: {
  setMessage: (msg: { type: 'error' | 'success'; text: string } | null) => void;
  getUserHeaders: () => Record<string, string>;
}) {
  const [info, setInfo] = useState<DatabaseInfo | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [tables, setTables] = useState<PostgresTableInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [label, setLabel] = useState('');
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableRows, setTableRows] = useState<any[]>([]);
  const [tableSchema, setTableSchema] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInfo = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/postgres/info`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch PostgreSQL info');
      const data = await res.json();
      setInfo(data);
    } catch (error) {
      console.error('Failed to fetch PostgreSQL info', error);
      setMessage({ type: 'error', text: 'Unable to load PostgreSQL info' });
    }
  }, [setMessage]);

  const fetchBackups = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/postgres/backups`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch backups');
      const data = await res.json();
      setBackups(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch backups', error);
      setMessage({ type: 'error', text: 'Unable to load backups' });
    } finally {
      setIsLoading(false);
    }
  }, [setMessage]);

  const fetchTables = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/postgres/tables`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch tables');
      const data = await res.json();
      setTables(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch tables', error);
      setMessage({ type: 'error', text: 'Unable to load tables' });
    }
  }, [setMessage]);

  const loadTableData = useCallback(
    async (tableName: string) => {
      try {
        const [schemaRes, rowsRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/postgres/tables/${encodeURIComponent(tableName)}/schema`, {
            cache: 'no-store',
          }),
          fetch(
            `${API_BASE}/api/admin/postgres/tables/${encodeURIComponent(tableName)}/rows?limit=50`,
            { cache: 'no-store' }
          ),
        ]);
        if (!schemaRes.ok || !rowsRes.ok) throw new Error('Failed to load table data');
        const schema = await schemaRes.json();
        const rows = await rowsRes.json();
        setTableSchema(schema.items ?? []);
        setTableRows(rows.items ?? []);
      } catch (error) {
        console.error('Failed to load table data', error);
        setMessage({ type: 'error', text: 'Unable to load table data' });
      }
    },
    [setMessage]
  );

  useEffect(() => {
    fetchInfo();
    fetchBackups();
    fetchTables();
  }, [fetchInfo, fetchBackups, fetchTables]);

  useEffect(() => {
    if (selectedTable) {
      loadTableData(selectedTable);
    }
  }, [selectedTable, loadTableData]);

  const createBackup = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/postgres/backups`, {
        method: 'POST',
        headers: getUserHeaders(),
        body: JSON.stringify({ label: label.trim() || undefined }),
      });
      if (!res.ok) throw new Error('Failed to create backup');
      setMessage({ type: 'success', text: 'PostgreSQL backup created successfully' });
      setLabel('');
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create backup' });
    } finally {
      setIsLoading(false);
    }
  };

  const downloadBackup = (filename: string) => {
    window.open(
      `${API_BASE}/api/admin/postgres/backups/download?filename=${encodeURIComponent(filename)}`,
      '_blank'
    );
  };

  const exportTable = (tableName: string) => {
    window.open(
      `${API_BASE}/api/admin/postgres/tables/${encodeURIComponent(tableName)}/export`,
      '_blank'
    );
  };

  const importBackup = async (file: File) => {
    if (!confirm(`Import PostgreSQL data from "${file.name}"? This may overwrite existing data.`))
      return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/api/admin/postgres/import`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to import data');
      setMessage({ type: 'success', text: 'PostgreSQL data imported successfully' });
      fetchInfo();
      fetchTables();
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to import data' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importBackup(file);
      e.target.value = '';
    }
  };

  return (
    <>
      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">PostgreSQL Server Info</h2>
          <Server className="h-5 w-5 text-accent-3" />
        </div>
        {info && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-fg-3">Version</div>
              <div className="text-fg-1 font-medium text-xs">
                {info.version?.substring(0, 50)}...
              </div>
            </div>
            <div>
              <div className="text-fg-3">Tables</div>
              <div className="text-fg-1 font-medium">{info.table_count}</div>
            </div>
            <div>
              <div className="text-fg-3">Database Size</div>
              <div className="text-fg-1 font-medium">{info.database_size}</div>
            </div>
          </div>
        )}
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">PostgreSQL Backups</h2>
        </div>
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="Optional backup label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="flex-1"
          />
          <Button onClick={createBackup} disabled={isLoading}>
            <Plus className="h-4 w-4 mr-2" />
            Create Backup
          </Button>
          <Button variant="outline" onClick={handleFileSelect} disabled={isLoading}>
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" onClick={fetchBackups} disabled={isLoading}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".dump,.sql"
          className="hidden"
          onChange={handleFileChange}
        />
        <ScrollArea className="h-[250px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Created By</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backups.map((backup) => (
                <TableRow key={backup.filename}>
                  <TableCell className="font-mono text-xs">{backup.filename}</TableCell>
                  <TableCell>{(backup.size_bytes / 1024 / 1024).toFixed(2)} MB</TableCell>
                  <TableCell>{new Date(backup.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {backup.created_by || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadBackup(backup.filename)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">Table Browser</h2>
          <Badge variant="outline">{tables.length} tables</Badge>
        </div>
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-3">
            <ScrollArea className="h-[400px] border border-white/10 rounded-md p-2">
              {tables.map((table) => (
                <div
                  key={table.name}
                  className={`p-2 rounded cursor-pointer hover:bg-white/5 ${selectedTable === table.name ? 'bg-accent-3/20' : ''}`}
                  onClick={() => setSelectedTable(table.name)}
                >
                  <div className="text-sm font-medium text-fg-1">{table.name}</div>
                  <div className="text-xs text-fg-3">{table.row_count} rows</div>
                </div>
              ))}
            </ScrollArea>
          </div>
          <div className="col-span-9">
            {selectedTable ? (
              <>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-fg-1">{selectedTable}</h3>
                  <Button size="sm" onClick={() => exportTable(selectedTable)}>
                    <Download className="h-4 w-4 mr-2" />
                    Export SQL
                  </Button>
                </div>
                <div className="text-xs text-fg-3 mb-2">
                  Columns: {tableSchema.map((c) => c.column_name).join(', ')}
                </div>
                <ScrollArea className="h-[350px] border border-white/10 rounded-md">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {tableSchema.map((col) => (
                          <TableHead key={col.column_name}>{col.column_name}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tableRows.map((row, idx) => (
                        <TableRow key={idx}>
                          {tableSchema.map((col) => (
                            <TableCell key={col.column_name} className="max-w-xs truncate text-xs">
                              {row[col.column_name] != null ? (
                                String(row[col.column_name])
                              ) : (
                                <span className="text-fg-4">null</span>
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              </>
            ) : (
              <div className="text-sm text-fg-3">Select a table to view data.</div>
            )}
          </div>
        </div>
      </Card>
    </>
  );
}

// ============================================================================
// MongoDB Tab Component
// ============================================================================

function MongoDBTab({
  setMessage,
  getUserHeaders,
}: {
  setMessage: (msg: { type: 'error' | 'success'; text: string } | null) => void;
  getUserHeaders: () => Record<string, string>;
}) {
  const [info, setInfo] = useState<DatabaseInfo | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [collections, setCollections] = useState<MongoCollectionInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [label, setLabel] = useState('');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInfo = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/mongodb/info`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch MongoDB info');
      const data = await res.json();
      setInfo(data);
    } catch (error) {
      console.error('Failed to fetch MongoDB info', error);
      setMessage({ type: 'error', text: 'Unable to load MongoDB info' });
    }
  }, [setMessage]);

  const fetchBackups = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/mongodb/backups`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch backups');
      const data = await res.json();
      setBackups(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch backups', error);
      setMessage({ type: 'error', text: 'Unable to load backups' });
    } finally {
      setIsLoading(false);
    }
  }, [setMessage]);

  const fetchCollections = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/mongodb/collections`, { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to fetch collections');
      const data = await res.json();
      setCollections(data.items ?? []);
    } catch (error) {
      console.error('Failed to fetch collections', error);
      setMessage({ type: 'error', text: 'Unable to load collections' });
    }
  }, [setMessage]);

  const loadCollectionData = useCallback(
    async (collectionName: string) => {
      try {
        const res = await fetch(
          `${API_BASE}/api/admin/mongodb/collections/${encodeURIComponent(collectionName)}/documents?limit=50`,
          { cache: 'no-store' }
        );
        if (!res.ok) throw new Error('Failed to load documents');
        const data = await res.json();
        setDocuments(data.items ?? []);
      } catch (error) {
        console.error('Failed to load documents', error);
        setMessage({ type: 'error', text: 'Unable to load documents' });
      }
    },
    [setMessage]
  );

  useEffect(() => {
    fetchInfo();
    fetchBackups();
    fetchCollections();
  }, [fetchInfo, fetchBackups, fetchCollections]);

  useEffect(() => {
    if (selectedCollection) {
      loadCollectionData(selectedCollection);
    }
  }, [selectedCollection, loadCollectionData]);

  const createBackup = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/mongodb/backups`, {
        method: 'POST',
        headers: getUserHeaders(),
        body: JSON.stringify({ label: label.trim() || undefined }),
      });
      if (!res.ok) throw new Error('Failed to create backup');
      setMessage({ type: 'success', text: 'MongoDB backup created successfully' });
      setLabel('');
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create backup' });
    } finally {
      setIsLoading(false);
    }
  };

  const downloadBackup = (filename: string) => {
    window.open(
      `${API_BASE}/api/admin/mongodb/backups/download?filename=${encodeURIComponent(filename)}`,
      '_blank'
    );
  };

  const exportCollection = (collectionName: string) => {
    window.open(
      `${API_BASE}/api/admin/mongodb/collections/${encodeURIComponent(collectionName)}/export`,
      '_blank'
    );
  };

  const importBackup = async (file: File) => {
    if (
      !confirm(`Import MongoDB data from "${file.name}"? This may overwrite existing collections.`)
    )
      return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/api/admin/mongodb/import`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to import data');
      setMessage({ type: 'success', text: 'MongoDB data imported successfully' });
      fetchInfo();
      fetchCollections();
      fetchBackups();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to import data' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importBackup(file);
      e.target.value = '';
    }
  };

  return (
    <>
      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">MongoDB Server Info</h2>
          <TableIcon className="h-5 w-5 text-accent-3" />
        </div>
        {info && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-fg-3">Version</div>
              <div className="text-fg-1 font-medium">{info.version}</div>
            </div>
            <div>
              <div className="text-fg-3">Database</div>
              <div className="text-fg-1 font-medium">{info.database_name}</div>
            </div>
            <div>
              <div className="text-fg-3">Collections</div>
              <div className="text-fg-1 font-medium">{info.collections}</div>
            </div>
          </div>
        )}
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">MongoDB Backups</h2>
        </div>
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="Optional backup label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="flex-1"
          />
          <Button onClick={createBackup} disabled={isLoading}>
            <Plus className="h-4 w-4 mr-2" />
            Create Backup
          </Button>
          <Button variant="outline" onClick={handleFileSelect} disabled={isLoading}>
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" onClick={fetchBackups} disabled={isLoading}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".archive,.gz"
          className="hidden"
          onChange={handleFileChange}
        />
        <ScrollArea className="h-[250px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Created By</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backups.map((backup) => (
                <TableRow key={backup.filename}>
                  <TableCell className="font-mono text-xs">{backup.filename}</TableCell>
                  <TableCell>{(backup.size_bytes / 1024).toFixed(2)} KB</TableCell>
                  <TableCell>{new Date(backup.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {backup.created_by || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadBackup(backup.filename)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </Card>

      <Card className="border border-white/10 bg-bg-1 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-fg-1">Collection Browser</h2>
          <Badge variant="outline">{collections.length} collections</Badge>
        </div>
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-3">
            <ScrollArea className="h-[400px] border border-white/10 rounded-md p-2">
              {collections.length > 0 ? (
                collections.map((collection) => (
                  <div
                    key={collection.name}
                    className={`p-2 rounded cursor-pointer hover:bg-white/5 ${selectedCollection === collection.name ? 'bg-accent-3/20' : ''}`}
                    onClick={() => setSelectedCollection(collection.name)}
                  >
                    <div className="text-sm font-medium text-fg-1">{collection.name}</div>
                    <div className="text-xs text-fg-3">{collection.document_count} documents</div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-fg-3 p-2">No collections</div>
              )}
            </ScrollArea>
          </div>
          <div className="col-span-9">
            {selectedCollection ? (
              <>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-fg-1">{selectedCollection}</h3>
                  <Button size="sm" onClick={() => exportCollection(selectedCollection)}>
                    <Download className="h-4 w-4 mr-2" />
                    Export JSON
                  </Button>
                </div>
                <ScrollArea className="h-[350px] border border-white/10 rounded-md p-4">
                  {documents.length > 0 ? (
                    <pre className="text-xs font-mono text-fg-1">
                      {JSON.stringify(documents, null, 2)}
                    </pre>
                  ) : (
                    <div className="text-sm text-fg-3">No documents found</div>
                  )}
                </ScrollArea>
              </>
            ) : (
              <div className="text-sm text-fg-3">Select a collection to view documents.</div>
            )}
          </div>
        </div>
      </Card>
    </>
  );
}
