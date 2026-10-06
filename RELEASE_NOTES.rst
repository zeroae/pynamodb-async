Release Notes
=============

v0.1.2
------

Fixes:

* Updating a model with a ``VersionAttribute`` without loading it first (``Model(id).update(...)``,
  or ``TransactWrite.update``) and ``add_version_condition=False`` no longer sets the stored version
  to 1, which rolled a stored version back (for example from 3 to 1). With the default version
  condition the old code failed the update instead. The update now sets the version to
  ``if_not_exists(version, 0) + 1``, so the stored version is incremented. The version condition and
  updates of a loaded model are unchanged. This fixes upstream PynamoDB issue #1247.
* ``update()`` no longer sends two actions on the version attribute when you pass your own action
  on it (DynamoDB rejected that with "Two document paths overlap"). Your action replaces the
  automatic increment; the version condition still applies.
* After ``TransactWrite.update`` commits, the local model's version is now ``None`` (unknown) when the
  version was not loaded or you supplied your own version action, instead of a guessed value; call
  ``refresh()`` to load it. A loaded version is still incremented locally as before.

The first two fixes come from Saturn-Technologies/async-pynamodb (MIT), commits 5903f16 and 94ef068.

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
