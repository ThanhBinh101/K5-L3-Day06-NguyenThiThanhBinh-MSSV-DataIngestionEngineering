"""One search box: dictionary/Han-Viet, semantic meaning, or mnemonic description."""
import difflib
import re
import unicodedata
import uuid
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt
from qdrant_client import models
from .common import norm
from .embeddings import encode

MNEMONIC_COLLECTION='kanji_ui_mnemonics'


def vietnamese_key(text):
    text=unicodedata.normalize('NFD',norm(text).casefold()).replace('đ','d')
    return ''.join(c for c in text if unicodedata.category(c)!='Mn')


def han_viet_lookup(entries,query,lesson=None):
    q=vietnamese_key(query)
    if not q:return []
    exact=norm(query).casefold()
    rows=[]
    for e in entries:
        if lesson is not None and e['lesson']!=lesson:continue
        sounds=[norm(part).casefold() for part in re.split(r'[,/;・]',e['han_viet'])]
        if q in [vietnamese_key(sound) for sound in sounds]:
            rows.append({'entry':e,'match':'han_viet','score':None,'tone_match':exact in sounds})
    # Stable sorting preserves source order among equally matching pronunciations.
    return sorted(rows,key=lambda r:not r['tone_match'])



def exact_lookup(entries,query,lesson=None):
    q=norm(query).casefold();rows=[]
    for e in entries:
        if lesson is not None and e['lesson']!=lesson:continue
        words=[v for v in e['vocabulary'] if q in [v['word'].casefold(),v['reading'].casefold()]
               or (len(query)==1 and query in v['word'])]
        if query==e['kanji'] or words:
            rows.append({'entry':{**e,'vocabulary':words or e['vocabulary']},'match':'exact','score':None})
    return rows


_DESCRIPTION_STOPWORDS={'tim','tra','cuu','chu','kanji','giong','hinh','cach','meo','nho','mieu','ta','co','la','cua','mot','nhu','duoc','voi','va','o','ben','nao','gi','toi','muon'}

def description_tokens(text):
    return {w for w in re.findall(r'[a-z0-9]+',vietnamese_key(text)) if w not in _DESCRIPTION_STOPWORDS}


def source_text_matches(entries,query,kind,lesson=None):
    """Accent-insensitive matching of source meanings/mnemonics before dense fallback."""
    q=vietnamese_key(query)
    tokens=description_tokens(query)
    matches=[]
    for e in entries:
        if lesson is not None and e['lesson']!=lesson:continue
        fields=[e['mnemonic']] if kind=='mnemonic' else [v['meaning_vi'] for v in e['vocabulary']]
        best=0;canonical=None
        for text in fields:
            key=vietnamese_key(text)
            if re.search(r'(?<![a-z0-9])'+re.escape(q)+r'(?![a-z0-9])',key):
                score=3.0+(1 if norm(query).casefold() in norm(text).casefold() else 0)
            else:
                overlap=tokens & description_tokens(text)
                score=len(overlap)/len(tokens) if len(tokens)>=2 and len(overlap)>=2 else 0
                if score<.8:continue
            if score>best:best,canonical=score,text
        if best:matches.append((best,e,canonical))
    matches.sort(key=lambda r:-r[0])
    if not matches:return [],None
    cutoff=matches[0][0]-.25
    matches=[r for r in matches if r[0]>=cutoff]
    return [{'entry':e,'match':kind,'score':None} for _,e,_ in matches],matches[0][2]


def infer_kind(entries,query):
    if han_viet_lookup(entries,query):return 'han_viet'
    if re.fullmatch(r'[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff々ー\s]+',query):return 'kanji'
    key=vietnamese_key(query)
    cues=['goi nho','cach nho','meo nho','hinh dang','cau tao','giong hinh','bo thu','net viet','chu gom','chu co bo','chu nhin','co hinh','hinh chu','mieng','ben trai','ben phai','giong','chu co','tan la','nhin nhu']
    if any(cue in key for cue in cues):return 'mnemonic'
    if source_text_matches(entries,query,'semantic')[0]:return 'semantic'
    if source_text_matches(entries,query,'mnemonic')[0]:return 'mnemonic'
    return 'semantic'


def ensure_mnemonic_index(client,model,config,entries):
    import hashlib,json
    snapshot=hashlib.sha256(json.dumps([(e['kanji'],e['mnemonic']) for e in entries],ensure_ascii=False).encode()).hexdigest()
    if client.collection_exists(MNEMONIC_COLLECTION):
        sample,_=client.scroll(MNEMONIC_COLLECTION,limit=1,with_payload=True,with_vectors=False)
        if client.count(MNEMONIC_COLLECTION,exact=True).count==len(entries) and sample and sample[0].payload.get('snapshot')==snapshot:return
        client.delete_collection(MNEMONIC_COLLECTION)
    vectors=encode(model,[f'{e["kanji"]} — {e["mnemonic"]}' for e in entries],config['document_prefix'],config['batch_size'])
    client.create_collection(MNEMONIC_COLLECTION,vectors_config=models.VectorParams(size=config['dimensions'],distance=models.Distance.COSINE))
    for start in range(0,len(entries),64):
        client.upsert(MNEMONIC_COLLECTION,[models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL,f'ui-mnemonic:{e["page"]}:{snapshot}')),
            vector=vectors[i].tolist(),payload={'kanji':e['kanji'],'lesson':e['lesson'],'snapshot':snapshot})
            for i,e in enumerate(entries) if start<=i<start+64],wait=True)


@lru_cache(maxsize=1024)
def glyph_mask(char):
    paths=['/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
    font_path=next((p for p in paths if Path(p).exists()),None)
    if font_path is None:return None
    font=ImageFont.truetype(font_path,80)
    image=Image.new('L',(110,110),0);ImageDraw.Draw(image).text((8,0),char,font=font,fill=255)
    bbox=image.getbbox()
    if not bbox:return None
    crop=image.crop(bbox);crop.thumbnail((48,48))
    result=Image.new('L',(64,64),0);result.paste(crop,((64-crop.width)//2,(64-crop.height)//2))
    return np.asarray(result)>100


def similar_characters(entries,query,lesson=None,limit=6):
    if len(query)!=1:return []
    mask=glyph_mask(query)
    if mask is None:return []
    distance=distance_transform_edt(~mask);ranked=[]
    for e in entries:
        if e['kanji']==query or (lesson is not None and e['lesson']!=lesson):continue
        candidate=glyph_mask(e['kanji'])
        if candidate is None:continue
        loss=(distance[candidate].mean()+distance_transform_edt(~candidate)[mask].mean())/2
        ranked.append((float(loss),e))
    return [{'text':e['kanji'],'label':e['han_viet'],'kind':'similar_shape'} for _,e in sorted(ranked,key=lambda r:r[0])[:limit]]


def spelling_suggestions(entries,query,lesson=None):
    if len(query)==1:return similar_characters(entries,query,lesson)
    words=sorted({v['word'] for e in entries if lesson is None or e['lesson']==lesson for v in e['vocabulary']})
    return [{'text':w,'label':'Có trong tài liệu','kind':'spelling'}
            for w in difflib.get_close_matches(query,words,n=6,cutoff=.5) if w!=query]


def related_words(entries,query,lesson=None,limit=8):
    words=[];seen=set()
    for e in entries:
        if lesson is not None and e['lesson']!=lesson:continue
        for v in e['vocabulary']:
            if v['word']!=query and query in v['word'] and v['word'] not in seen:
                words.append({'text':v['word'],'label':v['meaning_vi'],'kind':'related_word'});seen.add(v['word'])
    return words[:limit]


def build_vietnamese_lexicon(entries):
    """Source-derived accent variants, not a hand-written mapping of test queries."""
    from collections import Counter,defaultdict
    lexicon=defaultdict(Counter)
    for entry in entries:
        for text in [entry['mnemonic']]+[v['meaning_vi'] for v in entry['vocabulary']]:
            for word in re.findall(r'[^\W\d_]+',norm(text).casefold()):
                key=vietnamese_key(word)
                if re.fullmatch('[a-z]+',key):lexicon[key][word]+=1
    return dict(lexicon)


def accented_query_variants(query,lexicon,limit=8):
    """Bounded beam of plausible spellings; preserve accents explicitly provided by the user."""
    import math
    parts=re.split(r'([^\W\d_]+)',norm(query).casefold())
    beam=[('',0.0)]
    for index,part in enumerate(parts):
        if index%2==0:
            beam=[(text+part,score) for text,score in beam];continue
        key=vietnamese_key(part)
        variants=lexicon.get(key)
        if part!=key or not variants:
            choices=[(part,1)]
        else:
            choices=variants.most_common(3)
        expanded=[(text+word,score+math.log1p(count)) for text,score in beam for word,count in choices]
        beam=sorted(expanded,key=lambda pair:-pair[1])[:limit]
    variants=list(dict.fromkeys(text for text,_ in beam))
    original=norm(query).casefold()
    if original not in variants:variants.append(original)
    return variants


def expanded_vector_search(client,model,config,query,kind,lesson,lexicon):
    """Retrieve for several source-derived accent variants, select a coherent result list."""
    from .store import search
    variants=accented_query_variants(query,lexicon)
    vectors=encode(model,variants,config['query_prefix'],config['batch_size'])
    filt=models.Filter(must=[models.FieldCondition(key='lesson',match=models.MatchValue(value=lesson))]) if lesson else None
    options=[]
    for text,vector in zip(variants,vectors,strict=True):
        if kind=='mnemonic':
            found=client.query_points(MNEMONIC_COLLECTION,query=vector.tolist(),query_filter=filt,limit=3,with_payload=True).points
            rows=[{'kanji':p.payload['kanji'],'score':float(p.score)} for p in found]
        else:
            found=search(client,'C',vector,{'lesson':lesson} if lesson else {})
            rows=[{'kanji':p['kanji'],'score':float(p['score'])} for p in found]
        # Use top match quality as a heuristic to choose between ambiguous accent restorations.
        strength=rows[0]['score'] if rows else -1
        options.append((strength,text,rows))
    _,selected,rows=max(options,key=lambda option:option[0])
    return rows,{'variant_count':len(variants),'selected_variant':selected,
                 'method':'Source-derived accent expansion; top similarity heuristic, not verified accent restoration.'}
