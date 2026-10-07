---
name: publisher-onboarding
description: Use when a publisher needs to establish or verify an Oracle Cloud Marketplace publisher account before creating listings.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-06
---

# Publisher onboarding

Ask for the intended publisher tenancy OCID and compartment OCID. Run `publisher_readiness` with those IDs.

If `ashburn_subscribed` is false, direct the publisher to subscribe the tenancy to `us-ashburn-1` before Marketplace Publisher work. If `publishers` is empty, explain that a new publisher account is created through [Oracle's partner onboarding](https://docs.oracle.com/en-us/iaas/Content/Marketplace/new-partners.htm), not through this MCP server. Give the publisher that link and the [Marketplace Publisher page](https://www.oracle.com/cloud/marketplace/publisher/); ask them to complete the partner and Marketplace enrollment steps there. Do not call `create_lead_generation_listing` yet.

When a publisher record exists, report its ID and status. If its status is not active, direct the publisher to resolve that status with Oracle before listing creation. Never infer account approval from the presence of an OCI tenancy alone.
