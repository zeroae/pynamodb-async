# AUTO-GENERATED from tests/asyncio/test_transaction.py by scripts/make_addon.py - DO NOT EDIT
import pytest
from pynamodb.attributes import NumberAttribute, UnicodeAttribute, VersionAttribute

from pynamodb_async.connection import Connection
from pynamodb_async.connection.base import MetaTable
from pynamodb.constants import TABLE_KEY
from pynamodb_async.transactions import Transaction, TransactGet, TransactWrite
from pynamodb_async.models import Model
from tests.test_base_connection import PATCH_METHOD

from unittest.mock import patch


class MockModel(Model):
    class Meta:
        table_name = 'mock'

    mock_hash = NumberAttribute(hash_key=True)
    mock_range = NumberAttribute(range_key=True)
    mock_toot = UnicodeAttribute(null=True)
    mock_version = VersionAttribute()


MOCK_TABLE_DESCRIPTOR = {
    "Table": {
        "TableName": "mock",
        "KeySchema": [
            {
                "AttributeName": "mock_hash",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "mock_range",
                "KeyType": "RANGE"
            }
        ],
        "AttributeDefinitions": [
            {
                "AttributeName": "mock_hash",
                "AttributeType": "N"
            },
            {
                "AttributeName": "mock_range",
                "AttributeType": "N"
            }
        ]
    }
}


class TestTransaction:

    async def test_commit__not_implemented(self):
        t = Transaction(connection=Connection())
        with pytest.raises(NotImplementedError):
            await t._commit()


class TestTransactGet:

    async def test_commit(self, mocker):
        connection = Connection()
        connection.add_meta_table(MetaTable(MOCK_TABLE_DESCRIPTOR[TABLE_KEY]))

        mock_connection_transact_get = mocker.patch.object(connection, 'transact_get_items')

        async with TransactGet(connection=connection) as t:
            t.get(MockModel, 1, 2)

        mock_connection_transact_get.assert_awaited_once_with(
            get_items=[{'Key': {'mock_hash': {'N': '1'}, 'mock_range': {'N': '2'}}, 'TableName': 'mock'}],
            return_consumed_capacity=None
        )

    async def test_no_commit_when_block_raises(self, mocker):
        connection = Connection()
        connection.add_meta_table(MetaTable(MOCK_TABLE_DESCRIPTOR[TABLE_KEY]))
        mock_connection_transact_get = mocker.patch.object(connection, 'transact_get_items')

        with pytest.raises(ValueError):
            async with TransactGet(connection=connection) as t:
                t.get(MockModel, 1, 2)
                raise ValueError('abandon the transaction')

        mock_connection_transact_get.assert_not_called()


class TestTransactWrite:

    async def test_no_commit_when_block_raises(self, mocker):
        connection = Connection()
        mock_connection_transact_write = mocker.patch.object(connection, 'transact_write_items')

        with pytest.raises(ValueError):
            async with TransactWrite(connection=connection) as t:
                t.save(MockModel(3, 5))
                raise ValueError('abandon the transaction')

        mock_connection_transact_write.assert_not_called()

    async def test_condition_check__no_condition(self):
        with pytest.raises(TypeError):
            async with TransactWrite(connection=Connection()) as transaction:
                transaction.condition_check(MockModel, hash_key=1, condition=None)

    async def test_commit(self, mocker):
        connection = Connection()
        mock_connection_transact_write = mocker.patch.object(connection, 'transact_write_items')
        async with TransactWrite(connection=connection) as t:
            t.condition_check(MockModel, 1, 3, condition=(MockModel.mock_hash.does_not_exist()))
            t.delete(MockModel(2, 4))
            t.save(MockModel(3, 5))
            t.update(MockModel(4, 6), actions=[MockModel.mock_toot.set('hello')], return_values='ALL_OLD')

        expected_condition_checks = [{
            'ConditionExpression': 'attribute_not_exists (#0)',
            'ExpressionAttributeNames': {'#0': 'mock_hash'},
            'Key': {'mock_hash': {'N': '1'}, 'mock_range': {'N': '3'}},
            'TableName': 'mock'}
        ]
        expected_deletes = [{
            'ConditionExpression': 'attribute_not_exists (#0)',
            'ExpressionAttributeNames': {'#0': 'mock_version'},
            'Key': {'mock_hash': {'N': '2'}, 'mock_range': {'N': '4'}},
            'TableName': 'mock'
        }]
        expected_puts = [{
            'ConditionExpression': 'attribute_not_exists (#0)',
            'ExpressionAttributeNames': {'#0': 'mock_version'},
            'Item': {'mock_hash': {'N': '3'}, 'mock_range': {'N': '5'}, 'mock_version': {'N': '1'}},
            'TableName': 'mock'
        }]
        expected_updates = [{
            'ConditionExpression': 'attribute_not_exists (#0)',
            'TableName': 'mock',
            'Key': {'mock_hash': {'N': '4'}, 'mock_range': {'N': '6'}},
            'ReturnValuesOnConditionCheckFailure': 'ALL_OLD',
            'UpdateExpression': 'SET #1 = :0, #0 = if_not_exists (#0, :1) + :2',
            'ExpressionAttributeNames': {'#0': 'mock_version', '#1': 'mock_toot'},
            'ExpressionAttributeValues': {':0': {'S': 'hello'}, ':1': {'N': '0'}, ':2': {'N': '1'}}
        }]
        mock_connection_transact_write.assert_awaited_once_with(
            condition_check_items=expected_condition_checks,
            delete_items=expected_deletes,
            put_items=expected_puts,
            update_items=expected_updates,
            client_request_token=None,
            return_consumed_capacity=None,
            return_item_collection_metrics=None
        )

    async def test_update__blind_version_uses_if_not_exists(self, mocker):
        # Version not loaded: increment the stored version instead of resetting it to 1
        # (Saturn-Technologies/async-pynamodb 5903f16; pynamodb/pynamodb#1247).
        connection = Connection()
        mock_connection_transact_write = mocker.patch.object(connection, 'transact_write_items')
        async with TransactWrite(connection=connection) as t:
            t.update(MockModel(4, 6), actions=[MockModel.mock_toot.set('hello')])

        update_items = mock_connection_transact_write.call_args[1]['update_items']
        assert update_items == [{
            'ConditionExpression': 'attribute_not_exists (#0)',
            'TableName': 'mock',
            'Key': {'mock_hash': {'N': '4'}, 'mock_range': {'N': '6'}},
            'UpdateExpression': 'SET #1 = :0, #0 = if_not_exists (#0, :1) + :2',
            'ExpressionAttributeNames': {'#0': 'mock_version', '#1': 'mock_toot'},
            'ExpressionAttributeValues': {':0': {'S': 'hello'}, ':1': {'N': '0'}, ':2': {'N': '1'}},
        }]

    async def test_update__loaded_version_is_unchanged(self, mocker):
        connection = Connection()
        mock_connection_transact_write = mocker.patch.object(connection, 'transact_write_items')
        async with TransactWrite(connection=connection) as t:
            t.update(MockModel(4, 6, mock_version=2), actions=[MockModel.mock_toot.set('hello')])

        update_items = mock_connection_transact_write.call_args[1]['update_items']
        assert update_items[0]['UpdateExpression'] == 'SET #1 = :1 ADD #0 :2'

    async def test_update__caller_version_action_replaces_automatic_one(self, mocker):
        connection = Connection()
        mock_connection_transact_write = mocker.patch.object(connection, 'transact_write_items')
        async with TransactWrite(connection=connection) as t:
            t.update(MockModel(4, 6), actions=[MockModel.mock_version.set(9)])

        update_items = mock_connection_transact_write.call_args[1]['update_items']
        assert update_items[0]['UpdateExpression'] == 'SET #0 = :0'
        assert update_items[0]['ConditionExpression'] == 'attribute_not_exists (#0)'
        assert update_items[0]['ExpressionAttributeValues'] == {':0': {'N': '9'}}

    async def test_update__local_version_is_unknown_after_blind_update(self, mocker):
        # The stored version was incremented by an unknown amount: do not guess it locally.
        connection = Connection()
        mocker.patch.object(connection, 'transact_write_items')
        model = MockModel(4, 6)
        async with TransactWrite(connection=connection) as t:
            t.update(model, actions=[MockModel.mock_toot.set('hello')], add_version_condition=False)
        assert model.mock_version is None

    async def test_update__local_version_is_unknown_after_caller_version_action(self, mocker):
        connection = Connection()
        mocker.patch.object(connection, 'transact_write_items')
        for loaded in ({}, {'mock_version': 3}):
            model = MockModel(4, 6, **loaded)
            async with TransactWrite(connection=connection) as t:
                t.update(model, actions=[MockModel.mock_version.set(9)])
            assert model.mock_version is None

    async def test_update__local_version_is_incremented_when_loaded(self, mocker):
        connection = Connection()
        mocker.patch.object(connection, 'transact_write_items')
        model = MockModel(4, 6, mock_version=3)
        async with TransactWrite(connection=connection) as t:
            t.update(model, actions=[MockModel.mock_toot.set('hello')])
        assert model.mock_version == 4
