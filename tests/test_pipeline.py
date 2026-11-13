import unittest
import tempfile
from pathlib import Path
from qdrant_client import QdrantClient
import numpy as np
from src.chunking import chunk_entries
from src.evaluation import is_hit, validate_frozen
from src.common import ROOT,read_jsonl,read_json
from src.store import ingest_collection,search


class PipelineTests(unittest.TestCase):
    def test_corpus_and_gold(self):
        validate_frozen()
        entries=read_jsonl(ROOT/'data/processed/entries.jsonl')
        self.assertEqual(len(entries),454)
        self.assertEqual(set(e['lesson'] for e in entries),set(range(1,17)))
        qs=read_jsonl(ROOT/'benchmark/questions.jsonl')
        self.assertEqual(sum(q['split']=='dev' for q in qs),15)
        self.assertEqual(sum(q['split']=='test' for q in qs),5)
        self.assertGreaterEqual(sum(bool(q['filter']) for q in qs),3)
        self.assertTrue(any(q['filter'] for q in qs if q['split']=='test'))

    def test_single_chunk_evidence_cannot_cross_boundary(self):
        q={'gold_source_id':'doc','gold_pages':[4],'canonical_evidence':'語 | ご | từ'}
        chunk={'document_id':'doc','page':4,'text':'語 | ご'}
        self.assertFalse(is_hit(q,chunk))
        chunk['text']='語 | ご | từ'
        self.assertTrue(is_hit(q,chunk))
        chunk['page']=5
        self.assertFalse(is_hit(q,chunk))

    def test_fixed_chunk_covers_every_character(self):
        e=read_jsonl(ROOT/'data/processed/entries.jsonl')[0]
        chunks=chunk_entries([e],'A',{'chunking':'fixed_chars_within_entry','size':50,'overlap':10})
        covered=set()
        for c in chunks:
            self.assertEqual(c['text'],e['text'][c['start']:c['end']])
            covered.update(range(c['start'],c['end']))
        self.assertEqual(covered,set(range(len(e['text']))))

    def test_qdrant_filter_and_reload_real_backend(self):
        # Tiny synthetic vectors test only DB semantics; never used for lab embeddings/results.
        with tempfile.TemporaryDirectory() as d:
            client=QdrantClient(path=d)
            chunks=[{'id':'test1','lesson':1,'page':1,'text':'one'},
                    {'id':'test2','lesson':2,'page':2,'text':'two'}]
            vectors=np.array([[1.,0.],[0.,1.]])
            check=ingest_collection(client,'kanji_C',chunks,vectors)
            self.assertTrue(check['no_duplicates'])
            self.assertEqual(check['after_reload_count'],2)
            found=search(client,'C',np.array([1.,0.]),{'lesson':2})
            self.assertEqual([r['page'] for r in found],[2])
            client.close()

if __name__=='__main__': unittest.main()
