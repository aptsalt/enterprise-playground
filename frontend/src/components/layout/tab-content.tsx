"use client";

import { Suspense, lazy } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDashboardStore } from "@/lib/store/dashboard-store";
import { Skeleton } from "@/components/ui/skeleton";

const GenerateTab = lazy(() => import("@/components/tabs/generate-tab").then((m) => ({ default: m.GenerateTab })));
const GalleryTab = lazy(() => import("@/components/tabs/gallery-tab").then((m) => ({ default: m.GalleryTab })));
const PipelineTab = lazy(() => import("@/components/tabs/pipeline-tab").then((m) => ({ default: m.PipelineTab })));
const DataRagTab = lazy(() => import("@/components/tabs/data-rag-tab").then((m) => ({ default: m.DataRagTab })));
const MetricsTab = lazy(() => import("@/components/tabs/metrics-tab").then((m) => ({ default: m.MetricsTab })));
const ObservatoryTab = lazy(() => import("@/components/tabs/observatory-tab").then((m) => ({ default: m.ObservatoryTab })));
const AgentTab = lazy(() => import("@/components/tabs/agent-tab").then((m) => ({ default: m.AgentTab })));

function TabSkeleton() {
  return (
    <div className="space-y-4 p-6" role="status" aria-label="Loading tab content">
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <Skeleton className="h-64" />
      <span className="sr-only">Loading...</span>
    </div>
  );
}

const tabVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.2, ease: "easeOut" } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
};

const TAB_MAP = {
  generate: GenerateTab,
  gallery: GalleryTab,
  pipeline: PipelineTab,
  "data-rag": DataRagTab,
  metrics: MetricsTab,
  observatory: ObservatoryTab,
  agent: AgentTab,
} as const;

export function TabContent() {
  const activeTab = useDashboardStore((s) => s.activeTab);
  const ActiveComponent = TAB_MAP[activeTab];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={activeTab}
        variants={tabVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        role="tabpanel"
        id={`panel-${activeTab}`}
        aria-labelledby={`tab-${activeTab}`}
      >
        <Suspense fallback={<TabSkeleton />}>
          <ActiveComponent />
        </Suspense>
      </motion.div>
    </AnimatePresence>
  );
}
