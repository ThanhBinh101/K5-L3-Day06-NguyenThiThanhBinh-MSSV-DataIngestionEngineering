import unittest
from src.lookup import exact_lookup,han_viet_lookup,infer_kind,spelling_suggestions,vietnamese_key,source_text_matches,build_vietnamese_lexicon,accented_query_variants
from src.common import ROOT,read_jsonl

class LookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.entries=read_jsonl(ROOT/'data/processed/entries.jsonl')
    def test_word_only_matching_vocabulary(self):
        rows=exact_lookup(self.entries,'天井')
        self.assertTrue(rows)
        self.assertTrue(all(v['word']=='天井' for r in rows for v in r['entry']['vocabulary']))
        self.assertNotIn('浜',[r['entry']['kanji'] for r in rows])
    def test_unknown_word_does_not_decompose_into_characters(self):
        self.assertEqual(exact_lookup(self.entries,'井井井'),[])
    def test_single_kanji_has_only_containing_words(self):
        rows=exact_lookup(self.entries,'井')
        self.assertTrue(rows)
        self.assertTrue(all('井' in v['word'] for r in rows for v in r['entry']['vocabulary']))
    def test_lesson_filter(self):
        self.assertTrue(exact_lookup(self.entries,'砂丘',16))
        self.assertEqual(exact_lookup(self.entries,'砂丘',1),[])

    def test_automatic_query_kinds(self):
        self.assertEqual(infer_kind(self.entries,'井'),'kanji')
        self.assertEqual(infer_kind(self.entries,'TỈNH'),'han_viet')
        self.assertEqual(infer_kind(self.entries,'Cái giếng 2 tầng'),'mnemonic')
        self.assertEqual(infer_kind(self.entries,'miễn thuế'),'semantic')
    def test_all_han_viet_homophones(self):
        from collections import Counter
        counts=Counter(vietnamese_key(e['han_viet']) for e in self.entries)
        sound,count=next((k,v) for k,v in counts.items() if v>1)
        rows=han_viet_lookup(self.entries,sound.lower())
        self.assertEqual(len(rows),count)
        self.assertTrue(all(r['match']=='han_viet' for r in rows))
    def test_unknown_word_has_correction_candidates(self):
        candidates=spelling_suggestions(self.entries,'天井井')
        self.assertIn('天井',[r['text'] for r in candidates])

    def test_han_viet_ignores_tone_and_case(self):
        expected={e['kanji'] for e in self.entries if vietnamese_key(e['han_viet'])=='tinh'}
        self.assertTrue(expected)
        for query in ['Tinh','TINH','tính','TÌNH','tịnh']:
            rows=han_viet_lookup(self.entries,query)
            self.assertEqual({r['entry']['kanji'] for r in rows},expected)
        self.assertEqual(infer_kind(self.entries,'Tinh'),'han_viet')
    def test_han_viet_ignores_accents_but_not_other_letters(self):
        rows=han_viet_lookup(self.entries,'Tinh')
        self.assertTrue(all(vietnamese_key(r['entry']['han_viet'])=='tinh' for r in rows))
        self.assertEqual(han_viet_lookup(self.entries,'Tinh xyz'),[])

    def test_tone_exact_results_precede_similar_sounds(self):
        for query in ['TỈNH','tình','TÍNH','tịnh','Tinh']:
            rows=han_viet_lookup(self.entries,query)
            flags=[r['tone_match'] for r in rows]
            self.assertEqual(flags,sorted(flags,reverse=True))
            self.assertTrue(flags[0])
            self.assertTrue(all(r['entry']['han_viet'].casefold()==query.casefold() for r in rows if r['tone_match']))
        self.assertEqual([r['entry']['kanji'] for r in han_viet_lookup(self.entries,'TỈNH')[:2]],['井','省'])

    def test_unaccented_meaning_queries(self):
        for q,expected in [('cây thông','松'),('cay thong','松'),('tim cay thong','松'),('miễn thuế','免'),('mien thue','免')]:
            self.assertEqual(infer_kind(self.entries,q),'semantic')
            rows,_=source_text_matches(self.entries,q,'semantic')
            self.assertEqual(rows[0]['entry']['kanji'],expected)
    def test_unaccented_mnemonic_descriptions(self):
        for q,expected in [('Cái giếng 2 tầng','井'),('cai gieng 2 tang','井'),('giong cai gieng','井'),('chu co tan la rong','松')]:
            self.assertEqual(infer_kind(self.entries,q),'mnemonic')
            rows,_=source_text_matches(self.entries,q,'mnemonic')
            self.assertEqual(rows[0]['entry']['kanji'],expected)
    def test_unaccented_text_respects_lesson(self):
        self.assertEqual(source_text_matches(self.entries,'cay thong','semantic',1)[0],[])
        self.assertEqual(source_text_matches(self.entries,'cay thong','semantic',13)[0][0]['entry']['kanji'],'松')
    def test_many_source_phrases_keep_target_without_accents(self):
        samples=self.entries[::25]
        for e in samples:
            for kind,text in [('semantic',e['vocabulary'][0]['meaning_vi']),('mnemonic',e['mnemonic'])]:
                rows,_=source_text_matches(self.entries,vietnamese_key(text),kind)
                self.assertIn(e['kanji'],[r['entry']['kanji'] for r in rows],(kind,text))

    def test_semantic_expansion_includes_accented_paraphrase(self):
        lexicon=build_vietnamese_lexicon(self.entries)
        variants=accented_query_variants('cay nhieu la',lexicon)
        self.assertIn('cây nhiều lá',variants)
        self.assertLessEqual(len(variants),9)
        self.assertIn('cay nhieu la',variants)
    def test_query_expansion_preserves_explicit_accents(self):
        lexicon=build_vietnamese_lexicon(self.entries)
        self.assertEqual(accented_query_variants('cây nhiều lá',lexicon),['cây nhiều lá'])
        self.assertTrue(all(q.startswith('cây ') for q in accented_query_variants('cây nhieu la',lexicon)))
    def test_expansion_keeps_unknown_words_and_input_boundaries(self):
        lexicon=build_vietnamese_lexicon(self.entries)
        for q in accented_query_variants('xyztoken, cay!',lexicon):
            self.assertTrue(q.startswith('xyztoken, '));self.assertTrue(q.endswith('!'))
