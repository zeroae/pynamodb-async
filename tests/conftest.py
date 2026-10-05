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
    else:
        import asyncio

        # pytest-asyncio looks up the current loop before each async test and restores it
        # afterwards. With no loop set, asyncio creates a default one that nothing closes (and
        # unittest.IsolatedAsyncioTestCase later unsets it), which then fails the
        # `-W error::ResourceWarning` run. Start with no current loop instead.
        asyncio.set_event_loop(None)
