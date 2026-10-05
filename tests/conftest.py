# AUTO-GENERATED from tests/asyncio/conftest.py by scripts/make_addon.py - DO NOT EDIT
import sys

collect_ignore_glob = []
if sys.version_info < (3, 10):
    collect_ignore_glob = ["*"]
else:
    try:
        import aiobotocore  # noqa: F401
    except ImportError:
        collect_ignore_glob = ["*"]
