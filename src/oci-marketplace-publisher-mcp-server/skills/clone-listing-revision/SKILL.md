---
name: clone-listing-revision
description: Helps OCI Marketplace publishers clone an eligible listing revision into a new draft in staging. Use to clone a staging revision or find eligible staging sources; starts a fresh isolated browser login and checks eligibility before cloning.
---

# Clone listing revision

Guide a publisher from Oracle sign-in to a verified new draft under the same listing. Run the CLI work for them and explain results in plain language. The only service integration required is the installed OCI CLI, which Codex runs through the local terminal. The publisher completes OCI browser login in a fresh, isolated browser profile. Creating or reviewing the skill is not a request to clone a live resource.

Load [OCI access and commands](references/oci-cli.md) before access, [required checks](references/checks.md) before deciding eligibility, and [publisher responses and recovery](references/publisher-flow.md) when presenting choices, observing a clone, or handling a blocker. Reuse already loaded references unless their contents change.

## OCI CLI-only execution

Use `oci` commands for authentication, discovery, checks, cloning, and status polling. Do not discover, call, or ask the publisher to install MCP servers, connectors, browser automation, marctl, internal APIs, or a separate SDK. Normal Codex terminal/file access is sufficient. Do not introduce Python, jq, or another utility as an installation prerequisite; interpret CLI JSON using the capabilities already available.

Any Console step is performed by the publisher, not browser automation. Treat a pasted Console link as a resource locator: extract an OCID/region only when present and verify them through OCI CLI; otherwise ask for the resource OCID. For checks absent from installed CLI output, request the specific publisher-provided evidence described below and keep the check blocked until verified. Never require a missing integration or invent an API/CLI command to fill the gap.

This version targets **Staging — Phoenix (`us-phoenix-1`)**. Use `https://cloud-staging.oracle.com` for Publisher Console guidance and the explicit staging Publisher endpoint in [environment routing](references/oci-cli.md#staging-environment) for every Publisher read, clone, and poll. Announce the environment before login. Do not fall back to production or infer a tenancy from the environment. A request for another environment/region needs a verified configuration before access.

## 1. Sign in to the publisher account

At every new invocation, including a repeated `$clone-listing-revision` invocation or explicit restart, explain the requested inspection or cloning task, then say: “First, sign in to the OCI tenancy that owns your Marketplace listings.” Check OCI CLI availability; if missing, give the official setup link in the command reference and offer setup assistance.

Run a new `oci session authenticate` with an unused dedicated OCI profile and the [isolated browser login](references/oci-cli.md#browser-authentication) procedure. Never reuse an earlier invocation's token, saved profile, browser cookies, tenancy, or compartment, even if its session is valid. A new browser tab/window or OCI profile alone does not provide fresh browser authentication. Let the publisher complete Oracle sign-in and MFA themselves.

Ordinary replies such as “done,” source selection, and polling continue the current invocation; they do not start another login. If a fresh invocation replaces a pending login, stop only that invocation's owned login process and isolated login window before starting the new one; do not leave competing callbacks. After login, validate the new session and bind all reads and the clone to its explicit config, profile, region, and `--auth security_token`. Add the staging endpoint to every Publisher call; keep OCI identity calls on their own service endpoint.

Use the configured staging region and only a tenancy supplied for this invocation; otherwise let the publisher select the tenancy during fresh login. Show Staging, the authenticated tenancy name when available, its OCID suffix, and region before compartment/listing discovery. Proceed when it matches an account explicitly selected for this invocation. If no account was selected, require the publisher to confirm the observed account first. If a requested name cannot be verified, ask the publisher to identify the intended tenancy by OCID. A valid token does not establish the intended publisher account or staging access. If the account is wrong, repeat isolated login without searching its compartments. Never collect passwords, MFA codes, keys, or token contents in chat.

## 2. Find the source

Accept a listing name, revision OCID, listing OCID, or Oracle Console link. A name is a search hint, not a unique identifier. Resolve a supplied revision to its parent listing. For an ambiguous name, show matches with compartment and publisher names; let the publisher choose. If no target was supplied, discover listings in the authenticated tenancy and offer a short selection list instead of requiring the publisher to locate OCIDs.

Prefer the supplied listing or compartment. Otherwise search the tenancy root and accessible active compartments, including the root explicitly. Describe accessible compartments as places being searched, not as the publisher's confirmed location. If discovery is denied, use a supplied resource directly or ask for its Console link/compartment. Never equate access denied or a partial search with “no listings.” Do not repeatedly search a scope already known to be wrong or denied.

Read the parent listing, its actual publisher, and all sibling revision pages. Consider supported published sources for cloning. An existing active/updating `NEW` draft blocks another clone: show that draft and the appropriate next step. Check a narrowed candidate before performing expensive inventory reads; do not require publisher-wide package scans to inspect one source.

Use the command reference's output projections for discovery and polling. Keep the [scoped evidence record](references/checks.md#evidence-reuse) to deduplicate reads within a discovery pass and share publisher evidence across candidates. These optimizations do not replace detailed validation or the complete final refresh below.

## 3. Check eligibility

Evaluate all applicable rules in [required checks](references/checks.md), including:

- Session identity, publisher ownership, approved registration, active OPN, active OCMA, and publisher logo.
- Active parent/source, supported source status, no conflicting draft or operation.
- For package sources: usable packages, exactly one default, unique version names within the source, and no whitespace in package names or versions.

Use **Pass**, **Needs attention**, **Needs verification**, and **Not applicable** with evidence. Needs attention and Needs verification both block cloning. Missing CLI response fields are not failures or passes. First use supported OCI CLI read commands; then ask the publisher to provide the precise current Console/Oracle evidence needed for an unavailable check. Record its publisher/OPN identity, source, validity, and verification time. A generic “yes” must not silently resolve multiple unrelated checks.

Preserve the requested OPN/OCMA/logo/package gates. Explain them as this workflow's readiness requirements; do not claim they are all service-enforced clone restrictions. Offer concrete next steps, not raw exceptions or a blanket request to “fix permissions.” Never repair a published source, delete a draft, accept agreements, or change statuses as an implicit part of cloning.

## 4. Select and clone

Show the ready candidates and blockers using the compact format in [publisher responses](references/publisher-flow.md). Keep an exact mapping from each option to the full source and parent IDs. For the chosen option, show the listing, revision, publisher/compartment, and successful checks, and state that cloning creates a draft under that listing. Public/private visibility selection is unnecessary for cloning.

“Clone option 2” authorizes that displayed source. If the original request already unambiguously identifies a source and asks to clone it, show the successful checks and proceed without another identical confirmation. A request only to inspect or check eligibility does not authorize a clone. Never choose among multiple sources on the publisher's behalf.

Immediately before cloning, refresh the source, parent, publisher, all sibling pages, package inventory/details, and relevant operation evidence; confirm external evidence is still current. Re-run all checks. If anything affecting identity, source content, or eligibility changed, show the new result and resolve it before proceeding. Snapshot the source ETag and sibling IDs.

Send one clone request with the latest ETag when available and automatic mutation retries disabled. An ETag protects the source; it cannot prevent a concurrent sibling draft, which the service still validates. Preserve returned request/work request IDs. Do not use a live clone call as a compatibility or permissions test.

## 5. Verify and hand back the draft

Follow [targeted polling](references/publisher-flow.md#observe-the-clone): poll known operation/draft IDs with backoff for up to ten minutes, expanding sibling discovery when attribution, state changes, conflicts, timeout, or final verification require it. A successful command or accepted request alone is not completion.

Report success only for a distinct, attributable revision under the same listing with `status == NEW` and `lifecycle-state == ACTIVE`, plus a successful work request when available. Verify copied content/inventory as described in the checks. For an attributable draft with incomplete copy verification, report “Created, verification pending” with its ID. If attribution is unresolved, report “Outcome uncertain” and retain any candidate IDs without choosing one. Preserve the source's publication status and flag unexpected changes.

On timeout or interruption, retain nonsecret context in the chat: environment/endpoint, tenancy, region, parent/source IDs, baseline sibling IDs, and known request/draft IDs. A new invocation must authenticate afresh and verify the same target environment and tenancy before inspecting that saved operation; keep old session details only as history, never as credentials to reuse. Do not issue another clone. Handle definite failures through [recovery guidance](references/publisher-flow.md). Finish with the new draft ID and next action. Editing, submission, and publication require separate requests.

## Example requests

- “Use $clone-listing-revision to show which of my listings I can clone.”
- “Use $clone-listing-revision to clone the published revision of Analytics Connector.”
- “Use $clone-listing-revision to check this listing before cloning: <Console link>.”
