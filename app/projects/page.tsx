"use client"

import { Plus, Filter, FolderKanban } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export default function ProjectsPage() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-fg-0">Projects</h1>
          <p className="text-fg-2 mt-1">Manage your automation projects</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-500">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Search + Filter */}
      <div className="flex gap-3">
        <Input
          placeholder="Search projects..."
          className="flex-1 max-w-sm"
        />
        <Button variant="outline" className="gap-2">
          <Filter className="w-4 h-4" />
          Filter
        </Button>
      </div>

      {/* Projects Table */}
      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Project</TableHead>
              <TableHead>Client</TableHead>
              <TableHead>Project Lead</TableHead>
              <TableHead className="text-center">Instances</TableHead>
              <TableHead>Last Updated</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={6} className="h-64">
                <div className="flex flex-col items-center justify-center text-center py-12">
                  <FolderKanban className="w-16 h-16 text-fg-2 mb-4 opacity-50" />
                  <h3 className="text-lg font-semibold text-fg-0 mb-2">
                    No projects yet
                  </h3>
                  <p className="text-fg-2 mb-6 max-w-md">
                    Create your first project to get started with Agent Foundry
                  </p>
                  <Button className="bg-blue-600 hover:bg-blue-500">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Project
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
