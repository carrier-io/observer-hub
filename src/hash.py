import hashlib

hash1 = hashlib.md5("whatever your string is".encode('utf-8')).hexdigest()
hash2 = hashlib.md5("w".encode('utf-8')).hexdigest()

l1 = len(hash1)
l2 = len(hash2)

assert l1 == l2
