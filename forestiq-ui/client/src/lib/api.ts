/** ForestIQ API client with internal JWT and Keycloak Authorization Code + PKCE support. */
import type { AppUser } from "./types";

export const API_BASE_URL = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");
const BASE_URL = API_BASE_URL;
const ACCESS_TOKEN_KEY = "forestiq_access_token";
const REFRESH_TOKEN_KEY = "forestiq_refresh_token";
const OIDC_STATE_KEY = "forestiq_oidc_state";
const OIDC_VERIFIER_KEY = "forestiq_oidc_verifier";
const OIDC_NONCE_KEY = "forestiq_oidc_nonce";
let apiResourceRewriteInstalled = false;

export type OidcConfiguration = {
  enabled: boolean;
  localLoginEnabled: boolean;
  authorizationEndpoint?: string;
  clientId?: string;
  scope?: string;
};

type TokenPair = { actualToken: { token: string }; refreshToken: { token: string } };

export class ApiError extends Error {
  status: number;
  correlationId: string | null;

  constructor(message: string, status: number, correlationId: string | null = null) {
    super(message);
    this.status = status;
    this.correlationId = correlationId;
  }
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.correlationId ? `${error.message} (viide ${error.correlationId})` : error.message;
  }
  return error instanceof Error ? error.message : fallback;
}

export function apiUrl(path: string): string {
  const base = new URL(BASE_URL, window.location.origin);
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return new URL(`${base.pathname.replace(/\/$/, "")}${suffix}`, base.origin).toString();
}

export function normalizeApiResourceUrl(url: string): string {
  const candidate = new URL(url, window.location.origin);
  if (candidate.origin === window.location.origin && candidate.pathname.startsWith("/api/")) {
    return `${BASE_URL}${candidate.pathname.replace(/^\/api/, "")}${candidate.search}${candidate.hash}`;
  }
  return candidate.toString();
}

export function apiAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function installApiResourceRewrite(): void {
  if (apiResourceRewriteInstalled || typeof window === "undefined") return;
  apiResourceRewriteInstalled = true;
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    if (typeof input === "string" || input instanceof URL) {
      return nativeFetch(normalizeApiResourceUrl(String(input)), init);
    }
    const rewritten = normalizeApiResourceUrl(input.url);
    if (rewritten !== input.url) {
      return nativeFetch(new Request(rewritten, input), init);
    }
    return nativeFetch(input, init);
  };
}

installApiResourceRewrite();

export function mapResourceRequest(url: string): { url: string; headers?: Record<string, string> } {
  const token = apiAccessToken();
  const normalized = normalizeApiResourceUrl(url);
  return token && normalized.includes("/api/")
    ? { url: normalized, headers: { Authorization: `Bearer ${token}` } }
    : { url: normalized };
}

export function decodeToken(token: string): AppUser | null {
  try {
    const body = token.split(".")[1];
    const decoded = atob(body.replace(/-/g, "+").replace(/_/g, "/"));
    const json = JSON.parse(
      decodeURIComponent(
        Array.from(decoded)
          .map((character) => `%${character.charCodeAt(0).toString(16).padStart(2, "0")}`)
          .join(""),
      ),
    );
    return {
      id: json.userId,
      name: json.userName,
      privileges: json.privileges || [],
      roles: json.roles || [],
      organizationId: json.organizationId || json.organization_id || "",
    };
  } catch {
    return null;
  }
}

function headers(withJson = false): HeadersInit {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  return {
    ...(withJson ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    if (response.status === 401) window.dispatchEvent(new Event("forestiq:unauthorized"));
    const correlationId = response.headers.get("X-Correlation-ID") || data?.correlationId || null;
    throw new ApiError(data?.detail || `Päring ebaõnnestus (${response.status})`, response.status, correlationId);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function jsonRequest<T>(method: "POST" | "PUT" | "PATCH", path: string, body: unknown) {
  return fetch(`${BASE_URL}${path}`, { method, headers: headers(true), body: JSON.stringify(body) }).then(parse<T>);
}

function saveTokens(tokens: TokenPair): AppUser | null {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.actualToken.token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken.token);
  return decodeToken(tokens.actualToken.token);
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function randomValue(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

async function codeChallenge(verifier: string): Promise<string> {
  const source = new TextEncoder().encode(verifier);
  return base64Url(new Uint8Array(await crypto.subtle.digest("SHA-256", source)));
}

export function oidcRedirectUri(): string {
  const callbackPath = import.meta.env.VITE_KEYCLOAK_REDIRECT_PATH || "/login";
  return `${window.location.origin}${callbackPath}`;
}

export const api = {
  get: <T>(path: string) => fetch(`${BASE_URL}${path}`, { headers: headers() }).then(parse<T>),
  post: <T>(path: string, body: unknown) => jsonRequest<T>("POST", path, body),
  put: <T>(path: string, body: unknown) => jsonRequest<T>("PUT", path, body),
  patch: <T>(path: string, body: unknown) => jsonRequest<T>("PATCH", path, body),
  upload: <T>(path: string, body: FormData, method: "POST" | "PUT" = "POST") =>
    fetch(`${BASE_URL}${path}`, { method, headers: headers(), body }).then(parse<T>),
  delete: <T>(path: string, body?: unknown) => fetch(`${BASE_URL}${path}`, { method: "DELETE", headers: headers(body !== undefined), body: body === undefined ? undefined : JSON.stringify(body) }).then(parse<T>),
  async download(path: string, filename: string): Promise<void> {
    const response = await fetch(`${BASE_URL}${path}`, { headers: headers() });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new ApiError(data?.detail || `Allalaadimine ebaõnnestus (${response.status})`, response.status, response.headers.get("X-Correlation-ID"));
    }
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  },

  async oidcConfiguration(): Promise<OidcConfiguration> {
    return parse<OidcConfiguration>(await fetch(`${BASE_URL}/oidc/config`));
  },

  async startOidcLogin(config: OidcConfiguration): Promise<void> {
    if (!config.enabled || !config.authorizationEndpoint || !config.clientId) {
      throw new ApiError("Keycloak’i sisselogimine ei ole seadistatud.", 503);
    }
    const verifier = randomValue();
    const state = randomValue();
    const nonce = randomValue();
    localStorage.setItem(OIDC_STATE_KEY, state);
    localStorage.setItem(OIDC_VERIFIER_KEY, verifier);
    localStorage.setItem(OIDC_NONCE_KEY, nonce);

    const url = new URL(config.authorizationEndpoint);
    url.searchParams.set("client_id", config.clientId);
    url.searchParams.set("redirect_uri", oidcRedirectUri());
    url.searchParams.set("response_type", "code");
    url.searchParams.set("scope", config.scope || "openid profile email");
    url.searchParams.set("state", state);
    url.searchParams.set("nonce", nonce);
    url.searchParams.set("code_challenge", await codeChallenge(verifier));
    url.searchParams.set("code_challenge_method", "S256");
    window.location.assign(url.toString());
  },

  async completeOidcLogin(code: string, state: string): Promise<AppUser | null> {
    const expectedState = localStorage.getItem(OIDC_STATE_KEY);
    const verifier = localStorage.getItem(OIDC_VERIFIER_KEY);
    const nonce = localStorage.getItem(OIDC_NONCE_KEY);
    if (!code || !state || !expectedState || state !== expectedState || !verifier) {
      throw new ApiError("Keycloak’i sisselogimise olekukontroll ebaõnnestus.", 400);
    }
    const response = await fetch(`${BASE_URL}/oidc/exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, codeVerifier: verifier, redirectUri: oidcRedirectUri(), nonce }),
    });
    const tokens = await parse<TokenPair>(response);
    localStorage.removeItem(OIDC_STATE_KEY);
    localStorage.removeItem(OIDC_VERIFIER_KEY);
    localStorage.removeItem(OIDC_NONCE_KEY);
    return saveTokens(tokens);
  },

  async passwordLogin(userId: string, password: string) {
    return parse<{ token: string }>(
      await fetch(`${BASE_URL}/password-login`, {
        method: "POST",
        headers: { Authorization: `Basic ${btoa(`${userId}:${password}`)}` },
      }),
    );
  },

  async verifyTotp(preAuthToken: string, code: string) {
    const tokens = await parse<TokenPair>(
      await fetch(`${BASE_URL}/services/totp`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${preAuthToken}` },
        body: JSON.stringify({ code }),
      }),
    );
    return saveTokens(tokens);
  },

  logout() {
    [ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, OIDC_STATE_KEY, OIDC_VERIFIER_KEY, OIDC_NONCE_KEY].forEach((key) => localStorage.removeItem(key));
  },
};

export function realtimeWebSocketUrl(): string | null {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (!token) return null;
  const base = new URL(BASE_URL, window.location.origin);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = base.pathname.replace(/\/api\/?$/, "") + "/ws/events/";
  base.search = "";
  base.searchParams.set("token", token);
  return base.toString();
}
