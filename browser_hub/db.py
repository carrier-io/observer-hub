import shelve

DB_NAME = 'observer.db'


def save_to_storage(key, value):
    db = shelve.open(DB_NAME, writeback=True)
    try:
        db[key] = value
    finally:
        db.close()


def get_from_storage(key):
    db = shelve.open(DB_NAME, flag='r')
    try:
        existing = db[key]
    except Exception as e:
        return None
    finally:
        db.close()
    return existing
