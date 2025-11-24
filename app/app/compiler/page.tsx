'use client';

import { FileCode, Upload, FileText, ArrowRight } from 'lucide-react';
import { PageHeader } from '@/app/components/shared/PageHeader';
import { UnderConstruction } from '@/components/shared';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { useState } from 'react';

export default function CompilerPage() {
  const [disInput, setDisInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleCompile = async () => {
    setIsProcessing(true);
    // TODO: Implement DIS compilation logic
    setTimeout(() => {
      setIsProcessing(false);
    }, 2000);
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="container mx-auto p-6 max-w-7xl">
        <PageHeader
          title="From DIS"
          description="Import and compile agents from Domain Intelligence Schema (DIS) definitions"
          icon={FileCode}
          actions={
            <Button size="sm" variant="outline">
              <FileText className="w-4 h-4 mr-2" />
              Documentation
            </Button>
          }
        />

        <UnderConstruction
          className="mt-4"
          message="DIS compilation is under development. The UI is available but compilation is not yet functional."
        />

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Input Section */}
          <Card>
            <CardHeader>
              <CardTitle>DIS Input</CardTitle>
              <CardDescription>
                Paste your Domain Intelligence Schema (DIS 1.6.0) definition below
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={disInput}
                onChange={(e) => setDisInput(e.target.value)}
                placeholder={`{
  "dossierId": "my-domain-v1",
  "domainName": "My Business Domain",
  "version": "1.0.0",
  ...
}`}
                className="font-mono text-sm min-h-[400px]"
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleCompile}
                  disabled={!disInput || isProcessing}
                  className="flex-1"
                >
                  {isProcessing ? (
                    <>Processing...</>
                  ) : (
                    <>
                      <ArrowRight className="w-4 h-4 mr-2" />
                      Compile to Agent
                    </>
                  )}
                </Button>
                <Button variant="outline">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload File
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Output/Preview Section */}
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
              <CardDescription>
                Generated agent configuration from your DIS definition
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!disInput ? (
                <div className="flex flex-col items-center justify-center py-16 text-center text-fg-2">
                  <FileCode className="w-12 h-12 mb-4 opacity-50" />
                  <p>Enter a DIS definition to see the generated agent configuration</p>
                </div>
              ) : (
                <div className="bg-bg-2 rounded-lg p-4 font-mono text-sm min-h-[400px]">
                  <pre className="text-fg-2">
                    {`# Agent configuration will appear here
# after compilation

apiVersion: agent-foundry/v1
kind: Agent
metadata:
  name: generated-agent
  ...`}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Info Cards */}
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">DIS 1.6.0 Compliant</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-fg-2">
                Supports the latest Domain Intelligence Schema specification
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Automatic Validation</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-fg-2">
                Validates your DIS definition against the schema automatically
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Agent Generation</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-fg-2">
                Generates deployable agent configurations from DIS definitions
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
