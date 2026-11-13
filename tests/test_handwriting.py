import math
import unittest
import numpy as np
from src.handwriting import HandwritingMatcher,validate_strokes
from src.web import Service
from src.common import ROOT,read_jsonl


class HandwritingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher=HandwritingMatcher()
        cls.by_kanji={r['kanji']:r for r in cls.matcher.references}

    def test_reference_coverage(self):
        self.assertEqual(set(self.by_kanji),{e['kanji'] for e in read_jsonl(ROOT/'data/processed/entries.jsonl')})

    def test_exact_reference_and_reordered_strokes(self):
        for kanji in ['井','囲','領','畳','渋']:
            strokes=self.by_kanji[kanji]['strokes']
            result=self.matcher.recognize(list(reversed(strokes)))
            self.assertEqual(result['candidates'][0]['kanji'],kanji)

    def test_missing_dot_suggests_similar_kanji(self):
        strokes=self.by_kanji['丼']['strokes']
        # The short central dot is the distinction from 井; removing it should retain both candidates.
        short=min(range(len(strokes)),key=lambda i:np.linalg.norm(np.diff(np.array(strokes[i]),axis=0),axis=1).sum())
        incomplete=[stroke for i,stroke in enumerate(strokes) if i!=short]
        chars=[r['kanji'] for r in self.matcher.recognize(incomplete)['candidates']]
        self.assertIn('井',chars[:3]);self.assertIn('丼',chars)

    def test_mouse_drawn_井(self):
        strokes=[[[27,64],[174,64]],[[22,123],[177,123]],[[67,28],[60,173]],[[137,28],[139,173]]]
        self.assertEqual(self.matcher.recognize(strokes)['candidates'][0]['kanji'],'井')

    def test_invalid_or_empty_strokes_rejected(self):
        for invalid in [[],[[[math.nan,1]]],[[[300,1]]],[[[True,1]]],[[['x',1]]]]:
            with self.assertRaises(ValueError):validate_strokes(invalid)
        with self.assertRaises(ValueError):self.matcher.recognize([[[10,10]]])

    def test_single_slot_and_payload_boundaries(self):
        service=Service.__new__(Service)
        service.matcher=self.matcher
        service.by_kanji={e['kanji']:e for e in read_jsonl(ROOT/'data/processed/entries.jsonl')}
        result=service.recognize({'cells':[{'index':0,'strokes':self.by_kanji['井']['strokes']}]})
        self.assertEqual(len(result['cells']),1)
        self.assertEqual(result['cells'][0]['candidates'][0]['kanji'],'井')
        with self.assertRaises(ValueError):service.recognize({'cells':[{'index':i,'strokes':[]} for i in range(2)]})
        with self.assertRaises(ValueError):service.recognize({'cells':[{'index':1,'strokes':self.by_kanji['井']['strokes']}]})

if __name__=='__main__':unittest.main()
