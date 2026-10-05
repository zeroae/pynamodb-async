# AUTO-GENERATED from tests/asyncio/test_client_cache.py by scripts/make_addon.py - DO NOT EDIT
import asyncio
import gc
import json
import weakref
from unittest.mock import patch

import pytest

from aiobotocore.awsrequest import AioAWSResponse

import pynamodb_async
from pynamodb_async import _compat
from pynamodb_async.connection import Connection

from .test_base_connection import _FakeRaw


async def test_same_settings_share_one_client():
    a, b = Connection(region='us-east-1'), Connection(region='us-east-1')
    assert await a.get_client() is await b.get_client()
    await a.close()
    await b.close()


async def test_different_extra_headers_do_not_share():
    a = Connection(region='us-east-1', extra_headers={'x': '1'})
    b = Connection(region='us-east-1', extra_headers={'x': '2'})
    assert await a.get_client() is not await b.get_client()
    await a.close()
    await b.close()


async def test_closing_one_holder_keeps_client_open_for_others():
    a, b = Connection(region='us-east-1'), Connection(region='us-east-1')
    client = await a.get_client()
    await b.get_client()
    with patch.object(type(client), '__aexit__', wraps=client.__aexit__) as aexit:
        await a.close()
        aexit.assert_not_called()
        assert await b.get_client() is client
        await b.close()
        aexit.assert_called_once()


async def test_poisoned_shared_client_is_replaced():
    a, b = Connection(region='us-east-1'), Connection(region='us-east-1')
    old = await a.get_client()
    await b.get_client()
    old._request_signer._credentials = None  # simulate empty cached credentials
    new = await a.get_client()
    assert new is not old
    assert await b.get_client() is new  # b notices too and moves over
    await a.close()
    await b.close()


async def test_separate_event_loops_get_separate_clients():
    conn = Connection(region='us-east-1')
    async def use_and_close():
        client = await conn.get_client()
        await conn.close()
        return client

    # asyncio.run() in worker threads: on the test's own thread it would unset (and leak)
    # the event loop pytest-asyncio provides.
    first = await asyncio.to_thread(asyncio.run, use_and_close())
    second = await asyncio.to_thread(asyncio.run, use_and_close())
    assert first is not second


async def test_connections_context_closes_everything():
    async with pynamodb_async.connections():
        a, b = Connection(region='us-east-1'), Connection(region='eu-west-1')
        await a.get_client()
        await b.get_client()
    assert a._client is None and b._client is None
    assert not _compat._clients.get(asyncio.get_running_loop())


def _ok_response():
    response = AioAWSResponse(url='', status_code=200, headers={}, raw=_FakeRaw())
    response._content = json.dumps({'TableNames': []}).encode('utf-8')
    return response


async def _send_with_real_session(self, request):
    # Open the real aiohttp session (as AIOHTTPSession.send does) so the client
    # ends up holding its loop, then answer without touching the network.
    await self._get_session(None)
    return _ok_response()


@pytest.mark.filterwarnings('ignore::ResourceWarning')
async def test_finished_loop_is_dropped_from_cache_without_close():
    loops = []

    async def use_without_close():
        loops.append(weakref.ref(asyncio.get_running_loop()))
        conn = Connection(region='us-east-1')
        await conn.list_tables()  # a real request: the aiohttp session now exists
        assert (await conn.get_client())._endpoint.http_session._sessions

    async def open_on_new_loop():
        conn = Connection(region='us-east-1')
        await conn.get_client()  # opening a client prunes closed loops
        await conn.close()

    with patch('aiobotocore.httpsession.AIOHTTPSession.send', _send_with_real_session):
        await asyncio.to_thread(asyncio.run, use_without_close())
    await asyncio.to_thread(asyncio.run, open_on_new_loop())
    gc.collect()
    assert loops[0]() is None
    assert not [per_loop for per_loop in _compat._clients.values() if per_loop]


async def test_concurrent_first_use_shares_one_client_and_closes_extras():
    from aiobotocore.session import ClientCreatorContext

    created = []
    exited = []
    orig_enter = ClientCreatorContext.__aenter__

    async def slow_enter(self):
        await asyncio.sleep(0)
        client = await orig_enter(self)
        created.append(client)
        cls = type(client)
        if not getattr(cls, '_counting', False):
            orig_exit = cls.__aexit__

            async def counting_exit(self_, *args):
                exited.append(self_)
                return await orig_exit(self_, *args)

            cls.__aexit__ = counting_exit
            cls._counting = True
            cls._orig_exit = orig_exit
        return client

    a, b, c = (Connection(region='us-east-1') for _ in range(3))
    try:
        with patch.object(ClientCreatorContext, '__aenter__', slow_enter):
            got = await asyncio.gather(a.get_client(), a.get_client(), b.get_client(), c.get_client())
        shared = got[0]
        assert all(g is shared for g in got)
        assert len(created) > 1  # extras really were created concurrently
        # every extra client was closed right away; the shared one is still open
        assert sorted(map(id, exited)) == sorted(id(x) for x in created if x is not shared)
        for conn in (a, b):
            await conn.close()
        assert shared not in exited
        await c.close()
        assert exited.count(shared) == 1
        assert not _compat._clients.get(asyncio.get_running_loop())
    finally:
        for conn in (a, b, c):
            await conn.close()
        cls = type(created[0]) if created else None
        if cls is not None and getattr(cls, '_counting', False):
            cls.__aexit__ = cls._orig_exit
            del cls._counting, cls._orig_exit


async def test_last_holder_closing_while_extra_client_closes_keeps_shared_open():
    from aiobotocore.client import AioBaseClient
    from aiobotocore.session import ClientCreatorContext

    orig_enter = ClientCreatorContext.__aenter__
    orig_exit = AioBaseClient.__aexit__
    a_creating, b_opened = asyncio.Event(), asyncio.Event()
    extra_closing, b_closed = asyncio.Event(), asyncio.Event()
    extra, exited = [], []

    async def enter(self):
        if not extra and not a_creating.is_set():
            # a's client: finish only after b has opened and cached its own.
            a_creating.set()
            await b_opened.wait()
            client = await orig_enter(self)
            extra.append(client)
            return client
        return await orig_enter(self)

    async def gated_exit(self, *args):
        if extra and self is extra[0]:
            extra_closing.set()
            await b_closed.wait()  # b, the last other holder, closes meanwhile
        exited.append(self)
        return await orig_exit(self, *args)

    a, b = Connection(region='us-east-1'), Connection(region='us-east-1')
    with patch.object(ClientCreatorContext, '__aenter__', enter), \
            patch.object(AioBaseClient, '__aexit__', gated_exit):
        task = asyncio.ensure_future(a.get_client())
        await a_creating.wait()
        shared = await b.get_client()
        b_opened.set()
        await extra_closing.wait()
        await b.close()
        b_closed.set()
        got = await task
        try:
            assert got is shared
            assert extra[0] in exited and shared not in exited  # shared client still open
            cached = _compat._clients[asyncio.get_running_loop()][a._client_key()]
            assert cached.client is shared and cached is a._client_entry and cached.refs == 1
            assert await a.get_client() is shared
        finally:
            await a.close()
        assert shared in exited


async def test_connections_leaves_other_loops_connections_alone():
    import threading

    from pynamodb_async.connection.base import _open_connections

    opened, finish = threading.Event(), threading.Event()
    other = Connection(region='us-east-1')
    outcome = {}

    def run_other_loop():
        async def worker():
            await other.get_client()
            opened.set()
            await asyncio.to_thread(finish.wait)
            outcome['client_still_open'] = other._client is not None
            await other.close()  # closed on its own loop

        asyncio.run(worker())

    thread = threading.Thread(target=run_other_loop)
    thread.start()
    try:
        await asyncio.to_thread(opened.wait)
        mine = Connection(region='eu-west-1')
        async with pynamodb_async.connections():
            await mine.get_client()
        assert mine._client is None  # this loop's connection was closed
        assert other._client is not None  # the other loop's one was not
        assert other in _open_connections
    finally:
        finish.set()
        thread.join()
    assert outcome == {'client_still_open': True}
    assert other not in _open_connections


async def test_open_connections_is_locked_while_connections_snapshots_and_mutates():
    from pynamodb_async.connection import base

    seen = []

    class RecordingSet(weakref.WeakSet):
        def __iter__(self):
            seen.append(('iter', base._open_connections_lock.locked()))
            return super().__iter__()

        def add(self, item):
            seen.append(('add', base._open_connections_lock.locked()))
            super().add(item)

        def discard(self, item):
            seen.append(('discard', base._open_connections_lock.locked()))
            super().discard(item)

    with patch.object(base, '_open_connections', RecordingSet()):
        async with pynamodb_async.connections():
            conn = Connection(region='us-east-1')
            await conn.get_client()
    assert conn._client is None
    assert {'add', 'iter', 'discard'} <= {op for op, _ in seen}
    assert all(locked for _, locked in seen)


async def test_connections_survives_concurrent_opens_and_closes_on_other_threads():
    import threading

    stop = threading.Event()
    errors = []

    def churn():
        async def work():
            while not stop.is_set():
                conn = Connection(region='us-east-1')
                await conn.get_client()
                await conn.close()

        try:
            asyncio.run(work())
        except BaseException as e:  # noqa: B036
            errors.append(e)

    threads = [threading.Thread(target=churn) for _ in range(3)]
    for t in threads:
        t.start()
    try:
        for _ in range(50):
            async with pynamodb_async.connections():
                await asyncio.sleep(0)
    finally:
        stop.set()
        for t in threads:
            t.join()
    assert errors == []
