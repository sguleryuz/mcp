---
name: publisher-listing-types
description: Use when a Marketplace publisher wants to create a Lead Generation, Service, or OCI Application listing and its first draft.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-07
---

# Create a publisher listing

Complete the `publisher-onboarding` checks first. Ask which listing type the publisher intends and use the matching Oracle guide: [Lead Generation](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-lead-generation-listing.htm), [Service](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-service-listing.htm), or [OCI Application](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-oci-application-listing.htm). Do not infer a deployable package from a lead-generation or service offer.

For `LEAD_GENERATION` or `SERVICE`, use package type `NONE`. For `OCI_APPLICATION`, select a supported SDK package type: `CONTAINER_IMAGE`, `HELM_CHART`, `MACHINE_IMAGE`, or `STACK`. Oracle's Console documentation also describes SaaS, but the installed SDK's listing model does not expose a SaaS package type; use the Console for that option. Package upload, artwork, terms, and other attachments remain Console steps for all types.

Collect the internal listing name, compartment OCID, and type-specific revision metadata from the publisher. Use `create_publisher_listing` only after showing the exact listing type and package type and receiving approval. Save the listing OCID. Use `create_publisher_revision` with the fields supported by the installed SDK model, including public `display_name` and `headline`, only after reviewing those values and receiving approval. Nested fields use OCI SDK snake_case names. If draft creation fails, report the listing OCID so the publisher can resume without creating a duplicate.

For an existing listing, call `list_publisher_revisions` first. Edit an existing `NEW` draft; if a revision is already published, use `clone_publisher_revision` through the `listing-revision-publish` skill. Do not create a second `NEW` revision. After creation, call `get_publisher_revision` and report its OCID and status. Use `inspect_revision_assets` and the listing-type guide to identify remaining Console work before review; an empty attachment or package inventory is not a completed guideline check.
