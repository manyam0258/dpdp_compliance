

**DPDP Act 2023 Compliance App**

Product Requirements Document

*Frappe v16 · Doppio (Vue 3 \+ TypeScript) · Playwright E2E*

| Document Attribute | Value |
| :---- | :---- |
| Version | 2.0 — Full Stack \+ Testing |
| Date | February 2026 |
| Regulatory Basis | DPDP Act 2023 \+ DPDP Rules 2025 |
| Backend | Frappe v16 / ERPNext (Python \+ Frappe JS) |
| Frontend | Doppio framework · Vue 3 · TypeScript · Vite · Tailwind |
| Testing | Playwright (E2E) \+ Frappe Python unittest framework |
| Dev Accelerator | Frappe Assistant Core App (MCP tools for AI-assisted development) |
| Stakeholders | DPO, CTO, Full-Stack Dev Team, Legal, QA |

**Development server details**:

Using WSL in windows 11 having ubuntu 24 having the frappe-bench installed in /home/demo/frappe-v16/frappe-bench-v16 path and list apps present in the site are                dev1-demo1  .

demo@DESKTOP-D4GAJBD:\~/frappe-v16/frappe-bench-v16$ bench version  
drive 0.3.0 develop (776a712)  
erpnext 16.6.1 version-16 (9a0b54c)  
frappe 16.10.2 version-16 (6f63292)  
frappe\_assistant\_core 2.3.1 HEAD (1dbfd67)  
helpdesk 1.20.2 HEAD (7e33c6a)  
hrms 16.4.2 HEAD (7780627)  
ims 0.0.1 main (24d5d18)  
india\_compliance 16.0.0-dev HEAD (3a972c5)  
vms 0.0.1 develop (c266d64)  
demo@DESKTOP-D4GAJBD:\~/frappe-v16/frappe-bench-v16$ bench \--site dev1-demo1 list-apps

frappe                16.10.2    version-16  
erpnext               16.6.1     version-16  
hrms                  16.4.2     HEAD  
india\_compliance      16.0.0-dev HEAD  
frappe\_assistant\_core 2.3.1      HEAD	

and the mcp server details as follows: kindly consider the host dev1-demo1  
{  
    "mcpServers": {  
        "local-erpnext": {  
            "serverUrl": "http://192.168.252.6:8006/api/method/frappe\_assistant\_core.api.fac\_endpoint.handle\_mcp",  
            "headers": {  
                "Authorization": "token 4c1061912014500:69c287e555640b2",  
                "Content-Type": "application/json"  
            }  
        },  
        "dev1-demo1": {  
            "serverUrl": "http://192.168.252.6:8000/api/method/frappe\_assistant\_core.api.fac\_endpoint.handle\_mcp",  
            "headers": {  
                "Authorization": "token bc8fac49005e8ac:2a6c91cf2b2c0b4",  
                "Content-Type": "application/json"  
            }  
        }  
    }  
}

| 1\. Executive Summary & Architecture Overview |
| :---- |

This PRD specifies the complete dpdp\_compliance custom Frappe app — a production-grade implementation of the DPDP Act 2023 for Indian organizations. It covers five compliance modules, a Vue 3 \+ TypeScript self-service portal (built on Doppio), end-to-end Playwright testing, and leverages the Frappe Assistant Core App's MCP capabilities to dramatically accelerate development.

| *Frappe Assistant Core App's MCP server exposes Frappe's DocTypes, DB, and bench commands to AI — enabling developers to scaffold DocTypes, generate migrations, debug hooks, and create test data through natural language prompts during development. This is a development accelerator, not a runtime integration.* |
| :---- |

## **1.1 Technology Stack**

| Layer | Technology | Purpose |
| :---- | :---- | :---- |
| Backend Framework | Frappe v16 \+ ERPNext | DocTypes, hooks, APIs, scheduler |
| Backend Language | Python 3.14+ | Controllers, business logic, tests |
| Frontend Framework | Doppio \+ Vue 3 \+ TypeScript | Data Principal self-service portal |
| Frontend Build | Vite 5 \+ Tailwind CSS | Bundling, HMR, styling |
| E2E Testing | Playwright \+ TypeScript | Full-stack automated tests |
| Unit Testing | Frappe pytest framework | Python unit \+ integration tests |
| Dev Accelerator | Frappe Assistant MCP | AI-assisted scaffolding & debugging |
| Database | MariaDB 10.6+ | Frappe's primary store |
| Cache / Queue | Redis (via Frappe) | OTP cache, email queue, CSRF tokens |
| Identity (VPC) | DigiLocker OAuth2 | Verifiable Parental Consent |

## **1.2 Compliance Modules**

| \# | Module | Coverage | Act Sections |
| :---- | :---- | :---- | :---- |
| **M1** | Consent Management System | Notice, consent capture, withdrawal, legacy remediation | §5, §6 |
| M2 | Data Principal Rights Management | DSR, erasure, access, correction, nomination, grievance | §11–14 |
| **M3** | Breach Response | 72h DPB notification, IRT alerts, principal notification | §8(6) |
| M4 | Data Governance & Inventory | RoPA, encryption, retention, DPIA, processor management | §8, §10 |
| **M5** | Children's Data & VPC | Age verification, DigiLocker, parental consent, minor protection | §9 |
| **F1** | Doppio Portal (Vue 3 \+ TS) | Self-service portal for Data Principals (consent, DSR, data download) | §11–14 |
| **T1** | Playwright E2E Tests | Full coverage: backend APIs, frontend portal, CSRF security | All |

| 2\. Frappe Assistant MCP — Development Accelerator |
| :---- |

| *IMPORTANT CLARIFICATION: Frappe Assistant Core App's MCP features are used as a DEVELOPMENT TOOL to build dpdp\_compliance faster — not as a runtime feature of the app itself. The MCP server connects an AI (like Claude) to the live Frappe bench, enabling AI-assisted development.* |
| :---- |

## **2.1 What the MCP Enables During Development**

| Developer Task | MCP Action (via AI prompt) |
| :---- | :---- |
| Create DocTypes | 'Create Consent Log DocType with these 12 fields, submittable, track changes, DPO-only permissions' → AI calls frappe\_create\_doctype \+ runs migrate |
| Debug Hooks | 'My after\_insert hook on User isn't firing' → AI reads hooks.py \+ error logs \+ fixes \+ clears cache |
| Generate Test Data | 'Create 100 test Consent Log records across 5 users' → AI calls frappe\_create\_test\_data in batch |
| Query Live DB | 'Which users have Marketing consent but not Analytics?' → AI runs SQL query, returns results |
| Write & Test API | 'Write get\_dpo\_dashboard API, then execute it and show the response' → AI writes \+ runs in one step |
| Schema Inspection | 'What personal data fields exist in User, Customer, Employee?' → AI calls frappe\_get\_doctype\_schema for all 3 |
| Add Custom Fields | 'Add date\_of\_birth, is\_minor, vpc\_status to User via Custom Fields (not core DocType)' → AI creates fixtures |

## **2.2 MCP Setup**

1. Install Frappe Assistant Core App: bench get-app frappe\_assistant && bench install-app frappe\_assistant

2. Configure MCP server: bench \--site your-site.local frappe-assistant setup-mcp

3. Add MCP server to Claude Desktop config (stdio transport to bench)

4. Use natural language prompts during development — AI has full Frappe context

| 3\. Doppio Vue 3 \+ TypeScript Data Principal Portal |
| :---- |

The Data Principal Self-Service Portal is built as a Doppio app using Vue 3 with TypeScript. It is served by Frappe at /dpdp-portal and built into the dpdp\_compliance app's public directory. The portal handles all Data Principal-facing interactions: consent management, DSR submission, data access, and nomination.

| *CRITICAL: CSRF Token Handling — All POST requests to Frappe APIs MUST include the X-Frappe-CSRF-Token header. Token is sourced from window.\_\_FRAPPE\_BOOT\_\_.csrf\_token (server-injected by Frappe's web.py) or from the X-Frappe-CSRF-Token cookie. See skill\_03\_doppio\_vue\_typescript\_portal.md for complete implementation.* |
| :---- |

## **3.1 Portal Pages & Routes**

| Route | Page / Component | Functionality |
| :---- | :---- | :---- |
| / | PortalHome.vue | Welcome, quick links to all sections, compliance status banner |
| /my-data | MyData.vue | Data summary (profile, orders, processors); JSON download button (Right to Access §11) |
| /privacy-choices | PrivacyChoices.vue | List of active consents with Withdraw buttons; mandatory consents shown as non-removable |
| /my-requests | MyRequests.vue | History of DSRs with status, SLA deadline, and resolution notes |
| /make-request | MakeRequest.vue | DSR submission form (type, description, nomination fields). OTP confirmation shown on success. |
| /login | Login.vue | Authentication (delegates to Frappe login), redirects on success |
| /vpc-consent | VPCConsent.vue (Frappe www) | Guardian consent portal: shows minor's name, DigiLocker button for Aadhaar-based verification |

## **3.2 CSRF Token Flow**

| Step | Action | Technical Detail |
| :---- | :---- | :---- |
| 1 | User loads portal | Frappe www.py injects csrf\_token into window.\_\_FRAPPE\_BOOT\_\_ |
| 2 | Vue app boots | useCSRF.ts reads token from \_\_FRAPPE\_BOOT\_\_ or cookie fallback |
| 3 | User performs action | frappeClient.ts adds X-Frappe-CSRF-Token header to every POST |
| 4 | 403 received | Token invalidated, fresh token fetched via API, request retried once |
| 5 | Session expires | Router guard detects 401, redirects to /login with redirect param |

## **3.3 Build & Deploy Pipeline**

5. Development: npm run dev in doppio app → Vite proxies /api to Frappe

6. Build: npm run build → outputs to dpdp\_compliance/public/dpdp\_portal/

7. Deploy: bench build \--app dpdp\_compliance → Frappe serves at /assets/dpdp\_compliance/dpdp\_portal/

8. Route: Frappe www/dpdp-portal.py serves the Vue SPA shell with injected boot data

| 4\. Phase-by-Phase Implementation Plan |
| :---- |

| Phase 1: App Bootstrap & Foundation (Weeks 1–3) |
| :---- |

### **4.1.1 Deliverables**

* bench new-app dpdp\_compliance — app skeleton with modules.txt, hooks.py

* DPDP Settings (Single DocType) — all config in one place

* Data Asset DocType — RoPA / data inventory with 4-level classification

* Data Processor DocType — vendor DPA tracking

* Retention Policy DocType — pre-seeded with GST/labour law defaults

* Custom Fields on User — date\_of\_birth, is\_minor, guardian\_email, vpc\_status, account\_status

* create\_dpdp\_roles() — DPO, DPDP Admin roles

* Field-level encryption for Level 4 fields (Aadhaar, PAN, bank account)

### **4.1.2 Frappe Assistant MCP Acceleration**

* Use MCP: 'Create all foundation DocTypes with proper schemas in one batch'

* Use MCP: 'Add custom fields to User via fixtures JSON, not core DocType modification'

* Use MCP: 'Inspect User, Customer, Employee schemas and generate Data Asset fixture data'

### **4.1.3 Tests Delivered**

* Unit: test\_settings.py — validate DPDP Settings single doctype creation

* Unit: test\_data\_asset.py — classification level validation

| Phase 2: Consent Architecture (Weeks 4–8) |
| :---- |

### **4.2.1 Backend Deliverables**

* Consent Purpose DocType (submittable master)

* Privacy Notice DocType (submittable, versioned, language-specific)

* Consent Log DocType (submittable, immutable — no edit/delete after submit)

* consent.py — create\_consent\_log(), get\_active\_consent(), expire\_stale\_consents()

* api.py — get\_active\_notice(), get\_my\_consents(), withdraw\_consent()

* hooks.py — User.after\_insert → process\_signup\_consent()

* Scheduler: daily expire\_stale\_consents, weekly send\_legacy\_consent\_reminders

### **4.2.2 Frontend (Consent Modal — Frappe Web)**

* public/js/consent\_modal.js — intercepts Frappe signup, renders purpose checkboxes

* No pre-ticked optional checkboxes (Section 6 requirement)

* Mandatory purposes shown as checked \+ disabled

### **4.2.3 Tests Delivered**

* Unit: test\_consent.py — grant, withdraw, expire, immutability, mandatory bypass

* E2E: consent.spec.ts — full signup flow, consent modal rendering, log submission

| Phase 3: Data Principal Rights Portal — Backend (Weeks 9–12) |
| :---- |

### **4.3.1 Backend Deliverables**

* Data Subject Request DocType (submittable, SLA timer, ID verification)

* Data Nominee DocType — stores nomination details

* Data Erasure Log DocType — audit trail for anonymization

* dsr.py — submit\_dsr(), verify\_dsr\_otp(), process\_access\_request(), process\_erasure\_request()

* erasure.py — execute\_erasure() with ANONYMIZATION\_MAP, check\_retention\_blocks()

* access\_report.py — generate\_access\_report\_direct()

* Scheduler: daily check\_sla\_breaches()

### **4.3.2 Tests Delivered**

* Unit: test\_dsr.py — submission, OTP verification, SLA calculation

* Unit: test\_erasure.py — anonymization, retention blocks, referential integrity

| Phase 4: Doppio Portal — Vue 3 \+ TypeScript (Weeks 13–17) |
| :---- |

### **4.4.1 Deliverables**

* Doppio app scaffold: Vue 3 \+ TypeScript \+ Vite \+ Tailwind CSS

* src/lib/frappeClient.ts — central API caller with CSRF token management \+ 403 retry

* src/composables/useCSRF.ts — token from \_\_FRAPPE\_BOOT\_\_ or cookie fallback

* src/types/dpdp.ts — TypeScript interfaces for all DPDP entities

* src/composables/useDPDP.ts — useMyConsents(), useMyDSRs(), useMyData()

* PortalHome.vue, MyData.vue, PrivacyChoices.vue, MyRequests.vue, MakeRequest.vue

* Vue Router with auth guard — redirects unauthenticated users to Frappe login

* www/dpdp-portal.py — Frappe server controller injecting CSRF token into boot data

* Build pipeline: outputs to dpdp\_compliance/public/dpdp\_portal/

### **4.4.2 Screen Specifications**

| Screen | Key UI Elements | API Called |
| :---- | :---- | :---- |
| PortalHome | Welcome card, navigation tiles, alert banner | get\_dpo\_dashboard() for user's own summary |
| MyData | Data summary table, processors list, Download JSON button | get\_my\_data\_summary(), download\_my\_data() |
| PrivacyChoices | ConsentCard per purpose: name, status badge, expiry, Withdraw button | get\_my\_consents(), withdraw\_consent() |
| MyRequests | DSR table: type, status, SLA deadline, progress indicator | get\_my\_dsrs() |
| MakeRequest | Request type select, description textarea, conditional nomination fields | submit\_dsr() |

### **4.4.3 Tests Delivered**

* E2E: portal.spec.ts — load test, auth redirect, DSR submission, consent display

* E2E: Security test — all POST requests intercepted to verify X-Frappe-CSRF-Token header

| Phase 5: Breach Response (Weeks 18–20) |
| :---- |

### **4.5.1 Deliverables**

* Data Breach DocType (DPO-only, submittable, auto-deadline)

* breach.py — on\_breach\_creation(), check\_breach\_deadlines(), generate\_dpb\_report(), notify\_affected\_principals()

* 72h escalating alert schedule: hourly scheduler with T+24h, T+66h, T+0 thresholds

* DPB report HTML template → PDF generator

* DPO Dashboard — consent %, open DSRs, breach status, processor DPA health

### **4.5.2 Tests Delivered**

* E2E: breach.spec.ts — creation sets 72h deadline, DPB report generates PDF

| Phase 6: Children's Data & VPC (Weeks 21–23) |
| :---- |

### **4.6.1 Deliverables**

* vpc.py — detect\_minor\_on\_save(), initiate\_vpc(), get\_vpc\_session(), handle\_digilocker\_callback()

* DigiLocker OAuth2 flow: authorization → callback → guardian age verification → account activation

* www/vpc-consent.py \+ vpc-consent.html — guardian consent web page

* www/vpc-callback.py — DigiLocker callback handler

* Prohibited purpose auto-denial for all minor accounts (marketing, analytics, tracking)

* Custom Fields fixtures deployed (date\_of\_birth, is\_minor, etc. on User)

### **4.6.2 Tests Delivered**

* E2E: vpc.spec.ts — minor detection, account suspension, guardian flow (mocked DigiLocker)

| Phase 7: E2E Test Suite & CI/CD (Weeks 24–26) |
| :---- |

### **4.7.1 Playwright Configuration**

* playwright.config.ts — serial workers (shared DB), 3 projects: setup \+ frappe-backend \+ doppio-portal

* global.setup.ts — authenticate once, save storageState with CSRF cookie

* frappe.fixture.ts — frappeAPI helper with CSRF token from cookies \+ 403 retry

* dpdp.fixture.ts — data factories for Consent Purpose, User, DSR

* Page Objects: FrappeLoginPage, DPDPPortalPage, BreachFormPage, DSRFormPage

### **4.7.2 Test Coverage Matrix**

| Test Area | Unit Tests | E2E Tests | Coverage Target |
| :---- | :---- | :---- | :---- |
| Consent Capture | ✅ 5 tests | ✅ 3 specs | 95% |
| Consent Withdrawal | ✅ 3 tests | ✅ 2 specs | 90% |
| DSR Submission | ✅ 4 tests | ✅ 3 specs | 90% |
| OTP Verification | ✅ 3 tests | ✅ 2 specs | 90% |
| Erasure Engine | ✅ 5 tests | ✅ 2 specs | 85% |
| Breach Response | ✅ 4 tests | ✅ 3 specs | 90% |
| Portal UI | — | ✅ 6 specs | 80% |
| CSRF Security | — | ✅ 1 spec (intercept) | 100% |
| VPC / Children | ✅ 3 tests | ✅ 2 specs | 80% |
| Retention Engine | ✅ 3 tests | — | 85% |

| 5\. Skills Inventory (SKILL.md Files) |
| :---- |

The following SKILL.md files accompany this PRD. They provide the AI (Claude \+ Frappe Assistant MCP) with precise, code-level guidance for each development domain.

| \# | Skill File | Domain | Key Trigger Keywords |
| :---- | :---- | :---- | :---- |
| S1 | skill\_01\_frappe\_fullstack\_core.md | Frappe v16 backend: DocTypes, hooks, API, DB, scheduler, bench | Frappe, DocType, hooks.py, bench, frappe.db |
| S2 | skill\_02\_frappe\_assistant\_mcp\_devtool.md | Using Frappe Assistant MCP to accelerate dpdp\_compliance development | Frappe Assistant, MCP, scaffold, dev tool |
| S3 | skill\_03\_doppio\_vue\_typescript\_portal.md | Doppio \+ Vue 3 \+ TypeScript portal, CSRF handling, composables | Doppio, Vue 3, TypeScript, CSRF, portal |
| S4 | skill\_04\_consent\_management.md | Module 1: CMS — Consent Purpose, Privacy Notice, Consent Log | consent, notice, withdrawal, purpose |
| S5 | skill\_05\_data\_rights\_management.md | Module 2: DPRM — DSR, OTP, erasure, anonymization, retention | DSR, erasure, anonymize, OTP, retention |
| S6 | skill\_06\_breach\_governance\_vpc.md | Modules 3+4+5: Breach, Governance, RoPA, encryption, VPC, DigiLocker | breach, 72h, DPB, RoPA, DPIA, VPC, minor |
| S7 | skill\_07\_playwright\_e2e\_testing.md | Playwright E2E tests \+ Python unit tests \+ CI/CD; CSRF in tests | Playwright, E2E, test, CSRF test, CI |

| 6\. Security, NFR & Penalty Reference |
| :---- |

## **6.1 Non-Functional Requirements**

| ID | Requirement | Implementation |
| :---- | :---- | :---- |
| NFR-SEC-01 | Field-Level Encryption | Frappe Password fieldtype (Fernet) for Aadhaar, PAN, bank account fields |
| NFR-SEC-02 | Consent Log Immutability | Submitted DocType \+ on\_trash hook that always throws PermissionError |
| NFR-SEC-03 | CSRF Protection (Portal) | All Vue POST calls include X-Frappe-CSRF-Token; 403 retry with fresh token |
| NFR-SEC-04 | Session Auth (Portal) | credentials:'include' on all fetch; Vue Router guard checks session |
| NFR-SEC-05 | Export Restriction | Export permission disabled for all roles except DPO on personal-data DocTypes |
| NFR-PERF-01 | Consent Check Latency | \<50ms via frappe.cache() — get\_active\_consent() is cached per request |
| NFR-AUD-01 | Audit Trail | Track Changes enabled: Consent Log, DSR, Data Breach, Privacy Notice |
| NFR-TEST-01 | E2E CSRF Verification | Playwright intercepts all POST requests, asserts X-Frappe-CSRF-Token present |

## **6.2 Penalty Reference Matrix**

| Violation | Penalty | Technical Mitigation |
| :---- | :---- | :---- |
| Processing without valid consent | ₹250 Cr | get\_active\_consent() gate before every processing operation |
| Failure to secure personal data | ₹250 Cr | Field encryption, RBAC, VAPT, audit trail |
| Failure to notify DPB within 72h | ₹200 Cr | Auto-deadline, hourly scheduler, escalating alerts |
| Violation of children's data rules | ₹200 Cr | VPC/DigiLocker, minor detection hook, prohibited purpose auto-denial |
| Failure to honor DSR deadline | ₹50 Cr | SLA timer, DPO alerts 24h before breach, overdue escalation |
| Unlawful data retention | ₹150 Cr | Retention engine, daily automated review, DPO ToDo on flags |

# **1\. Executive Overview**

This Product Requirement Document (PRD) defines the complete specification for building the DPDP Compliance Suite — a purpose-built, installable custom Frappe application targeting Frappe Framework version 16\. The document governs the design, behaviour, data model, API contracts, user experience, and acceptance criteria for every product feature.

The Digital Personal Data Protection Act, 2023 and the DPDP Rules notified in November 2025 impose legally enforceable obligations on any organisation that collects, stores, or processes the personal data of individuals in India. Non-compliance exposes Data Fiduciaries to financial penalties ranging up to ₹250 Crore per violation. This product converts those statutory obligations into executable software on the Frappe v16 platform.

## **1.1 Product Vision**

| *Vision Statement: To be the definitive, open-source, Frappe-native compliance operating system for the DPDP Act — enabling any organisation running Frappe or ERPNext v16 to achieve, demonstrate, and sustain data protection compliance without proprietary tooling.* |
| :---- |

## **1.2 Strategic Objectives**

| Objective ID | Objective | Success Metric |
| :---- | :---- | :---- |
| SO-01 | Convert all DPDP Act obligations into configurable Frappe DocTypes and workflows | 100% DPDP Act sections mapped to a product feature |
| SO-02 | Provide a self-service Data Principal portal built on Frappe v16 Web Builder | Portal live; Data Principals can exercise 5 statutory rights unassisted |
| SO-03 | Automate the 72-hour Data Protection Board breach notification window | Zero missed deadlines; automated DPO alert at T-24h |
| SO-04 | Achieve full audit trail immutability for legal evidentiary use | Track Changes \+ Submit lock on all consent and breach records |
| SO-05 | Deliver a reusable, multi-tenant architecture for compliance-as-a-service SaaS | App installable on any Frappe v16 bench with zero code modification |
| SO-06 | Comply natively with Frappe v16 architectural patterns (Workspaces, Dashboards v2, Form Tours) | Zero deprecated v14/v15 APIs in codebase |

## **1.3 Frappe v16 Platform Leverage**

Frappe v16 introduces several architectural features that this product leverages as first-class capabilities:

| Frappe v16 Feature | DPDP Use Case |
| :---- | :---- |
| Workspaces v2 (card-based, drag-drop) | DPO Compliance Cockpit — real-time KPI cards, shortcut links, quick lists |
| Dashboard Charts (new renderer) | Consent coverage trend, DSR SLA compliance, breach heatmap |
| Form Tours | Guided first-time setup for DPO: Privacy Notice creation, Consent Purpose definition |
| Document Follow / Notification Bell | DPO follows Data Breach records; gets in-app alerts at 48h and 72h |
| Customize Form (No-code field additions) | Organisations add industry-specific data fields without forking the app |
| Frappe Query Builder (v16 ORM) | Complex consent eligibility queries without raw SQL |
| Background Jobs (RQ / Redis) | Batch legacy consent remediation emails; anonymisation engine |
| Frappe REST API v2 | Consent check API consumed by external websites and mobile apps |
| Role Profiles | Pre-configured role bundles: DPO Role Profile, Compliance Viewer, Data Principal |
| Web Builder Pages | Privacy Portal and Consent Modal built on Frappe v16 Web Builder — no external framework |

# **2\. Stakeholders, Personas & User Roles**

## **2.1 External Stakeholders**

| Stakeholder | Role Under DPDP Act | Interaction with This Product |
| :---- | :---- | :---- |
| Data Principal | Individual whose personal data is processed | Uses Privacy Portal; submits DSRs; manages consent |
| Data Protection Board of India (DPB) | Regulatory body; receives breach notifications; adjudicates disputes | Receives auto-generated breach reports; reviews audit exports |
| Independent Data Auditor | Audits Significant Data Fiduciaries periodically | Read-only audit view; exports evidence packages |
| Consent Manager | Registered intermediary managing consent on behalf of Data Principals | Consumes Consent Check API; pushes withdrawal events via webhook |
| Data Processor | Third-party vendor processing data on Fiduciary's behalf | Tracked in Data Processor Registry; receives deletion instructions via API |

## **2.2 Internal Personas**

| Persona | Job Title | Primary Goals | Pain Points Solved |
| :---- | :---- | :---- | :---- |
| PA-01 — DPO | Data Protection Officer | Monitor compliance posture; respond to breaches in 72h; oversee DSRs | No single view of consent coverage; manual breach timeline tracking |
| PA-02 — Legal | Legal Counsel / Compliance Manager | Maintain valid Privacy Notices; ensure lawful basis for all processing; manage Board interactions | Version-controlled notices scattered across email; no audit trail |
| PA-03 — IT Admin | Frappe System Administrator | Configure encryption; manage roles; deploy scheduled jobs | No DPDP-specific security configuration guide or tooling |
| PA-04 — Dev Lead | Full-Stack Frappe Developer | Build consent modal; integrate VPC; maintain API contracts | No reference implementation for Frappe v16 consent hooks |
| PA-05 — Data Principal | End User / Customer | View own data; withdraw consent easily; submit erasure request | Buried settings; no clear privacy dashboard |
| PA-06 — Auditor | Internal / External Auditor | Access immutable logs; export evidence; verify SLA compliance | Logs spread across multiple DocTypes; no export function |

## **2.3 User Role Matrix**

| Role (Frappe Role Name) | DocTypes: Full Access | DocTypes: Read Only | DocTypes: No Access |
| :---- | :---- | :---- | :---- |
| DPO Manager | All DPDP DocTypes | User, Customer | — |
| Compliance Viewer | — | All DPDP DocTypes | Data Breach (sensitive fields) |
| Privacy Portal User (Website User) | Own Consent Log (read), Own DSR | Privacy Notice (active) | All others |
| IT Admin | DPDP Settings, Retention Policy | Consent Log, Data Breach | — |
| Auditor (Read-Only) | — | All DPDP DocTypes \+ Version logs | — |
| System Manager | All | All | — |

# **3\. Product Scope**

## **3.1 In-Scope Modules**

| Module ID | Module Name | DPDP Act Sections Addressed | Frappe App Sub-module |
| :---- | :---- | :---- | :---- |
| M-01 | Privacy Governance | Sec 2, 10, Rules 1–3 | governance/ |
| M-02 | Data Inventory & RoPA | Sec 3, 8, Schedule | data\_inventory/ |
| M-03 | Consent Management System (CMS) | Sec 5, 6, Rules 3–4 | consent/ |
| M-04 | Verifiable Parental Consent (VPC) | Sec 9, Rule 10 | consent/vpc/ |
| M-05 | Data Principal Rights (DSR) | Sec 11–14 | rights/ |
| M-06 | Anonymisation & Erasure Engine | Sec 12, Rule 8 | rights/erasure/ |
| M-07 | Data Retention Engine | Sec 8(7), Rule 8 | retention/ |
| M-08 | Data Breach Management | Sec 8(6), Rule 7 | breach/ |
| M-09 | Grievance Redressal | Sec 13 | grievance/ |
| M-10 | Data Processor Governance | Sec 8(2) | processors/ |
| M-11 | DPO Dashboard & Compliance Cockpit | Sec 10 | dashboards/ |
| M-12 | DPIA & Audit (SDF) | Sec 10 | audits/ |
| M-13 | REST API & Webhook Gateway | Rules 3, 4 | api/ |
| M-14 | Privacy Portal (Web) | Sec 11–14 | portal/ |

## **3.2 Out of Scope (v1.0)**

9. Mobile native application (iOS/Android) — web-responsive portal only

10. Direct integration with Data Protection Board of India portal (pending API release)

11. Automated DPIA scoring engine (manual templates provided)

12. Cross-border data transfer risk scoring (registry only)

13. Consent Manager (external intermediary) SaaS platform — only API integration

## **3.3 Regulatory Obligation Coverage Map**

| DPDP Act Section | Obligation | Module | Priority |
| :---- | :---- | :---- | :---- |
| Sec 5 | Notice before/with consent request | M-03 | P0 — Critical |
| Sec 6 | Free, specific, informed, unambiguous consent | M-03 | P0 — Critical |
| Sec 6(4) | Withdrawal ease \= consent ease | M-03 | P0 — Critical |
| Sec 7 | Legitimate use (non-consent processing) | M-02 | P1 — High |
| Sec 8 | Reasonable security safeguards | M-02, M-06 | P0 — Critical |
| Sec 8(6) | Breach notification without delay (72h) | M-08 | P0 — Critical |
| Sec 8(7) | Erase data when purpose served | M-07 | P0 — Critical |
| Sec 9 | Verifiable Parental Consent for children | M-04 | P0 — Critical |
| Sec 10 | SDF obligations: DPO, DPIA, Audit | M-12 | P1 — High |
| Sec 11 | Right to access summary of data | M-05 | P0 — Critical |
| Sec 12 | Right to correction and erasure | M-05, M-06 | P0 — Critical |
| Sec 13 | Grievance redressal mechanism | M-09 | P0 — Critical |
| Sec 14 | Right to nomination | M-05 | P1 — High |
| Rule 3 | Notice content and language requirements | M-03 | P0 — Critical |
| Rule 7 | Breach intimation form and timeline | M-08 | P0 — Critical |
| Rule 10 | Parental consent age verification mechanism | M-04 | P0 — Critical |

# **4\. Information Architecture & Data Model**

## **4.1 Frappe v16 App Structure**

The product is packaged as a single installable Frappe app: dpdp\_compliance. All DocTypes, scripts, APIs, and pages reside within this app, ensuring clean separation from host ERPNext data.

| Directory | Contents | Purpose |
| :---- | :---- | :---- |
| dpdp\_compliance/governance/ | DocTypes: DPDP Settings, Organization Privacy Profile, DPO Record | Organisation-level configuration and fiduciary classification |
| dpdp\_compliance/data\_inventory/ | DocTypes: Data Asset, Personal Data Category, Data Processing Activity, Data Processor | RoPA — Record of Processing Activities |
| dpdp\_compliance/consent/ | DocTypes: Consent Purpose, Privacy Notice, Consent Log; JS: consent\_modal.js | Full consent lifecycle engine |
| dpdp\_compliance/consent/vpc/ | DocType: VPC Request; Python: digilocker.py | Verifiable Parental Consent via DigiLocker |
| dpdp\_compliance/rights/ | DocTypes: Data Subject Request, Nominee Record; Python: dsr\_engine.py | Rights exercise and fulfillment |
| dpdp\_compliance/rights/erasure/ | Python: anonymisation.py; DocType: Erasure Log | Anonymisation engine with retention pre-check |
| dpdp\_compliance/retention/ | DocType: Retention Policy; Python: retention\_engine.py | Scheduled lifecycle enforcement |
| dpdp\_compliance/breach/ | DocType: Data Breach; Python: breach\_engine.py | 72-hour breach response workflow |
| dpdp\_compliance/grievance/ | DocType reuses Data Subject Request (type=Grievance) | Grievance intake and SLA tracking |
| dpdp\_compliance/processors/ | DocType: Data Processor, Processor Sharing Log | Third-party processor accountability |
| dpdp\_compliance/audits/ | DocTypes: DPIA, Audit Record, Risk Register | SDF-level audit management |
| dpdp\_compliance/api/ | Python: consent.py, rights.py, breach.py, webhook.py | Public REST API v2 endpoints |
| dpdp\_compliance/dashboards/ | Python: dashboard.py; JS: dpo\_cockpit.js | DPO Compliance Cockpit |
| dpdp\_compliance/public/ | JS: consent\_modal.js; CSS: privacy\_portal.css | Frontend assets |
| dpdp\_compliance/templates/pages/ | HTML: privacy\_portal.html, vpc\_consent.html | Frappe v16 Web Builder pages |

## **4.2 Complete DocType Catalogue**

### **4.2.1 DPDP Settings (Single DocType — Global Config)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| organization\_name | Data | Yes | Legal name of the Data Fiduciary |
| fiduciary\_classification | Select | Yes | Data Fiduciary / Significant Data Fiduciary |
| dpo\_name | Data | Cond. | Required if SDF |
| dpo\_email | Data | Cond. | DPO public email — shown on Privacy Portal |
| grievance\_officer\_email | Data | Yes | Grievance Officer contact |
| dsr\_sla\_days | Int | Yes | Days to resolve DSR (default: 7\) |
| financial\_retention\_days | Int | Yes | Retention for financial records (default: 2920 \= 8 yrs) |
| legacy\_consent\_deadline | Date | No | Deadline for legacy data remediation campaign |
| consent\_modal\_enabled | Check | Yes | Toggle to enable/disable signup consent modal |
| vpc\_enabled | Check | Yes | Toggle Verifiable Parental Consent flow |
| digilocker\_client\_id | Password | Cond. | DigiLocker OAuth client ID (encrypted) |
| digilocker\_client\_secret | Password | Cond. | DigiLocker OAuth client secret (encrypted) |
| digilocker\_redirect\_uri | Data | Cond. | OAuth callback URL |

### **4.2.2 Consent Purpose (Master)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| purpose\_name | Data | Yes | e.g. Order Fulfilment, Email Marketing, Analytics |
| description | Small Text | Yes | Plain-language explanation displayed to user (SARAL principle) |
| is\_mandatory | Check | No | If Yes: pre-checked and disabled on consent form |
| lawful\_basis | Select | Yes | Consent / Legitimate Use (Sec 7\) / Legal Obligation |
| validity\_days | Int | Yes | Consent duration in days (e.g. 365\) |
| data\_categories | Table MultiSelect | Yes | Linked Personal Data Categories |
| applies\_to\_children | Check | No | If Yes: triggers additional VPC validation |
| is\_active | Check | Yes | Only active purposes appear on signup form |
| version | Int | Auto | Auto-incremented on each save |

### **4.2.3 Privacy Notice (Master — Submittable, Track Changes \= On)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| notice\_id | Data | Auto | PN-YYYY-NNN naming series |
| version | Data | Yes | Semantic version: 1.0, 1.1, 2.0 |
| effective\_date | Date | Yes | Date notice becomes live |
| language | Select | Yes | English / Hindi / Tamil / Telugu / Bengali / Kannada / Marathi / Gujarati |
| content\_html | Text Editor | Yes | Full notice content (WCAG 2.1 AA compliant HTML) |
| linked\_purposes | Table MultiSelect | Yes | Linked Consent Purpose records |
| is\_active | Check | No | Only one active notice per language at a time |
| approved\_by | Link (User) | No | DPO approval user |
| approval\_date | Datetime | No | Auto-set on workflow approval |
| workflow\_state | Data | Auto | Draft / Under Review / Approved / Active / Superseded |

### **4.2.4 Consent Log (Transaction — Submittable, Immutable, Track Changes \= On)**

| *This is the legal evidentiary record of every consent event. It must be Submittable \= Yes. Once submitted, no field can be modified by any user including System Manager. Immutability is enforced via before\_save validation in Python.* |
| :---- |

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| log\_id | Data | Auto | CL-YYYY-NNNNNN naming series |
| user | Link (User) | Yes | The Data Principal |
| purpose | Link (Consent Purpose) | Yes | Specific purpose consented to |
| status | Select | Yes | Granted / Denied / Withdrawn / Expired |
| timestamp | Datetime | Auto | UTC timestamp of action (system-set, not user-editable) |
| ip\_address | Data | Auto | Captured from frappe.request.environ (system-set) |
| user\_agent | Data | Auto | Browser/device string (system-set) |
| channel | Select | Yes | Web / Mobile App / API / Offline |
| notice\_version | Link (Privacy Notice) | Yes | Notice version presented to user |
| expiry\_date | Date | Auto | timestamp \+ purpose.validity\_days |
| is\_minor | Check | No | Set if user DOB indicates age \< 18 |
| parent\_user | Link (User) | Cond. | Parent/guardian — required if is\_minor \= 1 |
| verification\_token | Password | Cond. | DigiLocker OAuth token — required if is\_minor \= 1 |

### **4.2.5 Data Asset (Master — RoPA)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| asset\_name | Data | Yes | e.g. Customer Email Address |
| doctype\_name | Data | Yes | Frappe DocType where field resides (e.g. Customer) |
| field\_name | Data | Yes | DB column name (e.g. email\_id) |
| classification | Select | Yes | Public / Internal / Personal Data / Sensitive Personal Data |
| data\_category | Link (Personal Data Category) | Yes | Linked category record |
| processing\_purpose | Link (Consent Purpose) | Yes | Lawful processing purpose |
| storage\_location | Data | Yes | e.g. MariaDB, AWS S3, Redis Cache |
| is\_encrypted | Check | No | Is field encrypted at rest? |
| encryption\_method | Select | Cond. | Fernet / AES-256 / Frappe Password Field |
| shared\_with\_processors | Table | No | Linked Data Processor records |
| retention\_policy | Link (Retention Policy) | Yes | Linked retention rule |
| cross\_border\_transfer | Check | No | Is data transferred outside India? |
| transfer\_countries | Table | Cond. | Country list if cross\_border \= Yes |

### **4.2.6 Data Subject Request (Transaction — Submittable, Track Changes \= On)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| request\_id | Data | Auto | DSR-YYYY-NNNN naming series |
| user | Link (User) | Yes | Data Principal |
| request\_type | Select | Yes | Access / Correction / Erasure / Nomination / Grievance |
| description | Text | No | User-provided detail of request |
| status | Select | Auto | Open / Identity Verified / Processing / On Hold / Closed / Rejected |
| sla\_due\_date | Date | Auto | submission\_date \+ DPDP Settings.dsr\_sla\_days |
| sla\_breached | Check | Auto | True if closed\_date \> sla\_due\_date |
| assigned\_to | Link (User) | No | DPO team member |
| identity\_verified | Check | Auto | Set after OTP/email verification step |
| verification\_method | Select | No | OTP / Email Link / Aadhaar eKYC |
| resolution\_summary | Text | Cond. | Required on Close |
| rejection\_reason | Text | Cond. | Required on Reject |
| closed\_date | Date | Auto | Set on Close action |
| proof\_document | Attach | No | Data export or confirmation attachment |

### **4.2.7 Data Breach (Transaction — Submittable, Track Changes \= On)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| incident\_id | Data | Auto | BREACH-YYYY-NNN naming series |
| detection\_datetime | Datetime | Yes | T=0: When breach was first identified |
| reporting\_deadline | Datetime | Auto | detection\_datetime \+ 72 hours (system-calculated) |
| severity | Select | Yes | Critical / High / Medium / Low |
| breach\_type | Select | Yes | Unauthorised Access / Data Loss / Ransomware / Accidental Disclosure / Insider Threat |
| affected\_data\_categories | Table MultiSelect | Yes | Linked Data Asset categories |
| affected\_principals\_count | Int | Yes | Estimated number of Data Principals affected |
| geographic\_scope | Data | No | Regions/states/countries of affected individuals |
| nature\_of\_breach | Long Text | Yes | Detailed description (used in Board report) |
| remedial\_actions | Long Text | Yes | Steps taken and planned |
| notified\_board | Check | Auto | Checked when Board notification submitted |
| board\_notification\_datetime | Datetime | Auto | Timestamp of Board notification |
| notified\_principals | Check | Auto | Checked after user notifications sent |
| principal\_notification\_datetime | Datetime | Auto | Timestamp of user notifications |
| status | Select | Auto | Detected / Under Assessment / Contained / Board Notified / Closed |
| irt\_lead | Link (User) | No | Incident Response Team lead |

### **4.2.8 Retention Policy (Master)**

| Field Name | Fieldtype | Mandatory | Description |
| :---- | :---- | :---- | :---- |
| policy\_name | Data | Yes | e.g. Customer Records — 5 Years Post-Service |
| data\_category | Link (Personal Data Category) | Yes | Category this policy governs |
| retention\_period\_days | Int | Yes | Days to retain (e.g. 2920 \= 8 years) |
| legal\_basis | Small Text | Yes | e.g. GST Act Sec 36 mandates 8-year retention |
| action\_on\_expiry | Select | Yes | Anonymise / Hard Delete / Archive to Cold Storage |
| notify\_dpo\_before\_days | Int | No | Alert DPO N days before scheduled erasure |
| is\_active | Check | Yes | Only active policies trigger the scheduler |

### **4.2.9 Supporting DocTypes**

| DocType | Type | Key Fields | Purpose |
| :---- | :---- | :---- | :---- |
| Personal Data Category | Master | category\_name, description, is\_sensitive, applies\_to\_children | Classifies data types for mapping to assets |
| Data Processor | Master | processor\_name, country, services, dpa\_signed, deletion\_supported, api\_endpoint | Third-party processor registry and accountability |
| VPC Request | Transaction | child\_user, parent\_email, token, status, expiry | Tracks DigiLocker parental consent requests |
| Erasure Log | Transaction | original\_user\_hash, anon\_hash, erasure\_date, dsr\_reference, method | Audit trail for every anonymisation/deletion event |
| Nominee Record | Transaction | user, nominee\_name, nominee\_email, relationship, activation\_condition | Right to nomination per Sec 14 |
| DPIA | Transaction | dpia\_name, processing\_activity, risk\_level, risk\_description, mitigation\_steps, approval\_status | Data Protection Impact Assessment for SDF |
| Audit Record | Transaction | audit\_name, auditor, period\_from, period\_to, findings, status, report\_attachment | Independent audit record for SDF compliance |
| Risk Register | Master | risk\_id, description, likelihood, impact, owner, mitigation, residual\_risk | Ongoing risk tracking |
| Processor Sharing Log | Transaction | processor, data\_categories, purpose, shared\_date, deletion\_requested\_date | Tracks each data sharing event with processors |

# **5\. Functional Requirements**

| M-01 — Privacy Governance Module |
| :---- |

## **5.1 Privacy Governance**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-GOV-01 | DPDP Settings Single DocType must be the global configuration hub for all DPDP parameters | P0 | Settings saved; all dependent modules read from this record |
| FR-GOV-02 | System must classify the organisation as Data Fiduciary or Significant Data Fiduciary | P0 | Classification stored; if SDF, DPO and DPIA DocTypes become visible |
| FR-GOV-03 | Grievance Officer email must be publicly accessible via the Privacy Portal | P0 | Portal footer shows correct email from DPDP Settings |
| FR-GOV-04 | DPO Record must support appointment, mandate definition, and contact publication | P1 | DPO record linkable from Privacy Portal's 'Contact DPO' link |
| FR-GOV-05 | System must support multi-entity deployment (separate DPDP Settings per site) | P1 | Each Frappe site has independent DPDP Settings |

| M-02 — Data Inventory & RoPA |
| :---- |

## **5.2 Data Inventory**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-INV-01 | Every personal data field in any Frappe DocType must be registerable in the Data Asset inventory | P0 | DPO can register 'Customer.email\_id' as a Level 3 Data Asset |
| FR-INV-02 | Data Assets must be classified into four levels: Public, Internal, Personal Data, Sensitive Personal Data | P0 | Classification drives field-level security requirements |
| FR-INV-03 | Each Data Asset must link to a Processing Purpose establishing lawful basis | P0 | Cannot save Data Asset without a linked Processing Purpose |
| FR-INV-04 | System must identify all Data Assets without a Retention Policy and surface them in a dashboard alert | P0 | Zero assets without retention policy before go-live (DPO sign-off) |
| FR-INV-05 | Data Processor Registry must track every third-party vendor receiving personal data | P0 | Processor list exportable as evidence for audit |
| FR-INV-06 | Cross-border data transfer flag and destination country must be recorded per Data Asset | P1 | Transfer countries reportable in compliance export |

| M-03 — Consent Management System |
| :---- |

## **5.3 Consent Management**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-CMS-01 | System must render a dynamic, granular consent modal on every web signup form, driven by Consent Purpose and Privacy Notice DocTypes | P0 | Modal renders; all active non-mandatory purposes shown as unchecked checkboxes |
| FR-CMS-02 | Consent must be purpose-specific: separate checkbox per Consent Purpose; no bundled consent | P0 | One Consent Log record created per purpose per user on signup |
| FR-CMS-03 | Mandatory purposes must be pre-checked and non-removable; optional purposes must default to unchecked | P0 | HTML audit confirms no optional purpose has checked attribute |
| FR-CMS-04 | Privacy Notice must be multi-language; system selects notice based on browser Accept-Language header | P0 | Hindi browser receives Hindi notice; English browser receives English notice |
| FR-CMS-05 | Consent Log must be created as a submitted (immutable) document; no edit after submission | P0 | Any attempt to edit a submitted Consent Log returns validation error |
| FR-CMS-06 | Consent withdrawal must be achievable in equal or fewer steps than consent grant | P0 | User withdraws consent in 2 clicks from Privacy Portal |
| FR-CMS-07 | Withdrawal must propagate in real-time: email queue suppression, processor webhook, analytics opt-out | P0 | Within 60 seconds of withdrawal, Email Queue entries cancelled for that user and purpose |
| FR-CMS-08 | Consent expiry must be auto-calculated (timestamp \+ validity\_days) and enforced by a daily scheduler | P0 | Scheduler marks expired Consent Logs; DPO alerted about expiring consents |
| FR-CMS-09 | Legacy user remediation: batch email tool to send consent update requests to all users pre-dating Act commencement | P0 | DPO can trigger batch; all unconsented users receive email within 1 batch job run |
| FR-CMS-10 | Privacy Notice versioning: activating a new version auto-supersedes the prior version | P1 | Cannot have two active notices in the same language simultaneously |

| M-04 — Verifiable Parental Consent (VPC) |
| :---- |

## **5.4 Verifiable Parental Consent**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-VPC-01 | System must detect age \< 18 from Date of Birth field during signup and redirect to VPC flow | P0 | Any DOB yielding age \< 18 triggers VPC; normal signup is blocked |
| FR-VPC-02 | System must generate a time-limited (24h) JWT parental consent link and email it to the provided parent email | P0 | Parent receives email with link; link expires after 24 hours |
| FR-VPC-03 | VPC portal must integrate with DigiLocker OAuth 2.0 API to achieve identity verification of parent | P0 | Parent completes DigiLocker flow; system receives access token |
| FR-VPC-04 | DigiLocker token must be stored in Consent Log.verification\_token (encrypted Password field) | P0 | DB stores encrypted token, not plain text |
| FR-VPC-05 | Minor accounts must have is\_minor \= 1 and restricted processing flags: no behavioural tracking, no targeted advertising | P0 | Minor user's Consent Log shows is\_minor=1; targeted marketing Consent Purpose disabled |
| FR-VPC-06 | VPC Request DocType must track: child user, parent email, token status, VPC completion timestamp | P1 | DPO can audit all VPC requests and their outcomes |

| M-05 — Data Principal Rights (DSR) |
| :---- |

## **5.5 Data Principal Rights**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-DSR-01 | Privacy Portal must provide self-service submission of all five statutory rights: Access, Correction, Erasure, Grievance, Nomination | P0 | Each right has a dedicated portal tab with submission form |
| FR-DSR-02 | Identity Verification (OTP to registered mobile/email) is mandatory before any DSR is accepted | P0 | DSR creation API returns error if OTP not verified; no DSR created for unverified caller |
| FR-DSR-03 | DSR SLA timer must auto-calculate due date from DPDP Settings.dsr\_sla\_days | P0 | sla\_due\_date \= submission\_date \+ configured SLA days (verified in unit test) |
| FR-DSR-04 | DPO receives email notification for every new DSR within 5 minutes | P0 | Email received by DPO within 5 minutes of DSR creation in load tests |
| FR-DSR-05 | SLA breach alert: if DSR not closed 24 hours before due date, system sends escalation email to DPO Manager | P0 | Escalation email received; Open DSR Past SLA count increments in dashboard |
| FR-DSR-06 | Right to Access: system generates a data summary report listing all Data Assets linked to the user | P0 | Report lists asset name, field value (masked), processing purpose, and linked processors |
| FR-DSR-07 | Right to Correction: DPO can trigger correction on linked Frappe DocTypes (Customer, Lead, User) | P1 | Correction propagates to all registered DocTypes holding the field |
| FR-DSR-08 | Nominee Record allows user to designate a person to exercise rights on their behalf | P1 | Nominee record created; nominee can log in and submit DSR on behalf of principal |

| M-06 — Anonymisation & Erasure Engine |
| :---- |

## **5.6 Anonymisation Engine**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-ERA-01 | Before anonymising, system must check all linked financial DocTypes against retention period from DPDP Settings | P0 | Erasure rejected with explanation if Sales Invoice within retention window found |
| FR-ERA-02 | Anonymisation must replace name, email, phone with non-identifying values while preserving referential integrity | P0 | Sales Invoice references Customer record after erasure; no orphaned foreign keys |
| FR-ERA-03 | Anonymised email must use @anonymized.invalid domain to prevent re-identification | P0 | DB shows \[hash\]@anonymized.invalid, not original email |
| FR-ERA-04 | Every anonymisation event must create an Erasure Log record (immutable) | P0 | Erasure Log count increments by 1 per erasure; original\_user\_hash matches user |
| FR-ERA-05 | Erasure engine must propagate deletion signals to all linked Data Processors via webhook | P1 | Processor webhook receives DELETE event within 60 seconds of erasure |
| FR-ERA-06 | System must support Hard Delete for records with zero legal hold (e.g. unqualified leads) | P1 | Lead with no linked transactions deleted cleanly; no orphan records |

| M-07 — Data Retention Engine |
| :---- |

## **5.7 Data Retention**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-RET-01 | Daily scheduler job must scan all Data Assets against their linked Retention Policy and flag expired records | P0 | Scheduler runs daily; log entry created with count of expired records found |
| FR-RET-02 | Three expiry actions must be supported: Anonymise, Hard Delete, Archive to Cold Storage | P0 | Each action verified in UAT against test records |
| FR-RET-03 | DPO pre-alert must be triggered N days before expiry (configured per Retention Policy) | P1 | DPO receives email N days before first record in batch expires |
| FR-RET-04 | Retention enforcement must be skipped for records with an active Legal Hold flag | P0 | Legal Hold record blocks scheduler from acting on linked documents |

| M-08 — Data Breach Management |
| :---- |

## **5.8 Data Breach Management**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-BRE-01 | Reporting deadline must auto-compute as detection\_datetime \+ 72 hours with second-level precision | P0 | reporting\_deadline matches detection\_datetime \+ exactly 72 hours in unit test |
| FR-BRE-02 | Hourly scheduler checks all open Data Breach records; if deadline \< 24h and not notified, DPO receives urgent email | P0 | DPO receives email; email arrives within 1 scheduler cycle of threshold |
| FR-BRE-03 | 'Generate Board Report' button must produce a pre-filled notification document in statutory format per Rule 7 | P0 | Report contains all 8 mandatory fields from Rule 7; DPO can download as PDF/Word |
| FR-BRE-04 | Affected Data Principals must receive a notification email when DPO triggers 'Notify Principals' action | P0 | Email batch sent to all users in affected\_principals list within 30 minutes of trigger |
| FR-BRE-05 | Breach workflow states: Detected → Under Assessment → Contained → Board Notified → Closed | P0 | Workflow state transitions enforced; cannot skip Contained before Board Notified |
| FR-BRE-06 | DPO can follow Data Breach record; Frappe v16 Document Follow sends in-app bell notification at 48h and 72h marks | P1 | Bell notification received in DPO's Frappe notification centre |

| M-09 — Grievance Redressal |
| :---- |

## **5.9 Grievance Redressal**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-GRI-01 | Grievance submission must be available via Privacy Portal and direct email (parsed by Email Account) | P0 | Portal submission creates DSR with type=Grievance; email creates the same via Email Account link |
| FR-GRI-02 | Grievance Officer email from DPDP Settings must be listed on Privacy Portal and visible without login | P0 | Email visible in portal footer; no login required to view |
| FR-GRI-03 | SLA clock starts from submission; DPO receives escalation if not resolved within configured SLA days | P0 | Escalation email sent; sla\_breached \= 1 on DSR record after SLA breach |
| FR-GRI-04 | If Data Principal is unsatisfied, system must surface 'Escalate to Data Protection Board' option with DPB contact details | P1 | Button visible on closed/rejected grievances; links to DPB portal URL |

| M-10 — Data Processor Governance |
| :---- |

## **5.10 Data Processor Governance**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-PRO-01 | All third-party vendors receiving personal data must be registered in the Data Processor DocType | P0 | Data Asset cannot be saved with shared\_with\_processors populated by an unregistered processor |
| FR-PRO-02 | Processor Sharing Log must record every data sharing event with timestamp and purpose | P1 | Log entry created whenever data asset is shared with processor via API |
| FR-PRO-03 | Deletion propagation: when erasure is triggered, system sends webhook to each processor's API endpoint with DELETE instruction | P0 | Processor webhook receives event; Processor Sharing Log shows deletion\_requested\_date |
| FR-PRO-04 | DPO can generate a Processor Compliance Report listing all processors, their DPDP status, and pending deletion requests | P1 | Report exportable; shows processors with overdue deletion requests highlighted |

| M-11 — DPO Dashboard & Compliance Cockpit |
| :---- |

## **5.11 DPO Dashboard**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-DPO-01 | Frappe v16 Workspace 'DPDP Compliance Cockpit' must show 6 KPI number cards with real-time data | P0 | All 6 cards display accurate counts matching manual DB queries |
| FR-DPO-02 | KPI 1 — Consent Coverage %: (Active Granted Consent Logs / Total Active Users) × 100 | P0 | Percentage matches manual calculation; threshold \< 80% shows red card |
| FR-DPO-03 | KPI 2 — Open DSRs Past SLA: count of DSR records with status \!= Closed and sla\_due\_date \< today | P0 | Count matches; clicking card opens filtered DSR list |
| FR-DPO-04 | KPI 3 — Active Data Breaches: count of Data Breach records not in Closed state | P0 | Card shows count; red background if \> 0 |
| FR-DPO-05 | KPI 4 — Consents Expiring in 30 Days: count requiring renewal campaign | P1 | Count correct; DPO can trigger renewal emails from card action |
| FR-DPO-06 | KPI 5 — Data Assets Without Retention Policy: count of uncovered assets | P0 | Must be zero before go-live; list drills down to uncovered assets |
| FR-DPO-07 | KPI 6 — Processors With Pending Deletion Requests: overdue deletion instructions | P1 | Processors with deletion\_requested\_date \> 30 days ago highlighted |
| FR-DPO-08 | Dashboard must include a Line Chart showing Consent Coverage trend over last 90 days | P1 | Chart renders with correct historical data from Consent Log timestamps |

| M-12 — DPIA & Audit (Significant Data Fiduciaries) |
| :---- |

## **5.12 DPIA & Audit**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-AUD-01 | DPIA DocType must support: processing activity link, risk level, risk description, mitigation steps, approval workflow | P1 | DPIA submitted with approval workflow; approved by DPO |
| FR-AUD-02 | Audit Record DocType must support: auditor details, period, findings, status, report attachment | P1 | Audit record created; PDF attachment uploaded |
| FR-AUD-03 | DPIA and Audit modules must only be visible in Workspace when fiduciary\_classification \= SDF | P1 | Non-SDF organisation does not see DPIA menu items |
| FR-AUD-04 | Risk Register must allow ongoing risk tracking with likelihood, impact, owner, and residual risk fields | P1 | Risk Register exportable as evidence for independent auditor |

| M-13 — REST API & Webhook Gateway |
| :---- |

## **5.13 API Gateway**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-API-01 | GET /api/v1/dpdp/consent/check — Returns allowed:true/false for a given user and purpose | P0 | Response time \< 50ms under normal load; correct result verified in integration test |
| FR-API-02 | POST /api/v1/dpdp/consent/log — Creates Consent Log record from external system event | P0 | Creates Consent Log; returns log\_id; rejects unauthenticated requests with 403 |
| FR-API-03 | POST /api/v1/dpdp/rights/request — Submits DSR from external portal or mobile app | P0 | Creates DSR; returns request\_id; validates OTP token in payload |
| FR-API-04 | POST /api/v1/dpdp/breach/report — Reports breach from security monitoring system | P0 | Creates Data Breach; auto-sets reporting\_deadline; DPO receives email |
| FR-API-05 | POST /api/v1/dpdp/consent/withdraw — Withdraws specific consent purpose for user | P0 | Creates Withdrawal Consent Log; triggers propagation within 60s |
| FR-API-06 | Webhook outbound: CONSENT\_WITHDRAWN event pushed to all registered processor endpoints | P0 | Webhook fires within 60 seconds; retry 3x on failure; logged in Processor Sharing Log |
| FR-API-07 | All API endpoints must use Frappe REST API v2 authentication (API Key \+ API Secret) | P0 | Requests without valid API key return 403; no guest access to any DPDP endpoint |
| FR-API-08 | Rate limiting: max 100 consent check requests per minute per API key | P1 | 101st request returns 429 Too Many Requests |

| M-14 — Privacy Portal (Frappe v16 Web Builder) |
| :---- |

## **5.14 Privacy Portal**

| FR-ID | Requirement | Priority | Acceptance Criterion |
| :---- | :---- | :---- | :---- |
| FR-POR-01 | Privacy Portal at /privacy-portal must be built on Frappe v16 Web Builder; no external React/Vue framework | P0 | Portal loads with zero JS framework CDN calls outside Frappe core |
| FR-POR-02 | Portal requires login; guest users redirected to /login with return\_url parameter | P0 | Unauthenticated access redirects; after login, returns to portal |
| FR-POR-03 | Portal Tab 1 — My Data: lists all Data Assets linked to user with field name, classification, and purpose | P0 | List populated from Data Asset inventory; no data values shown (summary only per Sec 11\) |
| FR-POR-04 | Portal Tab 2 — My Consents: shows all Consent Log records with toggle to withdraw per purpose | P0 | Toggle triggers withdrawal API; UI updates within 2 seconds |
| FR-POR-05 | Portal Tab 3 — My Requests: shows all DSRs with status, type, and SLA due date | P0 | List accurate; clicking a request shows full history |
| FR-POR-06 | Portal Tab 4 — New Request: form to submit Access, Correction, Erasure, Nomination, or Grievance | P0 | OTP verification gate present; form submits correctly |
| FR-POR-07 | Portal must be WCAG 2.1 AA compliant and responsive on mobile (375px minimum width) | P1 | Lighthouse accessibility score \>= 90; renders on iPhone SE (375px) |
| FR-POR-08 | Portal footer must always show Grievance Officer email and link to Privacy Notice (active, current language) | P0 | Footer visible on all portal tabs without login |

# **6\. Non-Functional Requirements**

## **6.1 Security Requirements**

| NFR-ID | Category | Requirement | Verification |
| :---- | :---- | :---- | :---- |
| NFR-SEC-01 | Encryption at Rest | All Sensitive Personal Data fields (Aadhaar, PAN, financial) must use Frappe v16 Password field type (Fernet encryption) | DB query confirms no plaintext sensitive values |
| NFR-SEC-02 | Encryption in Transit | All communication between browser, Frappe server, and DigiLocker API must use TLS 1.2 minimum | SSL Labs grade A- or above on production URL |
| NFR-SEC-03 | Field-Level Access | Consent Log fields ip\_address and user\_agent must not be exposed in list view; accessible only in form view by DPO Manager role | Role test: Compliance Viewer cannot see ip\_address in list |
| NFR-SEC-04 | Session Security | Privacy Portal session timeout: 15 minutes of inactivity | Session cookie expires after 15 min idle; user redirected to login |
| NFR-SEC-05 | VAPT | Internal VAPT scan before go-live; zero Critical or High findings permitted | VAPT report attached to production deployment checklist |
| NFR-SEC-06 | Audit Log Integrity | Frappe Version (audit log) records must be retained for minimum 3 years per expected DPDP Rules requirement | Retention policy set on Version DocType; auto-purge disabled for DPDP DocTypes |

## **6.2 Performance Requirements**

| NFR-ID | Requirement | Target | Measurement |
| :---- | :---- | :---- | :---- |
| NFR-PERF-01 | Consent check API response time | \< 50ms at p99 under 100 concurrent requests | Load test with Locust: 100 users, 60-second ramp |
| NFR-PERF-02 | Privacy Portal initial page load | \< 2 seconds on 4G connection | Lighthouse Performance score \>= 75 on mobile |
| NFR-PERF-03 | Consent modal render time | \< 500ms from page load to modal visible | Browser DevTools network waterfall |
| NFR-PERF-04 | Batch legacy consent emails | 1000 emails dispatched per background job run | Frappe Background Job log shows completion time |
| NFR-PERF-05 | Anonymisation engine | Complete anonymisation of one user record \< 5 seconds | Timed in staging with 10,000 linked documents |

## **6.3 Reliability & Availability**

| NFR-ID | Requirement | Target |
| :---- | :---- | :---- |
| NFR-REL-01 | Consent Log creation availability | 99.9% uptime during business hours; failure returns graceful error, not data loss |
| NFR-REL-02 | Breach deadline scheduler | Hourly scheduler must not miss more than 1 consecutive cycle; missed cycles trigger PagerDuty/email alert |
| NFR-REL-03 | Webhook delivery | At least-once delivery with 3 retries on failure; failed webhooks logged and alertable |
| NFR-REL-04 | Database backup | Consent Logs and Data Breach records included in daily encrypted backup with 30-day retention |

## **6.4 Scalability**

14. Consent Log table must support 10 million records without query degradation (indexed on user, purpose, status, expiry\_date)

15. Batch email engine must scale horizontally using Frappe background workers

16. API Gateway must support 500 requests per second with Redis caching for consent check responses

## **6.5 Localisation**

| NFR-ID | Requirement |
| :---- | :---- |
| NFR-L10N-01 | Privacy Notice must support all 8th Schedule languages: English, Hindi, Tamil, Telugu, Bengali, Kannada, Marathi, Gujarati |
| NFR-L10N-02 | Consent modal language selection based on browser Accept-Language header with English fallback |
| NFR-L10N-03 | All user-facing error messages and notifications must be translatable via Frappe Translation system |
| NFR-L10N-04 | Date and time displays in Privacy Portal must use IST (UTC+5:30) with ISO 8601 format |

## **6.6 Frappe v16 Compatibility**

| NFR-ID | Requirement |
| :---- | :---- |
| NFR-FRP-01 | App must declare frappe\>=16.0.0 in requirements.txt; no deprecated v14/v15 APIs used |
| NFR-FRP-02 | Workspaces must use v16 JSON-based Workspace builder format (not legacy Module Page) |
| NFR-FRP-03 | Dashboard charts must use v16 Frappe Charts (not embedded Chartjs workarounds) |
| NFR-FRP-04 | Web pages must use Frappe v16 Web Builder (Jinja \+ Bootstrap 5 base template) |
| NFR-FRP-05 | Background jobs must use frappe.enqueue() with Frappe RQ worker pattern — no direct Celery calls |
| NFR-FRP-06 | REST APIs must expose via @frappe.whitelist() with allow\_guest=False for all protected endpoints |

# **7\. User Stories & Epics**

All stories follow the format: As a \[persona\], I want to \[action\] so that \[outcome\]. Each story maps to one or more functional requirements and one or more DocTypes.

## **Epic E-01: Organisation Governance Setup**

| Story ID | User Story | FR Mapping | Story Points |
| :---- | :---- | :---- | :---- |
| US-GOV-01 | As a DPO, I want to configure DPDP Settings once so that all modules derive their parameters from a single source of truth | FR-GOV-01 | 3 |
| US-GOV-02 | As a DPO, I want to classify our organisation as SDF so that the DPIA and Audit modules activate automatically | FR-GOV-02 | 2 |
| US-GOV-03 | As a Data Principal, I want to see the Grievance Officer email on the Privacy Portal without logging in so that I can report concerns easily | FR-GOV-03 | 1 |

## **Epic E-02: Consent Lifecycle**

| Story ID | User Story | FR Mapping | Story Points |
| :---- | :---- | :---- | :---- |
| US-CON-01 | As a new user, I want to see a clear, plain-language consent modal during signup with separate checkboxes per purpose so that I can make an informed choice | FR-CMS-01,02,03 | 5 |
| US-CON-02 | As a user browsing in Hindi, I want the consent modal and Privacy Notice shown in Hindi so that I understand what I am consenting to | FR-CMS-04 | 3 |
| US-CON-03 | As a Data Principal, I want to withdraw my Marketing consent in 2 clicks from My Consents tab so that my preference is respected immediately | FR-CMS-06, FR-CMS-07 | 5 |
| US-CON-04 | As a DPO, I want to run a batch email campaign to all legacy users who have not given consent so that our data is remediated before the Act deadline | FR-CMS-09 | 5 |
| US-CON-05 | As a Legal Counsel, I want to publish a new version of the Privacy Notice so that the old version is automatically superseded and the new one becomes active | FR-CMS-10 | 3 |
| US-CON-06 | As a DPO, I want an alert 30 days before a large batch of consents expire so that I can run a renewal campaign proactively | FR-CMS-08 | 3 |

## **Epic E-03: Children & Parental Consent**

| Story ID | User Story | FR Mapping | Story Points |
| :---- | :---- | :---- | :---- |
| US-VPC-01 | As a 14-year-old trying to sign up, I want the system to ask for my parent's approval so that my account is protected and legally valid | FR-VPC-01 | 3 |
| US-VPC-02 | As a parent, I want to receive a secure email link and verify my identity via DigiLocker so that I can approve my child's account without visiting any office | FR-VPC-02, FR-VPC-03 | 8 |
| US-VPC-03 | As a DPO, I want all minor accounts to be automatically restricted from targeted advertising so that we comply with Section 9 without manual intervention | FR-VPC-05 | 3 |

## **Epic E-04: Data Principal Rights**

| Story ID | User Story | FR Mapping | Story Points |
| :---- | :---- | :---- | :---- |
| US-DSR-01 | As a Data Principal, I want to submit a Right to Access request via the Privacy Portal after verifying my identity with an OTP so that I can see what data is held about me | FR-DSR-01, FR-DSR-02 | 5 |
| US-DSR-02 | As a Data Principal, I want to request deletion of my account and receive confirmation within 7 days so that my data is erased when I no longer use the service | FR-DSR-01, FR-ERA-01 to 04 | 8 |
| US-DSR-03 | As a DPO, I want to receive an escalation email if a DSR is not closed 24 hours before its SLA deadline so that we never breach the statutory timeline | FR-DSR-05 | 3 |
| US-DSR-04 | As an elderly user, I want to nominate my son to manage my data rights so that he can exercise them on my behalf if I become incapacitated | FR-DSR-08 | 3 |

## **Epic E-05: Breach Response**

| Story ID | User Story | FR Mapping | Story Points |
| :---- | :---- | :---- | :---- |
| US-BRE-01 | As an IT Security Officer, I want to log a detected breach in Frappe and have the 72-hour Board notification deadline auto-calculated so that I never miss the statutory window | FR-BRE-01 | 3 |
| US-BRE-02 | As a DPO, I want to receive an urgent in-app and email notification when a breach deadline is less than 24 hours away so that I can prioritise it above all other work | FR-BRE-02, FR-BRE-06 | 3 |
| US-BRE-03 | As a Legal Counsel, I want to click one button and generate the statutory Board notification form pre-filled from the breach record so that I do not have to manually type the report | FR-BRE-03 | 5 |

# **8\. Workflow Definitions**

## **8.1 Consent Log Lifecycle**

| State | Triggered By | Allowed Transitions | Role Required |
| :---- | :---- | :---- | :---- |
| Draft | New document created | → Submitted | System (auto on insert) |
| Submitted (Granted) | Consent given by user | → Withdrawn, → Expired | System / Data Principal via API |
| Withdrawn | User action via portal or API | → (Terminal state) | System / Data Principal |
| Expired | Daily scheduler (expiry\_date \< today) | → (Terminal state) | System |

## **8.2 Privacy Notice Lifecycle**

| State | Triggered By | Allowed Transitions | Role Required |
| :---- | :---- | :---- | :---- |
| Draft | New notice created by Legal | → Under Review | Legal / DPO Manager |
| Under Review | Legal submits for approval | → Approved, → Draft (rejection) | DPO Manager |
| Approved | DPO approves | → Active | DPO Manager |
| Active | DPO activates (prior Active → Superseded) | → Superseded | DPO Manager |
| Superseded | New notice activated | → (Read-only) | System |

## **8.3 Data Subject Request Lifecycle**

| State | Triggered By | Allowed Transitions | Role Required |
| :---- | :---- | :---- | :---- |
| Open | User submits via portal | → Identity Verified | System (after OTP verified) |
| Identity Verified | OTP confirmed | → Processing, → On Hold | DPO Manager |
| Processing | DPO assigns and begins work | → Closed, → Rejected | DPO Manager |
| On Hold | Waiting for information from user | → Processing | DPO Manager |
| Closed | Resolution complete | → (Terminal) | DPO Manager |
| Rejected | Legal hold or invalid request | → (Terminal) | DPO Manager |

## **8.4 Data Breach Lifecycle**

| State | Triggered By | Allowed Transitions | Role Required |
| :---- | :---- | :---- | :---- |
| Detected | IT Security / Monitoring system | → Under Assessment | IT Admin / DPO Manager |
| Under Assessment | IRT convened; severity classified | → Contained | DPO Manager |
| Contained | Technical mitigation applied | → Board Notified | DPO Manager / Legal |
| Board Notified | Board report submitted | → Closed | DPO Manager |
| Closed | Remediation complete; principals notified | → (Terminal) | DPO Manager |

# **9\. Screen Specifications**

This section defines every user-facing screen with layout, components, data sources, and interaction logic.

## **9.1 SCR-01 — DPDP Compliance Cockpit (Frappe v16 Workspace)**

| Attribute | Value |
| :---- | :---- |
| URL | Desk \> DPDP Compliance (Workspace) |
| Access Role | DPO Manager, Compliance Viewer |
| Layout | Frappe v16 Workspace with Card sections: Shortcuts, Number Cards, Charts, Quick Lists |

| Component | Type | Data Source | Alert Threshold |
| :---- | :---- | :---- | :---- |
| Consent Coverage % | Number Card | api.dashboard.get\_consent\_coverage() | Red if \< 80% |
| Open DSRs Past SLA | Number Card | api.dashboard.get\_overdue\_dsrs() | Red if \> 0 |
| Active Breaches | Number Card | api.dashboard.get\_active\_breaches() | Red if \> 0 |
| Consents Expiring 30d | Number Card | api.dashboard.get\_expiring\_consents() | Amber if \> 100 |
| Assets Without Policy | Number Card | api.dashboard.get\_uncovered\_assets() | Red if \> 0 |
| Consent Coverage Trend | Line Chart | Consent Log timestamps — 90 day window | N/A |
| Recent DSRs | Quick List | Data Subject Request — last 10 by creation | Status column colour-coded |
| Shortcuts | Link Cards | New Consent Purpose, New Breach, Manage Legacy Users | N/A |

## **9.2 SCR-02 — Signup Consent Modal (Web Page Overlay)**

| Attribute | Value |
| :---- | :---- |
| URL | Injected on /signup via app\_include\_js hook |
| Access Role | Guest (pre-login) |
| Framework | Plain JavaScript \+ Frappe v16 dialog/modal utility |
| Data Source | Privacy Notice (active, language-matched) \+ Consent Purpose (active) |

| UI Element | Behaviour | Validation Rule |
| :---- | :---- | :---- |
| Notice Title \+ Summary | Static HTML from Privacy Notice.content\_html (first 200 chars) \+ 'Read More' link | N/A |
| Purpose Checkbox — Mandatory | Pre-checked; disabled; label shows '(Required)' | Cannot be unchecked |
| Purpose Checkbox — Optional | Unchecked by default; user can check | No validation; unchecked \= Denied consent log |
| Date of Birth Field | Triggers age calculation on blur | If age \< 18: freeze submit; show VPC flow |
| 'Accept & Continue' Button | On click: submits all checked purposes to /api/v1/dpdp/consent/log | At least one mandatory purpose must exist |
| 'View Full Notice' Link | Opens Privacy Notice in new tab/modal | N/A |

## **9.3 SCR-03 — Privacy Portal (Frappe v16 Web Builder — Authenticated)**

| Attribute | Value |
| :---- | :---- |
| URL | /privacy-portal |
| Access | Logged-in Website Users only; redirect to /login if Guest |
| Framework | Frappe v16 Web Builder — Jinja template \+ Bootstrap 5 |

| Tab | Content | Key Interaction |
| :---- | :---- | :---- |
| My Data | List of all Data Assets linked to user: asset name, classification, processing purpose, linked processors | Read-only; no data values shown (summary per Sec 11\) |
| My Consents | List of all Consent Log records with purpose name, status, expiry date, and toggle | Toggle OFF → API call to withdraw; confirmation email sent |
| My Requests | Table of all DSRs: ID, type, status, submitted date, SLA due date | Click row → read-only DSR detail view |
| New Request | Request type dropdown; description field; 'Get OTP' button; OTP field; 'Submit' button | OTP gate enforced; submit disabled until OTP verified |
| My Nominee | Form: nominee name, email, relationship, activation condition | Save → creates/updates Nominee Record |

## **9.4 SCR-04 — VPC Consent Portal (/vpc-consent)**

| UI Step | Content | Backend Action |
| :---- | :---- | :---- |
| Step 1 | 'Your child \[Name\] is requesting an account. Please verify your identity.' \+ Verify via DigiLocker button | Validate JWT token from URL parameter; display child's name from DB |
| Step 2 | Redirect to DigiLocker OAuth 2.0 authorisation URL | Frappe generates OAuth state parameter; stores in Redis |
| Step 3 | DigiLocker callback: success screen 'Identity Verified. Your child's account is now active.' | Store DigiLocker token in VPC Request; activate child user; create Consent Log with VPC token |
| Step 4 (Error) | If JWT expired: 'This link has expired. Please ask your child to restart the signup process.' | No action taken; error logged |

## **9.5 SCR-05 — Data Breach Form (Frappe Desk)**

| UI Section | Fields Shown | Behaviour |
| :---- | :---- | :---- |
| Incident Details | incident\_id (auto), detection\_datetime, severity, breach\_type | reporting\_deadline auto-populates 72h after detection\_datetime is saved |
| Scope | affected\_data\_categories, affected\_principals\_count, geographic\_scope | Table MultiSelect for categories |
| Description | nature\_of\_breach, remedial\_actions | Long Text fields; mandatory before workflow advances |
| Timeline | reporting\_deadline (read-only), board\_notification\_datetime, principal\_notification\_datetime | Read-only computed fields |
| Status Bar | Frappe v16 Status Bar showing workflow state | State colour-coded: Detected=Red, Contained=Amber, Closed=Green |
| Action Buttons | Generate Board Report, Notify Principals, Follow (Document Follow v16) | Generate Board Report: opens print format; Notify Principals: triggers batch email |

# **10\. API Specifications**

All APIs are implemented as Frappe @frappe.whitelist() methods exposed via the standard Frappe REST API v2 path: /api/method/dpdp\_compliance.api.\[module\].\[function\]

## **10.1 Consent API**

| Endpoint | Method | Auth | Request Payload | Response | Error Codes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| dpdp\_compliance.api.consent.check | GET | API Key | user (str), purpose (str) | { allowed: bool, expiry\_date: date|null } | 403 Unauthorized, 404 Purpose not found |
| dpdp\_compliance.api.consent.log | POST | API Key | user, purpose, status, channel, notice\_version | { log\_id: str, status: str } | 400 Invalid payload, 409 Duplicate log |
| dpdp\_compliance.api.consent.withdraw | POST | Session/API Key | purpose | { status: 'withdrawn', log\_id: str } | 404 No active consent found |
| dpdp\_compliance.api.consent.get\_active\_notice | GET | Guest | language (optional) | { name, version, content\_html, purposes\[\] } | 404 No active notice |

## **10.2 Rights API**

| Endpoint | Method | Auth | Request Payload | Response | Error Codes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| dpdp\_compliance.api.rights.send\_otp | POST | Session | (none) | { status: 'otp\_sent' } | 429 Rate limit |
| dpdp\_compliance.api.rights.submit\_dsr | POST | Session | otp, request\_type, description | { request\_id: str, sla\_due\_date: date } | 401 OTP invalid, 400 Invalid type |
| dpdp\_compliance.api.rights.get\_user\_summary | GET | Session | (none) | { assets: \[{ name, classification, purpose, processors\[\] }\] } | 403 if not own data |

## **10.3 Breach API**

| Endpoint | Method | Auth | Request Payload | Response | Error Codes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| dpdp\_compliance.api.breach.report | POST | API Key (IT Systems) | severity, breach\_type, affected\_categories\[\], affected\_principals\_count | { incident\_id, reporting\_deadline } | 400 Missing severity or type |
| dpdp\_compliance.api.breach.generate\_board\_report | GET | Session (DPO) | incident\_id | PDF/Word stream with statutory report | 404 Breach not found |

## **10.4 Webhook Outbound Events**

| Event Name | Trigger | Payload | Retry Policy |
| :---- | :---- | :---- | :---- |
| CONSENT\_WITHDRAWN | User withdraws consent purpose | { user\_hash, purpose, timestamp, channel } | 3 retries, 30s backoff; log on final failure |
| DATA\_SUBJECT\_ERASURE | Anonymisation engine completes | { user\_hash, anon\_hash, erasure\_date, dsr\_reference } | 3 retries, 60s backoff |
| BREACH\_NOTIFIED | DPO triggers Board notification | { incident\_id, severity, affected\_count, notification\_timestamp } | 1 attempt; manual retry from Breach form |

# **11\. Acceptance Criteria & Test Cases**

These are the master acceptance tests that the QA Lead must execute and sign off before each release. P0 tests must pass before any production deployment.

## **11.1 P0 Critical Acceptance Tests**

| AC-ID | Feature | Test Description | Expected Outcome |
| :---- | :---- | :---- | :---- |
| AC-01 | Consent Immutability | Submit a Consent Log; attempt to edit any field via Frappe Desk and via direct API PUT call | Both attempts return validation error; record unchanged in DB |
| AC-02 | No Pre-Ticked Boxes | Render signup consent modal; inspect HTML source | No optional purpose checkbox has 'checked' attribute |
| AC-03 | OTP Gate for DSR | Call submit\_dsr API without prior send\_otp call; with wrong OTP; with correct OTP | First two return 401; third creates DSR record |
| AC-04 | 72h Breach Deadline | Create Data Breach with detection\_datetime \= now; check reporting\_deadline | reporting\_deadline \= detection\_datetime \+ exactly 72 hours (verified to the second) |
| AC-05 | Erasure — Retention Block | Submit erasure for user with Sales Invoice dated 2 years ago (within 8-year window) | Request rejected; DSR status \= Rejected; rejection\_reason contains legal hold explanation |
| AC-06 | Erasure — Clean User | Submit erasure for user with no transactions | User email shows @anonymized.invalid; Customer name shows Anonymized-\[hash\]; Erasure Log created |
| AC-07 | VPC Age Gate | Enter DOB yielding age 15 on signup form | Normal signup flow stops; parental consent message displayed; account not created |
| AC-08 | Consent Withdrawal Propagation | Withdraw Marketing consent; check Email Queue within 60 seconds | All Pending Email Queue records for that user and Marketing purpose show status Cancelled |
| AC-09 | Encryption at Rest | Save an Aadhaar number in a Password-type field; query MariaDB directly | DB column shows Fernet-encrypted string, not plain Aadhaar number |
| AC-10 | Role Isolation | Login as Compliance Viewer; attempt to open Data Breach form | Permission Denied error; Data Breach record not accessible |

## **11.2 P1 High Priority Acceptance Tests**

| AC-ID | Feature | Test Description | Expected Outcome |
| :---- | :---- | :---- | :---- |
| AC-11 | Multi-language Notice | Create Hindi notice; access signup with Accept-Language: hi-IN | Hindi notice renders; English notice not shown |
| AC-12 | Legacy Remediation | Run batch email tool; check Email Queue and Job Queue | All unconsented users appear in Email Queue; background job completes without error |
| AC-13 | DPO Dashboard Accuracy | Add 10 users; consent 7; check Consent Coverage card | Dashboard shows 70.0%; matches manual SQL count |
| AC-14 | SLA Breach Alert | Create DSR; set sla\_due\_date to yesterday; run daily scheduler | DPO receives escalation email; sla\_breached \= 1 on DSR record |
| AC-15 | Breach DPO Alert | Create breach with reporting\_deadline 20h from now; run hourly scheduler | DPO receives urgent email within 1 scheduler cycle |
| AC-16 | VPC DigiLocker Token | Complete VPC flow in DigiLocker sandbox | verification\_token populated in Consent Log (encrypted); is\_minor \= 1 on user |
| AC-17 | Board Report Generation | Click Generate Board Report on a Data Breach | Document generated; all 8 Rule 7 mandatory fields populated with correct values |
| AC-18 | Nominee Registration | Submit nomination via Privacy Portal | Nominee Record created; nominee\_email notified |
| AC-19 | SDF Module Visibility | Set fiduciary\_classification \= SDF | DPIA and Audit Record menu items appear in Workspace |
| AC-20 | API Rate Limiting | Send 101 consent check requests in 60 seconds from same API key | 101st request returns HTTP 429 |

# **12\. Implementation Plan**

## **12.1 Release Strategy**

| Release | Scope | Timeline | Go/No-Go Gate |
| :---- | :---- | :---- | :---- |
| v0.1 — Alpha | App scaffold, DPDP Settings, Consent Purpose, Privacy Notice, Data Asset, Retention Policy DocTypes | Weeks 1–3 | All Phase 1 DocTypes created and validated; encryption active |
| v0.2 — Beta | Consent Log, Signup Modal, Consent API, Withdrawal, Legacy Remediation Tool | Weeks 4–7 | Consent capture E2E working; immutability verified; no pre-ticked boxes |
| v0.3 — Beta | VPC (DigiLocker), DSR Portal, OTP Verification, Anonymisation Engine | Weeks 8–12 | VPC sandbox tested; DSR E2E with retention check working |
| v0.4 — RC | Data Breach Module, 72h Alerts, Board Report, Grievance Module, Processor Governance | Weeks 13–16 | Breach workflow E2E; Board report generated correctly |
| v1.0 — GA | DPO Dashboard, Frappe v16 Workspace, DPIA/Audit (SDF), Full API, VAPT, UAT | Weeks 17–20 | All P0 acceptance tests pass; VAPT zero critical; DPO UAT sign-off |

## **12.2 Team Structure**

| Role | Count | Responsibilities |
| :---- | :---- | :---- |
| Product Manager | 1 | PRD ownership, sprint planning, stakeholder alignment, DPO liaison |
| Backend Developer (Frappe Python) | 2 | DocTypes, hooks.py, API endpoints, scheduler jobs, anonymisation engine |
| Frontend Developer (JS/Jinja) | 1 | Consent modal, Privacy Portal (Web Builder), VPC portal, dashboard JS |
| QA Engineer | 1 | Test case execution, VAPT coordination, UAT facilitation |
| Data Protection Officer (DPO) | 1 (Client) | Requirements validation, Privacy Notice drafting, UAT sign-off |
| Legal Counsel | 1 (Client) | Consent purpose legal review, retention policy legal basis |
| Security Engineer | 1 (Part-time) | VAPT execution, encryption configuration review |
| DevOps | 1 (Part-time) | Bench setup, Frappe v16 deployment, Redis/RQ configuration |

## **12.3 Dependencies & Risks**

| Risk ID | Risk Description | Probability | Impact | Mitigation |
| :---- | :---- | :---- | :---- | :---- |
| R-01 | DigiLocker API approval delay (production credentials) | Medium | High | Use sandbox in all testing; submit production application in Week 1; VPC can be disabled via DPDP Settings toggle |
| R-02 | DPDP Rules notification for specific provisions not yet final | Low | Medium | Design to current November 2025 Rules; use configuration flags for anything likely to change |
| R-03 | Client organisation has incomplete Data Asset inventory | High | High | Phase 1 includes mandatory Data Classification Workshop; go-live blocked until RoPA complete |
| R-04 | Frappe v16 Web Builder has limitations for complex portal UI | Low | Medium | Fallback: standard Frappe Page (Python controller \+ Jinja); no external framework dependency |
| R-05 | MariaDB performance on large Consent Log table | Medium | Medium | Add composite index on (user, purpose, status) in v0.2; load test before v1.0 |

# **13\. Frappe v16 Configuration Reference**

## **13.1 DocType Configuration Flags**

| DocType | Is Submittable | Track Changes | Has Web Form | Search Fields | Indexes Required |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Consent Log | Yes | Yes | No | user, purpose, status | (user, purpose, status, expiry\_date) |
| Privacy Notice | Yes | Yes | No | notice\_id, language, version | (language, is\_active) |
| Data Subject Request | Yes | Yes | No | request\_id, user, status | (user, status, sla\_due\_date) |
| Data Breach | Yes | Yes | No | incident\_id, severity, status | (status, reporting\_deadline) |
| Data Asset | No | Yes | No | asset\_name, doctype\_name, classification | (doctype\_name, field\_name) |
| Consent Purpose | No | Yes | No | purpose\_name, is\_active | (is\_active) |
| Privacy Notice | Yes | Yes | No | notice\_id, language | (language, is\_active) |
| Retention Policy | No | No | No | policy\_name | (is\_active, data\_category) |

## **13.2 Scheduler Events (hooks.py)**

| Frequency | Function | Purpose |
| :---- | :---- | :---- |
| hourly | dpdp\_compliance.breach.check\_breach\_deadlines | Check all open breaches for 24h threshold; send DPO alerts |
| daily | dpdp\_compliance.retention.run\_retention\_engine | Scan Data Assets against Retention Policies; execute expiry actions |
| daily | dpdp\_compliance.consent.check\_consent\_expiry | Mark Consent Logs with expiry\_date \< today as Expired |
| daily | dpdp\_compliance.consent.suspend\_non\_consenting\_users | Disable users past legacy consent deadline with no valid consent |
| daily | dpdp\_compliance.rights.check\_sla\_breaches | Set sla\_breached=1 on DSRs past due; send escalation emails |

## **13.3 Role Profile Definitions**

| Role Profile | Roles Included | Use Case |
| :---- | :---- | :---- |
| DPO Manager | DPO Manager, System Manager (DPDP scope only) | Full access to all DPDP DocTypes; run erasure; manage breach; approve notices |
| Compliance Viewer | Compliance Viewer | Read-only access to all DPDP records; export reports; no edit capability |
| IT Admin — DPDP | DPDP IT Admin | Configure Settings, Retention Policy, Encryption; no access to personal data records |
| Auditor | DPDP Auditor | Read-only access to all records \+ Frappe Version history; export evidence packages |
| Privacy Portal User | Website User (extended) | Access own Consent Logs; submit own DSRs; manage own nominee |

## **13.4 Frappe v16 Workspace — DPDP Compliance Cockpit**

| Section | Components |
| :---- | :---- |
| Header | Workspace name: 'DPDP Compliance Cockpit'; Icon: privacy-shield; role: DPO Manager, Compliance Viewer |
| Row 1 — Shortcuts | New Data Breach; New Privacy Notice; New Consent Purpose; Run Legacy Remediation; View All DSRs |
| Row 2 — Number Cards | Consent Coverage %, Open DSRs Past SLA, Active Breaches, Consents Expiring 30d, Assets Without Policy |
| Row 3 — Chart | Consent Coverage Trend (Line Chart, last 90 days) |
| Row 4 — Quick Lists | Recent DSRs (last 10), Open Data Breaches (all active) |
| Row 5 — Links | Data Asset Inventory, Retention Policies, Data Processor Registry, Privacy Notices, Audit Records (SDF only) |

# **14\. Success Metrics & KPIs**

| KPI | Formula / Source | Target | Measurement Frequency |
| :---- | :---- | :---- | :---- |
| Consent Coverage % | Active Granted Logs / Active Users × 100 | ≥ 95% within 60 days of go-live | Weekly |
| DSR SLA Compliance % | Closed DSRs within SLA / Total Closed DSRs × 100 | ≥ 99% | Monthly |
| Breach Response Time | Board Notification Datetime − Detection Datetime | \< 60 hours (buffer before 72h) | Per incident |
| Consent Withdrawal Response Time | Time from withdrawal to Email Queue cancellation | \< 60 seconds | Automated monitoring |
| Anonymisation Accuracy | Erasure Log records with no PII detectable in DB post-erasure | 100% | Per erasure \+ quarterly audit |
| Data Asset Coverage | Assets with Retention Policy / Total Assets × 100 | 100% at go-live | Monthly |
| API Uptime | Consent check endpoint availability | ≥ 99.9% | Continuous (UptimeRobot) |
| Grievance Resolution Rate | Grievances resolved within SLA / Total Grievances × 100 | ≥ 95% | Monthly |

# **15\. Glossary & Regulatory Reference**

## **15.1 Glossary**

| Term | Definition |
| :---- | :---- |
| Data Principal | The individual whose personal data is being processed (equivalent to 'Data Subject' in GDPR) |
| Data Fiduciary | Any entity that determines the purpose and means of processing personal data |
| Significant Data Fiduciary (SDF) | A Data Fiduciary notified by the Central Government as having significant processing volumes or risk |
| Data Processor | A third party that processes personal data on behalf of a Data Fiduciary |
| Consent Manager | A registered entity that enables Data Principals to manage their consent across multiple fiduciaries |
| RoPA | Record of Processing Activities — the master inventory of all personal data, its purposes, and processors |
| DSR | Data Subject Request — a formal request by a Data Principal to exercise a statutory right |
| VPC | Verifiable Parental Consent — identity-verified consent by a parent/guardian for processing a child's data |
| DPIA | Data Protection Impact Assessment — a systematic risk evaluation for high-risk processing activities |
| SARAL | Simple, Accessible, Rational, Actionable — the design principle for consent notices under DPDP Rules |
| Anonymisation | Irreversible process rendering personal data incapable of identifying the individual |
| Pseudonymisation | Replacing identifying fields with artificial identifiers; reversible with key |
| DPB | Data Protection Board of India — the adjudicatory body under the DPDP Act |
| Fernet | Symmetric encryption algorithm used by Frappe for Password-type fields (from Python cryptography library) |

## **15.2 Regulatory Reference Table**

| Reference | Description | Relevance to This PRD |
| :---- | :---- | :---- |
| DPDP Act, 2023 — Sec 5 | Notice requirements before/with consent | FR-CMS-01, FR-CMS-04, Screen SCR-02 |
| DPDP Act, 2023 — Sec 6 | Consent must be free, specific, informed, unambiguous | FR-CMS-02, FR-CMS-03, FR-CMS-06, AC-02 |
| DPDP Act, 2023 — Sec 8(6) | Breach notification to DPB without delay | FR-BRE-01 to FR-BRE-05, Screen SCR-05 |
| DPDP Act, 2023 — Sec 8(7) | Erasure when purpose served | FR-RET-01 to FR-RET-04, FR-ERA-01 to FR-ERA-06 |
| DPDP Act, 2023 — Sec 9 | Children's data — no tracking, no targeting, VPC required | FR-VPC-01 to FR-VPC-06, Screen SCR-04 |
| DPDP Act, 2023 — Sec 11 | Right of Data Principal to access summary | FR-DSR-06, Portal Tab 1 — My Data |
| DPDP Act, 2023 — Sec 12 | Right to correction and erasure | FR-DSR-01, FR-ERA-01 to FR-ERA-06 |
| DPDP Act, 2023 — Sec 13 | Grievance redressal mechanism | FR-GRI-01 to FR-GRI-04, M-09 |
| DPDP Rules, Nov 2025 — Rule 3 | Notice content, language, SARAL principle | FR-CMS-04, NFR-L10N-01, Privacy Notice DocType |
| DPDP Rules, Nov 2025 — Rule 7 | Breach intimation form — 8 mandatory fields | FR-BRE-03, Board Report Generator |
| DPDP Rules, Nov 2025 — Rule 10 | Parental consent age verification mechanism | FR-VPC-01 to FR-VPC-06, DigiLocker integration |

*End of PRD — dpdp\_compliance v2.0*