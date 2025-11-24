'use client';

import { Database, FileText, Search, Upload } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function DatasetsPage() {
  const features = [
    {
      icon: Upload,
      title: 'Data Ingestion',
      description: 'Upload and process documents, PDFs, and structured data for agent use',
    },
    {
      icon: Search,
      title: 'Vector Search',
      description: 'Semantic search capabilities powered by embeddings and vector databases',
    },
    {
      icon: FileText,
      title: 'Knowledge Bases',
      description: 'Organize data into knowledge bases that agents can reference',
    },
    {
      icon: Database,
      title: 'Data Management',
      description: 'Version, update, and manage your datasets over time',
    },
  ];

  return (
    <div className="flex-1 overflow-auto">
      <PageHeader
        title="Datasets"
        description="Manage data sources for RAG-enabled agents"
        icon={Database}
        badge={{ label: 'Coming Soon', variant: 'secondary' }}
      />

      <div className="container mx-auto p-6 max-w-5xl">
        <div className="text-center mb-8">
          <Badge variant="outline" className="mb-4 text-amber-400 border-amber-500/40">
            Under Development
          </Badge>
          <p className="text-fg-2 max-w-2xl mx-auto">
            Datasets will enable you to build RAG (Retrieval-Augmented Generation) agents by
            managing knowledge bases, document collections, and vector embeddings.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-bg-1 border-white/10">
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-purple-600/10 flex items-center justify-center mb-3">
                    <Icon className="w-5 h-5 text-purple-500" />
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
