/**
 * Lightweight frontend OpenTelemetry-compatible tracing.
 * Captures performance spans and propagates trace context to backend.
 */

interface Span {
  name: string;
  traceId: string;
  spanId: string;
  startTime: number;
  endTime?: number;
  attributes: Record<string, string | number | boolean>;
  status: "ok" | "error" | "unset";
}

const generateId = (length: number): string => {
  const chars = "0123456789abcdef";
  let result = "";
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  for (const byte of array) {
    result += chars[byte % 16];
  }
  return result;
};

const spans: Span[] = [];

export function startSpan(name: string, attributes: Record<string, string | number | boolean> = {}): Span {
  const span: Span = {
    name,
    traceId: generateId(32),
    spanId: generateId(16),
    startTime: performance.now(),
    attributes,
    status: "unset",
  };
  spans.push(span);

  if (spans.length > 100) {
    spans.splice(0, spans.length - 100);
  }

  return span;
}

export function endSpan(span: Span, status: "ok" | "error" = "ok"): void {
  span.endTime = performance.now();
  span.status = status;
  span.attributes["duration_ms"] = Math.round(span.endTime - span.startTime);
}

export function getTraceHeaders(span: Span): Record<string, string> {
  return {
    traceparent: `00-${span.traceId}-${span.spanId}-01`,
    "x-trace-id": span.traceId,
  };
}

export function getRecentSpans(limit: number = 20): Span[] {
  return spans.slice(-limit);
}

export function tracedFetch(
  url: string,
  init?: RequestInit,
): Promise<Response> {
  const span = startSpan("fetch", { url, method: init?.method ?? "GET" });
  const headers = new Headers(init?.headers);
  const traceHeaders = getTraceHeaders(span);
  for (const [key, value] of Object.entries(traceHeaders)) {
    headers.set(key, value);
  }

  return fetch(url, { ...init, headers })
    .then((res) => {
      span.attributes["http.status_code"] = res.status;
      endSpan(span, res.ok ? "ok" : "error");
      return res;
    })
    .catch((err) => {
      span.attributes["error"] = (err as Error).message;
      endSpan(span, "error");
      throw err;
    });
}
