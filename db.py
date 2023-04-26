from pymongo import MongoClient
from functools import wraps
from config import config
from rich import print

client = None


def connect():
    client = MongoClient(config["mongodb"]["uri"])
    return client


client = connect()


def with_collection(db, collection):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global client
            if client is None:
                client = connect()

            _db = client[db]
            _collection = _db[collection]
            return func(_collection, *args, **kwargs)

        return wrapper

    return decorator


@with_collection("busserebatetraces", "tracings")
def find_with_pipeline(collection, pipeline):
    return list(collection.aggregate(pipeline))


if __name__ == "__main__":
    pipeline = [{"$match": {"gpo": "MAGNET"}}]
    print(find_with_pipeline(pipeline))
