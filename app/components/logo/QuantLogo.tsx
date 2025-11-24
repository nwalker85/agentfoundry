/**
 * Quant Platform Logo Component
 * Placeholder - replace with actual Quant logo SVG
 */

interface QuantLogoProps {
  className?: string;
}

export function QuantLogo({ className = 'h-8 w-auto' }: QuantLogoProps) {
  return (
    <svg className={className} viewBox="0 0 120 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Q Symbol */}
      <circle cx="16" cy="16" r="12" stroke="url(#quantGradient)" strokeWidth="2.5" fill="none" />
      <path
        d="M16 28 L24 20"
        stroke="url(#quantGradient)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* QUANT Text */}
      <text
        x="36"
        y="22"
        fill="white"
        fontSize="18"
        fontWeight="700"
        fontFamily="system-ui, -apple-system, sans-serif"
      >
        QUANT
      </text>

      <defs>
        <linearGradient id="quantGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#3B82F6" />
        </linearGradient>
      </defs>
    </svg>
  );
}

/**
 * Note: To use the actual Quant logo:
 * 1. Download logo from https://quant.ai or request from Quant team
 * 2. Place in public/logos/quant-logo.svg
 * 3. Update this component to use:
 *    <img src="/logos/quant-logo.svg" alt="Quant" className={className} />
 */
