"""Strict single-chunk evidence metric, separate dev and held-out test."""
import csv
import time
from .common import ROOT,read_json,read_jsonl,write_json,write_jsonl,digest,now
from .prepare_benchmark import match_text
from .store import search


def is_hit(question,chunk):
    return (chunk['document_id']==question['gold_source_id']
        and chunk['page'] in question['gold_pages']
        and match_text(question['canonical_evidence']) in match_text(chunk['text']))


def validate_frozen():
    frozen=read_json(ROOT/'benchmark/frozen.json')
    for key,path in [('questions_sha256','benchmark/questions.jsonl'),
                     ('config_sha256','configs/strategies.json'),
                     ('corpus_sha256','data/processed/entries.jsonl')]:
        if digest(ROOT/path)!=frozen[key]:
            raise RuntimeError(f'Frozen input changed: {path}. Create a new named experiment, do not reuse test.')


def evaluate_split(client,model,config,split,query_vectors):
    rows=[]
    for strategy in config['strategies']:
        for q,vector in query_vectors:
            if q['split']!=split:
                continue
            filt=q['filter'] if config['strategies'][strategy]['metadata_filter'] else {}
            started=time.perf_counter()
            top=search(client,strategy,vector,filt)
            elapsed=time.perf_counter()-started
            hits=[is_hit(q,c) for c in top]
            rows.append(dict(strategy=strategy,split=split,question_id=q['id'],question=q['question'],
                requested_filter=q['filter'],applied_filter=filt,top3=top,
                evidence_hits=hits,hit1=bool(hits and hits[0]),hit3=any(hits),
                search_seconds=elapsed))
    return rows


def summarize(rows):
    metrics=[]
    for strategy in ['A','B','C']:
        for split in ['dev','test']:
            group=[r for r in rows if r['strategy']==strategy and r['split']==split]
            if not group: continue
            n=len(group)
            metrics.append(dict(strategy=strategy,split=split,n=n,
                hit1_n=sum(r['hit1'] for r in group),hit3_n=sum(r['hit3'] for r in group),
                hit1=sum(r['hit1'] for r in group)/n,hit3=sum(r['hit3'] for r in group)/n,
                mean_search_ms=1000*sum(r['search_seconds'] for r in group)/n))
    return metrics


def select(dev_metrics,stats):
    priority={'B':2,'C':1,'A':0}
    best=max(dev_metrics,key=lambda r:(r['hit3'],r['hit1'],-stats[r['strategy']]['chunk_count'],priority[r['strategy']]))
    frozen=ROOT/'results/selection.json'
    result=dict(selected=best['strategy'],frozen_at=now(),split_used='dev only',
        rule=read_json(ROOT/'configs/strategies.json')['selection_rule'],dev_metrics=dev_metrics)
    if frozen.exists():
        old=read_json(frozen)
        if old['selected']!=result['selected']:
            raise RuntimeError('Previously frozen selection differs. Do not tune against existing test.')
        return old
    write_json(frozen,result)
    return result


def save_results(rows):
    write_jsonl(ROOT/'results/private/traces.jsonl',rows)
    metrics=summarize(rows)
    write_json(ROOT/'results/metrics.json',metrics)
    with (ROOT/'results/metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(metrics[0]),lineterminator='\n');writer.writeheader();writer.writerows(metrics)
    # Public summary omits full chunk text; local traces retain all evidence for review.
    write_jsonl(ROOT/'results/retrieval_summary.jsonl',[
        {k:v for k,v in r.items() if k!='top3'} | {'top3':[{'id':c['id'],'page':c['page'],
            'lesson':c['lesson'],'kanji':c['kanji'],'score':c['score']} for c in r['top3']]} for r in rows])
    return metrics
