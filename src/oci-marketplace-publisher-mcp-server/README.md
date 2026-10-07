# OCI Marketplace Publisher MCP Server

This reference server exposes focused tools for publisher readiness, IAM policy inspection, and lead generation listing drafts, review, and publication. It uses the OCI Python SDK and the repository's shared authentication library over stdio. It does not register a new publisher account: Oracle PartnerNetwork and Marketplace onboarding are handled through Oracle's partner process.

## Run from this checkout

Install Python 3.13 and `uv`, configure an OCI CLI profile with publisher tenancy access, then run:

```sh
uv --directory src/oci-marketplace-publisher-mcp-server run --locked oracle.oci-marketplace-publisher-mcp-server
```

An MCP client can launch the same command with `OCI_CONFIG_PROFILE` set to the intended profile. All tools use that profile's OCI permissions. Set `OCI_REGION=us-ashburn-1` when accessing Marketplace Publisher if the profile has another default region. The server uses `build_auth_context()` and accepts its supported stdio authentication modes.

## Workflow

1. Use `publisher_readiness` to find existing publisher records and check Ashburn subscription. If no publisher exists, complete [Oracle's partner onboarding](https://docs.oracle.com/en-us/iaas/Content/Marketplace/new-partners.htm).
2. Use `list_publisher_policies` for the tenancy root and relevant compartment. Review statements against [Marketplace publisher IAM policy guidance](https://docs.oracle.com/en-us/iaas/Content/Marketplace/publisher-iam-policy.htm). This lists policies; it does not evaluate group membership or effective access.
3. Use `create_lead_generation_listing`, then `create_lead_generation_revision` to create a draft. Supply a Marketplace product code and the pricing type for the listing. Use `get_publisher_revision` and `update_lead_generation_revision` to inspect and revise copy.
4. Use `submit_lead_generation_revision` after reviewing the draft and explicitly approving submission. The tool disables auto publication. Once Oracle approves the revision, use `publish_lead_generation_revision` with explicit publication approval. The server checks for `APPROVED` before publishing.

The draft tools cover the core listing text, pricing type, and product codes. Add any required support contacts, links, artwork, and other Marketplace content in the Console before submitting for review. Oracle may reject an incomplete revision; this server does not upload listing assets.

The bundled publisher skills are in [`skills/`](skills/) and are intended for publishers using a Codex-compatible skill runner. Copy a skill directory into the runner's skills directory to install it.

## Development

```sh
uv --directory src/oci-marketplace-publisher-mcp-server sync --all-extras --dev
uv --directory src/oci-marketplace-publisher-mcp-server run pytest --cov=oracle.oci_marketplace_publisher_mcp_server.server --cov-branch --cov-report=term-missing
```
