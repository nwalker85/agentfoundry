"use client"

import { Server } from "lucide-react"
import { Card } from "@/components/ui/card"

export default function InstancesPage() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-fg-0">Instances</h1>
        <p className="text-fg-2 mt-1">Monitor and manage running agent instances</p>
      </div>

      {/* Empty State */}
      <Card className="p-12">
        <div className="flex flex-col items-center justify-center text-center">
          <Server className="w-20 h-20 text-fg-2 mb-4 opacity-50" />
          <h3 className="text-xl font-semibold text-fg-0 mb-2">
            No instances running
          </h3>
          <p className="text-fg-2 max-w-md">
            Agent instances will appear here when they are deployed and running
          </p>
        </div>
      </Card>
    </div>
  )
}
