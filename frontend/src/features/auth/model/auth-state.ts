/**
 * Pure projection of the browser-specific upstream Allauth envelope.
 * A 401 may signal an ongoing authentication flow, not a bad password.
 *
 * No view is authorized by the presence of data.user alone.
 */
import type { FlowId } from "../api/contracts";

export type FieldError = Readonly<{
  code: string;
  message: string;
  param?: string;
}>;

export type AuthViewState =
  | Readonly<{ kind: "loading" }>
  | Readonly<{ kind: "anonymous"; flows: readonly FlowId[] }>
  | Readonly<{ kind: "pending-email"; flows: readonly FlowId[] }>
  | Readonly<{ kind: "pending-mfa"; flows: readonly FlowId[] }>
  | Readonly<{ kind: "reauth-required"; flows: readonly FlowId[] }>
  | Readonly<{ kind: "authenticated"; userId: string }>
  | Readonly<{ kind: "invalid-input"; errors: readonly FieldError[] }>
  | Readonly<{ kind: "forbidden" }>
  | Readonly<{ kind: "conflict"; requiresSessionRefresh: true }>
  | Readonly<{ kind: "rate-limited" }>
  | Readonly<{ kind: "unavailable"; retryable: boolean }>;

export type HttpEnvelope = Readonly<{ httpStatus: number; body: unknown }>;

const ALLOWED_FLOWS = new Set<FlowId>([
  "login", "login_by_code", "mfa_authenticate", "mfa_reauthenticate",
  "provider_redirect", "provider_signup", "provider_token",
  "reauthenticate", "reauthenticate_by_code", "signup",
  "verify_email", "verify_phone",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseFlows(body: Record<string, unknown>): readonly FlowId[] | null {
  if (!isRecord(body.data) || !Array.isArray(body.data.flows)) {
    return null;
  }
  const flows: FlowId[] = [];
  for (const item of body.data.flows) {
    if (!isRecord(item) || typeof item.id !== "string" || !ALLOWED_FLOWS.has(item.id as FlowId)) {
      return null;
    }
    flows.push(item.id as FlowId);
  }
  return flows;
}

function parseFieldErrors(body: Record<string, unknown>): readonly FieldError[] {
  if (!Array.isArray(body.errors)) return [];
  return body.errors.flatMap((item: unknown) => {
    if (!isRecord(item) || typeof item.code !== "string" || typeof item.message !== "string") {
      return [];
    }
    return [{
      code: item.code,
      message: item.message,
      ...(typeof item.param === "string" ? { param: item.param } : {}),
    }];
  });
}

export function mapAuthEnvelope({ httpStatus, body }: HttpEnvelope): AuthViewState {
  if (!isRecord(body) || body.status !== httpStatus) {
    return { kind: "unavailable", retryable: false };
  }

  if (httpStatus === 200) {
    const meta = body.meta;
    const data = body.data;
    if (!isRecord(meta) || meta.is_authenticated !== true || !isRecord(data)
      || !isRecord(data.user) || typeof data.user.id !== "string" || !data.user.id.trim()) {
      return { kind: "unavailable", retryable: false };
    }
    return { kind: "authenticated", userId: data.user.id };
  }

  if (httpStatus === 401) {
    const meta = body.meta;
    const flows = parseFlows(body);
    if (!isRecord(meta) || typeof meta.is_authenticated !== "boolean" || flows === null) {
      return { kind: "unavailable", retryable: false };
    }
    if (flows.includes("mfa_authenticate") || flows.includes("mfa_reauthenticate")) {
      return { kind: "pending-mfa", flows };
    }
    if (flows.includes("verify_email") || flows.includes("verify_phone")) {
      return { kind: "pending-email", flows };
    }
    if (meta.is_authenticated || flows.includes("reauthenticate")
      || flows.includes("reauthenticate_by_code")) {
      return { kind: "reauth-required", flows };
    }
    return { kind: "anonymous", flows };
  }

  if (httpStatus === 400) {
    return { kind: "invalid-input", errors: parseFieldErrors(body) };
  }
  if (httpStatus === 403) return { kind: "forbidden" };
  if (httpStatus === 409) return { kind: "conflict", requiresSessionRefresh: true };
  if (httpStatus === 429) return { kind: "rate-limited" };

  // A 410 is documented for app sessions only. Treat it as a protocol mismatch.
  if (httpStatus === 410) return { kind: "unavailable", retryable: false };
  return { kind: "unavailable", retryable: httpStatus >= 500 };
}
