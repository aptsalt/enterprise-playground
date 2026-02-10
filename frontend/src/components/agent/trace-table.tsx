"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatMs, formatDate } from "@/lib/utils/format";
import type { Trace } from "@/lib/schemas/agent";

export function TraceTable({ traces }: { traces: Trace[] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Trace History</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-72">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead className="w-[30%]">Prompt</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Router</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Steps</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>RAG</TableHead>
                <TableHead>Cache</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {traces.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(t.started_at)}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate text-xs">{t.prompt}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-[10px]">{t.task_type ?? "-"}</Badge>
                  </TableCell>
                  <TableCell className="text-xs">{t.router_method ?? "-"}</TableCell>
                  <TableCell className="text-xs font-mono">{t.final_model ?? "-"}</TableCell>
                  <TableCell className="text-xs">{t.total_steps ?? 0}</TableCell>
                  <TableCell className="text-xs font-mono">
                    {formatMs(t.total_latency_ms ?? 0)}
                  </TableCell>
                  <TableCell className="text-xs">
                    {t.rag_chunks ? (
                      <Badge variant="outline" className="border-cyan-500/50 text-cyan-400 text-[10px]">
                        {t.rag_chunks}
                      </Badge>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell>
                    {t.cache_hit ? (
                      <Badge className="bg-blue-500/20 text-blue-400 text-[10px]">HIT</Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {traces.length === 0 && (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-xs text-muted-foreground">
                    No traces yet
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
