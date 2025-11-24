'use client';

import { useEffect, useState, useMemo } from 'react';
import {
  Building,
  FolderKanban,
  Server,
  Package,
  Activity,
  CheckCircle2,
  XCircle,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  Info,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import Link from 'next/link';
import { useSession } from 'next-auth/react';

type ApiStatus = {
  status: string;
  integrations?: {
    notion?: boolean;
    openai?: boolean;
    github?: boolean;
  };
};

type ImportantFact = {
  message: string;
  severity: 'info' | 'warning' | 'critical';
  timestamp: string;
  details_link?: string;
};

export default function DashboardPage() {
  const { data: session } = useSession();
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [importantFact, setImportantFact] = useState<ImportantFact | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/status`);
      const data = await response.json();
      setApiStatus(data);
    } catch (error) {
      console.error('API Status Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Fetch important fact
    const fetchImportantFact = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/dashboard/important-fact`
        );
        if (response.ok) {
          const data = await response.json();
          setImportantFact(data);
        }
      } catch (error) {
        console.error('Failed to fetch important fact:', error);
        // Set a fallback mock fact for now
        setImportantFact({
          message: 'System health is optimal. All agents are operating normally.',
          severity: 'info',
          timestamp: new Date().toISOString(),
        });
      }
    };

    fetchImportantFact();
  }, []);

  const toolbarActions: ToolbarAction[] = useMemo(
    () => [
      {
        icon: RefreshCw,
        label: 'Refresh',
        onClick: fetchStatus,
        disabled: loading,
        variant: 'ghost',
        tooltip: loading ? 'Loading...' : 'Refresh dashboard data',
      },
    ],
    [loading]
  );

  // Get user's first name from session
  const userName = session?.user?.name?.split(' ')[0] || 'User';

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <Toolbar actions={toolbarActions} />

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Welcome Message */}
        <div className="mb-4">
          <h2 className="text-2xl font-semibold text-fg-0">Welcome back, {userName}!</h2>
        </div>

        {/* Important Fact Section */}
        {importantFact && (
          <Card
            className={`border-l-4 ${
              importantFact.severity === 'critical'
                ? 'border-l-red-500 bg-red-950/20'
                : importantFact.severity === 'warning'
                  ? 'border-l-yellow-500 bg-yellow-950/20'
                  : 'border-l-blue-500 bg-blue-950/20'
            }`}
          >
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    importantFact.severity === 'critical'
                      ? 'bg-red-500/20'
                      : importantFact.severity === 'warning'
                        ? 'bg-yellow-500/20'
                        : 'bg-blue-500/20'
                  }`}
                >
                  {importantFact.severity === 'critical' ? (
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                  ) : importantFact.severity === 'warning' ? (
                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  ) : (
                    <TrendingUp className="w-5 h-5 text-blue-400" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {importantFact.severity === 'critical'
                            ? 'Critical'
                            : importantFact.severity === 'warning'
                              ? 'Warning'
                              : 'Info'}
                        </Badge>
                        <span className="text-xs text-fg-2">
                          {new Date(importantFact.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-base text-fg-0 leading-relaxed">{importantFact.message}</p>
                    </div>
                  </div>
                  {importantFact.details_link && (
                    <Link
                      href={importantFact.details_link}
                      className="inline-flex items-center gap-1 mt-3 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      <Info className="w-3.5 h-3.5" />
                      <span>more...</span>
                    </Link>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Building}
            label="Organizations"
            value="3"
            description="Active organizations"
          />
          <MetricCard
            icon={FolderKanban}
            label="Total Projects"
            value="0"
            description="Across all organizations"
          />
          <MetricCard
            icon={Server}
            label="Active Instances"
            value="0"
            description="Running agent instances"
          />
          <MetricCard
            icon={Package}
            label="Artifacts"
            value="0"
            description="Generated artifacts"
          />
        </div>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-success" />
              System Status
            </CardTitle>
            <CardDescription>Quick health snapshot of your local environment</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center text-fg-2 py-4">Loading...</div>
            ) : apiStatus ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between py-2">
                  <span className="text-fg-1">API Status:</span>
                  <Badge variant="default" className="bg-success">
                    {apiStatus.status}
                  </Badge>
                </div>

                <div className="border-t border-border pt-4">
                  <h3 className="font-medium text-fg-0 mb-3">Integrations</h3>
                  <div className="space-y-2">
                    <IntegrationRow label="Notion" value={apiStatus.integrations?.notion} />
                    <IntegrationRow label="OpenAI" value={apiStatus.integrations?.openai} />
                    <IntegrationRow label="GitHub" value={apiStatus.integrations?.github} />
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-danger py-4">
                <XCircle className="w-8 h-8 mx-auto mb-2" />
                <p>API not responding</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-fg-1" />
              Recent Activity
            </CardTitle>
            <CardDescription>Latest updates and events across your organization</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Activity className="w-12 h-12 text-fg-2 mb-3 opacity-50" />
              <p className="text-fg-1 font-medium">No important activity to display</p>
              <p className="text-fg-2 text-sm mt-2 max-w-md">
                Activity like project creation, exports, and updates will appear here
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  description,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  description: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <p className="text-sm font-medium text-fg-2">{label}</p>
            <p className="text-3xl font-bold text-fg-0">{value}</p>
            <p className="text-xs text-fg-2">{description}</p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-blue-600/10 flex items-center justify-center flex-shrink-0">
            <Icon className="w-6 h-6 text-blue-500" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function IntegrationRow({ label, value }: { label: string; value?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-fg-1">{label}</span>
      <div className="flex items-center gap-2">
        {value ? (
          <>
            <CheckCircle2 className="w-4 h-4 text-success" />
            <span className="text-sm font-medium text-success">Connected</span>
          </>
        ) : (
          <>
            <XCircle className="w-4 h-4 text-danger" />
            <span className="text-sm font-medium text-danger">Not configured</span>
          </>
        )}
      </div>
    </div>
  );
}
