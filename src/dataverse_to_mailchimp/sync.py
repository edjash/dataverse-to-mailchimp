import logging
from datetime import datetime
from typing import Optional, Dict, Any

from .dataverse import DataverseClient
from .mailchimp import MailchimpClient

log = logging.getLogger(__name__)


class SyncEngine:
    def __init__(
        self,
        *,
        since: datetime,
        allow_partial: bool = False,
        dry_run: bool = False,
        limit: Optional[int] = None
    ):
        self.since = since
        self.allow_partial = allow_partial
        self.dry_run = dry_run
        self.limit = limit
        self.dv = DataverseClient()
        self.mc = MailchimpClient(dry_run=dry_run)

    def _map_contact(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "email_address": row.get("emailaddress1"),
            "status_if_new": "subscribed",
            "merge_fields": {
                "FNAME": row.get("firstname", ""),
                "LNAME": row.get("lastname", ""),
            },
        }

    def run(self):
        processed = success = failed = 0
        for row in self.dv.modified_contacts(self.since, limit=self.limit):
            processed += 1
            try:
                self.mc.upsert_contact(self._map_contact(row))
                success += 1
            except Exception as exc:
                failed += 1
                log.error(
                    "Upsert error for contact %s: %s", row.get("emailaddress1"), exc
                )
                if not self.allow_partial:
                    raise SystemExit(1) from exc
        log.info(
            "sync_summary: processed=%d success=%d failed=%d",
            processed,
            success,
            failed,
        )
