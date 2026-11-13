"""Fixed questions authored before retrieval. Never generate gold from retrieval output."""
from .common import ROOT, SOURCE, read_jsonl, read_json, write_json, write_jsonl, now, digest, norm

# split, page, query, answer, raw source quote, user-supplied lesson filter
QUESTIONS = [
('dev',4,'Chữ 井 có những âm Onyomi và Kunyomi nào?', 'Onyomi セイ・ショウ; Kunyomi い.', '井\nOn yomi\nセイ・ショウ\nKun yomi\nい',None),
('dev',4,'天井 đọc thế nào và nghĩa tiếng Việt là gì?', 'てんじょう — trần nhà.', '天井\nてんじょう\ntrần nhà',None),
('dev',6,'Trong bài 01, từ nào chỉ bầu không khí và đọc ra sao?', '雰囲気 — ふんいき.', '雰囲気\nふんいき\nbầu không khí',1),
('dev',7,'Miễn thuế trong tiếng Nhật viết và đọc như thế nào?', '免税 — めんぜい.', '免税\nめんぜい\nmiễn thuế',None),
('dev',32,'Trong bài 02, từ nào nghĩa là đồng thời giữ nhiều chức vụ?', '兼任 — けんにん.', '兼任\nけんにん\nđồng thời giữ nhiều chức vụ',2),
('dev',60,'窓枠 có cách đọc và nghĩa là gì?', 'まどわく — khung cửa sổ.', '窓枠\nまどわく\nkhung cửa sổ',None),
('dev',88,'Từ tiếng Nhật chỉ thời hạn trong mục chữ 限 là gì, đọc thế nào?', '期限 — きげん.', '期限\nきげん\nthời hạn',None),
('dev',116,'Theo bài 05, suối nước nóng viết và đọc thế nào?', '温泉 — おんせん.', '温泉\nおんせん\nsuối nước nóng',5),
('dev',144,'改札 có nghĩa gì và cách đọc ra sao?', 'かいさつ — cổng soát vé, kiểm soát vé.', '改札\nかいさつ\ncổng soát vé, kiểm soát vé',None),
('dev',172,'Trong bài 07, văn bản hợp đồng được viết và đọc ra sao?', '契約書 — けいやくしょ.', '契約書\nけいやくしょ\nvăn bản hợp đồng',7),
('dev',200,'裁縫 có phải là phán xử không? Nêu nghĩa và cách đọc đúng theo tài liệu.', 'Không. 裁縫 là さいほう — may vá.', '裁縫\nさいほう\nmay vá',None),
('dev',228,'怖がり mô tả người như thế nào và đọc ra sao?', 'こわがり — người nhát, hay sợ.', '怖がり\nこわがり\nngười nhát, hay sợ',None),
('dev',259,'Trong bài 10, từ nào nghĩa là mang theo, cách đọc là gì?', '持参 — じさん.', '持参\nじさん\nmang theo',10),
('dev',299,'披露宴 có nghĩa gì và đọc thế nào?', 'ひろうえん — tiệc cưới.', '披露宴\nひろうえん\ntiệc cưới',None),
('dev',331,'背負う dùng với nghĩa nào và đọc thế nào?', 'せおう — cõng, mang trên lưng; gánh vác.', '背負う\nせおう\ncõng, mang trên lưng; gánh vác',None),
('test',360,'Trong bài 13, từ chỉ dinh dưỡng viết và đọc thế nào?', '栄養 — えいよう.', '栄養\nえいよう\ndinh dưỡng',13),
('test',389,'半壊 nghĩa là sụp đổ hoàn toàn hay một phần? Cho cách đọc.', 'はんかい — sự hư hại, sụp đổ một phần.', '半壊\nはんかい\nsự hư hại, sụp đổ một phần',None),
('test',414,'折り畳み có cách đọc và nghĩa như thế nào?', 'おりたたみ — gấp gọn.', '折り畳み\nおりたたみ\ngấp gọn',None),
('test',439,'Theo bài 16, đồi cát viết bằng từ nào và đọc thế nào?', '砂丘 — さきゅう.', '砂丘\nさきゅう\nđồi cát',16),
('test',472,'渋滞 diễn tả tình trạng gì và đọc như thế nào?', 'じゅうたい — ùn tắc.', '渋滞\nじゅうたい\nùn tắc',None),
]


def match_text(s):
    return norm(s.replace('|', ' '))


def prepare():
    path = ROOT / 'benchmark/questions.jsonl'
    if (ROOT / 'benchmark/frozen.json').exists():
        raise RuntimeError('Benchmark already frozen. Do not overwrite after inspecting retrieval.')
    pages = {p['page']:p for p in read_jsonl(ROOT / 'data/processed/pages.jsonl')}
    entries = read_jsonl(ROOT / 'data/processed/entries.jsonl')
    by_page = {e['page']:e for e in entries}
    rows = []
    for i,(split,page,q,answer,quote,lesson) in enumerate(QUESTIONS,1):
        assert norm(quote) in norm(pages[page]['text']), (i,page,'raw evidence absent')
        # A reading-only question uses the canonical field labels introduced by normalization.
        evidence = (f'Kanji: 井 | Hán Việt: TỈNH\nOnyomi: セイ・ショウ\nKunyomi: い'
                    if i == 1 else quote)
        assert match_text(evidence) in match_text(by_page[page]['text']), (i,'canonical evidence absent')
        gold_pages = [e['page'] for e in entries if match_text(evidence) in match_text(e['text'])
                      and (lesson is None or e['lesson'] == lesson)]
        rows.append(dict(id=f'Q{i:02}',split=split,question=q,expected_answer=answer,
            gold_source_id=SOURCE,gold_page=page,gold_pages=gold_pages,
            evidence_quote=quote,canonical_evidence=evidence,
            filter={'lesson':lesson} if lesson else {},
            type='metadata' if lesson else ('condition_or_disambiguation' if i in [11,17] else 'lookup_or_paraphrase'),
            evidence_verified_in_raw=True))
    write_jsonl(path,rows)
    cfg = ROOT / 'configs/strategies.json'
    write_json(ROOT / 'benchmark/frozen.json',dict(frozen_at=now(),questions_sha256=digest(path),
        config_sha256=digest(cfg),corpus_sha256=digest(ROOT / 'data/processed/entries.jsonl'),
        split_rule='Dev lessons 01-12; test lessons 13-16. Same document/template; lexical overlap leakage remains possible.',
        selection_rule=read_json(cfg)['selection_rule'],
        source_validation='Each raw evidence quote checked against extracted PDF page; canonical structural labels checked against normalized entry.',
        author='Codex AI assistant; student review pending',
        no_retrieval_seen_at_freeze=True))
    print('Frozen 15 dev / 5 test questions and config hashes', flush=True)

if __name__ == '__main__':
    prepare()
