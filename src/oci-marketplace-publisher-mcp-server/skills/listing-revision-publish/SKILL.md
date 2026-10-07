---
name: listing-revision-publish
description: Use when a Marketplace publisher wants to clone, revise, submit, publish, or withdraw a listing revision.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-07
---

# Revise and publish

Get the listing OCID and call `list_publisher_revisions`. If a `NEW` revision exists, continue that draft; Oracle permits only one `NEW` revision per listing. If the source revision is `PUBLISHED`, `PUBLISHED_AS_PRIVATE`, or `UNPUBLISHED` and no `NEW` revision exists, show the source revision and ask for approval to call `clone_publisher_revision`. The clone becomes a new draft under the same listing. If the tool returns no `new_revision_id` yet, list revisions again before editing. Do not create a fresh revision in place of a required clone. See [Oracle's clone guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/clone-listing.htm).

Call `get_publisher_revision` for the selected draft. For a `NEW` or `REJECTED` revision, use `update_publisher_revision` for type-specific metadata fields supported by the installed OCI SDK; `update_lead_generation_revision` remains available for the focused lead-generation flow. Show the exact replacements and get the publisher's approval before updating. Re-read after the update. Use the Console for packages, artwork, terms, and other attachments, which these tools do not upload.

Before submission, call `inspect_revision_assets` and compare its revision, attachment, and package inventory with [Oracle's listing guidelines](https://docs.oracle.com/en-us/iaas/Content/Marketplace/pub-guidelines.htm) and the relevant listing-type guide. Check the headline, descriptions, product/category filters, support contacts and links, language, version, system requirements, usage text, artwork, screenshots, related documents, and package details when applicable. The inventory never certifies guideline compliance; confirm required assets and terms are complete in the Console. This server does not upload them. Confirm active OCMA through `publisher-onboarding`. Treat missing content as pending, not complete.

For an application listing, verify the public name is at most 80 characters with no line break; the headline states the purpose in at most two lines; the description names the audience and value; support has a working email or phone; and links, usage instructions, documents, terms, and any package version agree. Check image dimensions and size in the Console: listing icon 130×130 pixels, at most 5 MB; banner 1160×200 pixels, at most 10 MB. Use the [publishing guidelines](https://docs.oracle.com/en-us/iaas/Content/Marketplace/pub-guidelines.htm) for the remaining requirements, including package-specific security and documentation. Report each relevant check as confirmed, pending, or unknown; do not infer compliance from the presence of an attachment alone.

`submit_publisher_revision` defaults to **manual publication after approval**. If the publisher explicitly chooses auto-publication, confirm that Oracle has enabled that option for their account and show that approval will make the listing public without another step. Get separate approval for submission and auto-publication before setting both confirmation flags. The optional internal-tenancy-launch setting applies only when the publisher intends it. Re-read the revision after submission; submission is not approval. See [Oracle's listing lifecycle](https://docs.oracle.com/en-us/iaas/Content/Marketplace/manage-listings.htm).

Before publication, re-read the revision. Require `APPROVED`. Show the content and ask whether to publish **PUBLIC** or **PRIVATE**. For private publication, collect and verify the customer tenancy OCIDs and show the exact allowlist. Use `publish_publisher_revision` with explicit publication approval. Re-read and report the resulting status. See [Oracle's publication guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/publish-listing.htm).

If the publisher asks to remove a live public or private revision, show its status and explain that withdrawal removes availability. Get explicit approval, then call `withdraw_publisher_revision` and re-read its status. Do not use withdrawal to fix a `NEW` draft.
