"""Package bootstrap: exposes __version__ and loads a local .env if present."""

from importlib import metadata as _metadata

try:  # Prefer the version recorded in the installed dist‑info
    __version__: str = _metadata.version(__name__)
except _metadata.PackageNotFoundError:  # pragma: no cover – editable/dev mode
    __version__ = "0.0.0+dev"

# --- optional: load variables from a local .env in dev environments ---------
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()  # Will no‑op if file is missing.
except ImportError:  # pragma: no cover
    pass
