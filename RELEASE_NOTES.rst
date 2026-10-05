Release Notes
=============

v0.1.1
------

Fixes:

* ``pynamodb_async.connections()`` no longer fails with "Set changed size during iteration" when
  another thread opens a connection while it closes connections; the set of open connections is
  now guarded by a lock.
* ``pynamodb_async.connections()`` now closes only the connections whose client belongs to the
  running event loop. Connections opened on another event loop or thread are left for that loop to
  close, instead of having their client dropped from under them.

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
