import hashlib, requests, time, threading, os, logging
from typing import Dict, Any

log = logging.getLogger(__name__)


class RateLimiter:
    """Token‑bucket limiter (10 req/s default)."""

    def __init__(self, rate: int = 10):
        self.capacity = rate
        self.tokens = rate
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.monotonic()
            delta = now - self.updated
            self.updated = now
            self.tokens = min(self.capacity, self.tokens + delta * self.capacity)
            if self.tokens < 1:
                sleep = (1 - self.tokens) / self.capacity
                time.sleep(sleep)
                self.updated = time.monotonic()
                self.tokens = 0
            else:
                self.tokens -= 1


class MailchimpClient:
    """Mailchimp API client for adding contacts to an audience."""
    def __init__(
        self,
        *,
        api_key: str | None = None,
        audience_id: str | None = None,
        dry_run: bool = False,
    ):
        key = api_key or os.getenv("MAILCHIMP_API_KEY")
        if not key or "-" not in key:
            raise ValueError("MAILCHIMP_API_KEY missing or malformed")
        self.api_key = key
        self.dc = key.split("-")[-1]
        self.audience_id = audience_id or os.getenv("MAILCHIMP_AUDIENCE_ID")
        if not self.audience_id:
            raise ValueError("MAILCHIMP_AUDIENCE_ID not set")
        self.base = f"https://{self.dc}.api.mailchimp.com/3.0"
        self.session = requests.Session()
        self.session.auth = ("anystring", self.api_key)
        self.rl = RateLimiter(rate=int(os.getenv("MC_RATE_LIMIT", "10")))
        self.dry_run = dry_run
        self._ping()

    def _ping(self):
        r = self.session.get(f"{self.base}/ping", timeout=10)
        if r.status_code != 200:
            raise ValueError(f"Mailchimp credentials invalid: {r.status_code} {r.text}")

    @staticmethod
    def _subscriber_hash(email: str) -> str:
        return hashlib.md5(email.lower().encode()).hexdigest()

    def upsert_contact(self, contact: Dict[str, Any]):
        email = contact["email_address"]
        self.rl.wait()
        if self.dry_run:
            log.info("[DRY‑RUN] Would upsert → %s", email)
            return
        url = f"{self.base}/lists/{self.audience_id}/members/{self._subscriber_hash(email)}"
        r = self.session.put(url, json=contact, timeout=30)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Mailchimp upsert failed: {r.status_code} {r.text}")
