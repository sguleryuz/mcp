# Required checks

Use detailed current records and complete pagination. Use JSON from OCI CLI; map the actual returned field names, commonly kebab-case. All service reads in this reference must use installed OCI CLI commands. Console/Oracle evidence is supplied by the publisher, not retrieved with an MCP server or automated browser. Treat missing or contradictory evidence as **Needs verification**, invalid evidence as **Needs attention**, and apply **Not applicable** only when the listing type establishes it. Only Pass/Not applicable permit cloning. Report blocking reasons even if other independent checks pass.

## Evidence reuse

Within one discovery pass of the freshly authenticated invocation, reuse reads by bound environment/endpoint/tenancy/profile/region, resource type, and full resource ID. Share publisher-level evidence across candidates of that publisher; fetch each required detail once. Keep a compact record of scope, parent/source/publisher IDs, observed states, read times, pagination completeness, ETag/request IDs when exposed, check results, and unresolved fields. For external evidence retain its source, matching environment and publisher/OPN entity, verification time, and validity. Reuse it only after matching it to the freshly verified staging publisher; evidence never selects the login account. Production service records or approvals do not establish staging readiness.

Missing/projected-out fields require detailed reads, not an inferred pass. Invalidate relevant evidence on scope changes, changed states, contradictions, or expiry. Start a new service-read cache for each discovery pass; retain external evidence only while current and matching. Immediately before cloning, refresh the source, parent, publisher, every sibling page, package inventory/details, and relevant operation evidence, and revalidate external evidence. A cached record or source ETag cannot establish that sibling/package state is unchanged.

## Identity and publisher

| Check | Pass evidence | If it cannot pass |
|---|---|---|
| Environment | Phoenix staging is announced and every Publisher command explicitly uses the configured beta endpoint; OCI identity calls use their own service | Resolve endpoint/region mismatch or staging access before discovery/clone; never fall back to production |
| Session | New isolated browser login and unused OCI profile for this invocation, successful `oci session validate`, and actual tenancy/region matched to the publisher's current selection | Complete fresh login and account verification before discovery; never reuse a previous invocation's credentials |
| Ownership | Parent listing's `publisher-id` resolves to the intended publisher in the authenticated tenancy and authorized compartment | Resolve the selected account/listing first; use compartment ancestry if needed |
| Publisher registration | Detailed `publisher-status == APPROVED`; no authoritative suspension indication | Show the exact status and direct the publisher to their Publisher profile/support |
| OPN | `opn-membership.opn-status == ACTIVE`, matching nonempty OPN number, and valid current dates | Renewal in progress, inactive, expired, or future membership needs attention; missing dates need verification |
| OCMA | Approved and currently active Oracle Cloud Marketplace Agreement for the same OPN entity | Use current Console/Oracle confirmation when CLI evidence is insufficient |
| Publisher logo | Uploaded publisher profile content confirmed through a supported OCI CLI read/content command or publisher-provided current Console profile evidence | Explicitly empty logo needs attention; missing capability/filename-only evidence needs verification |

For OPN, parse timezone-aware `time-start` and `time-end`; require `time-start <= now < time-end`. For documented date-only agreement validity, use its documented timezone/inclusivity instead of inventing a cutoff. Match evidence to the actual publisher's legal entity and OPN number.

Some CLI versions expose OCMA as `enrollment-status`; a status alone may not establish current validity. Registration approval, acceptance/submission, or a generic terms record does not prove active OCMA. Ask only for the missing evidence: agreement status and validity (or an explicit current-active Oracle confirmation) for that OPN entity. Record source and when it was checked. Do not invent enrollment endpoints, use internal-only records, or accept agreements.

Older logo models use `logo.content-url`; newer models can expose profile/content operations. Confirm content without displaying or retaining signed URLs. A listing icon does not satisfy the publisher logo check. Do not infer dimensions or full artwork compliance merely from presence.

These OPN/OCMA/logo and package-quality checks are this workflow's requested readiness requirements. They do not imply every deployment enforces them during clone.

## Access and operation evidence

A successful read confirms read access, not clone permission. Use IAM evidence accessible through OCI CLI or evidence supplied by the publisher if available, and surface any known denial. Do not require an ordinary publisher to list administrator-only policies. When no supported read-only effective-permission check exists, label clone authorization “enforced by OCI on request,” not a fabricated Pass or an invented failed prerequisite. The real clone request still requires user authorization and all actual readiness checks to pass.

List relevant work requests when supported, correlate returned resource references to this listing and its revisions, and inspect nonterminal results. Do not block on unrelated compartment activity. Nonterminal clone/update/delete/publish/withdraw operations that can conflict need attention. If operation reads are denied, try an OCI CLI read of the specific known request or ask the publisher for current Console activity evidence. Unresolved conflict evidence needs verification; absence of a list permission alone does not prove a conflict. For prior failed/canceled clones, check for a remaining nondeleted draft.

## Source and siblings

- Require parent and source `lifecycle-state == ACTIVE`, matching source `listing-id`, and consistent publisher/compartment scope.
- `PUBLISHED` and `PUBLISHED_AS_PRIVATE` are supported source states. Oracle's general guide also includes `UNPUBLISHED`, while some service versions reject it. For `UNPUBLISHED`, use authoritative evidence specific to the target service or publisher-provided evidence of the selected revision's current Console capability; if unresolved, mark Needs verification. Do not execute a trial clone or withdraw a published source to test eligibility. `NEW`, `APPROVED`, rejected, review-pending, and transitional publication states are not cloneable defaults.
- List every sibling revision page without lifecycle/status filters. A `NEW` sibling in `ACTIVE` or `UPDATING` blocks another clone. Show the draft ID, and suggest continuing it or waiting for completion. A definitively `DELETED` `NEW` sibling does not block.
- A nondeleted sibling still creating/updating/deleting, or a failed state that could conceal a partial draft, needs resolution when it conflicts with cloning. Do not interpret an unrelated historical rejected review or publication failure as an in-progress clone; inspect the actual lifecycle/operation evidence.
- Re-read immediately before the mutation. Compare identity, source content/ETag, sibling IDs/states, package readiness, and operation evidence with the selected option. ETag protection applies to the source only. A concurrent sibling conflict is a service validation failure; re-read instead of forcing a retry.

## Packages

Determine applicability from the listing/revision type and package type. Package-based OCI applications require these checks; lead generation/service revisions with no package requirement get Not applicable. Unknown or inconsistent types need verification.

1. Fetch all package pages and detailed records, deduplicating repeated IDs. Exclude only definitively `DELETED` packages. Require at least one usable `ACTIVE` package; nondeleted transitional, failed, inactive, or unknown package states need resolution. Every package must reference the selected source revision.
2. Require exactly one Boolean `is-default == true` among applicable active packages. Summaries may omit `is-default`: get details. A missing/non-Boolean flag makes the count unverified even if one known flag is true. Zero or multiple defaults need attention.
3. Require nonempty `package-version` and `display-name`. Distinct packages in the same source revision cannot share the exact version string. Follow documented case-insensitive rules if the deployed service specifies them; otherwise do not invent case folding. Matching a package version in a historical revision is not a duplicate within the source.
4. Reject any Unicode whitespace in a package display name or version, including internal/leading/trailing spaces, tabs, newlines, and nonbreaking spaces. Use Unicode-aware whitespace detection with existing local capabilities; no additional runtime or utility installation is required. Do not trim values to make them pass, or apply this rule to descriptions, terms, or usage prose.
5. Show affected package names, versions, IDs, and default flags when a check fails. Offer correction through the supported Publisher workflow; if a published source is immutable, direct the publisher to Marketplace support rather than promising an edit or bypassing the check.

## Completion

Before cloning, capture source metadata and package/attachment inventories needed to compare the result. Exclude deleted entries and preserve identity/version/default information. Missing preflight inventory evidence relevant to a required check blocks cloning; a feature that does not apply gets Not applicable.

Require an attributable, distinct draft ID under the same parent/compartment, status `NEW`, lifecycle `ACTIVE`, and work request `SUCCEEDED` when available. Correlate work request resources or source lineage with before/after sibling IDs. Never choose the newest revision if concurrent activity makes attribution ambiguous.

Compare supported copied metadata and package/attachment inventory by stable content identifiers, names, versions, and default flags. Resource IDs, timestamps, revision numbers, and lifecycle fields can legitimately differ. Do not promise every field is copied identically when the service does not expose that evidence. Report a missing expected item as verification pending; retain the draft ID for recovery. Re-read the source to check its publication status. A partial clone is not authority to delete, edit, submit, or publish it.
