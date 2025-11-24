'use client';

import { signIn, useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { Button } from '@/components/ui/button';
import { AgentFoundryLogo } from '@/components/logo/AgentFoundryLogo';
import { QuantLogo } from '@/components/logo/QuantLogo';
import { motion } from 'framer-motion';
import { Shield, ExternalLink } from 'lucide-react';

function LoginContent() {
  const { status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') || '/app';
  const error = searchParams.get('error');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (status === 'authenticated') {
      router.push(callbackUrl);
    }
  }, [status, router, callbackUrl]);

  const handleZitadelSignIn = async () => {
    setIsLoading(true);
    await signIn('zitadel', { callbackUrl });
  };

  const getErrorMessage = (errorCode: string | null) => {
    switch (errorCode) {
      case 'OAuthAccountNotLinked':
        return 'This account is already linked to another provider.';
      case 'OAuthCallback':
        return 'Authentication failed. Please try again.';
      case 'OAuthSignin':
        return 'Could not connect to identity provider. Is Zitadel configured?';
      case 'Configuration':
        return 'Server configuration error. Check ZITADEL_CLIENT_ID is set.';
      default:
        return errorCode ? 'Authentication failed. Please try again.' : null;
    }
  };

  const errorMessage = getErrorMessage(error);

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-0 via-bg-1 to-bg-0 flex items-center justify-center relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:4rem_4rem]" />

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-md mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="bg-bg-1/80 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl"
        >
          {/* Logo and Header */}
          <div className="flex flex-col items-center mb-8">
            <AgentFoundryLogo className="h-16 w-16 mb-4" />
            <h1 className="text-2xl font-bold text-fg-0">Agent Foundry</h1>
            <p className="text-sm text-fg-2 mt-1">Enterprise AI Agent Platform</p>
          </div>

          {/* Error Messages */}
          {errorMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-3 rounded-lg bg-red-950/30 border border-red-500/30 text-red-400 text-sm text-center"
            >
              {errorMessage}
            </motion.div>
          )}

          {/* SSO Login */}
          <div className="space-y-4">
            <Button
              onClick={handleZitadelSignIn}
              disabled={isLoading || status === 'loading'}
              className="w-full h-12 bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all duration-200 flex items-center justify-center gap-3"
            >
              <Shield className="h-5 w-5" />
              {isLoading ? 'Connecting...' : 'Sign in with SSO'}
            </Button>

            <p className="text-xs text-center text-fg-3">
              Secure authentication via Zitadel Identity Provider
            </p>
          </div>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-bg-1 px-3 text-fg-3">need access?</span>
            </div>
          </div>

          {/* Help Section */}
          <div className="text-center space-y-3">
            <p className="text-sm text-fg-2">
              Contact your administrator to request access
            </p>
            <a
              href="http://localhost:8082"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              Identity Admin Console
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-8 flex flex-col items-center"
        >
          <QuantLogo className="h-6 w-auto opacity-30 hover:opacity-50 transition-opacity" />
          <p className="text-xs text-fg-3 mt-2">Powered by Quant</p>
        </motion.div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-bg-0 flex items-center justify-center">
          <div className="text-fg-2">Loading...</div>
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
