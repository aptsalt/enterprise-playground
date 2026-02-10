"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { z } from "zod";

export function useApiQuery<T>(
  key: string[],
  path: string,
  schema: z.ZodType<T>,
  options?: Partial<UseQueryOptions<T>>,
) {
  return useQuery<T>({
    queryKey: key,
    queryFn: async () => {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = await res.json();
      return schema.parse(json);
    },
    ...options,
  });
}
