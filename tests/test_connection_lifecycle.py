# AUTO-GENERATED from tests/asyncio/test_connection_lifecycle.py by scripts/make_addon.py - DO NOT EDIT
import asyncio

import pytest

from pynamodb_async.connection import Connection


async def test_client_property_raises_until_opened():
    conn = Connection(region='us-east-1')
    with pytest.raises(RuntimeError, match='get_client'):
        conn.client
    client = await conn.get_client()
    assert conn.client is client
    await conn.close()


async def test_get_client_is_cached_and_close_resets():
    conn = Connection(region='us-east-1')
    c1 = await conn.get_client()
    assert await conn.get_client() is c1
    await conn.close()
    assert conn._client is None
    c2 = await conn.get_client()
    assert c2 is not c1
    await conn.close()


async def test_close_without_open_is_noop():
    await Connection(region='us-east-1').close()


async def test_new_event_loop_gets_new_client():
    conn = Connection(region='us-east-1')

    async def open_and_close():
        client = await conn.get_client()
        await conn.close()  # on the loop that opened the client
        return client

    # asyncio.run() in a worker thread: on the test's own thread it would unset (and leak)
    # the event loop pytest-asyncio provides.
    c1 = await asyncio.to_thread(asyncio.run, open_and_close())
    c2 = await asyncio.to_thread(asyncio.run, open_and_close())
    assert c1 is not c2


async def test_repr_does_not_raise_before_open():
    conn = Connection(region='us-east-1')
    assert 'us-east-1' in repr(conn)
    await conn.get_client()
    assert 'dynamodb.us-east-1.amazonaws.com' in repr(conn)
    await conn.close()


async def test_table_connection_close_releases_client():
    from pynamodb_async import _compat
    from pynamodb_async.connection import TableConnection

    table = TableConnection('mock', region='us-east-1')
    client = await table.connection.get_client()
    await table.close()

    assert table.connection._client is None
    entries = _compat._clients.get(asyncio.get_running_loop(), {}).values()
    assert all(entry.client is not client for entry in entries)


async def test_open_connections_tracks_opened_clients():
    from pynamodb_async.connection.base import _open_connections

    conn = Connection(region='us-east-1')
    assert conn not in _open_connections
    await conn.get_client()
    assert conn in _open_connections
    await conn.close()
    assert conn not in _open_connections
