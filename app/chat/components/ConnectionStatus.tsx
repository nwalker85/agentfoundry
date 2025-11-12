'use client';

import { motion } from 'framer-motion';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { ConnectionStatus as ConnectionStatusType } from '@/lib/types/chat';
import { useChatStore } from '@/lib/stores/chat.store';

interface ConnectionStatusProps {
  status: ConnectionStatusType;
  latency?: number;
}

export function ConnectionStatus({ status, latency }: ConnectionStatusProps) {
  const { reconnectWebSocket } = useChatStore();
  
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: latency && latency > 0 ? `Connected (${latency}ms)` : 'Connected',
          color: 'text-green-600 dark:text-green-400',
          bgColor: 'bg-green-50 dark:bg-green-900/20',
          dotColor: 'bg-green-500',
          animate: false
        };
      case 'connecting':
        return {
          icon: RefreshCw,
          text: 'Connecting...',
          color: 'text-yellow-600 dark:text-yellow-400',
          bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
          dotColor: 'bg-yellow-500',
          animate: true
        };
      case 'reconnecting':
        return {
          icon: RefreshCw,
          text: 'Reconnecting...',
          color: 'text-yellow-600 dark:text-yellow-400',
          bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
          dotColor: 'bg-yellow-500',
          animate: true
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected',
          color: 'text-red-600 dark:text-red-400',
          bgColor: 'bg-red-50 dark:bg-red-900/20',
          dotColor: 'bg-red-500',
          animate: false
        };
    }
  };
  
  const config = getStatusConfig();
  const Icon = config.icon;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor}`}
    >
      <motion.div
        animate={config.animate ? { rotate: 360 } : {}}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <Icon className={`w-4 h-4 ${config.color}`} />
      </motion.div>
      <span className={`text-xs font-medium ${config.color}`}>
        {config.text}
      </span>
      {status === 'disconnected' && (
        <button
          onClick={reconnectWebSocket}
          className={`text-xs underline hover:no-underline ${config.color}`}
          title="Retry connection"
        >
          Retry
        </button>
      )}
    </motion.div>
  );
}
