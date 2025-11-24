'use client';

import { ChevronDown, Clock, User, CheckCircle2, GitCommit, Rocket } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface DeploymentVersion {
  version: string;
  deployedBy: string;
  deployedAt: string;
  environment: 'dev' | 'staging' | 'prod';
  commitHash?: string;
  isCurrent?: boolean;
  isDeployed?: boolean;
  versionId?: string; // The actual version ID for API calls
}

interface VersionSelectorProps {
  currentVersion?: string;
  versions: DeploymentVersion[];
  onSelectVersion: (version: DeploymentVersion) => void;
  onDeployVersion?: (version: DeploymentVersion) => void;
  disabled?: boolean;
}

export function VersionSelector({
  currentVersion = 'v1.0.0',
  versions,
  onSelectVersion,
  onDeployVersion,
  disabled = false,
}: VersionSelectorProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) {
      const diffInMins = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
      return `${diffInMins} min${diffInMins !== 1 ? 's' : ''} ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
      });
    }
  };

  const getEnvironmentColor = (env: string) => {
    switch (env) {
      case 'prod':
        return 'text-green-500';
      case 'staging':
        return 'text-yellow-500';
      case 'dev':
        return 'text-blue-500';
      default:
        return 'text-fg-2';
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          disabled={disabled}
          className={cn(
            'gap-2 h-9 min-w-[140px] justify-between',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <div className="flex items-center gap-2">
            <GitCommit className="w-4 h-4" />
            <span className="font-mono text-sm">{currentVersion}</span>
          </div>
          <ChevronDown className="w-3.5 h-3.5 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[400px]">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Deployment History</span>
          <Badge variant="secondary" className="text-xs">
            {versions.length} version{versions.length !== 1 ? 's' : ''}
          </Badge>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {versions.length === 0 ? (
          <div className="px-2 py-8 text-center text-sm text-fg-2">
            No deployment history available
          </div>
        ) : (
          <div className="max-h-[400px] overflow-y-auto">
            {versions.map((version, index) => (
              <DropdownMenuItem
                key={index}
                onClick={() => onSelectVersion(version)}
                className={cn(
                  'flex flex-col items-start gap-2 p-3 cursor-pointer',
                  version.isCurrent && 'bg-blue-600/10',
                  version.isDeployed && 'bg-green-600/10'
                )}
              >
                {/* Version and Badges */}
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-fg-0">{version.version}</span>
                    {version.isDeployed && (
                      <Badge variant="secondary" className="gap-1 text-xs bg-green-600/20 text-green-400">
                        <Rocket className="w-3 h-3" />
                        Deployed
                      </Badge>
                    )}
                    {version.isCurrent && !version.isDeployed && (
                      <Badge variant="secondary" className="gap-1 text-xs">
                        <CheckCircle2 className="w-3 h-3" />
                        Current
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {onDeployVersion && !version.isDeployed && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeployVersion(version);
                        }}
                      >
                        <Rocket className="w-3 h-3 mr-1" />
                        Deploy
                      </Button>
                    )}
                    <Badge
                      variant="outline"
                      className={cn('text-xs', getEnvironmentColor(version.environment))}
                    >
                      {version.environment}
                    </Badge>
                  </div>
                </div>

                {/* Created By */}
                <div className="flex items-center gap-1.5 text-xs text-fg-2">
                  <User className="w-3 h-3" />
                  <span>{version.deployedBy}</span>
                </div>

                {/* Timestamp */}
                <div className="flex items-center gap-1.5 text-xs text-fg-2">
                  <Clock className="w-3 h-3" />
                  <span>{formatTimestamp(version.deployedAt)}</span>
                  <span className="text-fg-2/60">
                    ({new Date(version.deployedAt).toLocaleString()})
                  </span>
                </div>

                {/* Version ID (commit hash) */}
                {version.commitHash && (
                  <div className="flex items-center gap-1.5 text-xs text-fg-2">
                    <GitCommit className="w-3 h-3" />
                    <code className="font-mono">{version.commitHash.substring(0, 7)}</code>
                  </div>
                )}
              </DropdownMenuItem>
            ))}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
