import redis

def expireCache(redis_db,comps):

    for comp in comps:
        keys = redis_db.keys('*'+comp+'*')
        for k in keys:
            redis_db.delete(k)
