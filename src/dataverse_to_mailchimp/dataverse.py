from __future__ import annotations
import logging, os, time, random
from datetime import datetime, timezone
from typing import Iterator, Dict, Any, Optional
import msal, requests

log = logging.getLogger(__name__)


class DataverseClient:
    """Thin Dataverse Web‑API wrapper with retry/back‑off."""

    def __init__(
        self,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        resource_url: str | None = None,
        max_retries: int = 5,
        backoff_base: float = 1.5,
    ) -> None:
        self.tenant_id = tenant_id or os.getenv("DATAVERSE_TENANT_ID")
        self.client_id = client_id or os.getenv("DATAVERSE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("DATAVERSE_CLIENT_SECRET")
        resource = resource_url or os.getenv("DATAVERSE_RESOURCE")
        if not all([self.tenant_id, self.client_id, self.client_secret, resource]):
            raise ValueError("Missing Dataverse OAuth environment variables")
        self.resource_url = resource.rstrip("/")
        self._session = requests.Session()
        self._token_cache: msal.TokenCache | None = None
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    # ── internal helpers ──
    def _acquire_token(self) -> str:
        if self._token_cache is None:
            self._token_cache = msal.TokenCache()
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
            token_cache=self._token_cache,
        )
        result = app.acquire_token_silent(
            [f"{self.resource_url}/.default"], account=None
        )
        if not result:
            result = app.acquire_token_for_client(
                scopes=[f"{self.resource_url}/.default"]
            )
        if "access_token" not in result:
            raise RuntimeError(result.get("error_description", "OAuth token error"))
        return result["access_token"]

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._acquire_token()}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _get_json(
        self, url: str, *, params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        for attempt in range(self.max_retries):
            r = self._session.get(
                url, headers=self._headers(), params=params, timeout=30
            )
            if r.status_code in (429, 503):
                wait = int(r.headers.get("Retry-After", self.backoff_base * 2**attempt))
                jitter = random.uniform(0, 0.3 * wait)
                log.warning(
                    "Dataverse throttled (%s). Sleeping %.1fs…",
                    r.status_code,
                    wait + jitter,
                )
                time.sleep(wait + jitter)
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError("Exceeded Dataverse retry budget")

    # ── public iterator ──
    def modified_contacts(
        self, since: datetime, *, limit: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        top = 5000
        url = f"{self.resource_url}/api/data/v9.2/contacts"
        filter_since = since.astimezone(timezone.utc).isoformat()
        params = {
            "$select": "contactid,firstname,lastname,emailaddress1,modifiedon",
            "$filter": f"modifiedon gt {filter_since}",
            "$top": str(min(top, limit) if limit else top),
        }
        remaining = limit
        while url:
            payload = self._get_json(url, params=params)
            for row in payload.get("value", []):
                yield row
                if remaining is not None:
                    remaining -= 1
                    if remaining <= 0:
                        return
            url = payload.get("@odata.nextLink")
            params = None  # next pages already encoded
