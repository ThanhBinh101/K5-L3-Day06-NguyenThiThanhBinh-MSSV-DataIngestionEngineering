"""Extract all pages; retain every Kanji study entry, not cover/TOC/practice grids."""
import logging
import re
import time
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from .common import ROOT, SOURCE, digest, norm, now, write_json, write_jsonl


def parse_entry(text, page):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    match = re.match(r'Bài\s+(\d+)\s*•\s*(\d+)/(\d+)', lines[0])
    if not match:
        raise ValueError(f'Page {page}: invalid lesson heading')
    on = lines.index('On yomi')
    kun = lines.index('Kun yomi')
    memory = lines.index('CÁCH NHỚ')
    practice = lines.index('LUYỆN VIẾT')
    words = lines.index('Ý NGHĨA') + 1
    raw_words = lines[words:]
    vocab = []
    while raw_words:
        m = re.match(r'(\d+)\.\s*(.+)', raw_words[0])
        if not m or len(raw_words) < 3:
            raise ValueError(f'Page {page}: malformed vocabulary {raw_words}')
        vocab.append({'word': m[2], 'reading': raw_words[1], 'meaning_vi': raw_words[2]})
        raw_words = raw_words[3:]
    expected = int(re.search(r'TỪ PHÁI SINH\s*•\s*(\d+) TỪ', text)[1])
    if len(vocab) != expected:
        raise ValueError(f'Page {page}: missing vocabulary')
    kanji, han_viet = lines[on - 1], lines[on - 2]
    if len(kanji) != 1:
        raise ValueError(f'Page {page}: invalid kanji {kanji}')
    record = dict(document_id=SOURCE, source='KANJI N2.pdf', page=page,
                  lesson=int(match[1]), entry_index=int(match[2]), kanji=kanji,
                  han_viet=han_viet, onyomi=norm(' '.join(lines[on + 1:kun])),
                  kunyomi=norm(' '.join(lines[kun + 1:memory])),
                  mnemonic=norm(' '.join(x for x in lines[memory + 1:practice] if x != '意味')),
                  vocabulary=vocab)
    record['text'] = '\n'.join([
        f'Bài {record["lesson"]:02d} | Kanji: {kanji} | Hán Việt: {han_viet}',
        f'Onyomi: {record["onyomi"]}', f'Kunyomi: {record["kunyomi"]}',
        f'Cách nhớ: {record["mnemonic"]}', 'Từ phái sinh:',
        *[f'{v["word"]} | {v["reading"]} | {v["meaning_vi"]}' for v in vocab]])
    return record


def ingest(pdf):
    started = time.perf_counter()
    pdf = Path(pdf).resolve()
    (ROOT / 'results').mkdir(exist_ok=True)
    handler = logging.FileHandler(ROOT / 'results/extraction_warnings.log', mode='w', encoding='utf-8')
    logging.getLogger('pypdf').addHandler(handler)
    pages, records, errors = [], [], []
    reader = PdfReader(pdf)
    for number, page in enumerate(reader.pages, 1):
        try:
            text = unicodedata.normalize('NFC', page.extract_text() or '')
            text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
            is_entry = 'On yomi' in text and 'TỪ PHÁI SINH' in text
            row = {'page': number, 'page_id': f'{SOURCE}:p{number:03}', 'text': text,
                   'normalized_char_count': len(norm(text)), 'included': is_entry,
                   'reason': 'kanji_entry' if is_entry else 'cover_toc_lesson_overview_or_notes'}
            if is_entry:
                records.append(parse_entry(text, number))
            if not text:
                errors.append({'page': number, 'error': 'empty_extraction'})
            pages.append(row)
        except Exception as exc:
            errors.append({'page': number, 'error': repr(exc)})
    write_jsonl(ROOT / 'data/processed/pages.jsonl', pages)
    write_jsonl(ROOT / 'data/processed/entries.jsonl', records)
    write_json(ROOT / 'results/extraction_errors.json', errors)
    included = [p for p in pages if p['included']]
    manifest = dict(source_id=SOURCE, title='KANJI N2 - Kaori Sensei', author_as_printed='Kaori Sensei',
        source_path_or_url='data/raw/KANJI N2.pdf', original_input=str(pdf), accessed_at=now(),
        sha256=digest(pdf), physical_pages=len(reader.pages), included_content_pages=len(included),
        counted_pages=[p['page'] for p in included], excluded_pages=[p['page'] for p in pages if not p['included']],
        page_count_rule='Count Kanji study pages with readings, mnemonic and vocabulary. Exclude cover, TOC, 16 lesson overviews and closing notes; blank writing cells add no pages.',
        license_or_permission={'processing':'Sensei authored the PDF; student confirmed on 2026-11-13 that sensei granted permission to use it for this lab and receive the lookup demo.',
            'redistribution':'Not verified; raw PDF and full corpus are ignored by Git. No public upload performed.',
            'attribution':'PDF p473 credits JMdict/EDRDG CC BY-SA 4.0 for vocabulary-derived data. This does not establish a license for the whole PDF.',
            'reference_urls':['https://www.edrdg.org/jmdict/j_jmdict.html','https://www.edrdg.org/edrdg/licence.html']},
        normalized_char_count=sum(p['normalized_char_count'] for p in included),
        page_units=[{k:p[k] for k in ['page_id','page','normalized_char_count','included','reason']} for p in pages],
        kanji_entries=len(records), vocabulary_entries=sum(len(r['vocabulary']) for r in records),
        extraction_seconds=round(time.perf_counter()-started,3), error_count=len(errors),
        warning_log='results/extraction_warnings.log', snapshot='SHA-256 of supplied PDF')
    write_json(ROOT / 'data/manifest.json', manifest)
    if errors or len(included) < 30:
        raise RuntimeError(f'Corpus validation failed: {len(errors)} errors, {len(included)} content pages')
    print(f'Extracted {len(records)} Kanji entries from {len(reader.pages)} pages', flush=True)
    return manifest
