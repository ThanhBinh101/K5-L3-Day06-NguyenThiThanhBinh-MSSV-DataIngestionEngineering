"""Loopback-only UI service. Source PDFs and handwriting stay on this machine."""
import argparse
import json
import mimetypes
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from .common import ROOT,read_jsonl,read_json,norm,now
from .handwriting import HandwritingMatcher
from .embeddings import load_model,encode
from .store import open_store,search
from .lookup import exact_lookup,han_viet_lookup,infer_kind,ensure_mnemonic_index,spelling_suggestions,related_words,similar_characters,MNEMONIC_COLLECTION,source_text_matches,build_vietnamese_lexicon,expanded_vector_search


class Service:
    def __init__(self):
        self.entries=read_jsonl(ROOT/'data/processed/entries.jsonl')
        self.by_kanji={e['kanji']:e for e in self.entries}
        self.vietnamese_lexicon=build_vietnamese_lexicon(self.entries)
        self.config=read_json(ROOT/'configs/strategies.json')
        self.matcher=HandwritingMatcher()
        self.lock=threading.RLock()
        self.model=None;self.client=None;self.error=None
        self.ready=threading.Event()
        threading.Thread(target=self.load,daemon=True).start()

    def load(self):
        try:
            self.model=load_model(self.config,offline=True)
            self.client=open_store()
            for s in ['B','C']:
                if not self.client.collection_exists('kanji_'+s):raise RuntimeError('Chưa build vector store. Chạy python -m src.run build.')
            ensure_mnemonic_index(self.client,self.model,self.config,self.entries)
        except Exception as exc:
            self.error=str(exc)
            traceback.print_exc()
        finally:self.ready.set()

    def status(self):
        return {'ready':self.ready.is_set() and self.error is None,'loading':not self.ready.is_set(),
                'error':self.error,'entries':len(self.entries),'vocabulary':sum(len(e['vocabulary']) for e in self.entries),
                'lessons':16,'templates':len(self.matcher.references),'local':True}

    def recognize(self,payload):
        cells=payload.get('cells')
        if not isinstance(cells,list) or len(cells)!=1:raise ValueError('Chỉ sử dụng một ô viết.')
        seen=set();result=[]
        # Recognition is across the entire corpus: lesson affects lookup, not shape candidates.
        for cell in cells:
            if not isinstance(cell,dict):raise ValueError('Ô viết không hợp lệ.')
            idx=cell.get('index')
            if isinstance(idx,bool) or not isinstance(idx,int) or idx!=0 or idx in seen:raise ValueError('Chỉ số ô không hợp lệ.')
            seen.add(idx)
            r=self.matcher.recognize(cell.get('strokes'))
            for candidate in r['candidates']:
                e=self.by_kanji[candidate['kanji']]
                candidate.update({'han_viet':e['han_viet'],'lesson':e['lesson'],'page':e['page']})
            result.append({'index':idx,**r})
        return {'cells':result}

    def lookup(self,payload):
        query=payload.get('query','')
        lesson=payload.get('lesson')
        if not isinstance(query,str) or not 1<=len(query.strip())<=500:raise ValueError('Nhập câu hỏi hoặc Kanji, tối đa 500 ký tự.')
        if lesson is not None and (isinstance(lesson,bool) or not isinstance(lesson,int) or not 1<=lesson<=16):raise ValueError('Chọn bài từ 1 đến 16.')
        query=query.strip()
        started=time.perf_counter()
        kind=infer_kind(self.entries,query)
        suggestions=[];similar=[];query_expansion=None
        if kind=='han_viet':
            rows=han_viet_lookup(self.entries,query,lesson)
            note='Các âm Hán Việt cùng dạng không dấu; giữ nguyên dấu của từng chữ trong kết quả.'
        elif kind=='kanji':
            rows=exact_lookup(self.entries,query,lesson)
            if not rows:suggestions=spelling_suggestions(self.entries,query,lesson)
            similar=related_words(self.entries,query,lesson)
            if len(query)==1:similar+=similar_characters(self.entries,query,lesson,4)
            note='Không có mục khớp. Có thể bạn muốn tra một trong các gợi ý dưới đây?' if not rows else ''
        else:
            rows,canonical=source_text_matches(self.entries,query,kind,lesson)
            if not rows:
                with self.lock:
                    if not self.ready.is_set():raise RuntimeError('Model đang khởi động. Hãy chờ một chút.')
                    if self.error:raise RuntimeError(self.error)
                    found,query_expansion=expanded_vector_search(self.client,self.model,self.config,
                        query,kind,lesson,self.vietnamese_lexicon)
                    rows=[{'entry':self.by_kanji[p['kanji']],'match':kind,'score':round(p['score'],4)} for p in found]
            note='Gợi ý theo cách nhớ và hình dung chữ trong tài liệu.' if kind=='mnemonic' else 'Các mục gần nghĩa; hãy đối chiếu từ và ngữ cảnh trong tài liệu.'
        return {'query':query,'kind':kind,'lesson':lesson,'results':rows,'suggestions':suggestions,'similar':similar,
                'total':len(rows),'vocabulary_count':sum(len(r['entry']['vocabulary']) for r in rows),
                'elapsed_ms':round((time.perf_counter()-started)*1000),'note':note,'query_expansion':query_expansion}


class Handler(BaseHTTPRequestHandler):
    server_version='KanjiN2Local/1.0'

    def send_bytes(self,status,data,content_type):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers();self.wfile.write(data)

    def send_json(self,status,data):self.send_bytes(status,json.dumps(data,ensure_ascii=False).encode(),'application/json; charset=utf-8')

    def do_GET(self):
        url=urlsplit(self.path)
        if url.path=='/api/status':return self.send_json(200,self.server.service.status())
        # Only explicit assets; never expose corpus, runtime paths or filesystem traversal.
        assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if url.path in assets:
            path=ROOT/'ui'/assets[url.path]
            mime=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
            return self.send_bytes(200,path.read_bytes(),mime+'; charset=utf-8')
        if url.path=='/source.pdf':
            pdf=ROOT/'data/raw/KANJI N2.pdf'
            if not pdf.exists():return self.send_json(404,{'error':'Không tìm thấy PDF nguồn.'})
            # Stream the one authorized source file; browsers can navigate with #page=N.
            self.send_response(200);self.send_header('Content-Type','application/pdf')
            self.send_header('Content-Length',str(pdf.stat().st_size));self.send_header('Cache-Control','private, no-store')
            self.send_header('Content-Disposition','inline; filename="KANJI-N2.pdf"');self.end_headers()
            try:
                with pdf.open('rb') as f:
                    while block:=f.read(256*1024):self.wfile.write(block)
            except (BrokenPipeError,ConnectionResetError):pass
            return
        return self.send_json(404,{'error':'Không tìm thấy đường dẫn.'})

    def do_POST(self):
        # Reject other origins; loopback alone does not stop a hostile site from posting to localhost.
        origin=self.headers.get('Origin')
        if origin and origin!=f'http://{self.headers.get("Host")}':return self.send_json(403,{'error':'Chỉ chấp nhận thao tác từ UI local.'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send_json(415,{'error':'Cần dữ liệu JSON.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=2_000_000:raise ValueError('Yêu cầu quá lớn hoặc rỗng.')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError('Nội dung JSON phải là object.')
            if self.path=='/api/recognize':result=self.server.service.recognize(data)
            elif self.path=='/api/search':result=self.server.service.lookup(data)
            else:return self.send_json(404,{'error':'Không tìm thấy API.'})
            self.send_json(200,result)
        except (ValueError,TypeError,KeyError) as exc:self.send_json(400,{'error':str(exc)})
        except RuntimeError as exc:self.send_json(503,{'error':str(exc)})
        except Exception:
            traceback.print_exc();self.send_json(500,{'error':'Có lỗi xử lý. Xem log server để kiểm tra.'})

    def log_message(self,format,*args):
        # Do not persist search questions or handwriting.
        if args and str(args[1] if len(args)>1 else '').startswith('5'):super().log_message(format,*args)


def main():
    parser=argparse.ArgumentParser(description='Kanji N2 local UI')
    parser.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    service=Service()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.service=service
    print(f'Kanji N2 UI: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close()
        with service.lock:
            if service.client:service.client.close()

if __name__=='__main__':main()
