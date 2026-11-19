/**
 * IDR-005 / P1: path-based loopback proxy for local Next.js development.
 *
 * These rewrites are server-side only. They are intentionally disabled for
 * production builds and MUST NOT substitute for staging edge routing/TLS.
 */
export type LocalRewrite = Readonly<{ source: string; destination: string }>;

export function makeLocalDjangoRewrites(
  nodeEnv: string | undefined,
  rawOrigin: string | undefined,
): LocalRewrite[] {
  if (nodeEnv !== "development" || !rawOrigin) return [];

  let upstream: URL;
  try {
    upstream = new URL(rawOrigin);
  } catch {
    throw new Error("INVALID_LOCAL_DJANGO_PROXY_ORIGIN");
  }

  const permittedHosts = new Set(["localhost", "127.0.0.1", "[::1]"]);
  if (
    upstream.protocol !== "http:" ||
    !permittedHosts.has(upstream.hostname) ||
    !upstream.port ||
    upstream.username ||
    upstream.password ||
    upstream.pathname !== "/" ||
    upstream.search ||
    upstream.hash
  ) {
    throw new Error("INVALID_LOCAL_DJANGO_PROXY_ORIGIN");
  }

  const origin = upstream.origin;
  return [
    { source: "/_allauth/:path*", destination: `${origin}/_allauth/:path*` },
    { source: "/accounts/:path*", destination: `${origin}/accounts/:path*` },
    { source: "/api/:path*", destination: `${origin}/api/:path*` },
    { source: "/health", destination: `${origin}/health/` },
    { source: "/health/", destination: `${origin}/health/` },
  ];
}
