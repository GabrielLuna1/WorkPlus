"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Columns, Database, Hexagon, Calendar, FileText, LineChart, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Sidebar() {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const links = [
    { href: "/", label: "Discovery", icon: LayoutDashboard },
    { href: "/hub", label: "Copilot", icon: Bot },
    { href: "/kanban", label: "Pipeline", icon: Columns },
    { href: "/vagas", label: "Vagas", icon: Database },
    { href: "/curriculo", label: "Currículo", icon: FileText },
    { href: "/analytics", label: "Analytics", icon: LineChart },
    { href: "/calendar", label: "Calendário", icon: Calendar },
  ];

  return (
    <aside className="w-[280px] bg-canvas border-r border-hairline h-screen flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center border border-[#F3E5AB]/20 shadow-[0_0_15px_rgba(212,175,55,0.3)]">
          <Hexagon className="w-6 h-6 text-[#FFF6D3] fill-black/20" />
        </div>
        <h1 className="font-heading font-semibold text-xl metallic-gradient">
          WorkHunter
        </h1>
      </div>
      
      <div className="px-4 mt-6">
        <p className="text-xs font-semibold text-ink-subtle uppercase tracking-wider mb-4 px-2">
          Menu Principal
        </p>
        <nav className="space-y-1">
          {links.map((link) => {
            const isActive = mounted && pathname === link.href;
            return (
              <Link 
                key={link.href}
                href={link.href} 
                className={cn(
                  "flex items-center gap-3 px-4 py-2.5 rounded-lg text-[15px] font-medium transition-colors",
                  isActive 
                    ? "bg-surface text-ink nav-active" 
                    : "text-ink-muted hover:text-ink hover:bg-surface-2"
                )}
              >
                <link.icon className={cn("w-5 h-5", isActive ? "text-accent" : "")} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 mt-auto">
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-surface border border-hairline group hover:border-hairline-strong transition-colors cursor-default">
          <Database className="w-5 h-5 text-ink-subtle group-hover:text-ink transition-colors" />
          <div className="flex-1">
            <p className="text-sm font-medium text-ink">MongoDB</p>
            <p className="text-xs text-ink-subtle">Local Server</p>
          </div>
          <div className="w-2 h-2 rounded-full bg-success animate-pulse-dot" />
        </div>
      </div>
    </aside>
  );
}
