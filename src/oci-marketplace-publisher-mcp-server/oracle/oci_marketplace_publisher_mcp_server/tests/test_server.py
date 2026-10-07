"""Copyright (c) 2026, Seyma Guleryuz.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import oci

from oracle.oci_marketplace_publisher_mcp_server import server


def test_publisher_readiness_reports_publisher_and_region(monkeypatch):
    publisher = Mock()
    publisher.get_publisher.return_value = SimpleNamespace(
        data=SimpleNamespace(
            id="pub1",
            publisher_status="APPROVED",
            opn_membership=SimpleNamespace(opn_status="ACTIVE", opn_number="12345"),
        )
    )
    identity = Mock()
    monkeypatch.setattr(server, "_clients", lambda: (publisher, identity), raising=False)
    monkeypatch.setattr(
        server,
        "_all",
        lambda method, *args: (
            [SimpleNamespace(id="pub1")]
            if method == publisher.list_publishers
            else [SimpleNamespace(region_name="us-ashburn-1")]
        ),
    )

    result = server.publisher_readiness("compartment", "tenancy")

    assert result == {
        "publishers": [{"id": "pub1", "status": "APPROVED", "opn_status": "ACTIVE", "opn_number": "12345"}],
        "ashburn_subscribed": True,
    }


@pytest.fixture
def clients(monkeypatch):
    publisher, identity = Mock(), Mock()
    monkeypatch.setattr(server, "_clients", lambda: (publisher, identity))
    return publisher, identity


def test_readiness_without_publisher_or_ashburn(monkeypatch, clients):
    monkeypatch.setattr(server, "_all", lambda *args: [])
    assert server.publisher_readiness("compartment", "tenancy") == {
        "publishers": [],
        "ashburn_subscribed": False,
    }


def test_get_publisher_profile_exposes_opn_and_approval(clients):
    publisher, _ = clients
    profile = oci.marketplace_publisher.models.Publisher(
        id="pub1",
        publisher_status="APPROVED",
        opn_membership=oci.marketplace_publisher.models.OpnMembership(
            opn_status="ACTIVE", opn_number="12345"
        ),
    )
    publisher.get_publisher.return_value = SimpleNamespace(data=profile)
    result = server.get_publisher_profile("pub1")
    assert result["publisher_status"] == "APPROVED"
    assert result["opn_membership"]["opn_status"] == "ACTIVE"


def test_policies_are_scoped_and_not_effective_access(monkeypatch, clients):
    monkeypatch.setattr(
        server,
        "_all",
        lambda *args: [
            SimpleNamespace(
                id="p1",
                name="publisher",
                statements=["Allow group G to manage marketplace-publisher-family in tenancy"],
            )
        ],
    )
    result = server.list_publisher_policies("root")
    assert result["scope"] == "root"
    assert result["effective_access_verified"] is False
    assert result["policies"][0]["id"] == "p1"


def test_pagination_helper_returns_all_pages(monkeypatch):
    page = Mock(return_value=SimpleNamespace(data=[{"id": "second"}]))
    monkeypatch.setattr(server.oci.pagination, "list_call_get_all_results", page)
    assert server._all(Mock(), "compartment") == [{"id": "second"}]
    assert page.call_args.args[1] == "compartment"


def test_listing_reads_use_oci_response_data(monkeypatch, clients):
    publisher, _ = clients
    monkeypatch.setattr(server, "_all", lambda *args: [{"id": "listing"}])
    publisher.get_listing_revision.return_value = SimpleNamespace(data={"id": "revision", "status": "NEW"})
    assert server.list_publisher_listings("compartment") == [{"id": "listing"}]
    assert server.get_publisher_revision("revision")["status"] == "NEW"


def test_list_revisions_returns_all_pages(monkeypatch, clients):
    publisher, _ = clients
    revision = oci.marketplace_publisher.models.ListingRevisionSummary(id="r1", status="NEW")
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(compartment_id="publisher-compartment"))

    def revisions(method, listing_id, **kwargs):
        assert method == publisher.list_listing_revisions
        assert listing_id == "listing"
        assert kwargs["compartment_id"] == "publisher-compartment"
        return [revision]

    monkeypatch.setattr(server, "_all", revisions)
    result = server.list_publisher_revisions("listing")
    assert result[0]["id"] == "r1" and result[0]["status"] == "NEW"


def test_revision_assets_lists_attachments_and_packages(monkeypatch, clients):
    publisher, _ = clients
    revision = oci.marketplace_publisher.models.OciListingRevision(
        id="r1",
        listing_type="OCI_APPLICATION",
        status="NEW",
        headline="Headline",
    )
    publisher.get_listing_revision.return_value = SimpleNamespace(data=revision)
    attachment = oci.marketplace_publisher.models.ListingRevisionAttachmentSummary(
        id="a1", attachment_type="SCREENSHOT"
    )
    package = oci.marketplace_publisher.models.ListingRevisionPackageSummary(
        id="p1", package_type="CONTAINER_IMAGE"
    )
    monkeypatch.setattr(
        server,
        "_all",
        lambda method, revision_id: (
            [attachment] if method == publisher.list_listing_revision_attachments else [package]
        ),
    )
    result = server.inspect_revision_assets("r1")
    assert result["attachments"][0]["id"] == "a1"
    assert result["packages"][0]["id"] == "p1"
    assert result["guideline_review_complete"] is False


def test_clone_published_revision_finds_new_copy(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(id="r1", listing_id="listing", compartment_id="publisher-compartment", status="PUBLISHED")
    )
    before = [SimpleNamespace(id="r1", status="PUBLISHED")]
    after = before + [SimpleNamespace(id="r2", status="NEW")]
    pages = iter([before, after])
    def revisions(method, listing_id, **kwargs):
        assert kwargs["compartment_id"] == "publisher-compartment"
        return next(pages)

    monkeypatch.setattr(server, "_all", revisions)
    result = server.clone_publisher_revision("r1", True)
    assert result == {"source_revision_id": "r1", "new_revision_id": "r2", "clone_requested": True}


def test_clone_refuses_existing_new_revision(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(id="r1", listing_id="listing", compartment_id="publisher-compartment", status="PUBLISHED")
    )
    monkeypatch.setattr(
        server,
        "_all",
        lambda method, listing_id, **kwargs: [
            SimpleNamespace(id="r1", status="PUBLISHED"),
            SimpleNamespace(id="r2", status="NEW"),
        ],
    )
    with pytest.raises(ValueError, match="NEW revision already exists"):
        server.clone_publisher_revision("r1", True)
    publisher.clone_listing_revision.assert_not_called()


def test_clone_ignores_deleted_new_revision(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(id="r1", listing_id="listing", compartment_id="publisher-compartment", status="PUBLISHED")
    )
    before = [
        SimpleNamespace(id="r1", status="PUBLISHED", lifecycle_state="ACTIVE"),
        SimpleNamespace(id="r2", status="NEW", lifecycle_state="DELETED"),
    ]
    after = before + [SimpleNamespace(id="r3", status="NEW", lifecycle_state="ACTIVE")]
    pages = iter([before, after])
    monkeypatch.setattr(server, "_all", lambda *args, **kwargs: next(pages))
    assert server.clone_publisher_revision("r1", True)["new_revision_id"] == "r3"


@pytest.mark.parametrize("status", ["NEW", "PENDING_REVIEW", "APPROVED"])
def test_clone_refuses_noncloneable_status(clients, status):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(id="r1", listing_id="listing", status=status)
    )
    with pytest.raises(ValueError, match="PUBLISHED"):
        server.clone_publisher_revision("r1", True)
    publisher.clone_listing_revision.assert_not_called()


def test_clone_requires_confirmation(clients):
    with pytest.raises(ValueError, match="confirmation"):
        server.clone_publisher_revision("r1", False)
    clients[0].clone_listing_revision.assert_not_called()


def test_submit_service_revision_with_manual_publication(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="SERVICE", status="NEW")
    )
    publisher.submit_listing_revision_for_review.return_value = SimpleNamespace(data={"id": "r1"})
    server.submit_publisher_revision("r1", True, note="Review")
    details = publisher.submit_listing_revision_for_review.call_args.args[0]
    assert details.should_auto_publish_on_approval is False
    assert details.note_details == "Review"


def test_submit_auto_publish_requires_separate_confirmation(clients):
    publisher, _ = clients
    with pytest.raises(ValueError, match="auto-publication confirmation"):
        server.submit_publisher_revision("r1", True, auto_publish_on_approval=True)
    publisher.submit_listing_revision_for_review.assert_not_called()


def test_submit_can_request_auto_publish_and_internal_launch(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="OCI_APPLICATION", status="NEW")
    )
    publisher.submit_listing_revision_for_review.return_value = SimpleNamespace(data={"id": "r1"})
    server.submit_publisher_revision(
        "r1",
        True,
        auto_publish_on_approval=True,
        confirm_auto_publish=True,
        allow_internal_tenancy_launch=True,
    )
    details = publisher.submit_listing_revision_for_review.call_args.args[0]
    assert details.should_auto_publish_on_approval is True
    assert details.are_internal_tenancy_launch_allowed is True


def test_publish_private_requires_allowed_tenancies(clients):
    publisher, _ = clients
    with pytest.raises(ValueError, match="allowed tenancy"):
        server.publish_publisher_revision("r1", "PRIVATE", True)
    publisher.publish_listing_revision_as_private.assert_not_called()


def test_publish_private_approved_revision(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(data=SimpleNamespace(status="APPROVED"))
    result = server.publish_publisher_revision("r1", "PRIVATE", True, ["ocid1.tenancy.oc1..example"])
    args = publisher.publish_listing_revision_as_private.call_args.args
    assert args[0].allowed_tenancies == ["ocid1.tenancy.oc1..example"]
    assert result["visibility"] == "PRIVATE"


def test_publish_public_rejects_private_tenancies(clients):
    publisher, _ = clients
    with pytest.raises(ValueError, match="PUBLIC"):
        server.publish_publisher_revision("r1", "PUBLIC", True, ["ocid1.tenancy.oc1..example"])
    publisher.publish_listing_revision.assert_not_called()


def test_withdraw_requires_published_status(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(data=SimpleNamespace(status="APPROVED"))
    with pytest.raises(ValueError, match="PUBLISHED"):
        server.withdraw_publisher_revision("r1", True)
    publisher.withdraw_listing_revision.assert_not_called()


def test_withdraw_published_revision(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(data=SimpleNamespace(status="PUBLISHED"))
    assert server.withdraw_publisher_revision("r1", True)["withdraw_requested"] is True


def test_create_listing_uses_lead_generation_and_no_package(clients):
    publisher, _ = clients
    publisher.create_listing.return_value = SimpleNamespace(data={"id": "listing"})
    result = server.create_lead_generation_listing("compartment", "Name")
    details = publisher.create_listing.call_args.args[0]
    assert (details.listing_type, details.package_type, result["id"]) == (
        "LEAD_GENERATION",
        "NONE",
        "listing",
    )


def test_create_service_listing_uses_none_package(clients):
    publisher, _ = clients
    publisher.create_listing.return_value = SimpleNamespace(data={"id": "listing"})
    result = server.create_publisher_listing("compartment", "Name", "SERVICE", "NONE", True)
    details = publisher.create_listing.call_args.args[0]
    assert details.listing_type == "SERVICE" and details.package_type == "NONE"
    assert result["id"] == "listing"


def test_create_oci_listing_rejects_none_package(clients):
    with pytest.raises(ValueError, match="package type"):
        server.create_publisher_listing("compartment", "Name", "OCI_APPLICATION", "NONE", True)
    clients[0].create_listing.assert_not_called()


@pytest.mark.parametrize(
    "listing_type,package_type,confirm_create,error",
    [
        ("SERVICE", "NONE", False, "confirmation"),
        ("SAAS", "NONE", True, "listing type"),
        ("SERVICE", "UNKNOWN", True, "package type"),
        ("SERVICE", "STACK", True, "package type NONE"),
    ],
)
def test_generic_listing_rejects_unsafe_or_unsupported_inputs(
    clients, listing_type, package_type, confirm_create, error
):
    with pytest.raises(ValueError, match=error):
        server.create_publisher_listing("compartment", "Name", listing_type, package_type, confirm_create)
    clients[0].create_listing.assert_not_called()


def test_create_generic_service_revision_converts_nested_fields(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="SERVICE", compartment_id="publisher-compartment")
    )
    publisher.create_listing_revision.return_value = SimpleNamespace(data={"id": "r1"})
    def revisions(method, listing_id, **kwargs):
        assert kwargs["compartment_id"] == "publisher-compartment"
        return []

    monkeypatch.setattr(server, "_all", revisions)
    result = server.create_publisher_revision(
        "listing",
        {
            "display_name": "Service",
            "headline": "Help",
            "short_description": "Summary",
            "support_contacts": [{"name": "Help", "email": "help@example.com"}],
            "product_codes": ["DATABASE"],
        },
        True,
    )
    details = publisher.create_listing_revision.call_args.args[0]
    assert details.listing_type == "SERVICE"
    assert details.support_contacts[0].email == "help@example.com"
    assert result["id"] == "r1"


def test_create_generic_revision_requires_clone_for_published(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="OCI_APPLICATION", compartment_id="publisher-compartment"))
    monkeypatch.setattr(server, "_all", lambda *args, **kwargs: [SimpleNamespace(id="r1", status="PUBLISHED")])
    with pytest.raises(ValueError, match="clone"):
        server.create_publisher_revision("listing", {"display_name": "App", "headline": "Headline"}, True)
    publisher.create_listing_revision.assert_not_called()


def test_create_generic_revision_requires_public_title(clients):
    clients[0].get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="SERVICE"))
    with pytest.raises(ValueError, match="display_name"):
        server.create_publisher_revision("listing", {"headline": "Headline"}, True)
    clients[0].create_listing_revision.assert_not_called()


def test_create_generic_revision_rejects_existing_draft(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="SERVICE", compartment_id="publisher-compartment"))
    monkeypatch.setattr(server, "_all", lambda *args, **kwargs: [SimpleNamespace(id="r1", status="NEW")])
    with pytest.raises(ValueError, match="NEW revision"):
        server.create_publisher_revision("listing", {"display_name": "Service", "headline": "Help"}, True)
    publisher.create_listing_revision.assert_not_called()


def test_update_generic_oci_revision_converts_pricing_plan(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="OCI_APPLICATION", status="NEW", lifecycle_state="ACTIVE")
    )
    publisher.update_listing_revision.return_value = SimpleNamespace(data={"id": "r1"})
    server.update_publisher_revision(
        "r1", {"pricing_type": "PAYGO", "pricing_plans": [{"plan_type": "METERED"}]}, True
    )
    details = publisher.update_listing_revision.call_args.args[1]
    assert details.pricing_plans[0].plan_type == "METERED"


def test_update_generic_revision_rejects_listing_type_override(clients):
    with pytest.raises(ValueError, match="Unsupported revision field"):
        server.update_publisher_revision("r1", {"listing_type": "SERVICE"}, True)
    clients[0].update_listing_revision.assert_not_called()


def test_update_generic_revision_rejects_pending_review(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="SERVICE", status="PENDING_REVIEW")
    )
    with pytest.raises(ValueError, match="NEW or REJECTED"):
        server.update_publisher_revision("r1", {"headline": "Revised"}, True)
    publisher.update_listing_revision.assert_not_called()


def test_update_generic_revision_rejects_deleted_draft(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="NEW", lifecycle_state="DELETED")
    )
    publisher.update_listing_revision.return_value = SimpleNamespace(data={"id": "r1"})
    with pytest.raises(ValueError, match="ACTIVE"):
        server.update_publisher_revision("r1", {"headline": "Revised"}, True)
    publisher.update_listing_revision.assert_not_called()


def test_publish_public_approved_revision(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(data=SimpleNamespace(status="APPROVED"))
    result = server.publish_publisher_revision("r1", "PUBLIC", True)
    publisher.publish_listing_revision.assert_called_once_with("r1")
    assert result["publication_requested"] is True


def test_create_revision_uses_lead_generation_model(monkeypatch, clients):
    publisher, _ = clients
    def revisions(method, listing_id, **kwargs):
        assert kwargs["compartment_id"] == "publisher-compartment"
        return []

    monkeypatch.setattr(server, "_all", revisions)
    publisher.get_listing.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", compartment_id="publisher-compartment")
    )
    publisher.create_listing_revision.return_value = SimpleNamespace(data={"id": "revision"})
    result = server.create_lead_generation_revision(
        "listing", "Name", "Headline", "Summary", "FREE", ["DATABASE"]
    )
    details = publisher.create_listing_revision.call_args.args[0]
    assert (details.listing_type, details.products[0].code, result["id"]) == (
        "LEAD_GENERATION",
        "DATABASE",
        "revision",
    )


def test_create_revision_accepts_guideline_fields_and_nested_products(monkeypatch, clients):
    publisher, _ = clients
    monkeypatch.setattr(server, "_all", lambda *args, **kwargs: [])
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="LEAD_GENERATION", compartment_id="publisher-compartment"))
    publisher.create_listing_revision.return_value = SimpleNamespace(data={"id": "r1"})
    server.create_lead_generation_revision(
        "listing",
        "Name",
        "Headline",
        "Summary",
        "FREE",
        ["DATABASE"],
        options={
            "tagline": "Useful app",
            "long_description": "Detailed value",
            "support_contacts": [{"name": "Support", "email": "support@example.com"}],
            "version_details": {"number": "1.0", "description": "Initial release"},
            "products": [
                {
                    "code": "DATABASE",
                    "categories": ["DATA"],
                    "additional_filters": [{"filter_code": "TYPE", "filter_properties": ["B2B"]}],
                }
            ],
        },
    )
    details = publisher.create_listing_revision.call_args.args[0]
    assert details.support_contacts[0].email == "support@example.com"
    assert details.version_details.number == "1.0"
    assert details.products[0].additional_filters[0].filter_properties == ["B2B"]


def test_create_revision_rejects_product_code_mismatch(clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="LEAD_GENERATION"))
    with pytest.raises(ValueError, match="product codes"):
        server.create_lead_generation_revision(
            "listing",
            "Name",
            "Headline",
            "Summary",
            "FREE",
            ["DATABASE"],
            options={"products": [{"code": "COMPUTE"}]},
        )
    publisher.create_listing_revision.assert_not_called()


def test_create_revision_rejects_unsupported_field(clients):
    with pytest.raises(ValueError, match="Unsupported revision field"):
        server.create_lead_generation_revision(
            "listing",
            "Name",
            "Headline",
            "Summary",
            "FREE",
            ["DATABASE"],
            options={"publisher_status": "APPROVED"},
        )
    clients[0].create_listing_revision.assert_not_called()


def test_create_revision_rejects_other_listing_type(clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="SERVICE"))
    with pytest.raises(ValueError, match="LEAD_GENERATION"):
        server.create_lead_generation_revision("listing", "Name", "Headline", "Summary", "FREE", ["DATABASE"])
    publisher.create_listing_revision.assert_not_called()


def test_create_revision_requires_clone_when_published_exists(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="LEAD_GENERATION", compartment_id="publisher-compartment"))
    publisher.create_listing_revision.return_value = SimpleNamespace(data={"id": "r2"})
    monkeypatch.setattr(
        server,
        "_all",
        lambda *args, **kwargs: [SimpleNamespace(id="r1", status="PUBLISHED")],
    )
    with pytest.raises(ValueError, match="clone"):
        server.create_lead_generation_revision("listing", "Name", "Headline", "Summary", "FREE", ["DATABASE"])
    publisher.create_listing_revision.assert_not_called()


def test_create_revision_refuses_existing_new_draft(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="LEAD_GENERATION", compartment_id="publisher-compartment"))
    publisher.create_listing_revision.return_value = SimpleNamespace(data={"id": "r2"})
    monkeypatch.setattr(server, "_all", lambda *args, **kwargs: [SimpleNamespace(id="r1", status="NEW")])
    with pytest.raises(ValueError, match="NEW revision"):
        server.create_lead_generation_revision("listing", "Name", "Headline", "Summary", "FREE", ["DATABASE"])
    publisher.create_listing_revision.assert_not_called()


def test_create_revision_ignores_deleted_new_draft(monkeypatch, clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", compartment_id="publisher-compartment")
    )
    publisher.create_listing_revision.return_value = SimpleNamespace(data={"id": "r2"})
    monkeypatch.setattr(
        server, "_all", lambda *args, **kwargs: [SimpleNamespace(id="r1", status="NEW", lifecycle_state="DELETED")]
    )
    assert server.create_lead_generation_revision(
        "listing", "Name", "Headline", "Summary", "FREE", ["DATABASE"]
    )["id"] == "r2"


def test_update_requires_change():
    with pytest.raises(ValueError, match="at least one"):
        server.update_lead_generation_revision("revision")


def test_update_accepts_support_and_listing_metadata(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="NEW", lifecycle_state="ACTIVE")
    )
    publisher.update_listing_revision.return_value = SimpleNamespace(data={"id": "r1"})
    server.update_lead_generation_revision(
        "r1",
        options={
            "long_description": "Detailed value",
            "support_links": [{"name": "Help", "url": "https://example.com/help"}],
            "pricing_type": "FREE",
        },
    )
    details = publisher.update_listing_revision.call_args.args[1]
    assert details.long_description == "Detailed value"
    assert details.support_links[0].url == "https://example.com/help"


def test_update_rejects_controlled_field(clients):
    with pytest.raises(ValueError, match="Unsupported revision field"):
        server.update_lead_generation_revision("r1", options={"listing_type": "SERVICE"})
    clients[0].update_listing_revision.assert_not_called()


@pytest.mark.parametrize("status", ["NEW", "REJECTED"])
def test_update_editable_revision(clients, status):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status=status, lifecycle_state="ACTIVE")
    )
    publisher.update_listing_revision.return_value = SimpleNamespace(data=SimpleNamespace(id="revision"))
    server.update_lead_generation_revision("revision", headline="New")
    details = publisher.update_listing_revision.call_args.args[1]
    assert details.headline == "New"


@pytest.mark.parametrize("listing_type,status", [("SERVICE", "NEW"), ("LEAD_GENERATION", "PENDING_REVIEW")])
def test_update_rejects_noneditable_revision(clients, listing_type, status):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type=listing_type, status=status)
    )
    with pytest.raises(ValueError, match="editable"):
        server.update_lead_generation_revision("revision", headline="New")
    publisher.update_listing_revision.assert_not_called()


def test_update_lead_generation_rejects_deleted_draft(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="NEW", lifecycle_state="DELETED")
    )
    publisher.update_listing_revision.return_value = SimpleNamespace(data={"id": "r1"})
    with pytest.raises(ValueError, match="ACTIVE"):
        server.update_lead_generation_revision("r1", headline="Revised")
    publisher.update_listing_revision.assert_not_called()


def test_submit_requires_confirmation(clients):
    with pytest.raises(ValueError, match="confirmation"):
        server.submit_lead_generation_revision("revision", False)
    clients[0].submit_listing_revision_for_review.assert_not_called()


def test_submit_disables_auto_publish(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="NEW")
    )
    publisher.submit_listing_revision_for_review.return_value = SimpleNamespace(
        data=SimpleNamespace(id="revision")
    )
    server.submit_lead_generation_revision("revision", True, "Review")
    details = publisher.submit_listing_revision_for_review.call_args.args[0]
    assert details.should_auto_publish_on_approval is False


def test_submit_rejects_pending_revision(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="PENDING_REVIEW")
    )
    with pytest.raises(ValueError, match="NEW or REJECTED"):
        server.submit_lead_generation_revision("revision", True)


def test_publish_requires_confirmation(clients):
    with pytest.raises(ValueError, match="confirmation"):
        server.publish_lead_generation_revision("revision", False)
    clients[0].publish_listing_revision.assert_not_called()


def test_publish_requires_approved_revision(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="PENDING_REVIEW")
    )
    with pytest.raises(ValueError, match="APPROVED"):
        server.publish_lead_generation_revision("revision", True)
    publisher.publish_listing_revision.assert_not_called()


def test_publish_approved_revision(clients):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status="APPROVED")
    )
    publisher.publish_listing_revision.return_value = SimpleNamespace(data=None)
    assert server.publish_lead_generation_revision("revision", True) == {
        "listing_revision_id": "revision",
        "publication_requested": True,
    }


@pytest.mark.parametrize(
    "auth_type",
    ["api_key", "security_token", "instance_principal", "resource_principal", "identity_domain_upst"],
)
def test_clients_use_common_auth_and_derived_user_agent(monkeypatch, auth_type):
    signer = object() if auth_type != "api_key" else None
    monkeypatch.setattr(
        server,
        "build_auth_context",
        lambda: SimpleNamespace(config={"region": "us-ashburn-1"}, signer=signer, auth_type=auth_type),
    )
    publisher, identity = Mock(), Mock()
    monkeypatch.setattr(server.oci.marketplace_publisher, "MarketplacePublisherClient", publisher)
    monkeypatch.setattr(server.oci.identity, "IdentityClient", identity)
    server._clients()
    for cls in (publisher, identity):
        config = cls.call_args.args[0]
        assert config["additional_user_agent"] == "oci-marketplace-publisher-mcp/0.1.0"
        assert cls.call_args.kwargs == ({"signer": signer} if signer else {})
