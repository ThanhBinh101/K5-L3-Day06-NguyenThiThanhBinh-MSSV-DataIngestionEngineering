"""Live local API regression checks; no mock model or database.
Run from repo root while `python -m src.web` serves port 8766.
"""
import http.client
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,read_json,write_json,now


def request(path,payload=None,headers=None):
    connection=http.client.HTTPConnection('127.0.0.1',8766,timeout=60)
    body=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    options={'Content-Type':'application/json'} if body else {}
    options.update(headers or {})
    connection.request('POST' if payload is not None else 'GET',path,body,options)
    response=connection.getresponse()
    data=json.loads(response.read())
    connection.close()
    return response.status,data


def main():
    status,health=request('/api/status')
    assert status==200 and health['ready'],health
    checks=[]
    cases=[('天井','井','kanji'),('Tinh',None,'han_viet'),('TỈNH','井','han_viet'),
           ('cây thông','松','semantic'),('cay thong','松','semantic'),
           ('cây nhiều lá','松','semantic'),('cay nhieu la','松','semantic'),
           ('miễn thuế','免','semantic'),('mien thue','免','semantic'),
           ('Cái giếng 2 tầng','井','mnemonic'),('cai gieng 2 tang','井','mnemonic'),
           ('giong cai gieng','井','mnemonic'),('chu co tan la rong','松','mnemonic')]
    for query,expected,kind in cases:
        status,data=request('/api/search',{'query':query})
        assert status==200,(query,status,data)
        assert data['kind']==kind,(query,data['kind'])
        rows=data['results']
        assert rows,(query,'no results')
        if expected:assert rows[0]['entry']['kanji']==expected,(query,[r['entry']['kanji'] for r in rows])
        if query=='Tinh':assert len(rows)==6
        if query=='TỈNH':assert [r['entry']['kanji'] for r in rows[:2]]==['井','省']
        if query=='天井':assert all(v['word']=='天井' for r in rows for v in r['entry']['vocabulary'])
        checks.append({'query':query,'kind':kind,'returned_kanji':[r['entry']['kanji'] for r in rows],
                       'expected_top1':expected,'query_expansion':data.get('query_expansion'),'passed':True})
    status,miss=request('/api/search',{'query':'資額'})
    assert status==200 and not miss['results'] and miss['suggestions']
    status,filtered=request('/api/search',{'query':'砂丘','lesson':16})
    assert status==200 and filtered['results'][0]['entry']['page']==439
    assert all(r['entry']['lesson']==16 for r in filtered['results'])
    references=read_json(ROOT/'data/handwriting/templates.json')['characters']
    strokes=next(r['strokes'] for r in references if r['kanji']=='井')
    status,drawing=request('/api/recognize',{'cells':[{'index':0,'strokes':strokes}]})
    assert status==200 and drawing['cells'][0]['candidates'][0]['kanji']=='井'
    status,_=request('/api/recognize',{'cells':[{'index':i,'strokes':strokes} for i in range(2)]})
    assert status==400
    status,_=request('/api/search',{'query':'井'},headers={'Origin':'https://example.com'})
    assert status==403
    status,_=request('/data/processed/entries.jsonl')
    assert status==404
    result={'verified_at':now(),'status':'passed','search_cases':checks,'single_handwriting_cell':True,
            'spelling_suggestions':True,'lesson_filter':True,'cross_origin_post_rejected':True,
            'private_corpus_not_served_as_static_asset':True,
            'method':'Live HTTP requests using real local E5 and persistent Qdrant; source-known regression, not an independent benchmark.'}
    write_json(ROOT/'results/final_ui_checks.json',result)
    print(f'PASS: {len(checks)} live search cases; handwriting/filter/input boundaries verified.')

if __name__=='__main__':main()
