"use client";

import { useCallback, useRef } from "react";
import { useDashboardStore, type TabId } from "@/lib/store/dashboard-store";
import { cn } from "@/lib/utils";

const TABS: { id: TabId; label: string }[] = [
  { id: "generate", label: "Generate" },
  { id: "gallery", label: "Gallery" },
  { id: "pipeline", label: "Pipeline" },
  { id: "data-rag", label: "Data & RAG" },
  { id: "metrics", label: "ML Metrics" },
  { id: "observatory", label: "Observatory" },
  { id: "agent", label: "Agent" },
];

export function TabBar() {
  const activeTab = useDashboardStore((s) => s.activeTab);
  const setActiveTab = useDashboardStore((s) => s.setActiveTab);
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIdx = TABS.findIndex((t) => t.id === activeTab);
      let nextIdx = currentIdx;

      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextIdx = (currentIdx + 1) % TABS.length;
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextIdx = (currentIdx - 1 + TABS.length) % TABS.length;
      } else if (e.key === "Home") {
        e.preventDefault();
        nextIdx = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        nextIdx = TABS.length - 1;
      }

      if (nextIdx !== currentIdx) {
        setActiveTab(TABS[nextIdx].id);
        tabRefs.current.get(TABS[nextIdx].id)?.focus();
      }
    },
    [activeTab, setActiveTab],
  );

  return (
    <nav
      className="flex items-center gap-1 overflow-x-auto border-b border-border bg-card/50 px-4 py-1"
      role="tablist"
      aria-label="Dashboard tabs"
      onKeyDown={handleKeyDown}
    >
      {TABS.map((tab) => (
        <button
          key={tab.id}
          ref={(el) => {
            if (el) tabRefs.current.set(tab.id, el);
          }}
          onClick={() => setActiveTab(tab.id)}
          role="tab"
          id={`tab-${tab.id}`}
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          data-tab={tab.id}
          className={cn(
            "flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-ring",
            activeTab === tab.id
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
          )}
        >
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
