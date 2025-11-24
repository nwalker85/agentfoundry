'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface AtomIndicatorProps {
  isSpeaking?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function AtomIndicator({ isSpeaking = false, className, size = 'md' }: AtomIndicatorProps) {
  // Track visual state with decay - stays true for 1 second after isSpeaking becomes false
  const [showSpeaking, setShowSpeaking] = useState(false);

  useEffect(() => {
    if (isSpeaking) {
      // Immediately show speaking state
      setShowSpeaking(true);
    } else {
      // Delay turning off by 1 second for smooth fadeout
      const timer = setTimeout(() => {
        setShowSpeaking(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [isSpeaking]);
  const sizeConfig = {
    sm: { container: 'w-8 h-8', nucleus: 'w-2 h-2', electron: 'w-1.5 h-1.5' },
    md: { container: 'w-12 h-12', nucleus: 'w-3 h-3', electron: 'w-2 h-2' },
    lg: { container: 'w-16 h-16', nucleus: 'w-4 h-4', electron: 'w-2.5 h-2.5' },
  };

  const config = sizeConfig[size];

  // Simple two-state styling: normal or speaking (blue glow) with smooth transitions
  const speed = showSpeaking ? 4 : 8;

  // Use custom className size if provided, otherwise use config size
  const containerClass = className?.includes('w-') ? className : cn(config.container, className);

  return (
    <div className={cn('relative flex items-center justify-center', containerClass)}>
      {/* Central Nucleus */}
      <motion.div
        className={cn('absolute rounded-full z-10', config.nucleus)}
        animate={{
          backgroundColor: showSpeaking ? 'rgb(59, 130, 246)' : 'rgb(156, 163, 175)', // blue-500 : gray-400
          scale: showSpeaking ? [1, 1.15, 1] : 1,
          boxShadow: showSpeaking
            ? [
                '0 0 15px rgba(59, 130, 246, 0.6)',
                '0 0 25px rgba(59, 130, 246, 0.8)',
                '0 0 15px rgba(59, 130, 246, 0.6)',
              ]
            : '0 0 0px rgba(0, 0, 0, 0)',
        }}
        transition={{
          backgroundColor: { duration: 0.8, ease: 'easeInOut' },
          scale: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
          boxShadow: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
        }}
      />

      {/* Orbit 1 - Horizontal */}
      <motion.div
        className="absolute border rounded-full"
        style={{
          width: '100%',
          height: '40%',
        }}
        animate={{
          rotateX: 360,
          borderColor: showSpeaking ? 'rgba(147, 197, 253, 0.4)' : 'rgba(209, 213, 219, 0.2)', // blue-300/40 : gray-300/20
        }}
        transition={{
          rotateX: { duration: speed, repeat: Infinity, ease: 'linear' },
          borderColor: { duration: 0.8, ease: 'easeInOut' },
        }}
      >
        {/* Electron 1 */}
        <motion.div
          className={cn('absolute rounded-full', config.electron)}
          style={{
            top: '50%',
            left: '0%',
            marginTop: `-${size === 'sm' ? '3' : size === 'md' ? '4' : '5'}px`,
            marginLeft: `-${size === 'sm' ? '3' : size === 'md' ? '4' : '5'}px`,
          }}
          animate={{
            backgroundColor: showSpeaking ? 'rgb(96, 165, 250)' : 'rgb(156, 163, 175)', // blue-400 : gray-400
          }}
          transition={{
            backgroundColor: { duration: 0.8, ease: 'easeInOut' },
          }}
        />
      </motion.div>

      {/* Orbit 2 - Diagonal */}
      <motion.div
        className="absolute border rounded-full"
        style={{
          width: '100%',
          height: '40%',
          transform: 'rotateZ(60deg)',
        }}
        animate={{
          rotateX: 360,
          borderColor: showSpeaking ? 'rgba(147, 197, 253, 0.4)' : 'rgba(209, 213, 219, 0.2)',
        }}
        transition={{
          rotateX: { duration: speed, repeat: Infinity, ease: 'linear' },
          borderColor: { duration: 0.8, ease: 'easeInOut' },
        }}
      >
        {/* Electron 2 */}
        <motion.div
          className={cn('absolute rounded-full', config.electron)}
          style={{
            top: '50%',
            left: '0%',
            marginTop: `-${size === 'sm' ? '3' : size === 'md' ? '4' : '5'}px`,
            marginLeft: `-${size === 'sm' ? '3' : size === 'md' ? '4' : '5'}px`,
          }}
          animate={{
            backgroundColor: showSpeaking ? 'rgb(96, 165, 250)' : 'rgb(156, 163, 175)',
          }}
          transition={{
            backgroundColor: { duration: 0.8, ease: 'easeInOut' },
          }}
        />
      </motion.div>

      {/* Orbit 3 - Diagonal opposite */}
      <motion.div
        className="absolute border rounded-full"
        style={{
          width: '100%',
          height: '40%',
          transform: 'rotateZ(-60deg)',
        }}
        animate={{
          rotateX: 360,
          borderColor: showSpeaking ? 'rgba(147, 197, 253, 0.4)' : 'rgba(209, 213, 219, 0.2)',
        }}
        transition={{
          rotateX: { duration: speed, repeat: Infinity, ease: 'linear' },
          borderColor: { duration: 0.8, ease: 'easeInOut' },
        }}
      >
        {/* Electron 3 */}
        <motion.div
          className={cn('absolute rounded-full', config.electron)}
          style={{
            top: '50%',
            left: '0%',
            marginTop: `-${size === 'sm' ? '3' : size === 'md' ? '4' : '5'}px`,
            marginLeft: `-${size === 'sm' ? '3' : size === 'md' ? '4' : '5'}px`,
          }}
          animate={{
            backgroundColor: showSpeaking ? 'rgb(96, 165, 250)' : 'rgb(156, 163, 175)',
          }}
          transition={{
            backgroundColor: { duration: 0.8, ease: 'easeInOut' },
          }}
        />
      </motion.div>

      {/* Outer glow - always present but fades in/out */}
      <motion.div
        className="absolute inset-0 rounded-full pointer-events-none"
        animate={{
          opacity: showSpeaking ? 1 : 0,
          boxShadow: showSpeaking
            ? [
                '0 0 30px rgba(59, 130, 246, 0.4)',
                '0 0 50px rgba(59, 130, 246, 0.6)',
                '0 0 30px rgba(59, 130, 246, 0.4)',
              ]
            : '0 0 0px rgba(59, 130, 246, 0)',
        }}
        transition={{
          opacity: { duration: 0.8, ease: 'easeInOut' },
          boxShadow: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
        }}
      />
    </div>
  );
}
