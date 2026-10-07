"""Copyright (c) 2026, Seyma Guleryuz.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from oracle.oci_marketplace_publisher_mcp_server import server


def test_publisher_readiness_reports_publisher_and_region(monkeypatch):
    publisher = Mock()
    publisher.list_publishers.return_value = SimpleNamespace(
        data=[SimpleNamespace(id="pub1", publisher_status="ACTIVE")]
    )
    identity = Mock()
    monkeypatch.setattr(server, "_clients", lambda: (publisher, identity), raising=False)
    monkeypatch.setattr(
        server,
        "_all",
        lambda method, *args: (
            [SimpleNamespace(id="pub1", publisher_status="ACTIVE")]
            if method == publisher.list_publishers
            else [SimpleNamespace(region_name="us-ashburn-1")]
        ),
    )

    result = server.publisher_readiness("compartment", "tenancy")

    assert result == {"publishers": [{"id": "pub1", "status": "ACTIVE"}], "ashburn_subscribed": True}


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


def test_create_revision_uses_lead_generation_model(clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="LEAD_GENERATION"))
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


def test_create_revision_rejects_other_listing_type(clients):
    publisher, _ = clients
    publisher.get_listing.return_value = SimpleNamespace(data=SimpleNamespace(listing_type="SERVICE"))
    with pytest.raises(ValueError, match="LEAD_GENERATION"):
        server.create_lead_generation_revision("listing", "Name", "Headline", "Summary", "FREE", ["DATABASE"])
    publisher.create_listing_revision.assert_not_called()


def test_update_requires_change():
    with pytest.raises(ValueError, match="at least one"):
        server.update_lead_generation_revision("revision")


@pytest.mark.parametrize("status", ["NEW", "REJECTED"])
def test_update_editable_revision(clients, status):
    publisher, _ = clients
    publisher.get_listing_revision.return_value = SimpleNamespace(
        data=SimpleNamespace(listing_type="LEAD_GENERATION", status=status)
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
