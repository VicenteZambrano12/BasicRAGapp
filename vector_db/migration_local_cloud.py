from qdrant_client import QdrantClient

local = QdrantClient(host="localhost", port=6333)
remote = QdrantClient(host="10.x.x.x", port=6333)  # Your VM internal IP

for c in local.get_collections().collections:
    cname = c.name
    print(f"Migrating collection: {cname}")
    info = local.get_collection(cname)
    remote.recreate_collection(
        collection_name=cname,
        vectors_config=info.config.params.vectors
    )
    offset = None
    while True:
        points, offset = local.scroll(cname, limit=1000, offset=offset, with_payload=True, with_vectors=True)
        if not points:
            break
        remote.upsert(cname, points=points)
