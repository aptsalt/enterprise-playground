import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig: NextConfig = {
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${api}/api/:path*` },
      { source: "/playground/:path*", destination: `${api}/playground/:path*` },
      { source: "/generated/:path*", destination: `${api}/generated/:path*` },
      { source: "/screenshots/:path*", destination: `${api}/screenshots/:path*` },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
