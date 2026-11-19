import type { NextConfig } from "next";

import { makeLocalDjangoRewrites } from "./src/config/backend-rewrites";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return makeLocalDjangoRewrites(process.env.NODE_ENV, process.env.DJANGO_PROXY_ORIGIN);
  },
  turbopack: {
    // Local dev/build commands run from frontend/; do not infer a parent lockfile.
    root: process.cwd(),
  },
};

export default nextConfig;
