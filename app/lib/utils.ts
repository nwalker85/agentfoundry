/**
 * Utility Functions for Agent Foundry
 * ====================================
 *
 * Common utility functions used across the application.
 *
 * @module lib/utils
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge class names with Tailwind CSS conflict resolution.
 *
 * Combines clsx for conditional class names with tailwind-merge
 * to properly handle Tailwind CSS class conflicts.
 *
 * @param inputs - Class values to merge (strings, objects, arrays)
 * @returns Merged class name string with conflicts resolved
 *
 * @example
 * ```typescript
 * // Basic usage
 * cn('px-4 py-2', 'bg-blue-500')
 * // => 'px-4 py-2 bg-blue-500'
 *
 * // With conditionals
 * cn('base-class', isActive && 'active-class', { 'error': hasError })
 * // => 'base-class active-class' (if isActive is true)
 *
 * // Conflict resolution
 * cn('px-4', 'px-8')
 * // => 'px-8' (later value wins)
 * ```
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
