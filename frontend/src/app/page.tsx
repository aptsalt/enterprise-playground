"use client";

import { TopNav } from "@/components/layout/top-nav";
import { TabBar } from "@/components/layout/tab-bar";
import { TabContent } from "@/components/layout/tab-content";
import { useHealth } from "@/lib/hooks/use-health";
import { useWebVitals } from "@/lib/hooks/use-web-vitals";

export default function Home() {
  useHealth();
  useWebVitals();

  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <TabBar />
      <main className="flex-1 overflow-auto" role="main">
        <TabContent />
      </main>
    </div>
  );
}
