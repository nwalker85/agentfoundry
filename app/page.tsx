'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, Sparkles, Workflow, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentFoundryLogo } from '@/components/logo/AgentFoundryLogo';
import { QuantLogo } from '@/components/logo/QuantLogo';
import { AtomIndicator } from '@/app/chat/components/AtomIndicator';
import { Badge } from '@/components/ui/badge';
import { useSession } from 'next-auth/react';

const highlights = [
  {
    title: 'Stateful agents',
    description: 'Typed state schemas, orchestration, and LangGraph-native flows.',
    icon: Workflow,
  },
  {
    title: 'Enterprise guardrails',
    description: 'RBAC, policy enforcement, and audit-grade logging out of the box.',
    icon: ShieldCheck,
  },
  {
    title: 'Execution visibility',
    description: 'Streaming traces, memory inspection, and live debugging tools.',
    icon: Sparkles,
  },
];

const assistantUpdates = [
  { label: 'Backend', status: 'Healthy', detail: 'All control plane services are online.' },
  { label: 'Graph runtime', status: 'Ready', detail: 'LangGraph worker pool warmed and idle.' },
  { label: 'Tool catalog', status: '29 tools', detail: 'Schemas validated and synced.' },
];

const stats = [
  { label: 'Agents orchestrated', value: '1,247', caption: 'Across internal teams' },
  { label: 'Avg. deploy time', value: '42s', caption: 'CI to runtime hand-off' },
  { label: 'Integrations live', value: '18', caption: 'Systems, tools, and data planes' },
];

export default function WelcomePage() {
  const router = useRouter();
  const { status } = useSession();

  useEffect(() => {
    if (status === 'authenticated') {
      router.replace('/app');
    }
  }, [status, router]);

  return (
    <div className="relative h-full w-full overflow-hidden bg-gradient-to-br from-[#05060b] via-[#070b1a] to-[#020205] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(0,102,255,0.25),_transparent_60%)] opacity-90" />
      <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(0deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[length:160px_160px]" />

      <div className="relative z-10 flex h-full flex-col px-6 py-8 lg:px-14">
        <header className="flex items-center gap-4">
          <AgentFoundryLogo className="h-12 w-12" />
          <div>
            <p className="text-lg font-semibold text-white">Agent Foundry</p>
            <p className="text-sm text-blue-200/80">Modern AI agent development platform</p>
          </div>
        </header>

        <div className="flex-1 items-center justify-center py-8 lg:py-10">
          <div className="grid h-full w-full gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <section className="flex flex-col justify-center space-y-10 text-center lg:text-left">
              <div className="inline-flex items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.24em] text-blue-100/80 lg:justify-start">
                <span className="font-semibold">Beta</span>
                <span>Access window open</span>
              </div>

              <div className="space-y-6">
                <div className="space-y-3">
                  <p className="text-sm uppercase tracking-[0.35em] text-blue-200/70">Welcome</p>
                  <h1 className="text-4xl font-semibold leading-tight text-white sm:text-5xl lg:text-6xl">
                    Build, deploy, and govern intelligent agents with confidence.
                  </h1>
                </div>
                <p className="text-base text-blue-100/90 sm:text-lg">
                  Agent Foundry brings LangGraph-native orchestration, policy controls, and
                  cross-domain tooling into a single workspace. Launch the console to start crafting
                  production-ready agents.
                </p>
              </div>

              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <Button
                  size="lg"
                  className="h-14 px-8 text-base font-semibold shadow-2xl shadow-blue-600/40"
                  asChild
                >
                  <Link href="/login">
                    Launch the console
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="ghost"
                  className="h-14 px-8 text-base text-blue-100 hover:bg-white/10"
                  asChild
                >
                  <Link href="https://docs.agentfoundry.ai" target="_blank">
                    Review platform brief
                  </Link>
                </Button>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left backdrop-blur"
                  >
                    <p className="text-xs uppercase tracking-[0.2em] text-blue-200/70">
                      {stat.label}
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-white">{stat.value}</p>
                    <p className="text-xs text-blue-100/80">{stat.caption}</p>
                  </div>
                ))}
              </div>

              <div className="space-y-3 text-left">
                <p className="text-xs uppercase tracking-[0.32em] text-blue-200/70">
                  Focused capabilities
                </p>
                <div className="grid gap-3">
                  {highlights.map(({ title, description, icon: Icon }) => (
                    <div
                      key={title}
                      className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-4"
                    >
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 text-blue-200">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold text-white">{title}</p>
                        <p className="text-sm text-blue-100/85">{description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="relative flex items-center justify-center">
              <div
                className="absolute inset-0 -z-10 opacity-70 blur-3xl"
                style={{
                  background:
                    'radial-gradient(circle at 30% 20%, rgba(58,129,246,0.4), transparent 45%), radial-gradient(circle at 80% 0%, rgba(147,51,234,0.35), transparent 40%)',
                }}
              />
              <div className="w-full max-w-xl rounded-[32px] border border-white/15 bg-black/50 p-8 shadow-2xl backdrop-blur-2xl">
                <div className="flex flex-col gap-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.35em] text-blue-200/70">
                        Mission Control
                      </p>
                      <h2 className="mt-2 text-2xl font-semibold text-white">
                        Foundry Admin Assistant
                      </h2>
                      <p className="text-sm text-blue-100/80">
                        Ask about orgs, domains, and real-time system health.
                      </p>
                    </div>
                    <AtomIndicator isSpeaking className="w-32 h-32" size="lg" />
                  </div>

                  <div className="space-y-4">
                    {assistantUpdates.map((update) => (
                      <div
                        key={update.label}
                        className="rounded-2xl border border-white/10 bg-white/5 p-4"
                      >
                        <div className="flex items-center justify-between text-sm font-medium text-white">
                          <span>{update.label}</span>
                          <Badge className="bg-blue-600/40 text-blue-100 hover:bg-blue-600/60">
                            {update.status}
                          </Badge>
                        </div>
                        <p className="mt-2 text-xs text-blue-100/80">{update.detail}</p>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-[#050914]/80 p-5">
                    <p className="text-sm font-medium text-blue-100">
                      “Need the governance playbook? I can walk you through policy enforcement,
                      LangGraph deployment, or start a new agent spec.”
                    </p>
                    <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-xs text-blue-200/70">
                      <span>Type / ask to begin</span>
                      <span>12 ms response · WS connected</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        <div className="mt-auto flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-6 text-xs text-blue-200/70 sm:flex-row">
          <div className="flex items-center gap-3">
            <QuantLogo className="h-6 opacity-70" />
            <span>Powered by Quant · secure cloud perimeter enforced</span>
          </div>
          <p>© {new Date().getFullYear()} Agent Foundry · LangGraph native</p>
        </div>
      </div>
    </div>
  );
}
