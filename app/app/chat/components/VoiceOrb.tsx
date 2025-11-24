'use client';

import { motion } from 'framer-motion';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export type VoiceOrbState = 'idle' | 'listening' | 'speaking' | 'processing' | 'disabled';

interface VoiceOrbProps {
  state: VoiceOrbState;
  audioLevel?: number; // 0-1 for visualizing audio input
  onClick?: () => void;
  className?: string;
}

export function VoiceOrb({ state, audioLevel = 0, onClick, className }: VoiceOrbProps) {
  const isInteractive = state !== 'disabled' && onClick;

  // Calculate scale based on audio level
  const scale = state === 'listening' || state === 'speaking' ? 1 + audioLevel * 0.3 : 1;

  // Different visual states
  const stateConfig = {
    idle: {
      gradient: 'from-blue-500/20 via-purple-500/20 to-pink-500/20',
      ring: 'ring-blue-500/30',
      glow: 'shadow-blue-500/20',
      icon: Mic,
      iconColor: 'text-blue-400',
    },
    listening: {
      gradient: 'from-green-500/30 via-emerald-500/30 to-teal-500/30',
      ring: 'ring-green-500/50',
      glow: 'shadow-green-500/40',
      icon: Mic,
      iconColor: 'text-green-400',
    },
    speaking: {
      gradient: 'from-purple-500/30 via-pink-500/30 to-rose-500/30',
      ring: 'ring-purple-500/50',
      glow: 'shadow-purple-500/40',
      icon: Mic,
      iconColor: 'text-purple-400',
    },
    processing: {
      gradient: 'from-yellow-500/30 via-orange-500/30 to-amber-500/30',
      ring: 'ring-yellow-500/50',
      glow: 'shadow-yellow-500/40',
      icon: Loader2,
      iconColor: 'text-yellow-400',
    },
    disabled: {
      gradient: 'from-gray-500/10 via-gray-500/10 to-gray-500/10',
      ring: 'ring-gray-500/20',
      glow: 'shadow-gray-500/10',
      icon: MicOff,
      iconColor: 'text-gray-500',
    },
  };

  const config = stateConfig[state];
  const IconComponent = config.icon;

  return (
    <div className={cn('relative flex items-center justify-center', className)}>
      {/* Outer glow rings - animated */}
      <motion.div
        className="absolute inset-0"
        animate={{
          scale: [1, 1.2, 1],
          opacity:
            state === 'listening' || state === 'speaking' ? [0.5, 0.8, 0.5] : [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <div
          className={cn(
            'w-full h-full rounded-full blur-3xl',
            `bg-gradient-to-br ${config.gradient}`
          )}
        />
      </motion.div>

      {/* Middle ring */}
      <motion.div
        className="absolute inset-4"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.4, 0.6, 0.4],
        }}
        transition={{
          duration: 1.5,
          delay: 0.2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <div
          className={cn(
            'w-full h-full rounded-full blur-2xl',
            `bg-gradient-to-br ${config.gradient}`
          )}
        />
      </motion.div>

      {/* Main orb */}
      <motion.button
        onClick={isInteractive ? onClick : undefined}
        disabled={!isInteractive}
        className={cn(
          'relative z-10 w-64 h-64 rounded-full',
          'backdrop-blur-xl bg-gradient-to-br',
          config.gradient,
          'border border-white/20',
          'shadow-2xl',
          config.glow,
          'transition-all duration-300',
          isInteractive && 'cursor-pointer hover:scale-105 active:scale-95',
          !isInteractive && 'cursor-default'
        )}
        animate={{
          scale: scale,
        }}
        transition={{
          type: 'spring',
          stiffness: 300,
          damping: 20,
        }}
      >
        {/* Glossy overlay */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-white/20 to-transparent" />

        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            animate={state === 'processing' ? { rotate: 360 } : {}}
            transition={
              state === 'processing' ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}
            }
          >
            <IconComponent className={cn('w-24 h-24', config.iconColor, 'drop-shadow-lg')} />
          </motion.div>
        </div>

        {/* Animated particles for active states */}
        {(state === 'listening' || state === 'speaking') && (
          <>
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 rounded-full bg-white/60"
                style={{
                  top: '50%',
                  left: '50%',
                }}
                animate={{
                  x: [0, Math.cos((i / 8) * Math.PI * 2) * 100],
                  y: [0, Math.sin((i / 8) * Math.PI * 2) * 100],
                  opacity: [0.6, 0],
                  scale: [1, 0],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: 'easeOut',
                }}
              />
            ))}
          </>
        )}
      </motion.button>

      {/* Audio level indicator rings */}
      {(state === 'listening' || state === 'speaking') && audioLevel > 0 && (
        <>
          {[1, 2, 3].map((ring) => (
            <motion.div
              key={ring}
              className={cn(
                'absolute rounded-full border-2',
                state === 'listening' ? 'border-green-400/40' : 'border-purple-400/40'
              )}
              style={{
                width: `${64 + ring * 20}%`,
                height: `${64 + ring * 20}%`,
              }}
              animate={{
                scale: [1, 1 + audioLevel * 0.2],
                opacity: [0.4, 0.1],
              }}
              transition={{
                duration: 0.5,
                delay: ring * 0.1,
              }}
            />
          ))}
        </>
      )}
    </div>
  );
}
