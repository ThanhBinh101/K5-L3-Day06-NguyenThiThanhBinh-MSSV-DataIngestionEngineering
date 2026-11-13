"""Produce audit packets; never invent human labels or turn Hit@3 into manual grounding."""
import csv
import re
from .common import ROOT, read_jsonl,read_json,write_json,write_jsonl,norm


def export_audit():
    entries=read_jsonl(ROOT/'data/processed/entries.jsonl')
    pages={p['page']:p for p in read_jsonl(ROOT/'data/processed/pages.jsonl')}
    questions={q['id']:q for q in read_jsonl(ROOT/'benchmark/questions.jsonl')}
    traces=read_jsonl(ROOT/'results/private/traces.jsonl')
    coherence=[]
    for strategy in ['A','B','C']:
        chunks=read_jsonl(ROOT/f'data/processed/chunks_{strategy}.jsonl')
        for entry in entries[:10]:
            anchor=entry['vocabulary'][-1]['word']
            candidates=[c for c in chunks if c['page']==entry['page'] and anchor in c['text']]
            chosen=min(candidates,key=lambda c:c['start'])
            coherence.append(dict(strategy=strategy,page=entry['page'],anchor=anchor,chunk_id=chosen['id'],
                text=chosen['text'],source_entry=entry['text'],score=None,reason='',reviewer=''))
    write_jsonl(ROOT/'results/private/coherence_packet.jsonl',coherence)
    grounding=[];metadata=[]
    for row in traces:
        if row['split']!='test': continue
        q=questions[row['question_id']]
        grounding.append(dict(strategy=row['strategy'],question_id=q['id'],question=q['question'],
            expected_answer=q['expected_answer'],evidence_quote=q['evidence_quote'],gold_pages=q['gold_pages'],
            top3=[{k:c[k] for k in ['id','text','page','lesson','kanji']} for c in row['top3']],
            score=None,reason='',reviewer=''))
        for rank,c in enumerate(row['top3'],1):
            raw=pages[c['page']]['text']
            header=re.match(r'Bài\s+(\d+)',raw)
            valid=(c['document_id']=='kanji_n2_kaori' and c['source']=='KANJI N2.pdf' and header is not None
                   and int(header[1])==c['lesson'] and c['kanji'] in raw.splitlines())
            complies=(not q['filter'] or all(c[k]==v for k,v in q['filter'].items()))
            metadata.append(dict(strategy=row['strategy'],question_id=q['id'],rank=rank,chunk_id=c['id'],
                page=c['page'],lesson=c['lesson'],kanji=c['kanji'],source=c['source'],
                automated_complete_and_correct=valid,requested_filter=q['filter'],
                complies_with_requested_filter=complies,reviewer='automated source cross-check',
                student_verified=None,student_note=''))
    write_jsonl(ROOT/'results/private/grounding_packet.jsonl',grounding)
    write_jsonl(ROOT/'results/metadata_audit.jsonl',metadata)
    write_json(ROOT/'results/audit_instructions.json',dict(
        coherence='Read each sampled chunk in isolation. 0 broken idea/unintelligible; 1 partially understandable/missing context; 2 self-contained. Same 10 source anchors across A/B/C.',
        grounding='Read top3 for each test question. 0 no relevant evidence; 1 partial/missing condition or requested reading; 2 enough to answer and trace. Do not copy Hit@3 as a score.',
        student_review='AI review is provisional. Student must read source/chunks and enter their own score/reason or explicitly verify with date. Do not relabel AI as human.',
        packets='results/private/*_packet.jsonl hold full text; results/ai_*_review.jsonl hold transparent AI labels.'))
    # Human sheets are intentionally blank and never overwritten on repeat runs.
    sheets=[('coherence',coherence,['strategy','page','anchor','chunk_id']),
            ('grounding',grounding,['strategy','question_id'])]
    for name,rows,keys in sheets:
        path=ROOT/f'results/student_{name}_review.csv'
        if not path.exists():
            with path.open('w',newline='',encoding='utf-8-sig') as f:
                w=csv.DictWriter(f,fieldnames=keys+['score_0_1_2','reason','reviewer','reviewed_at'],lineterminator='\n')
                w.writeheader()
                w.writerows({k:r[k] for k in keys} for r in rows)
    path=ROOT/'results/student_metadata_review.csv'
    if not path.exists():
        keys=['strategy','question_id','rank','page','lesson','kanji','source']
        with path.open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=keys+['correct_0_1','reason','reviewer','reviewed_at'],lineterminator='\n')
            w.writeheader();w.writerows({k:r[k] for k in keys} for r in metadata)
    print('Exported 30 coherence samples, 15 grounding cases, 45 metadata checks')

if __name__=='__main__':export_audit()
