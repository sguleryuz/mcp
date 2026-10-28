---
name: publisher-listing-types
description: Use when a Marketplace publisher is unsure which listing type fits their offer, or wants to create a Lead Generation, Service, or OCI Application draft.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-28
---

# Create a publisher listing

## Connect and verify the publisher account

Choosing a listing type or explaining requirements needs no sign-in. Before the first private read, call `get_publisher_connection_context` and compare its configured tenancy and region with the publisher's requested account and `us-ashburn-1`. Record the selected profile and authentication mode without requesting or displaying keys, tokens, or passwords. This tool loads configuration; it does not prove token validity, the authenticated principal, or Publisher permissions. A profile name is not tenancy evidence. Resolve any mismatch before a write; never silently switch profiles or use internal operator access for an outside publisher.

If a session is missing or expired, use the customer's chosen profile with `oci session authenticate --region us-ashburn-1 --profile-name <publisher-profile>` when local CLI access is available, and let the customer complete browser password/MFA entry. Validate with `oci session validate --profile <publisher-profile> --auth security_token`. Configure the MCP process with `OCI_CONFIG_PROFILE`, `OCI_REGION=us-ashburn-1`, and `OCI_MCP_AUTH_TYPE=security_token` for that session; preserve an existing API-key setup when selected. Restart the MCP process after changing its environment. Console login alone does not authenticate the server. If local authentication tools are unavailable, give these setup steps and stop private operations until the configured MCP read succeeds.

Use an operation-relevant read to verify access: `get_publisher_revision` for a supplied revision, `get_publisher_listing` for its parent listing, and `get_publisher_profile` when checking publisher identity. Before a write, match the returned listing, publisher, and compartment to the customer's requested target. A 401 needs authentication repair; a 403 or `NotAuthorizedOrNotFound` needs target/IAM investigation, not another write attempt. Perform authorized actions with the tools and re-read their result. Reuse approval covering the exact target and change; do not stop at illustrative instructions when execution was requested and access is verified. Report unavailable capabilities or uncertain outcomes accurately.

## Choose with the publisher

Do not ask the publisher to pick a listing type before explaining the choices. Ask only the unanswered questions, one at a time:

1. What does the customer receive: software, a professional service, or an AI agent? What happens when they select **Get App**, **Contact Us**, or **Activate**?
2. If software: will the customer deploy an artifact in OCI, activate a paid SaaS subscription through a partner provisioning URL, or be sent to your site / submit a lead for a separate sale? If deployed, what artifact do you have: container image, Helm chart, compute image, or Terraform stack?
3. Is the offer free, BYOL, or paid through Marketplace? Where will it run, and which Oracle product does it actually integrate with? Ask these only when they distinguish the remaining options or affect the listing workflow.

Use the answers, not the product name or marketing category, to recommend [Lead Generation](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-lead-generation-listing.htm) for redirect/lead capture, [Service](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-service-listing.htm) for professional services, or [OCI Application](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-oci-application-listing.htm) for Marketplace deployment or paid SaaS activation. If the offer is an [AI Agent](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-ai-listing.htm), route to its Console workflow; this MCP does not expose that listing type.

If an offer combines software and services, ask which customer action the listing must support first; explain when separate listings may better represent the two offers. If the publisher says “SaaS” but does not want a Marketplace subscription, distinguish an external redirect/lead from paid SaaS activation before recommending a type. A software offer running on OCI is not automatically a Compute Image package. Do not choose a package merely because the publisher has no artifact yet; ask whether they intend to prepare one or want lead capture instead.

Give a short recommendation in plain language: the type and package (if any), what the customer will do, the closest alternative and why it fits less well, and any unanswered fact that could change the answer. Ask the publisher to confirm the recommendation before moving to creation. If they already have a draft of another type or package, inspect it first and do not promise an in-place conversion; explain the supported route or confirm a new listing is needed before taking action.

For `LEAD_GENERATION` or `SERVICE`, use package type `NONE`. For `OCI_APPLICATION`, select a supported SDK package type: `CONTAINER_IMAGE`, `HELM_CHART`, `MACHINE_IMAGE`, or `STACK`. Oracle's Console documentation also describes paid SaaS, but the installed SDK's listing model does not expose a SaaS package type; use the Console for that option. Package upload, artwork, terms, and other attachments remain Console steps for all types.

Before creation, complete the `publisher-onboarding` checks. Collect the internal listing name, compartment OCID, and type-specific revision metadata from the publisher. List existing listings in that compartment and check the approved name before creating another. Use `create_publisher_listing` only after showing the exact listing type and package type and receiving approval. Save the listing OCID. Use `create_publisher_revision` with the fields supported by the installed SDK model, including public `display_name` and `headline`, only after reviewing those values and receiving approval. Nested fields use OCI SDK snake_case names. If draft creation fails, report the listing OCID so the publisher can resume without creating a duplicate. After an ambiguous creation timeout, reconcile the compartment or known listing by name, type, ID, and revision content before retrying; if no unique result is found, report the outcome as unknown and stop.

For an existing listing, call `list_publisher_revisions` first. Edit only an `ACTIVE` revision with `NEW` status; if a revision is already published, use `clone_publisher_revision` through the `listing-revision-publish` skill. Do not create a second `NEW` revision. After creation, call `get_publisher_revision` and report its OCID and status. Use `inspect_revision_assets` and the listing-type guide to identify remaining Console work before review; an empty attachment or package inventory is not a completed guideline check.
