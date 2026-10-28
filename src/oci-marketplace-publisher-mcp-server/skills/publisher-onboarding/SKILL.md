---
name: publisher-onboarding
description: Use when a new or existing Oracle Marketplace partner needs to confirm publisher onboarding before creating listings.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-28
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

For **any paid listing**, check the applicable paid-listing agreement and supplier setup in [Becoming an OCI Partner and Publisher](https://docs.oracle.com/en-us/iaas/Content/Marketplace/become-oci-partner.htm). Supplier verification may still be pending while the publisher creates a draft; label it **not ready to publish** until commercial setup is confirmed. For a **paid package listing or private offer**, also check the U.S. legal entity and paid-offer banking requirements. Do not apply the paid-package U.S. domicile restriction to a non-package Lead Generation or Service listing.

## New partner path

Follow [Oracle's new-partner onboarding](https://docs.oracle.com/en-us/iaas/Content/Marketplace/new-partners.htm): complete partner enrollment and the checks above, then use **Marketplace → Publisher → Publisher Registration** in the OCI Console. Confirm the OPN number used in registration matches the active membership and that the registration is approved. If `publisher_readiness` returns no publisher, keep registration and approval pending and stop listing creation.

## Existing partner migration path

Confirm the partner's OPN and OCMA remain active and that the intended OCI tenancy is ready. Check Publisher Registration in the production OCI Console before preparing a migration request. If an approved profile already exists, do not register again. If registration is missing, complete the [documented Publisher Registration flow](https://docs.oracle.com/en-us/iaas/Content/Marketplace/become-oci-partner.htm) and confirm approval before creating listings. If the OPN number is already associated with another publisher account, ask the tenancy administrator to verify access rather than retrying registration. Do not direct an external publisher to a staging Console or a legacy Partner Portal.

If migration is needed, confirm that the partner has provided **partner name, OPN number, and tenancy OCID** to Oracle Marketplace for migration, as described in the [existing-partner guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/existing-partners.htm). Do not send the email yourself unless the publisher explicitly authorizes it. Confirm migrated listings are visible under **Marketplace → Publisher → Listings** in the root compartment; if not, keep migration pending.

## Completion

Show the checklist with evidence and the next action for each pending or unknown item. Say **ready to create listings** only when every applicable common check and path check is confirmed; pending supplier verification alone does not block a paid draft, but blocks publication. For existing partners, also require migration confirmation before editing migrated listings. The MCP server can read Publisher approval, OPN status, and Ashburn subscription from OCI; OCMA activation, Console registration, and migration still require publisher or Oracle evidence outside this API.
