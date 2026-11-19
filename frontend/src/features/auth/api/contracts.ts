/**
 * IDR-004: statically derived from the checked-in upstream OpenAPI.
 * Never hand-edit the generated allauth.d.ts file.
 */
import type { components, paths } from "./generated/allauth";

export type BrowserPath = Extract<keyof paths, `/_allauth/browser/v1/${string}`>;

export const ENDPOINTS = {
  session: "/_allauth/browser/v1/auth/session",
  login: "/_allauth/browser/v1/auth/login",
  configuration: "/_allauth/browser/v1/config",
} as const satisfies Record<string, BrowserPath>;

export type AllauthFlow = components["schemas"]["Flow"];
export type FlowId = AllauthFlow["id"];
export type AllauthUser = components["schemas"]["User"];
export type AuthenticatedResponse = components["schemas"]["AuthenticatedResponse"];
export type AuthenticationResponse = components["schemas"]["AuthenticationResponse"];
export type ConfigurationResponse = components["schemas"]["ConfigurationResponse"];
export type UsernameLogin = components["schemas"]["Login"] & {
  username: string;
  password: string;
};

/** Static proof that the methods exist in the actual versioned OpenAPI. */
export type SessionGet = paths[typeof ENDPOINTS.session]["get"];
export type SessionDelete = paths[typeof ENDPOINTS.session]["delete"];
export type LoginPost = paths[typeof ENDPOINTS.login]["post"];
export type ConfigurationGet = paths[typeof ENDPOINTS.configuration]["get"];
