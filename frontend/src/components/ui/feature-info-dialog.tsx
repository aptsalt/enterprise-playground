"use client";

import { FEATURE_INFO } from "@/lib/data/feature-info";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface Props {
  featureId: string;
  children: React.ReactNode;
  className?: string;
}

export function FeatureInfoDialog({ featureId, children, className }: Props) {
  const info = FEATURE_INFO[featureId];

  if (!info) {
    return <>{children}</>;
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className={cn(
            "inline-flex items-center cursor-pointer rounded transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            className,
          )}
        >
          {children}
        </button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{info.title}</DialogTitle>
          <DialogDescription>{info.what}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm">
          <div>
            <h4 className="font-medium text-muted-foreground mb-1">How it works in this app</h4>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              {info.how.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="rounded-md border border-border bg-muted/30 p-3 space-y-2">
            <h4 className="font-medium text-muted-foreground">Example</h4>
            <p className="text-xs">
              <span className="font-medium">Scenario:</span> {info.example.scenario}
            </p>
            <p className="text-xs">
              <span className="font-medium">Result:</span> {info.example.result}
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
