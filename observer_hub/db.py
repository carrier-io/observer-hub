import shelve

DB_NAME = 'tmp/observer.db'


def save_to_storage(key, value):
    db = shelve.open(DB_NAME, writeback=True)
    try:
        db[key] = value
    finally:
        db.close()


def get_from_storage(key):
    db = None
    try:
        db = shelve.open(DB_NAME, flag='r')
        existing = db[key]
    except Exception as e:
        return None
    finally:
        if db:
            db.close()
    return existing
