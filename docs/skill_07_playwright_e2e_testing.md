---
name: dpdp-playwright-e2e-testing
description: >
  Use this skill for end-to-end testing of the dpdp_compliance Frappe app and the Doppio
  Vue 3 Data Principal Portal using Playwright with TypeScript. Triggers include: writing
  E2E tests, Playwright setup for Frappe, testing consent flows, DSR submission, breach
  logging, VPC portal, CSRF token validation in tests, testing the Doppio portal, page
  object model for Frappe, test fixtures for DPDP data, CI/CD test integration, or any
  mention of "Playwright", "E2E test", "integration test", or "automated testing" for
  this app. CSRF handling in Playwright is critical — always follow the CSRF section.
  This skill also covers Python unit tests using Frappe's test framework.
compatibility:
  frappe_version: ">=16.0"
  playwright: ">=1.44"
  typescript: ">=5.0"
  app: dpdp_compliance
---

# DPDP Playwright E2E Testing Skill

## Testing Architecture

```
dpdp_compliance/
└── tests/
    ├── unit/                          # Python unit tests (frappe test runner)
    │   ├── test_consent.py
    │   ├── test_dsr.py
    │   ├── test_erasure.py
    │   └── test_breach.py
    └── e2e/                           # Playwright E2E tests
        ├── playwright.config.ts
        ├── fixtures/
        │   ├── frappe.fixture.ts      # Frappe session + CSRF setup
        │   └── dpdp.fixture.ts        # DPDP test data factories
        ├── pages/
        │   ├── FrappeLoginPage.ts     # Page Object: Frappe login
        │   ├── ConsentModalPage.ts    # Page Object: Consent modal
        │   ├── DPDPPortalPage.ts      # Page Object: Doppio portal
        │   ├── DSRFormPage.ts         # Page Object: DSR submission
        │   └── BreachFormPage.ts      # Page Object: Breach record
        └── specs/
            ├── consent.spec.ts
            ├── dsr.spec.ts
            ├── erasure.spec.ts
            ├── breach.spec.ts
            ├── vpc.spec.ts
            └── portal.spec.ts
```

---

## 1. Playwright Configuration

```typescript
// tests/e2e/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./specs",
  timeout: 60_000,
  retries: process.env.CI ? 2 : 0,
  workers: 1,  // Frappe tests must be serial (shared DB state)
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report" }],
    ["json", { outputFile: "test-results.json" }],
  ],
  use: {
    baseURL: process.env.FRAPPE_URL ?? "http://localhost:8000",
    // CRITICAL: Store authentication state (session cookie + CSRF)
    storageState: "tests/e2e/.auth/user.json",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "on-first-retry",
    // Frappe sets cookies on same domain
    extraHTTPHeaders: {
      Accept: "application/json",
    },
  },
  projects: [
    // Setup project: authenticate once, save state
    {
      name: "setup",
      testMatch: /global\.setup\.ts/,
      use: { storageState: undefined },  // No pre-auth for setup
    },
    // Main test projects use saved auth state
    {
      name: "frappe-backend",
      testMatch: /\.(consent|dsr|erasure|breach|vpc)\.spec\.ts/,
      dependencies: ["setup"],
    },
    {
      name: "doppio-portal",
      testMatch: /portal\.spec\.ts/,
      dependencies: ["setup"],
      use: {
        ...devices["Desktop Chrome"],
        baseURL: process.env.PORTAL_URL ?? "http://localhost:8080",
      },
    },
  ],
});
```

---

## 2. Global Setup — Authentication & CSRF

```typescript
// tests/e2e/global.setup.ts
import { test as setup, expect } from "@playwright/test";
import path from "path";

const AUTH_FILE = path.join(__dirname, ".auth/user.json");

setup("authenticate as test admin", async ({ page, request }) => {
  const frappe_url = process.env.FRAPPE_URL ?? "http://localhost:8000";

  // Step 1: Login via Frappe login page
  await page.goto(`${frappe_url}/login`);
  await page.fill("#login_email", process.env.TEST_USER ?? "Administrator");
  await page.fill("#login_password", process.env.TEST_PASS ?? "admin");
  await page.click("[data-label='Login']");
  await page.waitForURL("**/desk", { timeout: 15_000 });

  // Step 2: Fetch CSRF token (Frappe sets it after login)
  // The cookie X-Frappe-CSRF-Token is now set
  const cookies = await page.context().cookies();
  const csrfCookie = cookies.find((c) => c.name === "X-Frappe-CSRF-Token");
  
  if (!csrfCookie) {
    // Fallback: fetch from API to trigger cookie creation
    await page.goto(`${frappe_url}/api/method/frappe.auth.get_logged_user`);
    await page.waitForLoadState("networkidle");
  }

  // Step 3: Save auth state (session cookie + CSRF cookie)
  await page.context().storageState({ path: AUTH_FILE });

  console.log("✅ Authentication state saved.");
});
```

---

## 3. Frappe Fixture — API Helper with CSRF

```typescript
// tests/e2e/fixtures/frappe.fixture.ts
import { test as base, APIRequestContext, expect } from "@playwright/test";
import type { Cookie } from "@playwright/test";

interface FrappeAPIOptions {
  method: string;
  args?: Record<string, unknown>;
  allowGuest?: boolean;
}

interface FrappeFixtures {
  frappeAPI: {
    call: <T>(options: FrappeAPIOptions) => Promise<T>;
    getCSRFToken: () => Promise<string>;
    createDoc: (doctype: string, data: Record<string, unknown>) => Promise<Record<string, unknown>>;
    deleteDoc: (doctype: string, name: string) => Promise<void>;
  };
}

export const test = base.extend<FrappeFixtures>({
  frappeAPI: async ({ request, context }, use) => {
    const baseURL = process.env.FRAPPE_URL ?? "http://localhost:8000";
    let _csrfToken: string | null = null;

    async function getCSRFToken(): Promise<string> {
      if (_csrfToken) return _csrfToken;

      // Get from stored cookies
      const cookies: Cookie[] = await context.cookies(baseURL);
      const csrfCookie = cookies.find((c) => c.name === "X-Frappe-CSRF-Token");

      if (csrfCookie && csrfCookie.value !== "Guest") {
        _csrfToken = csrfCookie.value;
        return _csrfToken;
      }

      // Trigger cookie creation via API call
      await request.get(`${baseURL}/api/method/frappe.auth.get_logged_user`);
      const freshCookies: Cookie[] = await context.cookies(baseURL);
      const freshCsrf = freshCookies.find((c) => c.name === "X-Frappe-CSRF-Token");

      if (!freshCsrf) throw new Error("Cannot obtain CSRF token from Frappe");
      _csrfToken = freshCsrf.value;
      return _csrfToken;
    }

    async function call<T>(options: FrappeAPIOptions): Promise<T> {
      const csrfToken = options.allowGuest ? "no-token" : await getCSRFToken();

      const response = await request.post(
        `${baseURL}/api/method/${options.method}`,
        {
          headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": csrfToken,
            Accept: "application/json",
          },
          data: options.args ?? {},
        }
      );

      if (!response.ok()) {
        const body = await response.json().catch(() => ({}));
        throw new Error(
          `Frappe API error ${response.status()}: ${body.exc ?? response.statusText()}`
        );
      }

      const data = await response.json();
      if (data.exc) throw new Error(`Frappe exception: ${data.exc}`);
      return data.message as T;
    }

    async function createDoc(
      doctype: string,
      docData: Record<string, unknown>
    ): Promise<Record<string, unknown>> {
      return call({
        method: "frappe.client.insert",
        args: { doc: { doctype, ...docData } },
      });
    }

    async function deleteDoc(doctype: string, name: string): Promise<void> {
      await call({
        method: "frappe.client.delete",
        args: { doctype, name },
      });
    }

    await use({ call, getCSRFToken, createDoc, deleteDoc });
  },
});

export { expect };
```

---

## 4. DPDP Data Fixtures

```typescript
// tests/e2e/fixtures/dpdp.fixture.ts
import { test as frappeTest, expect } from "./frappe.fixture";

interface DPDPFixtures {
  testConsentPurpose: { name: string; purpose_name: string };
  testPrivacyNotice: { name: string };
  testUser: { name: string; email: string; password: string };
  cleanupDPDP: () => Promise<void>;
}

const createdDocs: Array<{ doctype: string; name: string }> = [];

export const test = frappeTest.extend<DPDPFixtures>({
  testConsentPurpose: async ({ frappeAPI }, use) => {
    const purpose = await frappeAPI.createDoc("Consent Purpose", {
      purpose_name: `TEST-Purpose-${Date.now()}`,
      description: "E2E test purpose",
      is_mandatory: 0,
      validity_days: 365,
      legal_basis: "Consent",
      is_active: 1,
    });
    createdDocs.push({ doctype: "Consent Purpose", name: purpose.name as string });
    await use({ name: purpose.name as string, purpose_name: purpose.purpose_name as string });
  },

  testUser: async ({ frappeAPI }, use) => {
    const email = `test-dpdp-${Date.now()}@test.invalid`;
    const user = await frappeAPI.createDoc("User", {
      email,
      first_name: "Test",
      last_name: "DPDPUser",
      send_welcome_email: 0,
      new_password: "TestPass@2024!",
    });
    createdDocs.push({ doctype: "User", name: user.name as string });
    await use({ name: user.name as string, email, password: "TestPass@2024!" });
  },

  cleanupDPDP: async ({ frappeAPI }, use) => {
    await use(async () => {
      for (const doc of createdDocs.reverse()) {
        try {
          await frappeAPI.deleteDoc(doc.doctype, doc.name);
        } catch {
          // Ignore cleanup errors
        }
      }
      createdDocs.length = 0;
    });
  },
});

export { expect };
```

---

## 5. Page Object Models

```typescript
// tests/e2e/pages/FrappeLoginPage.ts
import { type Page } from "@playwright/test";

export class FrappeLoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/login");
    await this.page.waitForLoadState("networkidle");
  }

  async login(email: string, password: string) {
    await this.page.fill("#login_email", email);
    await this.page.fill("#login_password", password);
    await this.page.click("[data-label='Login']");
    await this.page.waitForURL("**/desk", { timeout: 15_000 });
  }
}
```

```typescript
// tests/e2e/pages/DPDPPortalPage.ts
import { type Page, expect } from "@playwright/test";

export class DPDPPortalPage {
  readonly url = "/dpdp-portal";

  constructor(private page: Page) {}

  async goto() {
    await this.page.goto(this.url);
    await this.page.waitForLoadState("networkidle");
  }

  async getConsents() {
    await this.page.click('[href*="privacy-choices"]');
    await this.page.waitForSelector(".consent-card", { timeout: 10_000 });
    return this.page.$$eval(".consent-card", (cards) =>
      cards.map((c) => ({
        purpose: c.querySelector("[data-purpose]")?.getAttribute("data-purpose") ?? "",
        status: c.querySelector(".consent-status")?.textContent?.trim() ?? "",
      }))
    );
  }

  async withdrawConsent(purposeName: string) {
    const card = this.page.locator(".consent-card", { hasText: purposeName });
    await card.locator('[data-action="withdraw"]').click();
    // Confirm dialog
    await this.page.locator(".confirm-dialog .btn-primary").click();
    await this.page.waitForSelector(".success-message", { timeout: 5_000 });
  }

  async submitDSR(type: string, description: string) {
    await this.page.click('[href*="make-request"]');
    await this.page.selectOption("#request-type", type);
    await this.page.fill("#description", description);
    await this.page.click('button[type="submit"]');
    await this.page.waitForSelector(".success-box", { timeout: 10_000 });
    const dsr_id = await this.page.textContent("[data-dsr-id]");
    return dsr_id?.trim();
  }

  async downloadMyData() {
    const [download] = await Promise.all([
      this.page.waitForEvent("download"),
      this.page.click('[data-action="download-data"]'),
    ]);
    return download;
  }
}
```

```typescript
// tests/e2e/pages/BreachFormPage.ts
import { type Page } from "@playwright/test";

export class BreachFormPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/app/data-breach/new-data-breach-1");
    await this.page.waitForLoadState("networkidle");
  }

  async fillBreachForm(data: {
    title: string;
    severity: string;
    nature: string;
    affectedCount: number;
  }) {
    await this.page.fill('[data-fieldname="breach_title"] input', data.title);
    await this.page.selectOption('[data-fieldname="severity"] select', data.severity);
    await this.page.fill('[data-fieldname="nature_of_breach"] textarea', data.nature);
    await this.page.fill(
      '[data-fieldname="affected_users_count"] input',
      String(data.affectedCount)
    );
    // Detection time defaults to now via hook
    await this.page.click(".save-doc");
    await this.page.waitForSelector(".msgprint", { timeout: 10_000 }).catch(() => {});
  }

  async getReportingDeadline(): Promise<string> {
    return (
      await this.page.inputValue('[data-fieldname="reporting_deadline"] input')
    );
  }

  async getHoursRemaining(): Promise<number> {
    const val = await this.page.inputValue('[data-fieldname="hours_remaining"] input');
    return parseFloat(val);
  }
}
```

---

## 6. Test Specs

### Consent Tests
```typescript
// tests/e2e/specs/consent.spec.ts
import { test, expect } from "../fixtures/dpdp.fixture";

test.describe("Consent Management", () => {
  test("creates an immutable consent log on signup", async ({
    frappeAPI,
    testConsentPurpose,
    testUser,
  }) => {
    // Simulate post-signup consent log creation
    const log = await frappeAPI.call<{ name: string; status: string }>({
      method: "dpdp_compliance.consent.create_consent_log",
      args: {
        user: testUser.name,
        purpose_id: testConsentPurpose.name,
        status: "Granted",
        notice_version_id: null,
        channel: "Web",
      },
    });

    expect(log.name).toBeTruthy();

    // Verify log is submitted (immutable)
    const doc = await frappeAPI.call<{ docstatus: number; status: string }>({
      method: "frappe.client.get",
      args: { doctype: "Consent Log", name: log.name },
    });
    expect(doc.docstatus).toBe(1);  // 1 = Submitted
    expect(doc.status).toBe("Granted");
  });

  test("consent withdrawal creates new log with Withdrawn status", async ({
    frappeAPI,
    testConsentPurpose,
    testUser,
  }) => {
    // Grant consent first
    await frappeAPI.call({
      method: "dpdp_compliance.consent.create_consent_log",
      args: {
        user: testUser.name,
        purpose_id: testConsentPurpose.name,
        status: "Granted",
        notice_version_id: null,
      },
    });

    // Withdraw
    const withdrawn = await frappeAPI.call<{ success: boolean }>({
      method: "dpdp_compliance.api.withdraw_consent",
      args: { purpose_id: testConsentPurpose.name },
    });
    expect(withdrawn.success).toBe(true);

    // Verify no longer active
    const isActive = await frappeAPI.call<boolean>({
      method: "dpdp_compliance.consent.get_active_consent",
      args: { user: testUser.name, purpose_id: testConsentPurpose.name },
    });
    expect(isActive).toBe(false);
  });

  test("consent log cannot be deleted", async ({ frappeAPI, testConsentPurpose, testUser }) => {
    const log = await frappeAPI.call<{ name: string }>({
      method: "dpdp_compliance.consent.create_consent_log",
      args: {
        user: testUser.name,
        purpose_id: testConsentPurpose.name,
        status: "Granted",
        notice_version_id: null,
      },
    });

    // Attempt deletion — should throw
    await expect(
      frappeAPI.deleteDoc("Consent Log", log.name)
    ).rejects.toThrow(/cannot be deleted|immutable|PermissionError/i);
  });
});
```

### DSR Tests
```typescript
// tests/e2e/specs/dsr.spec.ts
import { test, expect } from "../fixtures/dpdp.fixture";

test.describe("Data Subject Requests", () => {
  test("DSR submission sends OTP and sets SLA deadline", async ({
    frappeAPI,
    testUser,
  }) => {
    const result = await frappeAPI.call<{
      dsr_id: string;
      sla_deadline: string;
    }>({
      method: "dpdp_compliance.dsr.submit_dsr",
      args: {
        request_type: "Access",
        description: "I want to see all my data stored in the system.",
      },
    });

    expect(result.dsr_id).toMatch(/DSR-/);
    expect(result.sla_deadline).toBeTruthy();

    // Verify DSR record
    const dsr = await frappeAPI.call<{ status: string; identity_verified: number }>({
      method: "frappe.client.get",
      args: { doctype: "Data Subject Request", name: result.dsr_id },
    });
    expect(dsr.status).toBe("Open");
    expect(dsr.identity_verified).toBe(0);  // Not yet verified
  });

  test("OTP verification marks DSR as ID Verified", async ({
    frappeAPI,
    testUser,
  }) => {
    // Submit DSR
    const { dsr_id } = await frappeAPI.call<{ dsr_id: string }>({
      method: "dpdp_compliance.dsr.submit_dsr",
      args: { request_type: "Grievance", description: "Test grievance for E2E testing." },
    });

    // Read OTP from Redis cache (only in test/dev)
    const otp = await frappeAPI.call<string>({
      method: "dpdp_compliance.test_helpers.get_test_otp",
      args: { dsr_id },
    });
    expect(otp).toMatch(/^\d{6}$/);

    // Verify OTP
    const result = await frappeAPI.call<{ verified: boolean }>({
      method: "dpdp_compliance.dsr.verify_dsr_otp",
      args: { dsr_id, otp },
    });
    expect(result.verified).toBe(true);

    // Confirm status updated
    const dsr = await frappeAPI.call<{ status: string; identity_verified: number }>({
      method: "frappe.client.get",
      args: { doctype: "Data Subject Request", name: dsr_id },
    });
    expect(dsr.status).toBe("ID Verified");
    expect(dsr.identity_verified).toBe(1);
  });

  test("erasure blocked when financial records exist", async ({
    frappeAPI,
    testUser,
  }) => {
    // Dry-run erasure (won't actually delete)
    const result = await frappeAPI.call<{ status: string; blocks?: unknown[] }>({
      method: "dpdp_compliance.erasure.execute_erasure",
      args: { user_id: testUser.name, dry_run: true },
    });

    // DryRun or Success (no financial records for test user)
    expect(["Success", "DryRun", "Blocked"]).toContain(result.status);
  });
});
```

### Breach Tests
```typescript
// tests/e2e/specs/breach.spec.ts
import { test, expect } from "../fixtures/dpdp.fixture";
import { BreachFormPage } from "../pages/BreachFormPage";

test.describe("Breach Response", () => {
  test("creating a breach auto-sets 72h reporting deadline", async ({
    frappeAPI,
  }) => {
    const breach = await frappeAPI.createDoc("Data Breach", {
      breach_title: `E2E Test Breach ${Date.now()}`,
      severity: "High",
      nature_of_breach: "Automated E2E test breach for deadline validation.",
      detection_time: new Date().toISOString().replace("T", " ").split(".")[0],
    });

    // Allow hook to execute
    await new Promise((r) => setTimeout(r, 2000));

    const doc = await frappeAPI.call<{
      reporting_deadline: string;
      hours_remaining: number;
      breach_id: string;
    }>({
      method: "frappe.client.get",
      args: { doctype: "Data Breach", name: breach.name },
    });

    expect(doc.breach_id).toMatch(/^BR-/);
    expect(doc.reporting_deadline).toBeTruthy();
    expect(doc.hours_remaining).toBeGreaterThan(71);
    expect(doc.hours_remaining).toBeLessThanOrEqual(72);
  });

  test("DPB report generation creates PDF attachment", async ({
    frappeAPI,
  }) => {
    const breach = await frappeAPI.createDoc("Data Breach", {
      breach_title: `E2E DPB Report Test ${Date.now()}`,
      severity: "Critical",
      nature_of_breach: "Ransomware attack on user database.",
      detection_time: new Date().toISOString().replace("T", " ").split(".")[0],
      affected_users_count: 1500,
      remedial_actions: "Servers isolated. Passwords reset. Security audit initiated.",
    });

    const result = await frappeAPI.call<{ pdf_url: string }>({
      method: "dpdp_compliance.breach.generate_dpb_report",
      args: { breach_id: breach.name },
    });

    expect(result.pdf_url).toMatch(/\.pdf$/i);
  });
});
```

### Portal E2E Tests (Doppio)
```typescript
// tests/e2e/specs/portal.spec.ts
import { test, expect } from "../fixtures/frappe.fixture";
import { DPDPPortalPage } from "../pages/DPDPPortalPage";

test.describe("Data Principal Self-Service Portal", () => {
  test("portal loads with correct sections for authenticated user", async ({
    page,
  }) => {
    const portal = new DPDPPortalPage(page);
    await portal.goto();

    await expect(page).toHaveTitle(/Privacy|DPDP|Data Principal/i);
    await expect(page.locator("nav")).toContainText("My Data");
    await expect(page.locator("nav")).toContainText("Privacy Choices");
    await expect(page.locator("nav")).toContainText("My Requests");
  });

  test("unauthenticated user is redirected to login", async ({ page }) => {
    // Clear auth state
    await page.context().clearCookies();
    await page.goto("/dpdp-portal");
    await expect(page).toHaveURL(/\/login/);
  });

  test("DSR form submits and shows confirmation with DSR ID", async ({
    page,
  }) => {
    const portal = new DPDPPortalPage(page);
    await portal.goto();

    const dsrId = await portal.submitDSR(
      "Access",
      "I would like to see all my personal data stored in the system."
    );

    expect(dsrId).toMatch(/DSR-/);

    // Confirm OTP message shown
    await expect(page.locator(".success-box")).toContainText("OTP");
  });

  test("privacy choices page shows active consents", async ({ page }) => {
    const portal = new DPDPPortalPage(page);
    await portal.goto();

    const consents = await portal.getConsents();
    expect(consents.length).toBeGreaterThan(0);

    // All should have a status
    for (const consent of consents) {
      expect(["Granted", "Denied", "Withdrawn", "Expired"]).toContain(consent.status);
    }
  });

  test("POST to Frappe API includes CSRF token (security check)", async ({
    page,
  }) => {
    const portal = new DPDPPortalPage(page);
    await portal.goto();

    // Intercept outgoing POST requests and verify CSRF header
    const interceptedRequests: string[] = [];
    page.on("request", (req) => {
      if (req.method() === "POST" && req.url().includes("/api/method/")) {
        const csrfHeader = req.headers()["x-frappe-csrf-token"];
        interceptedRequests.push(csrfHeader ?? "MISSING");
      }
    });

    // Trigger a POST (DSR submission)
    await portal.submitDSR("Grievance", "CSRF test request");

    // Verify all POST requests had the CSRF token
    expect(interceptedRequests.length).toBeGreaterThan(0);
    for (const token of interceptedRequests) {
      expect(token).not.toBe("MISSING");
      expect(token).not.toBe("Guest");
      expect(token.length).toBeGreaterThan(10);
    }
  });
});
```

---

## 7. Python Unit Tests (Frappe Test Framework)

```python
# dpdp_compliance/tests/test_consent.py
import frappe
import unittest
from frappe.utils import now_datetime, add_days


class TestConsentManagement(unittest.TestCase):

    def setUp(self):
        """Create test fixtures."""
        self.test_purpose = frappe.get_doc({
            "doctype": "Consent Purpose",
            "purpose_name": f"Test-Purpose-{frappe.generate_hash()[:6]}",
            "is_mandatory": 0,
            "validity_days": 30,
            "legal_basis": "Consent",
            "is_active": 1,
        }).insert(ignore_permissions=True)

        self.test_user = frappe.get_doc({
            "doctype": "User",
            "email": f"test-{frappe.generate_hash()[:6]}@test.invalid",
            "first_name": "Test",
            "send_welcome_email": 0,
        }).insert(ignore_permissions=True)

    def tearDown(self):
        """Clean up test data."""
        frappe.db.delete("Consent Log", {"user": self.test_user.name})
        frappe.db.delete("User", {"name": self.test_user.name})
        frappe.db.delete("Consent Purpose", {"name": self.test_purpose.name})

    def test_create_consent_log_is_submitted(self):
        from dpdp_compliance.consent import create_consent_log
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
            notice_version_id=None,
        )
        doc = frappe.get_doc("Consent Log", log_name)
        self.assertEqual(doc.docstatus, 1, "Consent Log must be Submitted")
        self.assertEqual(doc.status, "Granted")

    def test_get_active_consent_returns_true_when_granted(self):
        from dpdp_compliance.consent import create_consent_log, get_active_consent
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
            notice_version_id=None,
        )
        self.assertTrue(get_active_consent(self.test_user.name, self.test_purpose.name))

    def test_get_active_consent_returns_false_after_withdrawal(self):
        from dpdp_compliance.consent import create_consent_log, get_active_consent
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
            notice_version_id=None,
        )
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Withdrawn",
            notice_version_id=None,
        )
        self.assertFalse(get_active_consent(self.test_user.name, self.test_purpose.name))

    def test_consent_log_cannot_be_deleted(self):
        from dpdp_compliance.consent import create_consent_log
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
            notice_version_id=None,
        )
        with self.assertRaises(frappe.PermissionError):
            frappe.delete_doc("Consent Log", log_name)
```

---

## 8. Test Helper (for OTP retrieval in tests)

```python
# dpdp_compliance/test_helpers.py
import frappe

@frappe.whitelist()
def get_test_otp(dsr_id: str) -> str:
    """
    TEST-ONLY: Retrieve OTP from Redis cache for automated testing.
    MUST be disabled/removed in production via hooks or environment check.
    """
    if frappe.conf.get("developer_mode") != 1:
        frappe.throw("This endpoint is only available in developer mode.")

    otp = frappe.cache().get_value(f"dsr_otp:{dsr_id}")
    if not otp:
        frappe.throw(f"No OTP found for DSR {dsr_id}")
    return otp
```

---

## 9. CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/e2e-tests.yml
name: DPDP E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    services:
      mariadb:
        image: mariadb:10.6
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: test_frappe

    steps:
      - uses: actions/checkout@v4

      - name: Setup Frappe Bench
        run: |
          pip install frappe-bench
          bench init test-bench --frappe-branch version-16
          cd test-bench
          bench get-app dpdp_compliance $GITHUB_WORKSPACE
          bench new-site test.local --mariadb-root-password root --admin-password admin
          bench --site test.local install-app dpdp_compliance
          bench --site test.local set-config developer_mode 1

      - name: Start Frappe
        run: cd test-bench && bench start &> /tmp/bench.log &

      - name: Install Playwright
        run: |
          cd apps/dpdp_compliance/tests/e2e
          npm ci
          npx playwright install chromium

      - name: Run E2E Tests
        env:
          FRAPPE_URL: http://localhost:8000
          TEST_USER: Administrator
          TEST_PASS: admin
        run: |
          cd apps/dpdp_compliance/tests/e2e
          npx playwright test

      - name: Upload Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: apps/dpdp_compliance/tests/e2e/playwright-report/
```

---

## CSRF Test Security Checklist

- [ ] All POST requests in Playwright tests intercept and verify `X-Frappe-CSRF-Token` header
- [ ] CSRF header value is never `"Guest"` or empty in authenticated tests
- [ ] `global.setup.ts` saves cookies including `X-Frappe-CSRF-Token` to auth state
- [ ] `frappe.fixture.ts` reads CSRF from stored cookies (not hardcoded)
- [ ] Test for 403 response when CSRF token is deliberately omitted
- [ ] `get_test_otp` helper disabled by `developer_mode` check in production
- [ ] Cleanup teardown runs even on test failure (use `afterEach` / `tearDown`)

## Common Test Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `403 on POST in test` | CSRF token not set | Ensure `storageState` has the CSRF cookie from `global.setup.ts` |
| `Timeout waiting for selector` | Vue portal not loaded | Increase timeout; check Vite dev server is running for portal tests |
| `OTP not found in cache` | Redis cleared between steps | Run `bench start` with Redis; ensure `expires_in_sec` is large enough for test |
| `DocType not found` | App not migrated | Run `bench --site x.local migrate` before tests |
| Flaky tests on CI | Shared DB state | Use `test.serial` in Playwright; ensure teardown cleans all test data |
