Release Notes
=============

v0.1.0
------

First release of ``pynamodb-async``: a native asyncio API for PynamoDB, built on aiobotocore.
Requires Python 3.10+, official ``pynamodb>=6.1,<6.2`` and ``aiobotocore>=2.13.0``.

* ``pynamodb_async.models.Model`` with awaitable ``get``, ``save``, ``update``, ``delete``,
  ``refresh``, ``count`` and table operations; ``query``, ``scan`` and ``batch_get`` return
  async iterators; ``batch_write()`` is an async context manager.
* Async transactions: ``pynamodb_async.transactions.TransactGet`` / ``TransactWrite``.
* Close clients with ``await Model.close()`` or ``async with pynamodb_async.connections():``.
  Models with the same settings on the same event loop share one client.

Known limitations:

* Use each model and connection from one event loop at a time.
* No built-in concurrency yet (for example parallel scan); gather independent operations
  yourself.
