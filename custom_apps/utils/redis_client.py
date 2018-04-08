import random

from redis import StrictRedis, BlockingConnectionPool

url = random.choice('redis://admin:ALBHRYUGMHCLOEDK@gcp-us-east1-cpu.7.dblayer.com:18564;redis://admin:ALBHRYUGMHCLOEDK@gcp-us-east1-cpu.5.dblayer.com:18564'.split(';'))
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


def get_key(name):
    conn = get_conn()
    return conn.get(name)
