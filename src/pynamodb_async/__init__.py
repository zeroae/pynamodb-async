# AUTO-GENERATED from pynamodb/asyncio/__init__.py by scripts/make_addon.py - DO NOT EDIT
"""
Async API for PynamoDB, built on aiobotocore.

Install with ``pip install pynamodb-async`` (Python 3.10+). Usage mirrors the
sync API: ``from pynamodb_async.models import Model``.
"""
import sys

if sys.version_info < (3, 10):  # pragma: no cover
    raise ImportError("pynamodb_async requires Python 3.10+; install pynamodb-async")
try:
    import aiobotocore  # noqa: F401
except ImportError as e:
    raise ImportError(
        "pynamodb_async requires aiobotocore; install pynamodb-async (Python 3.10+)"
    ) from e

from pynamodb_async.connection.base import connections  # noqa: E402

__all__ = ['connections']
