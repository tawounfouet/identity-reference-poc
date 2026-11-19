import assert from "node:assert/strict";
import test from "node:test";

import { AuthClientError, BrowserAuthClient, readCsrfCookie } from "../src/features/auth/api/browser-client";

const demo = { id: "9427237d-77ba-4793-b84c-edf7ee588afe" };
const authenticated = {
  status: 200,
  data: { user: demo, methods: [{ method: "password" }] },
  meta: { is_authenticated: true },
};

const jsonResponse = (status: number, body: object, contentType = "application/json") =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": contentType } });

test("CSRF cookie parsing is exact and handles encoding", () => {
  assert.equal(readCsrfCookie("x=1; csrftoken=abc%3D123; sessionid=hidden"), "abc=123");
  assert.equal(readCsrfCookie("notcsrftoken=wrong; sessionid=1"), undefined);
  assert.equal(readCsrfCookie("csrftoken=%ZZ"), undefined);
});

test("GET session uses relative path, same-origin browser cookies, no-store", async () => {
  let calls = 0;
  const fetcher = async (input: RequestInfo | URL, init?: RequestInit) => {
    calls++;
    assert.equal(input, "/_allauth/browser/v1/auth/session");
    assert.equal(init?.method, "GET");
    assert.equal(init?.credentials, "same-origin");
    assert.equal(init?.mode, "same-origin");
    assert.equal(init?.cache, "no-store");
    assert.equal(init?.redirect, "error");
    assert.equal(new Headers(init?.headers).has("X-CSRFToken"), false);
    return jsonResponse(200, authenticated);
  };
  const state = await new BrowserAuthClient({ fetcher: fetcher as typeof fetch }).loadSession();
  assert.deepEqual(state, { kind: "authenticated", userId: demo.id });
  assert.equal(calls, 1);
});

test("login sends only username/password, JSON and CSRF without persisting tokens", async () => {
  let calls = 0;
  const fetcher = async (input: RequestInfo | URL, init?: RequestInit) => {
    calls++;
    assert.equal(input, "/_allauth/browser/v1/auth/login");
    assert.equal(init?.method, "POST");
    assert.equal(new Headers(init?.headers).get("X-CSRFToken"), "csrf-test");
    assert.equal(new Headers(init?.headers).get("Content-Type"), "application/json");
    assert.deepEqual(JSON.parse(String(init?.body)), { username: "demo", password: "test-only-secret" });
    return jsonResponse(401, { status: 401, meta: { is_authenticated: false }, data: { flows: [{ id: "verify_email" }] } });
  };
  const state = await new BrowserAuthClient({
    fetcher: fetcher as typeof fetch,
    readCsrfToken: () => "csrf-test",
  }).login("demo", "test-only-secret");
  assert.equal(state.kind, "pending-email");
  assert.equal(calls, 1);
});

test("fail closed on missing CSRF without any HTTP request", async () => {
  let calls = 0;
  const fetcher = async () => { calls++; return jsonResponse(401, { status: 401 }); };
  const client = new BrowserAuthClient({ fetcher: fetcher as typeof fetch, readCsrfToken: () => undefined });
  await assert.rejects(client.login("demo", "pass"), (err: unknown) =>
    err instanceof AuthClientError && err.code === "CSRF_NOT_READY");
  await assert.rejects(client.logout(), (err: unknown) =>
    err instanceof AuthClientError && err.code === "CSRF_NOT_READY");
  assert.equal(calls, 0);
});

test("logout requires a CSRF token, never retries automatically", async () => {
  let calls = 0;
  const fetcher = async (_input: RequestInfo | URL, init?: RequestInit) => {
    calls++;
    assert.equal(init?.method, "DELETE");
    assert.equal(new Headers(init?.headers).get("X-CSRFToken"), "csrf-rotated");
    return jsonResponse(401, {
      status: 401,
      meta: { is_authenticated: false },
      data: { flows: [{ id: "login" }] },
    });
  };
  const client = new BrowserAuthClient({ fetcher: fetcher as typeof fetch, readCsrfToken: () => "csrf-rotated" });
  assert.equal((await client.logout()).kind, "anonymous");
  assert.equal(calls, 1);
});

test("non-JSON responses, malformed payload and status mismatch are rejected", async () => {
  const nonJson = new BrowserAuthClient({
    fetcher: (async () => new Response("<html>error</html>", { status: 403, headers: { "content-type": "text/html" } })) as typeof fetch,
  });
  await assert.rejects(nonJson.loadSession(), (e: unknown) =>
    e instanceof AuthClientError && e.code === "NON_JSON_RESPONSE" && e.httpStatus === 403);

  const mismatch = new BrowserAuthClient({
    fetcher: (async () => jsonResponse(200, { status: 401 })) as typeof fetch,
  });
  await assert.rejects(mismatch.loadSession(), (e: unknown) =>
    e instanceof AuthClientError && e.code === "ENVELOPE_MISMATCH");

  const invalid = new BrowserAuthClient({
    fetcher: (async () => new Response("{", { status: 200, headers: { "content-type": "application/json" } })) as typeof fetch,
  });
  await assert.rejects(invalid.loadSession(), (e: unknown) =>
    e instanceof AuthClientError && e.code === "INVALID_JSON");
});

test("network failure and abort are classified without leaking credentials", async () => {
  const client = new BrowserAuthClient({
    fetcher: (async () => { throw new Error("private-details"); }) as typeof fetch,
  });
  await assert.rejects(client.loadSession(), (e: unknown) =>
    e instanceof AuthClientError && e.code === "NETWORK_ERROR" && !e.message.includes("private-details"));

  const controller = new AbortController();
  controller.abort();
  await assert.rejects(client.loadSession(controller.signal), (e: unknown) =>
    e instanceof AuthClientError && e.code === "REQUEST_ABORTED");
});

test("configuration uses the typed official endpoint", async () => {
  let calls = 0;
  const client = new BrowserAuthClient({
    fetcher: (async (input: RequestInfo | URL) => {
      calls++;
      assert.equal(input, "/_allauth/browser/v1/config");
      return jsonResponse(200, { status: 200, data: { account: {} } });
    }) as typeof fetch,
  });
  const data = await client.loadConfiguration();
  assert.equal(data.status, 200);
  assert.equal(calls, 1);
});
