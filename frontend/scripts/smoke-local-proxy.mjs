/**
 * IDR-005 P1: real local HTTP smoke from a single browser-visible origin.
 * Executed only with Django and Next.js running in a GitHub Actions runner.
 */
import assert from "node:assert/strict";

const origin = "http://127.0.0.1:3000";
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForServers() {
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const response = await fetch(`${origin}/health/`, { cache: "no-store" });
      if (response.ok) {
        const body = await response.json();
        if (body.status === "ok" && body.service === "identity-reference-poc") return;
      }
    } catch {
      // The development servers may still be starting.
    }
    await pause(500);
  }
  throw new Error("LOCAL_SAME_ORIGIN_HEALTHCHECK_NOT_READY");
}

async function main() {
  await waitForServers();

  const health = await fetch(`${origin}/health/`, { cache: "no-store" });
  assert.equal(health.status, 200, "healthcheck must be proxied to Django");
  assert.deepEqual(await health.json(), { status: "ok", service: "identity-reference-poc" });

  const config = await fetch(`${origin}/_allauth/browser/v1/config`, { cache: "no-store" });
  assert.equal(config.status, 200, "allauth config should be proxied to Django");
  assert.match(config.headers.get("content-type") ?? "", /application\/json/);
  const configJson = await config.json();
  assert.equal(configJson.status, 200);

  const session = await fetch(`${origin}/_allauth/browser/v1/auth/session`, { cache: "no-store" });
  assert.equal(session.status, 401, "anonymous session must remain unauthenticated");
  assert.match(session.headers.get("content-type") ?? "", /application\/json/);
  const sessionJson = await session.json();
  assert.equal(sessionJson.status, 401);
  assert.equal(sessionJson.meta?.is_authenticated, false);
  assert.ok(Array.isArray(sessionJson.data?.flows));

  const page = await fetch(`${origin}/`, { cache: "no-store" });
  assert.equal(page.status, 200, "Next.js still owns the root page");
  assert.match(page.headers.get("content-type") ?? "", /text\/html/);

  // These requests all use one visible scheme, host and port.
  assert.equal(new URL(session.url).origin, new URL(page.url).origin);
  console.log("IDR-005 local HTTP smoke: frontend, Django health, allauth config/session OK");
}

await main();
