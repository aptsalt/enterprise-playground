import { describe, it, expect } from "vitest";
import { formatBytes, formatMs, formatDate, formatNumber } from "@/lib/utils/format";

describe("formatBytes", () => {
  it("formats 0 bytes", () => {
    expect(formatBytes(0)).toBe("0 B");
  });

  it("formats bytes", () => {
    expect(formatBytes(500)).toBe("500 B");
  });

  it("formats kilobytes", () => {
    expect(formatBytes(1024)).toBe("1 KB");
    expect(formatBytes(1536)).toBe("1.5 KB");
  });

  it("formats megabytes", () => {
    expect(formatBytes(1048576)).toBe("1 MB");
  });

  it("formats gigabytes", () => {
    expect(formatBytes(1073741824)).toBe("1 GB");
  });
});

describe("formatMs", () => {
  it("formats sub-millisecond", () => {
    expect(formatMs(0.5)).toBe("<1ms");
  });

  it("formats milliseconds", () => {
    expect(formatMs(150)).toBe("150ms");
    expect(formatMs(999)).toBe("999ms");
  });

  it("formats seconds", () => {
    expect(formatMs(1500)).toBe("1.5s");
    expect(formatMs(5000)).toBe("5.0s");
  });
});

describe("formatDate", () => {
  it("formats recent timestamps", () => {
    const now = new Date();
    const fiveMinAgo = new Date(now.getTime() - 5 * 60 * 1000).toISOString();
    expect(formatDate(fiveMinAgo)).toBe("5m ago");
  });

  it("formats just now", () => {
    const now = new Date().toISOString();
    expect(formatDate(now)).toBe("just now");
  });

  it("formats hours ago", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
    expect(formatDate(twoHoursAgo)).toBe("2h ago");
  });

  it("handles invalid date string", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("formatNumber", () => {
  it("formats small numbers", () => {
    expect(formatNumber(42)).toBe("42");
    expect(formatNumber(999)).toBe("999");
  });

  it("formats thousands", () => {
    expect(formatNumber(1500)).toBe("1.5K");
    expect(formatNumber(10000)).toBe("10.0K");
  });

  it("formats millions", () => {
    expect(formatNumber(1500000)).toBe("1.5M");
  });
});
