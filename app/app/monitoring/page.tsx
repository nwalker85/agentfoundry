'use client';

import { Activity, BarChart3, AlertTriangle, Clock } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function MonitoringPage() {
  const features = [
    {
      icon: Activity,
      title: 'Real-time Metrics',
      description: 'Monitor agent performance, response times, and throughput in real-time',
    },
    {
      icon: BarChart3,
      title: 'Analytics Dashboard',
      description: 'Visualize trends, usage patterns, and key performance indicators',
    },
    {
      icon: AlertTriangle,
      title: 'Alerting & Incidents',
      description: 'Set up alerts for anomalies and track incident resolution',
    },
    {
      icon: Clock,
      title: 'Session Tracking',
      description: 'Review conversation histories and agent decision paths',
    },
  ];

  return (
    <div className="flex-1 overflow-auto">
      <PageHeader
        title="Monitoring"
        description="Observe and analyze agent performance and behavior"
        icon={Activity}
        badge={{ label: 'Coming Soon', variant: 'secondary' }}
      />

      <div className="container mx-auto p-6 max-w-5xl">
        <div className="text-center mb-8">
          <Badge variant="outline" className="mb-4 text-amber-400 border-amber-500/40">
            Under Development
          </Badge>
          <p className="text-fg-2 max-w-2xl mx-auto">
            Monitoring will provide comprehensive observability into your deployed agents - from
            real-time metrics to historical analytics and incident management.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-bg-1 border-white/10">
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-green-600/10 flex items-center justify-center mb-3">
                    <Icon className="w-5 h-5 text-green-500" />
                  </div>
                  <CardTitle className="text-fg-0">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-fg-2">{feature.description}</CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
