---
name: lead-generation-listing
description: Use when a Marketplace publisher wants to create or inspect a lead generation listing and its draft revision.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-07
---

# Lead generation listing

Use the `publisher-onboarding` skill first and require its applicable checks to be confirmed. Call `publisher_readiness` with the publisher tenancy and compartment IDs to refresh the API-verifiable checks. If there is no approved publisher or any required onboarding check is pending or unknown, stop listing creation and report what remains to be confirmed.

Collect the internal listing name, public display name, headline, short description, pricing type, and at least one OCI Marketplace product code. Use [Oracle's lead generation listing guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-lead-generation-listing.htm) to collect relevant categories and filters, keywords, long description, languages, version details, demo/training URLs, support contacts and links, system requirements, usage information, and lead destination or message. Pass supported SDK fields through the `options` argument; when supplying detailed `products`, their codes must match `product_codes`. Show the values to the publisher and get explicit approval before creating OCI resources.

Call `create_lead_generation_listing`; save its returned listing OCID. Then call `create_lead_generation_revision` with that OCID and the approved content. If the revision call fails, report the created listing OCID so the publisher can resume without creating a duplicate. For an existing listing, call `list_publisher_revisions` first: edit an existing `NEW` draft or clone a published revision using the `listing-revision-publish` skill. Call `get_publisher_revision` and report its revision OCID and status. Keep the revision as a draft until the publisher asks to submit it.

Before review submission, have the publisher add any required support contacts, links, artwork, and other content in the Marketplace Console. This MCP server does not upload listing assets.
