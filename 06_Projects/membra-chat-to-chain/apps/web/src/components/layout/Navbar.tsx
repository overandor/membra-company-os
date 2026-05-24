"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, PenTool, BookOpen, Shield } from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/studio", label: "Studio", icon: PenTool },
  { href: "/ledger", label: "Ledger", icon: BookOpen },
  { href: "/support", label: "Support", icon: Shield },
];

export function Navbar() {
  const pathname = usePathname();
  return (
    <nav className="border-b border-white/5 bg-background/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/dashboard" className="flex items-center gap-2">
            <span className="text-xl font-bold text-gradient">MEMBRA</span>
          </Link>
          <div className="flex items-center gap-1">
            {nav.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    active
                      ? "bg-primary-orange/10 text-primary-orange"
                      : "text-text-muted hover:text-text-primary hover:bg-white/5"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </div>
          <div className="text-xs text-text-muted">Devnet</div>
        </div>
      </div>
    </nav>
  );
}
