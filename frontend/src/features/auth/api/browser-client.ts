/**
 * Browser-only, same-origin Allauth transport (IDR-004).
 *
 * - Auth cookies remain controlled by the browser, never localStorage.
 * - Unsafe mutations require a present CSRF cookie. G1 owns bootstrap,
 *   origin, cookie rotation, proxy and end-to-end CSRF tests.
 * - No silent retries, provider redirects, or absolute URLs.
 */
import {
  ENDPOINTS,
  type ConfigurationResponse,
  type UsernameLogin,
} from "./contracts";
import { mapAuthEnvelope, type AuthViewState, type HttpEnvelope } from "../model/auth-state";

type Method = "GET" | "POST" | "DELETE";

export type ClientFailureCode =
  | "CSRF_NOT_READY"
  | "NETWORK_ERROR"
  | "REQUEST_ABORTED"
  | "NON_JSON_RESPONSE"
  | "INVALID_JSON"
  | "ENVELOPE_MISMATCH";

export class AuthClientError extends Error {
  constructor(
    readonly code: ClientFailureCode,
    readonly httpStatus?: number,
  ) {
    // Avoid serializing request bodies, cookies and credentials into logs.
    super(code);
    this.name = "AuthClientError";
  }
}

/** A minimal cookie accessor. The session cookie itself stays HttpOnly. */
export function readCsrfCookie(cookieString: string): string | undefined {
  for (const entry of cookieString.split(";")) {
    const [name, ...rest] = entry.trim().split("=");
    if (name !== "csrftoken" || rest.length === 0) continue;
    try {
      const token = decodeURIComponent(rest.join("="));
      return token || undefined;
    } catch {
      return undefined;
    }
  }
  return undefined;
}

export type BrowserAuthClientOptions = Readonly<{
  fetcher?: typeof fetch;
  readCsrfToken?: () => string | undefined;
}>;

export class BrowserAuthClient {
  private readonly fetcher: typeof fetch;
  private readonly readCsrfToken: () => string | undefined;

  constructor(options: BrowserAuthClientOptions = {}) {
    this.fetcher = options.fetcher ?? fetch;
    this.readCsrfToken = options.readCsrfToken ?? (() => {
      if (typeof document === "undefined") return undefined;
      return readCsrfCookie(document.cookie);
    });
  }

  private async send(
    path: (typeof ENDPOINTS)[keyof typeof ENDPOINTS],
    method: Method,
    data?: unknown,
    signal?: AbortSignal,
  ): Promise<HttpEnvelope> {
    const headers = new Headers({ Accept: "application/json" });
    if (method !== "GET") {
      const token = this.readCsrfToken();
      if (!token) throw new AuthClientError("CSRF_NOT_READY");
      headers.set("X-CSRFToken", token);
    }
    if (data !== undefined) {
      headers.set("Content-Type", "application/json");
    }

    let response: Response;
    try {
      response = await this.fetcher(path, {
        method,
        headers,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        ...(data === undefined ? {} : { body: JSON.stringify(data) }),
        ...(signal ? { signal } : {}),
      });
    } catch {
      throw new AuthClientError(signal?.aborted ? "REQUEST_ABORTED" : "NETWORK_ERROR");
    }

    const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
    if (!contentType.includes("application/json") && !contentType.includes("+json")) {
      throw new AuthClientError("NON_JSON_RESPONSE", response.status);
    }
    let parsed: unknown;
    try {
      parsed = await response.json();
    } catch {
      throw new AuthClientError("INVALID_JSON", response.status);
    }
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)
      || !("status" in parsed) || parsed.status !== response.status) {
      throw new AuthClientError("ENVELOPE_MISMATCH", response.status);
    }
    return { httpStatus: response.status, body: parsed };
  }

  async loadSession(signal?: AbortSignal): Promise<AuthViewState> {
    return mapAuthEnvelope(await this.send(ENDPOINTS.session, "GET", undefined, signal));
  }

  /** No email-only login while AbstractUser.email is not unique. */
  async login(username: string, password: string, signal?: AbortSignal): Promise<AuthViewState> {
    const payload: UsernameLogin = { username, password };
    return mapAuthEnvelope(await this.send(ENDPOINTS.login, "POST", payload, signal));
  }

  async logout(signal?: AbortSignal): Promise<AuthViewState> {
    return mapAuthEnvelope(await this.send(ENDPOINTS.session, "DELETE", undefined, signal));
  }

  async loadConfiguration(signal?: AbortSignal): Promise<ConfigurationResponse> {
    const result = await this.send(ENDPOINTS.configuration, "GET", undefined, signal);
    if (result.httpStatus !== 200) {
      throw new AuthClientError("ENVELOPE_MISMATCH", result.httpStatus);
    }
    // The generated type represents the compile-time contract. Deeper runtime
    // validation is a follow-up and no user claims are authorized by config.
    return result.body as ConfigurationResponse;
  }
}
