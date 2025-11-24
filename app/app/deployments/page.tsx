'use client';

import { Rocket, Package, Server, GitBranch } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function DeploymentsPage() {
  const features = [
    {
      icon: Package,
      title: 'Solution Packaging',
      description:
        'Bundle multiple agents, workflows, and configurations into deployable solutions',
    },
    {
      icon: Server,
      title: 'Environment Management',
      description: 'Deploy to dev, staging, and production environments with full tracking',
    },
    {
      icon: GitBranch,
      title: 'Version Control',
      description: 'Track deployment versions, rollback capabilities, and change history',
    },
  ];

  return (
    <div className="flex-1 overflow-auto">
      <PageHeader
        title="Deployments"
        description="Package and deploy agent solutions to higher environments"
        icon={Rocket}
        badge={{ label: 'Coming Soon', variant: 'secondary' }}
      />

      <div className="container mx-auto p-6 max-w-5xl">
        <div className="text-center mb-8">
          <Badge variant="outline" className="mb-4 text-amber-400 border-amber-500/40">
            Under Development
          </Badge>
          <p className="text-fg-2 max-w-2xl mx-auto">
            Deployments will allow you to package complete agent solutions - including multiple
            agents, channel workflows, and system configurations - for deployment to higher
            environments.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-bg-1 border-white/10">
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-blue-600/10 flex items-center justify-center mb-3">
                    <Icon className="w-5 h-5 text-blue-500" />
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
