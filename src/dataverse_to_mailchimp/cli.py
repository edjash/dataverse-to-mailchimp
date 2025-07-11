import argparse, logging, os, sys
from datetime import datetime, timezone, timedelta

from .sync import SyncEngine


def main(argv: list[str] | None = None):
    argv = argv or sys.argv[1:]
    p = argparse.ArgumentParser(description="Sync Dataverse contacts to Mailchimp.")

    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--since", type=str, help="ISO datetime; default 1h ago UTC")
    grp.add_argument("--full-sync", action="store_true", help="Sync ALL contacts")

    p.add_argument("--limit", type=int, help="Process at most N contacts")
    p.add_argument("--dry-run", action="store_true", help="Skip writes")
    p.add_argument("--allow-partial", action="store_true", help="Continue after first error")
    p.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))

    args = p.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    if args.full_sync:
        since = datetime(1970, 1, 1, tzinfo=timezone.utc)
    elif args.since:
        since = datetime.fromisoformat(args.since).astimezone(timezone.utc)
    else:
        since = datetime.now(timezone.utc) - timedelta(hours=1)

    log = logging.getLogger(__name__)
    log.info("sync_started: since=%s full_sync=%s limit=%s dry_run=%s", since.isoformat(), args.full_sync, args.limit, args.dry_run)

    engine = SyncEngine(since=since, allow_partial=args.allow_partial, dry_run=args.dry_run, limit=args.limit)
    engine.run()
    log.info("sync_finished")