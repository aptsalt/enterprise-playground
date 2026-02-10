"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { PlaygroundListSchema } from "@/lib/schemas/playground";
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
import { formatBytes, formatDate } from "@/lib/utils/format";

export function RecentTable() {
  const { data: playgrounds } = useApiQuery(
    ["playgrounds"],
    "/api/playgrounds",
    PlaygroundListSchema,
    { refetchInterval: 15_000 },
  );

  const recent = (playgrounds ?? []).slice(0, 15);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Recent Playgrounds</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-72">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[40%]">Prompt</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>RAG</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((pg) => (
                <TableRow key={pg.id}>
                  <TableCell className="max-w-[300px] truncate text-xs">
                    <a
                      href={`/playground/${pg.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-indigo-400"
                    >
                      {pg.prompt}
                    </a>
                  </TableCell>
                  <TableCell className="text-xs">{pg.model ?? "-"}</TableCell>
                  <TableCell className="text-xs font-mono">
                    {pg.size ? formatBytes(pg.size) : "-"}
                  </TableCell>
                  <TableCell>
                    {pg.source === "cache" ? (
                      <Badge variant="secondary" className="text-xs">CACHE</Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs">GEN</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-xs">
                    {pg.rag_chunks ? (
                      <Badge variant="outline" className="border-cyan-500/50 text-cyan-400 text-xs">
                        RAG:{pg.rag_chunks}
                      </Badge>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {pg.created ? formatDate(pg.created) : "-"}
                  </TableCell>
                </TableRow>
              ))}
              {recent.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-xs text-muted-foreground">
                    No playgrounds yet. Generate one above!
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
