/** Compile-time contract checks: the paths are generated from our OpenAPI. */
import { ENDPOINTS, type SessionGet, type SessionDelete, type LoginPost } from "../src/features/auth/api/contracts";
import type { paths } from "../src/features/auth/api/generated/allauth";

const route: keyof paths = ENDPOINTS.session;
void route;

// The supported endpoint + HTTP method pairs must remain available.
type Present<T> = T extends never ? never : T;
type _SessionGet = Present<SessionGet>;
type _SessionDelete = Present<SessionDelete>;
type _LoginPost = Present<LoginPost>;

// @ts-expect-error the app client is excluded from the generated browser-only schema
const appRoute: keyof paths = "/_allauth/app/v1/auth/session";
void appRoute;
