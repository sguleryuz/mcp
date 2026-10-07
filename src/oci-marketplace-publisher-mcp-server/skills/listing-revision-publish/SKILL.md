---
name: listing-revision-publish
description: Use when a Marketplace publisher wants to revise, submit for review, or publish a lead generation listing revision.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-06
---

# Revise and publish

Get the revision OCID and call `get_publisher_revision`. Show its listing type, current text, and review status. Use `update_lead_generation_revision` only for a `LEAD_GENERATION` revision with status `NEW` or `REJECTED`; show the exact replacement fields and get the publisher's approval before the update. Re-read the revision after updating.

Before submission, confirm that required support contacts, links, artwork, and other Marketplace content have been completed in the Console. Tell the publisher that `submit_lead_generation_revision` sends the revision to Oracle for review and does not auto publish it. Ask for explicit submission approval, then call that tool with `confirm_submission=true`. Report the returned status. Do not treat submission as approval.

Before publication, re-read the revision. If its status is not `APPROVED`, stop and report the current status. If approved, show the revision OCID and public listing content, ask for explicit publication approval, then call `publish_lead_generation_revision` with `confirm_publish=true`. Re-read and report the status after the call. Follow [Oracle's publication guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/publish-listing.htm) for Marketplace review requirements.
