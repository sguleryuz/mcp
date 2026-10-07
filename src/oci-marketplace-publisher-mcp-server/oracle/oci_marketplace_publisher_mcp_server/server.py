"""Copyright (c) 2026, Seyma Guleryuz.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Publisher focused OCI Marketplace MCP tools.
"""

from typing import Annotated

import oci
from fastmcp import FastMCP
from oracle_mcp_common import build_auth_context
from pydantic import Field

from . import __project__, __version__

_USER_AGENT = f"{__project__.removeprefix('oracle.').removesuffix('-server')}/{__version__}"
mcp = FastMCP(name=__project__)


def _clients():
    auth = build_auth_context()
    config = {**auth.config, "additional_user_agent": _USER_AGENT}
    kwargs = {"signer": auth.signer} if auth.signer is not None else {}
    return (
        oci.marketplace_publisher.MarketplacePublisherClient(config, **kwargs),
        oci.identity.IdentityClient(config, **kwargs),
    )


def _all(client_method, *args, **kwargs):
    return oci.pagination.list_call_get_all_results(client_method, *args, **kwargs).data


def _data(response):
    return oci.util.to_dict(response.data)


def publisher_readiness(
    compartment_id: Annotated[str, Field(description="Publisher compartment OCID")],
    tenancy_id: Annotated[str, Field(description="Publisher tenancy OCID")],
) -> dict:
    """Report existing publisher records and Ashburn region subscription."""
    publisher, identity = _clients()
    publishers = _all(publisher.list_publishers, compartment_id)
    regions = _all(identity.list_region_subscriptions, tenancy_id)
    return {
        "publishers": [{"id": item.id, "status": item.publisher_status} for item in publishers],
        "ashburn_subscribed": any(item.region_name == "us-ashburn-1" for item in regions),
    }


def list_publisher_policies(
    compartment_id: Annotated[str, Field(description="Compartment OCID containing IAM policies")],
) -> dict:
    """List policy statements for one compartment; this does not prove effective access."""
    _, identity = _clients()
    policies = _all(identity.list_policies, compartment_id)
    return {
        "policies": [
            {"id": policy.id, "name": policy.name, "statements": policy.statements} for policy in policies
        ],
        "scope": compartment_id,
        "effective_access_verified": False,
    }


def list_publisher_listings(
    compartment_id: Annotated[str, Field(description="Publisher compartment OCID")],
) -> list[dict]:
    """List Marketplace publisher listings in a compartment."""
    publisher, _ = _clients()
    return [oci.util.to_dict(item) for item in _all(publisher.list_listings, compartment_id)]


def get_publisher_revision(
    listing_revision_id: Annotated[str, Field(description="Listing revision OCID")],
) -> dict:
    """Get a listing revision including its current review status."""
    publisher, _ = _clients()
    return _data(publisher.get_listing_revision(listing_revision_id))


def create_lead_generation_listing(
    compartment_id: Annotated[str, Field(description="Publisher compartment OCID")],
    name: Annotated[str, Field(min_length=1, description="Internal listing name")],
) -> dict:
    """Create a lead generation listing container with no deployable package."""
    publisher, _ = _clients()
    details = oci.marketplace_publisher.models.CreateListingDetails(
        compartment_id=compartment_id,
        name=name,
        listing_type="LEAD_GENERATION",
        package_type="NONE",
    )
    return _data(publisher.create_listing(details))


def create_lead_generation_revision(
    listing_id: Annotated[str, Field(description="Lead generation listing OCID")],
    display_name: Annotated[str, Field(min_length=1, description="Public listing title")],
    headline: Annotated[str, Field(min_length=1, description="Public headline")],
    short_description: Annotated[str, Field(min_length=1, description="Public summary")],
    pricing_type: Annotated[str, Field(description="Marketplace pricing type")],
    product_codes: Annotated[list[str], Field(min_length=1, description="OCI Marketplace product codes")],
) -> dict:
    """Create a draft lead generation listing revision."""
    publisher, _ = _clients()
    listing = publisher.get_listing(listing_id).data
    if listing.listing_type != "LEAD_GENERATION":
        raise ValueError("Listing must have type LEAD_GENERATION")
    details = oci.marketplace_publisher.models.CreateLeadGenListingRevisionDetails(
        listing_id=listing_id,
        display_name=display_name,
        headline=headline,
        short_description=short_description,
        pricing_type=pricing_type,
        products=[oci.marketplace_publisher.models.ListingProduct(code=code) for code in product_codes],
    )
    return _data(publisher.create_listing_revision(details))


def update_lead_generation_revision(
    listing_revision_id: Annotated[str, Field(description="Draft listing revision OCID")],
    display_name: Annotated[str | None, Field(description="Replacement public title")] = None,
    headline: Annotated[str | None, Field(description="Replacement headline")] = None,
    short_description: Annotated[str | None, Field(description="Replacement public summary")] = None,
) -> dict:
    """Update selected copy fields on a draft or rejected lead generation revision."""
    changes = {
        key: value
        for key, value in {
            "display_name": display_name,
            "headline": headline,
            "short_description": short_description,
        }.items()
        if value is not None
    }
    if not changes:
        raise ValueError("Supply at least one revision field")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.listing_type != "LEAD_GENERATION" or revision.status not in {"NEW", "REJECTED"}:
        raise ValueError("Revision must be lead generation and editable (NEW or REJECTED)")
    details = oci.marketplace_publisher.models.UpdateLeadGenListingRevisionDetails(**changes)
    return _data(publisher.update_listing_revision(listing_revision_id, details))


def submit_lead_generation_revision(
    listing_revision_id: Annotated[str, Field(description="Listing revision OCID")],
    confirm_submission: Annotated[bool, Field(description="Explicit approval to submit for Oracle review")],
    note: Annotated[str | None, Field(description="Optional note for reviewers")] = None,
) -> dict:
    """Submit an editable revision for review without auto-publishing."""
    if not confirm_submission:
        raise ValueError("Explicit submission confirmation is required")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.listing_type != "LEAD_GENERATION" or revision.status not in {"NEW", "REJECTED"}:
        raise ValueError("Revision must be lead generation and NEW or REJECTED")
    details = oci.marketplace_publisher.models.SubmitListingRevisionForReviewDetails(
        note_details=note,
        should_auto_publish_on_approval=False,
    )
    return _data(publisher.submit_listing_revision_for_review(details, listing_revision_id))


def publish_lead_generation_revision(
    listing_revision_id: Annotated[str, Field(description="Approved listing revision OCID")],
    confirm_publish: Annotated[bool, Field(description="Explicit approval to publish publicly")],
) -> dict:
    """Publish a lead generation revision after Oracle approval."""
    if not confirm_publish:
        raise ValueError("Explicit publication confirmation is required")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.listing_type != "LEAD_GENERATION" or revision.status != "APPROVED":
        raise ValueError("Revision must be lead generation and APPROVED")
    publisher.publish_listing_revision(listing_revision_id)
    return {"listing_revision_id": listing_revision_id, "publication_requested": True}


for tool in (
    publisher_readiness,
    list_publisher_policies,
    list_publisher_listings,
    get_publisher_revision,
    create_lead_generation_listing,
    create_lead_generation_revision,
    update_lead_generation_revision,
    submit_lead_generation_revision,
    publish_lead_generation_revision,
):
    mcp.tool()(tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
