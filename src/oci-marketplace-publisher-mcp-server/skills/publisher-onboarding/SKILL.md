---
name: publisher-onboarding
description: Use when a new or existing Oracle Marketplace partner needs to confirm publisher onboarding before creating listings.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-07
---

# Publisher onboarding

Identify whether the publisher is a **new partner** or an **existing partner migrating listings**. Use the matching Oracle guide: [new partners](https://docs.oracle.com/en-us/iaas/Content/Marketplace/new-partners.htm) or [existing partners](https://docs.oracle.com/en-us/iaas/Content/Marketplace/existing-partners.htm). Check each applicable item below. Report every item as **confirmed**, **pending**, or **unknown**, with the evidence or the person who confirmed it. Never turn an unknown into a confirmation merely because `publisher_readiness` returns a publisher record.

## Checks for both paths

1. Confirm the partner has a verified Oracle account and an OCI tenancy. Record the tenancy OCID and the intended publisher compartment OCID; do not request credentials.
2. Confirm **active OPN membership** and its OPN Company ID or number. `publisher_readiness` and `get_publisher_profile` can report the OCI Publisher record's `opn_membership.opn_status` and `opn_number`; check that they match the intended legal entity and current partner records. An application or renewal in progress is pending, not confirmed. Direct uncertainty to [Partner Assistance](https://partnerhelp.oracle.com/).
3. Confirm the **Oracle Cloud Marketplace Agreement (OCMA) is approved and active** for that OPN entity. Acceptance or submission alone is pending until activation is confirmed. The [Publisher FAQ](https://docs.oracle.com/en-us/iaas/Content/Marketplace/faq-publisher.htm) describes first-time application, renewal, and confirmation email. Do not accept terms on the publisher's behalf.
4. Call `publisher_readiness` with the tenancy and compartment OCIDs. Confirm the tenancy is subscribed to `us-ashburn-1`; the publisher must select that region to create or edit Publisher resources. A missing subscription is pending.
5. Confirm the publisher registration was submitted in the OCI Console and its **Publisher Profile shows Approved**. `publisher_readiness` now reads the detailed OCI Publisher record, which reports `publisher_status`; compare it with the Console. A returned publisher ID or a submitted registration does not by itself establish approval. If the API status and Console status differ, report both and leave the check pending until resolved.
6. Confirm the publisher's OCI user has the required Marketplace Publisher IAM access using the `publisher-iam` skill. Policy text alone does not prove effective access; ask an administrator to confirm group membership and scope, or verify an authorized read-only Publisher operation.

For a **paid package listing or private offer**, also check the applicable U.S. legal entity, paid-listing agreement, and supplier setup in [Becoming an OCI Partner and Publisher](https://docs.oracle.com/en-us/iaas/Content/Marketplace/become-oci-partner.htm). Do not apply those paid-package requirements to a lead generation listing.

## New partner path

Follow [Oracle's new-partner onboarding](https://docs.oracle.com/en-us/iaas/Content/Marketplace/new-partners.htm): complete partner enrollment and the checks above, then use **Marketplace → Publisher → Publisher Registration** in the OCI Console. Confirm the OPN number used in registration matches the active membership and that the registration is approved. If `publisher_readiness` returns no publisher, keep registration and approval pending and stop listing creation.

## Existing partner migration path

Confirm the partner's OPN and OCMA remain active and that the intended OCI tenancy is ready. **Before the migration email**, ask the partner to complete Publisher Registration at the [staging Console registration page supplied for this workflow](https://cloud-staging.oracle.com/publisher/register), and confirm the submission there. Publisher approval remains a separate readiness check. This staging step is an additional requirement supplied by the workflow owner; [Oracle's public existing-partner guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/existing-partners.htm) says no legacy Partner Portal step is required. If the staging page is unavailable or submission cannot be verified, mark this check unknown and have the workflow owner resolve it; do not substitute a legacy portal step.

After staging registration is confirmed, confirm that the partner has provided **partner name, OPN number, and tenancy OCID** to Oracle Marketplace for migration, as described in the [existing-partner guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/existing-partners.htm). Do not send the email yourself unless the publisher explicitly authorizes it. Confirm migrated listings are visible under **Marketplace → Publisher → Listings** in the root compartment; if not, keep migration pending.

## Completion

Show the checklist with evidence and the next action for each pending or unknown item. Say **ready to create listings** only when every applicable common check and path check is confirmed. For existing partners, also require migration confirmation before editing migrated listings. The MCP server can read Publisher approval, OPN status, and Ashburn subscription from OCI; OCMA activation, staging registration, and migration still require publisher or Oracle evidence outside this API.
