"use client"

import { useEffect, useState } from "react"
import { Building, FolderKanban, Server, Package, Activity, CheckCircle2, XCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

type ApiStatus = {
  status: string
  integrations?: {
    notion?: boolean
    openai?: boolean
    github?: boolean
  }
}

export default function DashboardPage() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchStatus() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/status`)
        const data = await response.json()
        setApiStatus(data)
      } catch (error) {
        console.error("API Status Error:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-fg-0">Dashboard</h1>
        <p className="text-fg-2 mt-1">Welcome back, nwalker85</p>
      </div>

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
          <CardDescription>
            Quick health snapshot of your local environment
          </CardDescription>
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
          <CardDescription>
            Latest updates and events across your organization
          </CardDescription>
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
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  description,
}: {
  icon: React.ElementType
  label: string
  value: string
  description: string
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
  )
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
  )
}
