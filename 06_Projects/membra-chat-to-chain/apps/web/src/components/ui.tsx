import React from 'react';
import { cn } from '@/lib/utils';

interface StatusChipProps {
  status: 'active' | 'pending' | 'locked' | 'complete';
  children: React.ReactNode;
}

export function StatusChip({ status, children }: StatusChipProps) {
  return (
    <span className={cn('status-chip', status)}>
      {children}
    </span>
  );
}

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({ children, className }: GlassCardProps) {
  return (
    <div className={cn('glass-card p-6', className)}>
      {children}
    </div>
  );
}

interface TerminalPanelProps {
  lines: { type: 'prompt' | 'output' | 'error'; text: string }[];
  className?: string;
}

export function TerminalPanel({ lines, className }: TerminalPanelProps) {
  return (
    <div className={cn('terminal-panel', className)}>
      {lines.map((line, i) => (
        <div key={i} className={line.type}>
          {line.type === 'prompt' && '$ '}
          {line.text}
        </div>
      ))}
    </div>
  );
}

interface StateStep {
  number: number;
  label: string;
  status: 'complete' | 'pending' | 'locked' | 'required';
  decisive?: boolean;
}

interface StateMachineProps {
  title: string;
  subtitle?: string;
  steps: StateStep[];
  className?: string;
}

export function StateMachine({ title, subtitle, steps, className }: StateMachineProps) {
  return (
    <GlassCard className={className}>
      <h3 className="font-semibold text-sm mb-1">{title}</h3>
      {subtitle && <p className="text-xs text-text-muted mb-4">{subtitle}</p>}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {steps.map((step, i) => (
          <React.Fragment key={step.label}>
            <div className={cn(
              "min-w-[120px] p-3 rounded-lg border text-center",
              step.decisive ? "bg-danger/10 border-danger/30" :
              step.status === 'complete' ? "bg-success/10 border-success/30" :
              "bg-background-100 border-white/5"
            )}>
              <span className="text-xs font-bold text-primary-orange">{step.number}</span>
              <p className="text-xs mt-1">{step.label}</p>
              <StatusChip status={step.status === 'complete' ? 'active' : step.status === 'locked' ? 'locked' : 'pending'}>
                {step.status}
              </StatusChip>
            </div>
            {i < steps.length - 1 && <span className="text-primary-orange/50 text-xs">→</span>}
          </React.Fragment>
        ))}
      </div>
    </GlassCard>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  sublabel?: string;
  variant?: 'default' | 'gold' | 'danger' | 'success';
}

export function MetricCard({ label, value, sublabel, variant = 'default' }: MetricCardProps) {
  return (
    <div className={cn(
      "p-4 rounded-lg border text-center",
      variant === 'gold' ? "bg-gradient-to-br from-primary-gold/10 to-primary-bronze/5 border-primary-gold/30" :
      variant === 'danger' ? "bg-danger/10 border-danger/20" :
      variant === 'success' ? "bg-success/10 border-success/20" :
      "bg-background-100 border-primary-orange/10"
    )}>
      <p className="text-xs text-text-muted mb-1">{label}</p>
      <p className={cn(
        "text-xl font-bold",
        variant === 'gold' ? "text-primary-gold" :
        variant === 'danger' ? "text-danger" :
        variant === 'success' ? "text-success" :
        "text-primary-orange"
      )}>{value}</p>
      {sublabel && <p className="text-xs text-text-muted mt-1">{sublabel}</p>}
    </div>
  );
}
