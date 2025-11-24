/**
 * Agent Foundry Logo Component
 * Hexagonal forge symbol with gradient
 */

interface AgentFoundryLogoProps {
  className?: string;
}

export function AgentFoundryLogo({ className = 'h-8 w-8' }: AgentFoundryLogoProps) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Hexagon Frame */}
      <path
        d="M24 2L42 14V34L24 46L6 34V14L24 2Z"
        stroke="url(#gradient1)"
        strokeWidth="2"
        fill="none"
      />

      {/* Inner Forge Symbol */}
      <path d="M24 12L32 18V30L24 36L16 30V18L24 12Z" fill="url(#gradient2)" />

      {/* Hammer/Anvil Icon (representing forge) */}
      <path d="M20 24H28M24 20V28" stroke="white" strokeWidth="2.5" strokeLinecap="round" />

      {/* Spark effect */}
      <circle cx="28" cy="20" r="1.5" fill="#60A5FA" opacity="0.8" />
      <circle cx="20" cy="28" r="1.5" fill="#8B5CF6" opacity="0.8" />

      <defs>
        <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#8B5CF6" />
        </linearGradient>
        <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.3" />
        </linearGradient>
      </defs>
    </svg>
  );
}
