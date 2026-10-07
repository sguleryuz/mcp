---
name: lead-generation-listing
description: Use when a Marketplace publisher wants to create or inspect a lead generation listing and its draft revision.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-06
---

# Lead generation listing

Call `publisher_readiness` first with the publisher tenancy and compartment IDs. If no active publisher is returned, stop listing creation and use the `publisher-onboarding` skill.

Collect the internal listing name, public display name, headline, short description, pricing type, and at least one OCI Marketplace product code. Use [Oracle's lead generation listing guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-lead-generation-listing.htm) to identify other content the publisher must prepare before review. Show the values to the publisher and get explicit approval before creating OCI resources.

Call `create_lead_generation_listing`; save its returned listing OCID. Then call `create_lead_generation_revision` with that OCID and the approved content. If the revision call fails, report the created listing OCID so the publisher can resume without creating a duplicate. Call `get_publisher_revision` and report its revision OCID and status. Keep the revision as a draft until the publisher asks to submit it.

Before review submission, have the publisher add any required support contacts, links, artwork, and other content in the Marketplace Console. This MCP server does not upload listing assets.
