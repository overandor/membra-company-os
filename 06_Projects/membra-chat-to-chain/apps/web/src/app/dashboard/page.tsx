"use client";
import { MetricCard, StateMachine, StatusChip } from "@/components/ui";
export default function DashboardPage() {
  const machines = [
    {
      title: "Privacy Doctrine",
      steps: [
        { number: 1, label: "OPEN", status: "complete" as const },
        { number: 2, label: "ARMED", status: "complete" as const, decisive: true },
        { number: 3, label: "BLOCKED", status: "locked" as const },
      ],
    },
    {
      title: "Chain Commit",
      steps: [
        { number: 1, label: "DRAFT", status: "complete" as const },
        { number: 2, label: "SIGNED", status: "complete" as const, decisive: true },
        { number: 3, label: "CONFIRMED", status: "pending" as const },
      ],
    },
    {
      title: "Appraisal Engine",
      steps: [
        { number: 1, label: "IDLE", status: "complete" as const },
        { number: 2, label: "ASSESSING", status: "complete" as const, decisive: true },
        { number: 3, label: "APPROVED", status: "pending" as const },
        { number: 4, label: "DENIED", status: "locked" as const },
      ],
    },
  ];
  return (
    <div className="space-y-8">
      <div className="text-center py-8">
        <div className="flex justify-center gap-3 mb-4">
          <StatusChip status="active">MEMBRA STATUS: MANIFESTED, NOT MINTED</StatusChip>
          <StatusChip status="locked">MAINNET GATED</StatusChip>
        </div>
        <h1 className="text-4xl font-bold text-gradient mb-4">MEMBRA Chat-to-Chain</h1>
        <p className="text-text-muted max-w-3xl mx-auto text-lg">Human stream to chat labor to artifact to appraisal to proof to funding to Solana payout.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard label="MEMBRA Status" value="Manifested" sublabel="Not minted" variant="gold" />
        <MetricCard label="Mint Address" value="Not Created" sublabel="No live token yet" />
        <MetricCard label="Official Money" value="$0.00" sublabel="Until external settlement" />
        <MetricCard label="Signature" value="Required" sublabel="Human / multisig approval" variant="success" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {machines.map((m) => (
          <StateMachine key={m.title} title={m.title} steps={m.steps} />
        ))}
      </div>
    </div>
  );
}
