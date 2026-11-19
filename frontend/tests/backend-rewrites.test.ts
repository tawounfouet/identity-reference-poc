import assert from "node:assert/strict";
import test from "node:test";

import { makeLocalDjangoRewrites } from "../src/config/backend-rewrites";

test("IDR-005: development rewrites preserve official Django path prefixes", () => {
  const rewrites = makeLocalDjangoRewrites("development", "http://127.0.0.1:8000");
  assert.deepEqual(rewrites.map(({ source }) => source), [
    "/_allauth/:path*",
    "/accounts/:path*",
    "/api/:path*",
    "/health",
    "/health/",
  ]);
  assert.deepEqual(rewrites.map(({ destination }) => destination), [
    "http://127.0.0.1:8000/_allauth/:path*",
    "http://127.0.0.1:8000/accounts/:path*",
    "http://127.0.0.1:8000/api/:path*",
    "http://127.0.0.1:8000/health/",
    "http://127.0.0.1:8000/health/",
  ]);
});

test("IDR-005: absent origin or non-dev runtime never installs backend rewrites", () => {
  assert.deepEqual(makeLocalDjangoRewrites("development", undefined), []);
  assert.deepEqual(makeLocalDjangoRewrites("production", "http://127.0.0.1:8000"), []);
  assert.deepEqual(makeLocalDjangoRewrites("test", "http://127.0.0.1:8000"), []);
});

test("IDR-005: reject non-loopback or ambiguous Django proxy origins", () => {
  const rejected = [
    "https://127.0.0.1:8000",
    "http://evil.example.org:8000",
    "http://localhost.evil.org:8000",
    "http://user:password@localhost:8000",
    "http://localhost:8000/other",
    "http://localhost:8000/?url=other",
    "http://localhost:8000/#auth",
    "http://localhost",
    "http://0.0.0.0:8000",
    "http://127.0.0.2:8000",
    "ftp://localhost:8000",
    "not-a-url",
  ];
  for (const origin of rejected) {
    assert.throws(
      () => makeLocalDjangoRewrites("development", origin),
      /INVALID_LOCAL_DJANGO_PROXY_ORIGIN/,
      origin,
    );
  }
});

test("IDR-005: accepted localhost targets remain server-only", () => {
  const rules = makeLocalDjangoRewrites("development", "http://localhost:8000");
  assert.equal(rules[0].destination, "http://localhost:8000/_allauth/:path*");
  assert.equal(rules.some((rule) => rule.source.startsWith("/_next")), false);
  assert.equal(rules.some((rule) => rule.source === "/"), false);
});
