"""Pytest verifying 403 halt behaviour."""

from datetime import datetime, timezone
from unittest import mock
import pytest

from dataverse_to_mailchimp.sync import SyncEngine, DataverseClient, MailchimpClient


@pytest.fixture(autouse=True)
def patch_clients(monkeypatch):
    # Fake a single contact
    monkeypatch.setattr(
        DataverseClient,
        "modified_contacts",
        lambda self, since, limit=None: [
            {"emailaddress1": "x@example.com", "firstname": "X", "lastname": "Y"}
        ],
    )
    # Force upsert to raise
    monkeypatch.setattr(
        MailchimpClient,
        "upsert_contact",
        lambda self, payload: (_ for _ in ()).throw(RuntimeError("403")),
    )


def test_halt_on_error():
    with pytest.raises(SystemExit):
        SyncEngine(since=datetime.now(timezone.utc), allow_partial=False).run()


def test_continue_with_allow_partial():
    SyncEngine(since=datetime.now(timezone.utc), allow_partial=True).run()
