"""Persistent Qdrant local collections; no custom similarity backend."""
import uuid
from qdrant_client import QdrantClient, models
from .common import ROOT


def open_store():
    return QdrantClient(path=str(ROOT / '.local/qdrant'))


def point_id(chunk_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def ingest_collection(client, name, chunks, vectors):
    # This lab owns only these named collections. Rebuild removes stale chunks after a PDF change.
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(name, vectors_config=models.VectorParams(size=len(vectors[0]),distance=models.Distance.COSINE))
    points = [models.PointStruct(id=point_id(c['id']), vector=v.tolist(), payload=c) for c,v in zip(chunks,vectors,strict=True)]
    for start in range(0,len(points),64):
        client.upsert(name,points[start:start+64],wait=True)
    first = client.count(name,exact=True).count
    # Repeat identical upserts, measure actual persisted count rather than assuming idempotence.
    for start in range(0,len(points),64):
        client.upsert(name,points[start:start+64],wait=True)
    second = client.count(name,exact=True).count
    if first != len(chunks) or second != first:
        raise RuntimeError('Duplicate/reload check failed')
    return {'first_count':first,'after_reload_count':second,'no_duplicates':True,
            'update_policy':'Rebuild lab-owned strategy collection; stable UUID upserts within a snapshot.'}


def search(client, strategy, vector, query_filter=None):
    filt = None
    if query_filter:
        if set(query_filter) != {'lesson'} or not isinstance(query_filter['lesson'],int):
            raise ValueError('Only integer lesson filter supported')
        filt = models.Filter(must=[models.FieldCondition(key='lesson',match=models.MatchValue(value=query_filter['lesson']))])
    points = client.query_points(collection_name=f'kanji_{strategy}',query=vector.tolist(),
        query_filter=filt,limit=3,search_params=models.SearchParams(exact=True),with_payload=True).points
    return [{**p.payload,'score':p.score,'point_id':str(p.id)} for p in points]
