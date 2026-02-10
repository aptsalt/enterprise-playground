"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatBytes, formatDate } from "@/lib/utils/format";
import type { Playground } from "@/lib/schemas/playground";

const cardVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.25, ease: "easeOut" } },
};

export function PlaygroundCard({ playground, index = 0 }: { playground: Playground; index?: number }) {
  const pg = playground;

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      transition={{ delay: index * 0.03 }}
    >
      <Card className="group overflow-hidden transition-colors hover:border-primary/50">
        <div className="relative aspect-video overflow-hidden bg-muted">
          <iframe
            src={`/playground/${pg.id}`}
            title={`Preview: ${pg.prompt}`}
            className="pointer-events-none h-[286%] w-[286%] origin-top-left scale-[0.35]"
            sandbox="allow-scripts"
            loading="lazy"
            aria-hidden="true"
          />
          <a
            href={`/playground/${pg.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
            aria-label={`Open playground: ${pg.prompt}`}
          >
            <span className="text-sm font-medium text-white">Open</span>
          </a>
        </div>
        <CardContent className="p-3">
          <p className="mb-2 line-clamp-2 text-xs">{pg.prompt}</p>
          <div className="flex flex-wrap items-center gap-1.5" role="list" aria-label="Playground metadata">
            {pg.model && (
              <Badge variant="outline" className="text-[10px]">{pg.model}</Badge>
            )}
            {pg.size && (
              <Badge variant="secondary" className="text-[10px]">{formatBytes(pg.size)}</Badge>
            )}
            {pg.source === "cache" && (
              <Badge className="bg-blue-500/20 text-blue-400 text-[10px]">CACHE</Badge>
            )}
            {pg.rag_chunks && pg.rag_chunks > 0 && (
              <Badge className="bg-cyan-500/20 text-cyan-400 text-[10px]">RAG:{pg.rag_chunks}</Badge>
            )}
          </div>
          {pg.created && (
            <p className="mt-1.5 text-[10px] text-muted-foreground">{formatDate(pg.created)}</p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
