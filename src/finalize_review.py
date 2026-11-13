"""Validate real student-entered labels; do not fill blanks with AI suggestions."""
import csv
from .common import ROOT,read_jsonl,write_json,now


def reviewed_rows(name,expected,keys,score_field,allowed):
    path=ROOT/f'results/student_{name}_review.csv'
    with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    identity=lambda r:tuple(str(r[k]) for k in keys)
    if len(rows)!=len(expected) or len({identity(r) for r in rows})!=len(rows) or {identity(r) for r in rows}!={identity(r) for r in expected}:
        raise ValueError(f'{path.name}: row identities changed/duplicated/missing')
    for r in rows:
        if r.get(score_field) not in allowed or any(not r.get(k,'').strip() for k in ['reason','reviewer','reviewed_at']):
            raise ValueError(f'{path.name}: missing score/reason/reviewer/date at {identity(r)}. Read the packet and enter actual student labels.')
        r[score_field]=int(r[score_field])
    return rows


def main():
    coherence=reviewed_rows('coherence',read_jsonl(ROOT/'results/private/coherence_packet.jsonl'),
        ['strategy','page','anchor','chunk_id'],'score_0_1_2',{'0','1','2'})
    grounding=reviewed_rows('grounding',read_jsonl(ROOT/'results/private/grounding_packet.jsonl'),
        ['strategy','question_id'],'score_0_1_2',{'0','1','2'})
    metadata=reviewed_rows('metadata',read_jsonl(ROOT/'results/metadata_audit.jsonl'),
        ['strategy','question_id','rank','page','lesson','kanji','source'],'correct_0_1',{'0','1'})
    result={'finalized_at':now(),'label_provenance':'Student-entered CSVs; not automatically copied from AI labels.','strategies':{}}
    for s in ['A','B','C']:
        co=[r['score_0_1_2'] for r in coherence if r['strategy']==s]
        gr=[r['score_0_1_2'] for r in grounding if r['strategy']==s]
        md=[r['correct_0_1'] for r in metadata if r['strategy']==s]
        result['strategies'][s]={'coherence_mean':sum(co)/len(co),'coherence_n':len(co),
            'grounding_counts':{str(i):gr.count(i) for i in [0,1,2]},'grounding_mean':sum(gr)/len(gr),
            'metadata_correct':sum(md),'metadata_total':len(md)}
    write_json(ROOT/'results/student_audit_summary.json',result)
    from .report import render
    render()
    print('Student audit validated; report updated.')

if __name__=='__main__':main()
