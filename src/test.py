import redis, pickle
r = redis.Redis(host="localhost", port=6379, db=0)
r.set("testkey", pickle.dumps({"x": 1}), ex=30)
print(pickle.loads(r.get("testkey")))
