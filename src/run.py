import argparse
import importlib.metadata
import logging
import platform
import sys
import time
import traceback
from .common import ROOT,read_json,read_jsonl,write_json,write_jsonl,now,digest
from .ingestion import ingest
from .chunking import chunk_entries
from .embeddings import load_model,encode
from .store import open_store,ingest_collection,search
from .evaluation import validate_frozen,evaluate_split,summarize,select,save_results


def build():
    validate_frozen()
    config=read_json(ROOT/'configs/strategies.json')
    entries=read_jsonl(ROOT/'data/processed/entries.jsonl')
    model=load_model(config,offline=True)
    client=open_store()
    stats={};saved_vectors=None
    try:
        for strategy,settings in config['strategies'].items():
            started=time.perf_counter()
            chunks=chunk_entries(entries,strategy,settings)
            write_jsonl(ROOT/f'data/processed/chunks_{strategy}.jsonl',chunks)
            lengths=[len(c['text']) for c in chunks]
            token_lengths=[len(model.tokenizer(config['document_prefix']+c['text'])['input_ids']) for c in chunks]
            if max(token_lengths)>config['max_tokens']:
                raise RuntimeError('A chunk would be silently truncated by embedding model')
            enc_started=time.perf_counter()
            if strategy=='C':
                # Same exact text and embeddings as B: isolate the filter effect.
                assert [c['text'] for c in chunks]==[c['text'] for c in saved_vectors[0]]
                vectors=saved_vectors[1]
            else:
                vectors=encode(model,[c['text'] for c in chunks],config['document_prefix'],config['batch_size'])
            embedding_seconds=time.perf_counter()-enc_started
            if vectors.shape!=(len(chunks),config['dimensions']):
                raise RuntimeError('Unexpected embedding shape')
            if strategy=='B': saved_vectors=(chunks,vectors)
            store_started=time.perf_counter()
            reload_check=ingest_collection(client,f'kanji_{strategy}',chunks,vectors)
            store_seconds=time.perf_counter()-store_started
            stats[strategy]=dict(chunk_count=len(chunks),char_min=min(lengths),char_max=max(lengths),
                char_mean=sum(lengths)/len(lengths),total_chars=sum(lengths),total_tokens=sum(token_lengths),
                max_tokens=max(token_lengths),embedding_seconds=embedding_seconds,
                embeddings_reused_from='B' if strategy=='C' else None,store_seconds_including_reload=store_seconds,
                ingest_seconds=time.perf_counter()-started,cost_usd=0,reload_check=reload_check)
            print(strategy,stats[strategy],flush=True)
    finally:
        client.close()
    # Re-open after close: verify persistence, not only in-memory counts.
    reopened=open_store()
    try:
        for strategy in stats:
            count=reopened.count(f'kanji_{strategy}',exact=True).count
            assert count==stats[strategy]['chunk_count']
            stats[strategy]['persisted_count_after_reopen']=count
    finally: reopened.close()
    write_json(ROOT/'results/ingestion_stats.json',stats)
    write_json(ROOT/'results/runtime.json',dict(ran_at=now(),python=sys.version,platform=platform.platform(),
        packages={p:importlib.metadata.version(p) for p in ['pypdf','qdrant-client','sentence-transformers','torch','transformers','numpy']},
        model=read_json(ROOT/'artifacts/model_snapshot.json'),device=config['device'],seed=0,
        store='Qdrant local persistent',store_path='.local/qdrant',collections=['kanji_A','kanji_B','kanji_C'],
        distance='cosine',search='exact',paid_api_cost_usd=0,electricity_and_hardware_cost='not measured',
        corpus_sha256=digest(ROOT/'data/processed/entries.jsonl'),config_sha256=digest(ROOT/'configs/strategies.json')))


def benchmark():
    validate_frozen()
    config=read_json(ROOT/'configs/strategies.json')
    questions=read_jsonl(ROOT/'benchmark/questions.jsonl')
    model=load_model(config,offline=True)
    vectors=encode(model,[q['question'] for q in questions],config['query_prefix'],config['batch_size'])
    client=open_store()
    try:
        dev=evaluate_split(client,model,config,'dev',list(zip(questions,vectors)))
        write_jsonl(ROOT/'results/private/dev_traces.jsonl',dev)
        selection=select(summarize(dev),read_json(ROOT/'results/ingestion_stats.json'))
        print('Selection frozen before test:',selection['selected'],flush=True)
        test=evaluate_split(client,model,config,'test',list(zip(questions,vectors)))
        write_json(ROOT/'results/test_execution.json',{'executed_at':now(),'selection_frozen_at':selection['frozen_at'],
            'no_test_tuning':True,'note':'Re-running unchanged inputs is reproducibility checking, not a fresh independent test.'})
        print(save_results(dev+test),flush=True)
    finally: client.close()


def lookup(question,strategy,lesson):
    config=read_json(ROOT/'configs/strategies.json')
    model=load_model(config,offline=True)
    vector=encode(model,[question],config['query_prefix'])[0]
    client=open_store()
    try:
        rows=search(client,strategy,vector,{'lesson':lesson} if lesson is not None and strategy=='C' else {})
        for i,r in enumerate(rows,1):
            print(f'\n#{i} | trang {r["page"]} | bài {r["lesson"]:02} | cosine {r["score"]:.4f}\n{r["text"]}')
    finally: client.close()


def interactive():
    config=read_json(ROOT/'configs/strategies.json')
    model=load_model(config,offline=True)
    client=open_store()
    print('\nTRA CỨU KANJI N2 — tài liệu Kaori Sensei')
    print('Nhập câu hỏi tiếng Việt/Nhật. Gõ /bai 16 để lọc, /tat để bỏ lọc, /thoat để kết thúc.')
    print('Kết quả là đoạn nguồn gần nhất, cần đọc đối chiếu; hệ thống không tự sinh đáp án.')
    lesson=None
    try:
        while True:
            try: q=input(f'\n[Bài {lesson or "tất cả"}] Câu hỏi: ').strip()
            except (EOFError,KeyboardInterrupt): break
            if q=='/thoat': break
            if q=='/tat': lesson=None;continue
            if q.startswith('/bai '):
                value=q.removeprefix('/bai ').strip()
                if value.isdigit() and 1<=int(value)<=16: lesson=int(value)
                else: print('Chọn số bài từ 1 đến 16.')
                continue
            if not q: continue
            vector=encode(model,[q],config['query_prefix'])[0]
            for i,r in enumerate(search(client,'C',vector,{'lesson':lesson} if lesson else {}),1):
                print(f'\n#{i} | Nguồn KANJI N2.pdf | trang {r["page"]} | bài {r["lesson"]:02} | cosine {r["score"]:.4f}\n{r["text"]}')
    finally: client.close()


def main():
    parser=argparse.ArgumentParser(description='Kanji N2 data ingestion lab')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('ingest');p.add_argument('--pdf',default=str(ROOT/'data/raw/KANJI N2.pdf'))
    sub.add_parser('build');sub.add_parser('benchmark');sub.add_parser('interactive')
    p=sub.add_parser('search');p.add_argument('question');p.add_argument('--strategy',choices=['A','B','C'],default='C');p.add_argument('--lesson',type=int,choices=range(1,17))
    args=parser.parse_args()
    try:
        if args.command=='ingest': ingest(args.pdf)
        elif args.command=='build': build()
        elif args.command=='benchmark': benchmark()
        elif args.command=='interactive': interactive()
        else: lookup(args.question,args.strategy,args.lesson)
    except Exception:
        (ROOT/'results').mkdir(exist_ok=True)
        with (ROOT/'results/runtime_errors.log').open('a',encoding='utf-8') as f:
            f.write(now()+'\n'+traceback.format_exc()+'\n')
        raise

if __name__=='__main__': main()
