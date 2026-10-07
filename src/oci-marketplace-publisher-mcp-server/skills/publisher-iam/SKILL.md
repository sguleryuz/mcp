---
name: publisher-iam
description: Use when a publisher wants to inspect Marketplace Publisher IAM policies or diagnose missing listing permissions in an OCI tenancy.
metadata:
  owner: sguleryuz
  last_updated: 2026-10-06
---

# Publisher IAM review

Ask for the tenancy root OCID and each compartment OCID that may contain relevant IAM policies. Call `list_publisher_policies` once per scope. Report the returned policy names, IDs, and statements relevant to `marketplace-publisher-family`, including where each policy was found.

Compare the statements with [Oracle's Marketplace publisher IAM guidance](https://docs.oracle.com/en-us/iaas/Content/Marketplace/publisher-iam-policy.htm). Explain missing or narrow statements in plain language. Do not assert that access is effective: the tool does not evaluate the caller's group membership, conditions, or inherited grants. If policies appear adequate but a call fails with 403, report the failing operation and ask an IAM administrator to check principal membership and policy conditions.

Never create or change an IAM policy as part of this skill. Draft a proposed statement for the administrator only when asked, using the publisher's actual group and scope; do not guess either value.
