# OCI Marketplace Publisher MCP Server

This reference server exposes focused tools for publisher readiness, IAM policy inspection, lead generation listing drafts, and shared listing-revision lifecycle actions. It uses the OCI Python SDK and the repository's shared authentication library over stdio. The SDK can read publisher approval and OPN membership from the detailed Publisher record; OCMA activation and new publisher registration still require Oracle partner and Console processes. The bundled `publisher-onboarding` skill tracks those confirmations for new and existing partners.

## Run from this checkout

Install Python 3.13 and `uv`, configure an OCI CLI profile with publisher tenancy access, then run:

```sh
uv --directory src/oci-marketplace-publisher-mcp-server run --locked oracle.oci-marketplace-publisher-mcp-server
```

An MCP client can launch the same command with `OCI_CONFIG_PROFILE` set to the intended profile. All tools use that profile's OCI permissions. Set `OCI_REGION=us-ashburn-1` when accessing Marketplace Publisher if the profile has another default region. The server uses `build_auth_context()` and accepts its supported stdio authentication modes.

## Workflow

1. Use the [`publisher-onboarding` skill](skills/publisher-onboarding/SKILL.md) to confirm every applicable step, including active OPN membership, active OCMA, production Console registration and approval, Ashburn subscription, and IAM. New partners follow [Oracle's new-partner guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/new-partners.htm). Existing partners follow the [migration guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/existing-partners.htm) and check production Publisher Registration before the migration request. `publisher_readiness` fetches detailed Publisher records to report approval and OPN status as well as the Ashburn subscription; it cannot verify OCMA.
2. Use `list_publisher_policies` for the tenancy root and relevant compartment. Review statements against [Marketplace publisher IAM policy guidance](https://docs.oracle.com/en-us/iaas/Content/Marketplace/publisher-iam-policy.htm). This lists policies; it does not evaluate group membership or effective access.
3. Use `create_publisher_listing` and `create_publisher_revision` to create a first draft for Lead Generation, Service, or OCI Application using the installed SDK's type-specific metadata model. The focused `create_lead_generation_listing` and `create_lead_generation_revision` tools remain available; the latter's `options` argument accepts the other lead-generation fields listed below. For an existing listing, use `list_publisher_revisions` to find a `NEW` draft or `clone_publisher_revision` to copy a `PUBLISHED`, `PUBLISHED_AS_PRIVATE`, or `UNPUBLISHED` revision into a new draft. A published revision must be cloned before editing; a listing can have only one `NEW` revision. See [Oracle's clone guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/clone-listing.htm).
4. Use `get_publisher_revision` and `update_publisher_revision` to inspect and edit type-specific modeled fields on a draft; the focused lead-generation update tool remains available. `inspect_revision_assets` inventories attachments and OCI Application packages for guideline review; it does not certify compliance. `submit_publisher_revision` supports manual or explicitly confirmed auto publication after Oracle approval, plus the optional internal-tenancy-launch setting. `publish_publisher_revision` supports public publication or private publication to an explicit tenancy allowlist. `withdraw_publisher_revision` removes a published revision from availability. The earlier lead-generation submit/publish tools remain available for manual public publication.

`create_publisher_listing` supports the SDK's `LEAD_GENERATION`, `SERVICE`, and `OCI_APPLICATION` listing types. The first two require package type `NONE`; OCI Application requires `CONTAINER_IMAGE`, `HELM_CHART`, `MACHINE_IMAGE`, or `STACK`. The SDK version pinned here does not model a SaaS package type even though Oracle's Console guide mentions it; create those listings in the Console. `create_publisher_revision` and `update_publisher_revision` validate metadata field names against the corresponding Lead Generation, Service, or OCI Application SDK model and convert nested model objects. They do not create package artifacts, upload media, or manage terms. Those steps remain in the Console before review.

### Lead-generation revision fields

`create_lead_generation_revision` takes the public title, headline, short description, pricing type, and product codes as direct arguments. Its `options` mapping accepts the remaining fields in the installed OCI SDK's `CreateLeadGenListingRevisionDetails`: `tagline`, `keywords`, `usage_information`, `long_description`, `content_language`, `supportedlanguages`, `support_contacts`, `support_links`, `freeform_tags`, `defined_tags`, `version_details`, `system_requirements`, `demo_url`, `self_paced_training_url`, `recommended_service_provider_listing_ids`, `vanity_url`, `download_info`, and `pricing_plans`. It also accepts detailed `products` with `code`, `categories`, and `additional_filters`; the product codes must match the direct `product_codes` argument. `update_lead_generation_revision` accepts the corresponding editable SDK fields through `options`, including `products` and `pricing_type`. Nested objects use the OCI SDK's snake_case field names and are checked against its model schema before a request is sent. The server controls listing ID, type, and status rather than accepting them as options.

The lead-generation tools cover modeled revision metadata, including support contacts and links. Add required artwork, screenshots, documents, banner, terms, and other attachments in the Console before submitting for review. Oracle may reject an incomplete revision; this server does not upload listing assets or packages. Check the [lead-generation guide](https://docs.oracle.com/en-us/iaas/Content/Marketplace/Tasks/creating-lead-generation-listing.htm) and [listing guidelines](https://docs.oracle.com/en-us/iaas/Content/Marketplace/pub-guidelines.htm) before submission.

The bundled publisher skills are in [`skills/`](skills/) and are intended for publishers using a Codex-compatible skill runner. The wheel also includes them under `oracle/oci_marketplace_publisher_mcp_server/skills/`. Copy the required skill directories from one pinned release into the runner's skills directory. `lead-generation-listing` uses `publisher-onboarding`, `publisher-iam`, and `listing-revision-publish`; `listing-revision-publish` also uses the onboarding and IAM checks. A missing dependency blocks the dependent workflow. Installing a single skill directory does not install its dependencies.

### Clone a listing revision with OCI CLI

The standalone [`clone-listing-revision` skill](skills/clone-listing-revision/SKILL.md) helps publishers create a new draft in **Marketplace staging (Phoenix)** using their installed OCI CLI and a Codex-compatible runner with terminal access. This version uses `https://cloud-staging.oracle.com` for Console guidance and `https://beta.marketplace-publisher.us-phoenix-1.oci.oracleiaas.com` for every Publisher operation, with no production fallback. Staging access is required. OCI authentication and IAM retain their standard regional identity endpoints. It has no MCP server or other skill dependency. Every new invocation uses `oci session authenticate` with a fresh OCI profile and an isolated browser profile; the publisher completes Oracle login and MFA and verifies the selected tenancy before listing discovery. An installed browser capable of profile isolation is required; the command reference documents the macOS/Linux flow and the boundary for other platforms.

Copy the entire `skills/clone-listing-revision` directory from a pinned checkout or release into your runner's skills directory, including `agents/` and `references/`. For Codex, install it as `$CODEX_HOME/skills/clone-listing-revision` (normally `~/.codex/skills/clone-listing-revision`). Then ask:

```text
Use $clone-listing-revision to show which of my listings I can clone.
```

After reviewing the results, select a source with a request such as `Clone option 2`. The skill checks publisher ownership and readiness, active OPN membership and OCMA, publisher logo, source status, conflicting drafts or operations, and applicable package defaults, version uniqueness, and whitespace rules. When the CLI cannot provide required evidence, it asks for the specific current Console or Oracle confirmation and keeps cloning blocked until verified.

The skill refreshes the checks before sending one clone request, verifies the new draft, and resumes inspection after an uncertain result without resending the request. Editing, submission, and publication require separate requests.

## Development

```sh
uv --directory src/oci-marketplace-publisher-mcp-server sync --all-extras --dev
uv --directory src/oci-marketplace-publisher-mcp-server run pytest --cov=oracle.oci_marketplace_publisher_mcp_server.server --cov-branch --cov-report=term-missing
```
