---
name: doppio-vue-typescript-portal
description: >
  Use this skill for building the Data Principal Self-Service Portal using Doppio framework
  with Vue 3 and TypeScript on Frappe v16. Triggers include: Doppio setup, Vue 3 component
  development for Frappe, TypeScript types for Frappe APIs, CSRF token handling in custom
  fetch calls, composables for Frappe data, the privacy portal UI, consent management UI,
  DSR submission form, data download, nomination form, or any frontend development for the
  dpdp_compliance app using Doppio. Always use when the user mentions "Doppio", "Vue 3
  Frappe", "frontend portal", "privacy portal", "TypeScript Frappe", "CSRF", or "custom
  frontend". CSRF handling is critical — never skip the CSRF section of this skill.
compatibility:
  frappe_version: ">=16.0"
  doppio: ">=2.0"
  vue: ">=3.4"
  typescript: ">=5.0"
  vite: ">=5.0"
---

# Doppio + Vue 3 + TypeScript — Data Principal Portal Skill

## Why Vue 3 over React for Doppio?
Doppio's official SDK (`@frappe-ui/doppio`) ships first-class Vue 3 support with pre-built
composables (`useDoc`, `useList`, `createResource`) tightly integrated with Frappe's API
conventions. While React works, Vue 3's Composition API + TypeScript delivers the most
ergonomic DX with the least boilerplate for Frappe-connected UIs.

---

## 1. Project Setup

```bash
# Create Doppio app inside Frappe bench
cd /path/to/frappe-bench/apps
npx create-doppio-app@latest dpdp_portal
# Select: Vue 3, TypeScript, Vite, Tailwind CSS

# Install dependencies
cd dpdp_portal
npm install

# Install Frappe UI (Doppio's component library)
npm install frappe-ui@latest

# Dev server (proxies Frappe API calls to bench)
npm run dev
# → http://localhost:8080 (proxies /api to http://localhost:8000)
```

### `vite.config.ts`
```typescript
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 8080,
    proxy: {
      // Proxy all /api calls to Frappe backend
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        // CRITICAL: Forward cookies so session + CSRF work
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq, req) => {
            proxyReq.setHeader("Origin", "http://localhost:8000");
          });
        },
      },
      "/assets": { target: "http://localhost:8000", changeOrigin: true },
      "/files": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  build: {
    outDir: "../dpdp_compliance/public/dpdp_portal",  // Serve from Frappe
    emptyOutDir: true,
  },
});
```

---

## 2. CSRF Token — Critical Pattern

**This is the most common source of 403 errors in Frappe + custom frontends.**

Frappe uses a session-scoped CSRF token stored in:
- Cookie: `X-Frappe-CSRF-Token` (readable by JS)
- OR fetched via: `GET /api/method/frappe.auth.get_logged_user` response headers

### CSRF Composable (`src/composables/useCSRF.ts`)
```typescript
// src/composables/useCSRF.ts
import { ref } from "vue";

let _csrfToken: string | null = null;

/**
 * Gets the CSRF token from the Frappe cookie.
 * Frappe sets `X-Frappe-CSRF-Token` as a readable (non-httpOnly) cookie.
 */
function getCsrfTokenFromCookie(): string | null {
  const match = document.cookie.match(/X-Frappe-CSRF-Token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Fetches CSRF token from Frappe if not cached.
 * Call once on app mount, then reuse.
 */
export async function ensureCSRFToken(): Promise<string> {
  if (_csrfToken) return _csrfToken;

  // First try cookie (most reliable when cookies are enabled)
  const fromCookie = getCsrfTokenFromCookie();
  if (fromCookie && fromCookie !== "Guest") {
    _csrfToken = fromCookie;
    return _csrfToken;
  }

  // Fallback: fetch from Frappe API (triggers session + sets cookie)
  const resp = await fetch("/api/method/frappe.auth.get_logged_user", {
    credentials: "include",  // Send session cookie
  });
  if (!resp.ok) throw new Error("Not authenticated");

  // After this call, Frappe sets the CSRF cookie — read it
  const fromCookieAfterFetch = getCsrfTokenFromCookie();
  if (!fromCookieAfterFetch) throw new Error("CSRF token not set by Frappe");

  _csrfToken = fromCookieAfterFetch;
  return _csrfToken;
}

/** Invalidate cached token (on logout or session change) */
export function clearCSRFToken(): void {
  _csrfToken = null;
}
```

### Frappe API Client (`src/lib/frappeClient.ts`)
```typescript
// src/lib/frappeClient.ts
import { ensureCSRFToken } from "@/composables/useCSRF";

interface FrappeResponse<T = unknown> {
  message: T;
  exc?: string;
}

type FrappeCallArgs = Record<string, unknown>;

/**
 * Central Frappe API caller — handles CSRF, auth, error parsing.
 * Use this instead of raw fetch for ALL Frappe API calls.
 */
export async function frappeCall<T = unknown>(
  method: string,
  args: FrappeCallArgs = {},
  options: { method?: "GET" | "POST"; raw?: boolean } = {}
): Promise<T> {
  const csrfToken = await ensureCSRFToken();
  const httpMethod = options.method ?? "POST";

  let url = `/api/method/${method}`;
  let body: BodyInit | undefined;
  const headers: Record<string, string> = {
    Accept: "application/json",
    // CRITICAL: Always include CSRF token for POST/PUT/DELETE
    "X-Frappe-CSRF-Token": csrfToken,
  };

  if (httpMethod === "GET") {
    const params = new URLSearchParams(
      Object.entries(args).map(([k, v]) => [k, String(v)])
    );
    url = `${url}?${params.toString()}`;
  } else {
    // Frappe expects form-encoded or JSON body
    headers["Content-Type"] = "application/json";
    body = JSON.stringify({ ...args });
  }

  const response = await fetch(url, {
    method: httpMethod,
    headers,
    credentials: "include",  // CRITICAL: send session cookie
    body,
  });

  // Handle 403 specifically (CSRF failure or session expired)
  if (response.status === 403) {
    // Try refreshing CSRF token once
    clearCSRFToken();
    const freshToken = await ensureCSRFToken();
    headers["X-Frappe-CSRF-Token"] = freshToken;

    const retryResponse = await fetch(url, {
      method: httpMethod,
      headers,
      credentials: "include",
      body,
    });
    if (!retryResponse.ok) {
      throw new FrappeAPIError(403, "Session expired. Please log in again.");
    }
    const retryData: FrappeResponse<T> = await retryResponse.json();
    if (retryData.exc) throw new FrappeAPIError(500, retryData.exc);
    return retryData.message;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new FrappeAPIError(response.status, errorData?.exc || response.statusText);
  }

  const data: FrappeResponse<T> = await response.json();
  if (data.exc) throw new FrappeAPIError(500, data.exc);
  return data.message;
}

export class FrappeAPIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "FrappeAPIError";
  }
}
```

---

## 3. TypeScript Types for DPDP Entities

```typescript
// src/types/dpdp.ts

export interface ConsentPurpose {
  name: string;
  purpose_name: string;
  description: string;
  is_mandatory: 0 | 1;
  validity_days: number;
  legal_basis: string;
}

export interface PrivacyNotice {
  name: string;
  notice_id: string;
  version: string;
  language: string;
  content_html: string;
  purposes: ConsentPurpose[];
}

export type ConsentStatus = "Granted" | "Denied" | "Withdrawn" | "Expired";

export interface ConsentLog {
  name: string;
  user: string;
  purpose: string;
  purpose_name?: string;  // populated from Consent Purpose
  status: ConsentStatus;
  timestamp: string;  // ISO datetime
  expiry_date?: string;
  notice_version?: string;
  channel: string;
}

export type DSRType = "Access" | "Correction" | "Erasure" | "Nomination" | "Grievance";
export type DSRStatus = "Open" | "ID Verified" | "Processing" | "Completed" | "Rejected";

export interface DataSubjectRequest {
  name: string;
  user: string;
  request_type: DSRType;
  description: string;
  status: DSRStatus;
  received_on: string;
  sla_deadline: string;
  identity_verified: 0 | 1;
  resolution_notes?: string;
  rejection_reason?: string;
}

export interface MyDataSummary {
  email: string;
  full_name: string;
  customer_records: number;
  order_count: number;
  data_shared_with: Array<{ processor_name: string; purpose: string }>;
}

export interface DSRSubmitPayload {
  request_type: DSRType;
  description: string;
  nominee_name?: string;
  nominee_email?: string;
}
```

---

## 4. Vue 3 Composables for DPDP Data

```typescript
// src/composables/useDPDP.ts
import { ref, computed } from "vue";
import { frappeCall } from "@/lib/frappeClient";
import type {
  PrivacyNotice, ConsentLog, DataSubjectRequest,
  MyDataSummary, DSRSubmitPayload,
} from "@/types/dpdp";

// ── Consent ────────────────────────────────────────────────────────────────
export function useActiveNotice(language = "English") {
  const notice = ref<PrivacyNotice | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetch() {
    loading.value = true;
    error.value = null;
    try {
      notice.value = await frappeCall<PrivacyNotice>(
        "dpdp_compliance.api.get_active_notice",
        { language },
        { method: "GET" }
      );
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  return { notice, loading, error, fetch };
}

export function useMyConsents() {
  const consents = ref<ConsentLog[]>([]);
  const loading = ref(false);

  async function fetch() {
    loading.value = true;
    try {
      consents.value = await frappeCall<ConsentLog[]>(
        "dpdp_compliance.api.get_my_consents",
        {},
        { method: "GET" }
      );
    } finally {
      loading.value = false;
    }
  }

  async function withdraw(purposeId: string) {
    await frappeCall("dpdp_compliance.api.withdraw_consent", { purpose_id: purposeId });
    await fetch();  // Refresh
  }

  return { consents, loading, fetch, withdraw };
}

// ── DSR ────────────────────────────────────────────────────────────────────
export function useMyDSRs() {
  const dsrs = ref<DataSubjectRequest[]>([]);
  const loading = ref(false);

  async function fetch() {
    loading.value = true;
    try {
      dsrs.value = await frappeCall<DataSubjectRequest[]>(
        "dpdp_compliance.api.get_my_dsrs",
        {},
        { method: "GET" }
      );
    } finally {
      loading.value = false;
    }
  }

  async function submit(payload: DSRSubmitPayload) {
    const result = await frappeCall<{ dsr_id: string; sla_deadline: string }>(
      "dpdp_compliance.dsr.submit_dsr",
      payload
    );
    await fetch();
    return result;
  }

  return { dsrs, loading, fetch, submit };
}

// ── My Data Summary ────────────────────────────────────────────────────────
export function useMyData() {
  const summary = ref<MyDataSummary | null>(null);
  const loading = ref(false);

  async function fetch() {
    loading.value = true;
    try {
      summary.value = await frappeCall<MyDataSummary>(
        "dpdp_compliance.api.get_my_data_summary",
        {},
        { method: "GET" }
      );
    } finally {
      loading.value = false;
    }
  }

  async function downloadData() {
    // Direct link download — no CSRF needed for GET
    const a = document.createElement("a");
    a.href = "/api/method/dpdp_compliance.api.download_my_data";
    a.download = `my_data_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
  }

  return { summary, loading, fetch, downloadData };
}
```

---

## 5. Portal Pages (Vue Router)

### Router (`src/router/index.ts`)
```typescript
import { createRouter, createWebHistory } from "vue-router";
import { ensureCSRFToken } from "@/composables/useCSRF";

const routes = [
  {
    path: "/",
    component: () => import("@/views/PortalHome.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/my-data",
    component: () => import("@/views/MyData.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/privacy-choices",
    component: () => import("@/views/PrivacyChoices.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/my-requests",
    component: () => import("@/views/MyRequests.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/make-request",
    component: () => import("@/views/MakeRequest.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    component: () => import("@/views/Login.vue"),
    meta: { requiresAuth: false },
  },
];

const router = createRouter({
  history: createWebHistory("/dpdp-portal/"),
  routes,
});

// Auth guard
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true;
  try {
    await ensureCSRFToken();
    return true;
  } catch {
    return { path: "/login", query: { redirect: to.fullPath } };
  }
});

export default router;
```

---

## 6. Core Components

### `PrivacyChoices.vue` — Consent Management Screen
```vue
<!-- src/views/PrivacyChoices.vue -->
<template>
  <div class="privacy-choices">
    <h1 class="page-title">My Privacy Choices</h1>
    <p class="page-subtitle">
      Manage what {{ appName }} can do with your personal data.
      Withdrawal takes effect immediately.
    </p>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner />
    </div>

    <div v-else-if="error" class="error-banner" role="alert">
      {{ error }}
    </div>

    <div v-else class="consent-list">
      <ConsentCard
        v-for="consent in consents"
        :key="consent.name"
        :consent="consent"
        @withdraw="handleWithdraw"
      />

      <EmptyState
        v-if="consents.length === 0"
        message="No active consent records found."
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useMyConsents } from "@/composables/useDPDP";
import ConsentCard from "@/components/ConsentCard.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const appName = import.meta.env.VITE_APP_NAME ?? "Our Service";
const { consents, loading, error, fetch, withdraw } = useMyConsents();

onMounted(() => fetch());

async function handleWithdraw(purposeId: string) {
  const confirmed = window.confirm(
    "Withdrawing consent will immediately stop processing for this purpose. Continue?"
  );
  if (!confirmed) return;
  try {
    await withdraw(purposeId);
  } catch (e) {
    alert("Failed to withdraw consent. Please try again.");
  }
}
</script>
```

### `MakeRequest.vue` — DSR Submission Form
```vue
<!-- src/views/MakeRequest.vue -->
<template>
  <div class="make-request">
    <h1 class="page-title">Make a Privacy Request</h1>
    <p class="page-subtitle">
      You have the right to access, correct, or erase your personal data.
    </p>

    <form class="dsr-form" @submit.prevent="handleSubmit" novalidate>
      <!-- Request Type -->
      <div class="form-group">
        <label for="request-type">Request Type *</label>
        <select
          id="request-type"
          v-model="form.request_type"
          :class="{ error: errors.request_type }"
          required
        >
          <option value="">Select a request type</option>
          <option value="Access">Access My Data</option>
          <option value="Correction">Correct My Data</option>
          <option value="Erasure">Delete My Data</option>
          <option value="Nomination">Add a Nominee</option>
          <option value="Grievance">File a Grievance</option>
        </select>
        <span v-if="errors.request_type" class="error-msg">{{ errors.request_type }}</span>
      </div>

      <!-- Warning for Erasure -->
      <div v-if="form.request_type === 'Erasure'" class="warning-box" role="alert">
        ⚠️ Data erasure is irreversible. Financial records required by law (e.g., invoices)
        will be retained but anonymized. Your account will be deactivated.
      </div>

      <!-- Description -->
      <div class="form-group">
        <label for="description">Details *</label>
        <textarea
          id="description"
          v-model="form.description"
          :class="{ error: errors.description }"
          rows="4"
          placeholder="Describe your request in detail..."
          required
        ></textarea>
        <span v-if="errors.description" class="error-msg">{{ errors.description }}</span>
      </div>

      <!-- Nomination fields (conditional) -->
      <template v-if="form.request_type === 'Nomination'">
        <div class="form-group">
          <label for="nominee-name">Nominee Full Name *</label>
          <input
            id="nominee-name"
            v-model="form.nominee_name"
            type="text"
            placeholder="Full legal name of nominee"
          />
        </div>
        <div class="form-group">
          <label for="nominee-email">Nominee Email *</label>
          <input
            id="nominee-email"
            v-model="form.nominee_email"
            type="email"
            placeholder="nominee@example.com"
          />
        </div>
      </template>

      <!-- Submit -->
      <div class="form-actions">
        <button
          type="submit"
          class="btn-primary"
          :disabled="submitting"
        >
          <span v-if="submitting">Submitting...</span>
          <span v-else>Submit Request</span>
        </button>
      </div>
    </form>

    <!-- Success State -->
    <div v-if="submitted" class="success-box" role="status">
      ✅ Request submitted! Reference: <strong>{{ submittedDSRId }}</strong><br />
      An OTP has been sent to your registered email for identity verification.
      <br /><br />
      <router-link to="/my-requests">View My Requests →</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useMyDSRs } from "@/composables/useDPDP";
import type { DSRType } from "@/types/dpdp";

interface DSRForm {
  request_type: DSRType | "";
  description: string;
  nominee_name: string;
  nominee_email: string;
}

const form = reactive<DSRForm>({
  request_type: "",
  description: "",
  nominee_name: "",
  nominee_email: "",
});
const errors = reactive<Partial<DSRForm>>({});
const submitting = ref(false);
const submitted = ref(false);
const submittedDSRId = ref("");

const { submit } = useMyDSRs();

function validate(): boolean {
  Object.keys(errors).forEach((k) => delete errors[k as keyof DSRForm]);
  let valid = true;
  if (!form.request_type) {
    errors.request_type = "Please select a request type.";
    valid = false;
  }
  if (!form.description || form.description.trim().length < 10) {
    errors.description = "Please provide at least 10 characters of detail.";
    valid = false;
  }
  return valid;
}

async function handleSubmit() {
  if (!validate()) return;
  submitting.value = true;
  try {
    const result = await submit({
      request_type: form.request_type as DSRType,
      description: form.description,
      nominee_name: form.nominee_name || undefined,
      nominee_email: form.nominee_email || undefined,
    });
    submittedDSRId.value = result.dsr_id;
    submitted.value = true;
  } catch (e) {
    alert("Failed to submit request: " + (e instanceof Error ? e.message : "Unknown error"));
  } finally {
    submitting.value = false;
  }
}
</script>
```

---

## 7. Serving the Doppio App from Frappe

```python
# dpdp_compliance/www/dpdp-portal.py
import frappe

no_cache = 1  # Prevent Frappe from caching the SPA shell

def get_context(context):
    # Guard: redirect to login if not authenticated
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = (
            f"/login?redirect-to=/dpdp-portal"
        )
        raise frappe.Redirect

    # Pass boot data to Vue app
    context.boot = {
        "user": frappe.session.user,
        "full_name": frappe.get_value("User", frappe.session.user, "full_name"),
        "csrf_token": frappe.sessions.get_csrf_token(),  # Pass token to Vue boot
    }
    context.no_breadcrumbs = True
    context.no_sidebar = True
```

```html
<!-- dpdp_compliance/www/dpdp-portal.html -->
{% extends "templates/web.html" %}
{% block page_content %}
<script>
  // Inject Frappe boot data for Vue app (avoids extra API call for CSRF)
  window.__FRAPPE_BOOT__ = {
    user: "{{ boot.user }}",
    full_name: "{{ boot.full_name }}",
    csrf_token: "{{ boot.csrf_token }}"
  };
</script>
<!-- Vue SPA mount point -->
<div id="dpdp-portal-app"></div>
<!-- Built Doppio assets -->
<script src="/assets/dpdp_compliance/dpdp_portal/assets/index.js" type="module"></script>
<link rel="stylesheet" href="/assets/dpdp_compliance/dpdp_portal/assets/index.css" />
{% endblock %}
```

```typescript
// src/composables/useCSRF.ts — Update to use boot data
export async function ensureCSRFToken(): Promise<string> {
  // BEST: Use token injected by Frappe server into window.__FRAPPE_BOOT__
  const boot = (window as Record<string, unknown>).__FRAPPE_BOOT__ as
    { csrf_token?: string } | undefined;
  
  if (boot?.csrf_token && boot.csrf_token !== "Guest") {
    _csrfToken = boot.csrf_token;
    return _csrfToken;
  }
  
  // Fallback to cookie method (see above)
  // ...
}
```

---

## 8. Doppio Build & Deploy

```json
// package.json scripts
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "type-check": "vue-tsc --noEmit",
    "lint": "eslint src --ext .ts,.vue",
    "deploy": "npm run build && cd /frappe-bench && bench build --app dpdp_compliance"
  }
}
```

```bash
# Build and deploy to Frappe
npm run deploy

# The built assets land in:
# dpdp_compliance/public/dpdp_portal/
# Frappe serves them at: /assets/dpdp_compliance/dpdp_portal/

# After deploy — clear Frappe cache
bench --site your-site.local clear-cache
```

---

## CSRF Security Checklist

- [ ] All POST calls include `X-Frappe-CSRF-Token` header
- [ ] All fetch calls use `credentials: "include"` (sends session cookie)
- [ ] CSRF token sourced from `window.__FRAPPE_BOOT__.csrf_token` (server-injected)
- [ ] Cookie fallback implemented for direct navigation
- [ ] 403 retry logic: invalidate cached token, fetch fresh, retry once
- [ ] No CSRF token hardcoded in source code or committed to git
- [ ] GET requests (read-only) do NOT need CSRF token — only POST/PUT/DELETE
- [ ] Test: Logout → try POST → should get 403 → router redirects to login

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `403 Forbidden` on POST | Missing CSRF token | Ensure `X-Frappe-CSRF-Token` header is set |
| `401 Unauthorized` | Session cookie not sent | Add `credentials: "include"` to all fetch calls |
| `CORS error` in dev | Vite proxy not configured | Check `vite.config.ts` proxy section |
| `net::ERR_NAME_NOT_RESOLVED` in build | Hardcoded `localhost` URL | Use relative paths `/api/...` not `http://localhost:8000/api/...` |
| TypeScript error on `frappe.call` | No TS types for frappe globals | Use `frappeClient.ts` instead of relying on `window.frappe` |
| Vue component not updating after withdraw | Missing `await fetch()` after action | Always re-fetch after mutations |
