# pynamodb-async

A native asyncio API for [PynamoDB](https://github.com/pynamodb/PynamoDB), built on
[aiobotocore](https://github.com/aio-libs/aiobotocore). It runs next to official PynamoDB:
you keep using PynamoDB's attributes, indexes and expressions, and get awaitable models,
queries, batches and transactions.

```
pip install pynamodb-async
```

Needs Python 3.10+. This installs official `pynamodb` (6.1.x) and `aiobotocore`.

## Usage

Declare a model with `Model` from `pynamodb_async.models` and attributes from `pynamodb.attributes`:

```python
import pynamodb_async
from pynamodb.attributes import UnicodeAttribute
from pynamodb_async.models import Model


class User(Model):
    class Meta:
        table_name = "users"
        region = "us-east-1"

    email = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(null=True)


async def main():
    async with pynamodb_async.connections():
        await User("ada@example.com", name="Ada").save()
        user = await User.get("ada@example.com")
        async for u in User.query("ada@example.com"):
            print(u.name)
```

## Closing clients and event loops

Every async client holds an HTTP session. Close it when you are done with
`await User.close()`, or wrap your code in `async with pynamodb_async.connections():`, which
closes every connection opened inside the block. A client belongs to the event loop that
created it, so use each model and `Connection` from one event loop at a time, and prefer one
long-lived event loop for the whole program.

## Relationship to PynamoDB

This package works alongside official PynamoDB. Its code is generated from a private source
repository, a fork that also offers the same async API as a drop-in replacement for `pynamodb`.
This add-on has its own async `Connection.get_client()`. What it does not have are the fork's
sync additions: `pynamodb.models.Model.close()`, `pynamodb.connections()` and the sync
`pynamodb.connection.Connection.get_client()`. It also lacks upstream fixes merged after the
supported PynamoDB release (for example [#1302](https://github.com/pynamodb/PynamoDB/pull/1302))
until upstream ships them.

## Contributing

The code here is generated from a private source repository. Please open issues in this
repository; pull requests are ported over by hand.

## License

MIT, derived from PynamoDB. See `LICENSE`.
