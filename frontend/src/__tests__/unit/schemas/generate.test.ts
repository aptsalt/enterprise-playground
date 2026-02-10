import { describe, it, expect } from "vitest";
import { StreamEventSchema, GenerateRequestSchema } from "@/lib/schemas/generate";

describe("GenerateRequestSchema", () => {
  it("parses valid request with defaults", () => {
    const result = GenerateRequestSchema.parse({ prompt: "test prompt" });
    expect(result.prompt).toBe("test prompt");
    expect(result.style).toBe("default");
    expect(result.workflow_id).toBeNull();
    expect(result.force_generate).toBe(false);
  });

  it("rejects empty prompt", () => {
    expect(() => GenerateRequestSchema.parse({ prompt: "" })).toThrow();
  });

  it("accepts full request", () => {
    const result = GenerateRequestSchema.parse({
      prompt: "banking dashboard",
      style: "banking",
      workflow_id: "wf-123",
      force_generate: true,
    });
    expect(result.style).toBe("banking");
    expect(result.workflow_id).toBe("wf-123");
    expect(result.force_generate).toBe(true);
  });
});

describe("StreamEventSchema", () => {
  it("parses status event", () => {
    const result = StreamEventSchema.parse({ type: "status", message: "Starting generation" });
    expect(result.type).toBe("status");
  });

  it("parses chunk event", () => {
    const result = StreamEventSchema.parse({ type: "chunk", content: "<div>" });
    expect(result.type).toBe("chunk");
    if (result.type === "chunk") expect(result.content).toBe("<div>");
  });

  it("parses rag event", () => {
    const result = StreamEventSchema.parse({ type: "rag", chunks: 3, preview: ["a", "b"] });
    expect(result.type).toBe("rag");
  });

  it("parses cache_hit event", () => {
    const result = StreamEventSchema.parse({ type: "cache_hit", playground_id: "pg-123" });
    expect(result.type).toBe("cache_hit");
  });

  it("parses done event", () => {
    const result = StreamEventSchema.parse({ type: "done", playground_id: "pg-456", size: 1024 });
    expect(result.type).toBe("done");
  });

  it("parses error event", () => {
    const result = StreamEventSchema.parse({ type: "error", message: "Failed" });
    expect(result.type).toBe("error");
  });

  it("rejects unknown event type", () => {
    expect(() => StreamEventSchema.parse({ type: "unknown", data: "x" })).toThrow();
  });
});
