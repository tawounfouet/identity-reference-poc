import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  turbopack: {
    // Local dev/build commands run from frontend/; do not infer a parent lockfile.
    root: process.cwd(),
  },
};

export default nextConfig;
