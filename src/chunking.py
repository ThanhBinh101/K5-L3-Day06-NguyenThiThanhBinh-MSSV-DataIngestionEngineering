import hashlib
from .common import SOURCE


def chunk_entries(entries, strategy, config):
    chunks = []
    for entry in entries:
        text = entry['text']
        if config['chunking'] == 'whole_kanji_entry':
            spans = [(0, len(text))]
        else:
            size, overlap = config['size'], config['overlap']
            if not 0 <= overlap < size:
                raise ValueError('Require 0 <= overlap < size')
            spans = []
            start = 0
            while start < len(text):
                end = min(start+size, len(text))
                spans.append((start,end))
                if end == len(text):
                    break
                start += size-overlap
        for index,(start,end) in enumerate(spans):
            part = text[start:end]
            identity = f'{SOURCE}:{strategy}:{entry["page"]}:{index}:{hashlib.sha256(part.encode()).hexdigest()[:12]}'
            chunks.append({'id':identity,'text':part,'start':start,'end':end,
                **{k:entry[k] for k in ['document_id','source','page','lesson','kanji','han_viet']}})
    return chunks
