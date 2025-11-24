'use client';

import { Store, Share2, Download, Star } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function MarketplacePage() {
  const features = [
    {
      icon: Share2,
      title: 'Share Agents',
      description: 'Publish your agents for others to discover and use',
    },
    {
      icon: Download,
      title: 'Import Solutions',
      description: 'Browse and import pre-built agents and workflows',
    },
    {
      icon: Star,
      title: 'Community Ratings',
      description: 'Rate and review agents to help others find quality solutions',
    },
    {
      icon: Store,
      title: 'Template Library',
      description: 'Start from proven templates for common use cases',
    },
  ];

  return (
    <div className="flex-1 overflow-auto">
      <PageHeader
        title="Marketplace"
        description="Discover and share agent solutions"
        icon={Store}
        badge={{ label: 'Coming Soon', variant: 'secondary' }}
      />

      <div className="container mx-auto p-6 max-w-5xl">
        <div className="text-center mb-8">
          <Badge variant="outline" className="mb-4 text-amber-400 border-amber-500/40">
            Under Development
          </Badge>
          <p className="text-fg-2 max-w-2xl mx-auto">
            The Marketplace will be a community hub for sharing and discovering agent solutions -
            from individual agents to complete deployment packages.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-bg-1 border-white/10">
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-orange-600/10 flex items-center justify-center mb-3">
                    <Icon className="w-5 h-5 text-orange-500" />
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
