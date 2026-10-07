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


def _oci_field(field_type: str, value):
    if value is None:
        return None
    if field_type.startswith("list["):
        if not isinstance(value, list):
            raise ValueError(f"Expected a list for {field_type}")
        item_type = field_type[5:-1]
        return [_oci_field(item_type, item) for item in value]
    if field_type.startswith("dict("):
        if not isinstance(value, dict):
            raise ValueError(f"Expected a mapping for {field_type}")
        return value
    if field_type in {"str", "int", "bool"}:
        expected = {"str": str, "int": int, "bool": bool}[field_type]
        if not isinstance(value, expected):
            raise ValueError(f"Expected {field_type}")
        return value
    model = getattr(oci.marketplace_publisher.models, field_type)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping for {field_type}")
    schema = model().swagger_types
    unknown = set(value) - set(schema)
    if unknown:
        raise ValueError(f"Unsupported {field_type} field: {', '.join(sorted(unknown))}")
    return model(**{key: _oci_field(schema[key], item) for key, item in value.items()})


def _revision_options(model, options: dict | None, excluded: set[str]) -> dict:
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError("Revision options must be a mapping")
    schema = model().swagger_types
    unknown = set(options) - (set(schema) - excluded)
    if unknown:
        raise ValueError(f"Unsupported revision field: {', '.join(sorted(unknown))}")
    return {key: _oci_field(schema[key], value) for key, value in options.items()}


_REVISION_MODELS = {
    "LEAD_GENERATION": (
        oci.marketplace_publisher.models.CreateLeadGenListingRevisionDetails,
        oci.marketplace_publisher.models.UpdateLeadGenListingRevisionDetails,
    ),
    "SERVICE": (
        oci.marketplace_publisher.models.CreateServiceListingRevisionDetails,
        oci.marketplace_publisher.models.UpdateServiceListingRevisionDetails,
    ),
    "OCI_APPLICATION": (
        oci.marketplace_publisher.models.CreateOciListingRevisionDetails,
        oci.marketplace_publisher.models.UpdateOciListingRevisionDetails,
    ),
}


def publisher_readiness(
    compartment_id: Annotated[str, Field(description="Publisher compartment OCID")],
    tenancy_id: Annotated[str, Field(description="Publisher tenancy OCID")],
) -> dict:
    """Report existing publisher records and Ashburn region subscription."""
    publisher, identity = _clients()
    publishers = [
        publisher.get_publisher(item.id).data for item in _all(publisher.list_publishers, compartment_id)
    ]
    regions = _all(identity.list_region_subscriptions, tenancy_id)
    return {
        "publishers": [
            {
                "id": item.id,
                "status": item.publisher_status,
                "opn_status": item.opn_membership.opn_status if item.opn_membership else None,
                "opn_number": item.opn_membership.opn_number if item.opn_membership else None,
            }
            for item in publishers
        ],
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


def get_publisher_profile(
    publisher_id: Annotated[str, Field(description="Marketplace publisher OCID")],
) -> dict:
    """Get publisher approval and OPN membership details from OCI."""
    publisher, _ = _clients()
    return _data(publisher.get_publisher(publisher_id))


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


def list_publisher_revisions(
    listing_id: Annotated[str, Field(description="Listing OCID")],
) -> list[dict]:
    """List all revisions and statuses for a listing."""
    publisher, _ = _clients()
    return [oci.util.to_dict(item) for item in _all(publisher.list_listing_revisions, listing_id)]


def inspect_revision_assets(
    listing_revision_id: Annotated[str, Field(description="Listing revision OCID")],
) -> dict:
    """Inventory revision attachments and packages for a guideline review."""
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    attachments = _all(publisher.list_listing_revision_attachments, listing_revision_id)
    packages = (
        _all(publisher.list_listing_revision_packages, listing_revision_id)
        if revision.listing_type == "OCI_APPLICATION"
        else []
    )
    return {
        "revision": oci.util.to_dict(revision),
        "attachments": [oci.util.to_dict(item) for item in attachments],
        "packages": [oci.util.to_dict(item) for item in packages],
        "guideline_review_complete": False,
    }


def clone_publisher_revision(
    listing_revision_id: Annotated[str, Field(description="Published or unpublished source revision OCID")],
    confirm_clone: Annotated[bool, Field(description="Explicit approval to create a new draft revision")],
) -> dict:
    """Clone a published, privately published, or unpublished revision into a new draft."""
    if not confirm_clone:
        raise ValueError("Explicit clone confirmation is required")
    publisher, _ = _clients()
    source = publisher.get_listing_revision(listing_revision_id).data
    if source.status not in {"PUBLISHED", "PUBLISHED_AS_PRIVATE", "UNPUBLISHED"}:
        raise ValueError("Source must be PUBLISHED, PUBLISHED_AS_PRIVATE, or UNPUBLISHED")
    before = _all(publisher.list_listing_revisions, source.listing_id)
    if any(item.status == "NEW" for item in before):
        raise ValueError("A NEW revision already exists for this listing; edit or submit it first")
    old_ids = {item.id for item in before}
    publisher.clone_listing_revision(listing_revision_id)
    after = _all(publisher.list_listing_revisions, source.listing_id)
    cloned = next((item for item in after if item.status == "NEW" and item.id not in old_ids), None)
    return {
        "source_revision_id": listing_revision_id,
        "new_revision_id": cloned.id if cloned else None,
        "clone_requested": True,
    }


def submit_publisher_revision(
    listing_revision_id: Annotated[str, Field(description="Draft revision OCID")],
    confirm_submission: Annotated[bool, Field(description="Explicit approval to submit for Oracle review")],
    note: Annotated[str | None, Field(description="Optional reviewer note")] = None,
    auto_publish_on_approval: Annotated[
        bool, Field(description="Publish publicly when Oracle approves")
    ] = False,
    confirm_auto_publish: Annotated[
        bool, Field(description="Separate approval for automatic public publication")
    ] = False,
    allow_internal_tenancy_launch: Annotated[
        bool, Field(description="Allow internal tenancy launches")
    ] = False,
) -> dict:
    """Submit a draft revision for review with explicit publication controls."""
    if not confirm_submission:
        raise ValueError("Explicit submission confirmation is required")
    if auto_publish_on_approval and not confirm_auto_publish:
        raise ValueError("Separate auto-publication confirmation is required")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.status not in {"NEW", "REJECTED"}:
        raise ValueError("Revision must be NEW or REJECTED")
    details = oci.marketplace_publisher.models.SubmitListingRevisionForReviewDetails(
        note_details=note,
        should_auto_publish_on_approval=auto_publish_on_approval,
        are_internal_tenancy_launch_allowed=allow_internal_tenancy_launch,
    )
    return _data(publisher.submit_listing_revision_for_review(details, listing_revision_id))


def publish_publisher_revision(
    listing_revision_id: Annotated[str, Field(description="Approved revision OCID")],
    visibility: Annotated[str, Field(description="PUBLIC or PRIVATE")],
    confirm_publish: Annotated[bool, Field(description="Explicit approval to publish")],
    allowed_tenancies: Annotated[
        list[str] | None, Field(description="Customer tenancy OCIDs for PRIVATE publication")
    ] = None,
) -> dict:
    """Publish an approved revision publicly or for specified tenancies."""
    if not confirm_publish:
        raise ValueError("Explicit publication confirmation is required")
    visibility = visibility.upper()
    if visibility not in {"PUBLIC", "PRIVATE"}:
        raise ValueError("Visibility must be PUBLIC or PRIVATE")
    if visibility == "PRIVATE" and not allowed_tenancies:
        raise ValueError("PRIVATE publication requires at least one allowed tenancy OCID")
    if visibility == "PUBLIC" and allowed_tenancies:
        raise ValueError("PUBLIC publication cannot include allowed tenancies")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.status != "APPROVED":
        raise ValueError("Revision must be APPROVED")
    if visibility == "PRIVATE":
        details = oci.marketplace_publisher.models.PublishListingRevisionAsPrivateDetails(
            allowed_tenancies=allowed_tenancies
        )
        publisher.publish_listing_revision_as_private(details, listing_revision_id)
    else:
        publisher.publish_listing_revision(listing_revision_id)
    return {
        "listing_revision_id": listing_revision_id,
        "visibility": visibility,
        "publication_requested": True,
    }


def withdraw_publisher_revision(
    listing_revision_id: Annotated[str, Field(description="Published revision OCID")],
    confirm_withdraw: Annotated[bool, Field(description="Explicit approval to withdraw from Marketplace")],
) -> dict:
    """Withdraw a public or private published revision."""
    if not confirm_withdraw:
        raise ValueError("Explicit withdrawal confirmation is required")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.status not in {"PUBLISHED", "PUBLISHED_AS_PRIVATE"}:
        raise ValueError("Revision must be PUBLISHED or PUBLISHED_AS_PRIVATE")
    publisher.withdraw_listing_revision(listing_revision_id)
    return {"listing_revision_id": listing_revision_id, "withdraw_requested": True}


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


def create_publisher_listing(
    compartment_id: Annotated[str, Field(description="Publisher compartment OCID")],
    name: Annotated[str, Field(min_length=1, description="Internal listing name")],
    listing_type: Annotated[str, Field(description="LEAD_GENERATION, SERVICE, or OCI_APPLICATION")],
    package_type: Annotated[
        str, Field(description="NONE, CONTAINER_IMAGE, HELM_CHART, MACHINE_IMAGE, or STACK")
    ],
    confirm_create: Annotated[bool, Field(description="Explicit approval to create the listing")],
) -> dict:
    """Create a listing container using the package types in the installed SDK."""
    if not confirm_create:
        raise ValueError("Explicit listing creation confirmation is required")
    if listing_type not in _REVISION_MODELS:
        raise ValueError("Unsupported listing type")
    package_types = {"NONE", "CONTAINER_IMAGE", "HELM_CHART", "MACHINE_IMAGE", "STACK"}
    if package_type not in package_types:
        raise ValueError("Unsupported package type")
    if listing_type == "OCI_APPLICATION" and package_type == "NONE":
        raise ValueError("OCI_APPLICATION requires a deployable package type")
    if listing_type != "OCI_APPLICATION" and package_type != "NONE":
        raise ValueError("Non-OCI listings require package type NONE")
    publisher, _ = _clients()
    details = oci.marketplace_publisher.models.CreateListingDetails(
        compartment_id=compartment_id,
        name=name,
        listing_type=listing_type,
        package_type=package_type,
    )
    return _data(publisher.create_listing(details))


def create_publisher_revision(
    listing_id: Annotated[str, Field(description="Listing OCID")],
    fields: Annotated[
        dict, Field(description="SDK fields for the listing type, including headline and display_name")
    ],
    confirm_create: Annotated[bool, Field(description="Explicit approval to create a draft revision")],
) -> dict:
    """Create a first draft with type-specific OCI SDK metadata fields."""
    if not confirm_create:
        raise ValueError("Explicit revision creation confirmation is required")
    if not isinstance(fields, dict) or not fields.get("headline") or not fields.get("display_name"):
        raise ValueError("Revision fields require a display_name and headline")
    publisher, _ = _clients()
    listing = publisher.get_listing(listing_id).data
    model_pair = _REVISION_MODELS.get(listing.listing_type)
    if model_pair is None:
        raise ValueError("Unsupported listing type")
    values = _revision_options(model_pair[0], fields, {"listing_id", "listing_type", "status"})
    revisions = _all(publisher.list_listing_revisions, listing_id)
    if any(item.status == "NEW" for item in revisions):
        raise ValueError("A NEW revision already exists; edit or submit it instead")
    if any(item.status in {"PUBLISHED", "PUBLISHED_AS_PRIVATE"} for item in revisions):
        raise ValueError("A published revision exists; clone it to create the next draft")
    details = model_pair[0](listing_id=listing_id, listing_type=listing.listing_type, **values)
    return _data(publisher.create_listing_revision(details))


def update_publisher_revision(
    listing_revision_id: Annotated[str, Field(description="Draft listing revision OCID")],
    fields: Annotated[dict, Field(description="Replacement SDK fields for this listing type")],
    confirm_update: Annotated[bool, Field(description="Explicit approval to update the draft")],
) -> dict:
    """Edit type-specific fields on a NEW or REJECTED revision."""
    if not confirm_update:
        raise ValueError("Explicit revision update confirmation is required")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("Supply at least one revision field")
    if "listing_type" in fields:
        raise ValueError("Unsupported revision field: listing_type")
    publisher, _ = _clients()
    revision = publisher.get_listing_revision(listing_revision_id).data
    if revision.status not in {"NEW", "REJECTED"}:
        raise ValueError("Revision must be NEW or REJECTED")
    model_pair = _REVISION_MODELS.get(revision.listing_type)
    if model_pair is None:
        raise ValueError("Unsupported listing type")
    values = _revision_options(model_pair[1], fields, {"listing_type"})
    details = model_pair[1](**values)
    return _data(publisher.update_listing_revision(listing_revision_id, details))


def create_lead_generation_revision(
    listing_id: Annotated[str, Field(description="Lead generation listing OCID")],
    display_name: Annotated[str, Field(min_length=1, description="Public listing title")],
    headline: Annotated[str, Field(min_length=1, description="Public headline")],
    short_description: Annotated[str, Field(min_length=1, description="Public summary")],
    pricing_type: Annotated[str, Field(description="Marketplace pricing type")],
    product_codes: Annotated[list[str], Field(min_length=1, description="OCI Marketplace product codes")],
    options: Annotated[
        dict | None,
        Field(
            description="Additional SDK revision fields, including categories, support, version, URLs, and descriptions"
        ),
    ] = None,
) -> dict:
    """Create a draft lead generation listing revision."""
    extra = _revision_options(
        oci.marketplace_publisher.models.CreateLeadGenListingRevisionDetails,
        options,
        {
            "listing_id",
            "listing_type",
            "status",
            "display_name",
            "headline",
            "short_description",
            "pricing_type",
        },
    )
    products = extra.pop("products", None)
    if products is None:
        products = [oci.marketplace_publisher.models.ListingProduct(code=code) for code in product_codes]
    elif sorted(item.code for item in products) != sorted(product_codes):
        raise ValueError("Detailed products must match the supplied product codes")
    publisher, _ = _clients()
    listing = publisher.get_listing(listing_id).data
    if listing.listing_type != "LEAD_GENERATION":
        raise ValueError("Listing must have type LEAD_GENERATION")
    revisions = _all(publisher.list_listing_revisions, listing_id)
    if any(item.status == "NEW" for item in revisions):
        raise ValueError("A NEW revision already exists; edit or submit it instead")
    if any(item.status in {"PUBLISHED", "PUBLISHED_AS_PRIVATE"} for item in revisions):
        raise ValueError("A published revision exists; clone it to create the next draft")
    details = oci.marketplace_publisher.models.CreateLeadGenListingRevisionDetails(
        listing_id=listing_id,
        display_name=display_name,
        headline=headline,
        short_description=short_description,
        pricing_type=pricing_type,
        products=products,
        **extra,
    )
    return _data(publisher.create_listing_revision(details))


def update_lead_generation_revision(
    listing_revision_id: Annotated[str, Field(description="Draft listing revision OCID")],
    display_name: Annotated[str | None, Field(description="Replacement public title")] = None,
    headline: Annotated[str | None, Field(description="Replacement headline")] = None,
    short_description: Annotated[str | None, Field(description="Replacement public summary")] = None,
    options: Annotated[
        dict | None,
        Field(
            description="Additional SDK revision fields, including products, support, version, URLs, and descriptions"
        ),
    ] = None,
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
    extra = _revision_options(
        oci.marketplace_publisher.models.UpdateLeadGenListingRevisionDetails,
        options,
        {"listing_type", *changes},
    )
    changes.update(extra)
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
    get_publisher_profile,
    list_publisher_policies,
    list_publisher_listings,
    get_publisher_revision,
    list_publisher_revisions,
    inspect_revision_assets,
    clone_publisher_revision,
    submit_publisher_revision,
    publish_publisher_revision,
    withdraw_publisher_revision,
    create_lead_generation_listing,
    create_publisher_listing,
    create_publisher_revision,
    update_publisher_revision,
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
