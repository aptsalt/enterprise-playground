"use client";

import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  playgroundId: string;
  prompt: string;
}

type Rating = "up" | "down" | null;

export function FeedbackButtons({ playgroundId, prompt }: Props) {
  const [rating, setRating] = useState<Rating>(null);
  const [submitted, setSubmitted] = useState(false);

  const submit = useCallback(
    async (value: "up" | "down") => {
      setRating(value);
      setSubmitted(true);
      try {
        await fetch("/api/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ playground_id: playgroundId, rating: value, prompt }),
        });
      } catch {
        // Silently fail - feedback is non-critical
      }
    },
    [playgroundId, prompt],
  );

  if (submitted) {
    return (
      <span className="text-xs text-muted-foreground" role="status">
        {rating === "up" ? "Saved as positive example" : "Flagged for review"}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1" role="group" aria-label="Rate this generation">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => submit("up")}
        className={cn("h-7 w-7 p-0", rating === "up" && "text-green-400")}
        aria-label="Good generation - add to training data"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
          <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
        </svg>
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => submit("down")}
        className={cn("h-7 w-7 p-0", rating === "down" && "text-red-400")}
        aria-label="Bad generation - flag for review"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
          <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.106-1.79l-.05-.025A4 4 0 0011.057 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
        </svg>
      </Button>
    </div>
  );
}
