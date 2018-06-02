import random

from redis import StrictRedis, BlockingConnectionPool

url = 'redis://h:pa40c5a1cd1d9e59256784d85851a608c523aa5a5fa9a2502f5b502fed6a6d660@ec2-54-88-234-13.compute-1.amazonaws.com:12539'
_conn = None


def get_conn():
    global _conn
    if not _conn:
        pool = BlockingConnectionPool.from_url(url)
        _conn = StrictRedis(connection_pool=pool)
    return _conn


def set_key(name, value, ttl=None):
    conn = get_conn()
    return conn.set(name, value, ex=ttl)


def del_key(name):
    conn = get_conn()
    return conn.delete(name)


def get_key(name):
    conn = get_conn()
    return conn.get(name)
