import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function truncateAddress(address: string, chars = 4): string {
  if (!address) return '';
  return `${address.slice(0, chars)}...${address.slice(-chars)}`;
}

export function formatLamports(lamports: number): string {
  return (lamports / 1_000_000_000).toFixed(4);
}

export function formatUSD(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
}

export function generateArtifactId(): string {
  const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
  const rand = Math.random().toString(36).slice(2, 8).toUpperCase();
  return `MEMBRA-ART-${ts}-${rand}`;
}

export function sha256Hash(input: string): string {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  return Array.from(new Uint8Array(data))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}
