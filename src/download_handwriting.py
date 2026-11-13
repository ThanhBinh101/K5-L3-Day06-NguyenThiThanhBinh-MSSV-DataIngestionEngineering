"""Fetch KanjiVG stroke references. Derived samples retain CC BY-SA 3.0 attribution."""
import io
import ssl
import certifi
import json
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from .common import ROOT,read_json,read_jsonl,write_json,now


def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'KanjiN2-Lab/1.0'})
    with urllib.request.urlopen(req,timeout=120,context=ssl.create_default_context(cafile=certifi.where())) as response:
        return response.read()


def main():
    from svgpathtools import parse_path
    snapshot=ROOT/'artifacts/kanjivg_snapshot.json'
    revision=read_json(snapshot)['revision'] if snapshot.exists() else json.loads(get('https://api.github.com/repos/KanjiVG/kanjivg/commits/master'))['sha']
    archive=zipfile.ZipFile(io.BytesIO(get(f'https://codeload.github.com/KanjiVG/kanjivg/zip/{revision}')))
    entries=read_jsonl(ROOT/'data/processed/entries.jsonl')
    prefix=archive.namelist()[0]
    rows=[];missing=[]
    for entry in entries:
        name=f'{ord(entry["kanji"]):05x}.svg'
        try: xml=archive.read(prefix+'kanji/'+name)
        except KeyError:missing.append(entry['kanji']);continue
        doc=ET.fromstring(xml)
        strokes=[]
        for node in doc.iter('{http://www.w3.org/2000/svg}path'):
            if '-s' not in node.attrib.get('id',''):continue
            path=parse_path(node.attrib['d'])
            # Uniform samples along SVG path parameter; rasterization densifies segments later.
            points=[]
            for i in range(48):
                point=path.point(i/47)
                points.append([round(point.real,3),round(point.imag,3)])
            strokes.append(points)
        if not strokes:raise ValueError(f'No strokes for {name}')
        rows.append({'kanji':entry['kanji'],'strokes':strokes})
    write_json(ROOT/'data/handwriting/templates.json',{'attribution':'KanjiVG © Ulrich Apel and contributors',
        'license':'CC BY-SA 3.0','license_url':'https://creativecommons.org/licenses/by-sa/3.0/',
        'source':'https://github.com/KanjiVG/kanjivg','revision':revision,
        'modifications':'SVG stroke curves sampled to polylines, rounded to 3 decimals; limited to corpus characters.',
        'characters':rows})
    template_path=ROOT/'data/handwriting/templates.json'
    template_path.write_text(json.dumps(read_json(template_path),ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    write_json(snapshot,{'source':'https://github.com/KanjiVG/kanjivg','revision':revision,
        'downloaded_at':now(),'license':'CC BY-SA 3.0','characters':len(rows),'missing':missing})
    print(f'Prepared {len(rows)} KanjiVG templates; missing {missing}')

if __name__=='__main__':main()
