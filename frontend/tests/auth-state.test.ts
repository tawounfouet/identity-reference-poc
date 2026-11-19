import assert from "node:assert/strict";
import test from "node:test";

import { mapAuthEnvelope } from "../src/features/auth/model/auth-state";

const user = { id: "9427237d-77ba-4793-b84c-edf7ee588afe", display: "Demo" };

function auth401(flows: string[], isAuthenticated = false, extra: object = {}) {
  return {
    httpStatus: 401,
    body: {
      status: 401,
      meta: { is_authenticated: isAuthenticated },
      data: { flows: flows.map((id) => ({ id })), user, ...extra },
    },
  };
}

test("200 authenticated requires an explicit meta flag and a non-empty user id", () => {
  assert.deepEqual(
    mapAuthEnvelope({ httpStatus: 200, body: { status: 200, meta: { is_authenticated: true }, data: { user } } }),
    { kind: "authenticated", userId: user.id },
  );
  assert.equal(
    mapAuthEnvelope({ httpStatus: 200, body: { status: 200, data: { user } } }).kind,
    "unavailable",
  );
  assert.equal(
    mapAuthEnvelope({ httpStatus: 200, body: { status: 200, meta: { is_authenticated: true }, data: { user: { id: "" } } } }).kind,
    "unavailable",
  );
});

test("401 with data.user never grants authenticated state", () => {
  assert.deepEqual(mapAuthEnvelope(auth401(["login"])), { kind: "anonymous", flows: ["login"] });
  assert.equal(mapAuthEnvelope(auth401(["verify_email"])).kind, "pending-email");
  assert.equal(mapAuthEnvelope(auth401(["mfa_authenticate"])).kind, "pending-mfa");
  assert.equal(mapAuthEnvelope(auth401(["mfa_reauthenticate"], true)).kind, "pending-mfa");
  assert.equal(mapAuthEnvelope(auth401(["reauthenticate"], true)).kind, "reauth-required");
  assert.equal(mapAuthEnvelope(auth401(["login"], true)).kind, "reauth-required");
});

test("malformed or unknown flows fail closed", () => {
  assert.equal(mapAuthEnvelope(auth401(["unknown_future_flow"])).kind, "unavailable");
  assert.equal(mapAuthEnvelope({ httpStatus: 401, body: { status: 401, meta: { is_authenticated: false }, data: {} } }).kind, "unavailable");
  assert.equal(mapAuthEnvelope({ httpStatus: 200, body: { status: 401, meta: { is_authenticated: true }, data: { user } } }).kind, "unavailable");
});

test("400 errors, 403, 409, 429 and unsupported app-only 410 are classified", () => {
  assert.deepEqual(
    mapAuthEnvelope({ httpStatus: 400, body: { status: 400, errors: [{ code: "invalid", message: "Invalid field", param: "username" }] } }),
    { kind: "invalid-input", errors: [{ code: "invalid", message: "Invalid field", param: "username" }] },
  );
  assert.deepEqual(mapAuthEnvelope({ httpStatus: 403, body: { status: 403 } }), { kind: "forbidden" });
  assert.deepEqual(mapAuthEnvelope({ httpStatus: 409, body: { status: 409 } }), { kind: "conflict", requiresSessionRefresh: true });
  assert.deepEqual(mapAuthEnvelope({ httpStatus: 429, body: { status: 429 } }), { kind: "rate-limited" });
  assert.deepEqual(mapAuthEnvelope({ httpStatus: 410, body: { status: 410 } }), { kind: "unavailable", retryable: false });
  assert.deepEqual(mapAuthEnvelope({ httpStatus: 503, body: { status: 503 } }), { kind: "unavailable", retryable: true });
});
