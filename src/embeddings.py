import os
from .common import ROOT


def setup_cache():
    os.environ.setdefault('HF_HOME',str(ROOT / '.local/huggingface'))
    os.environ.setdefault('HF_HUB_DISABLE_XET','1')
    os.environ.setdefault('TOKENIZERS_PARALLELISM','false')


def load_model(config, offline=False):
    setup_cache()
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4)
    torch.manual_seed(0)
    path = ROOT / '.local/model'
    model = SentenceTransformer(str(path) if path.exists() else config['model'],device=config['device'],local_files_only=offline)
    model.max_seq_length = config['max_tokens']
    return model


def encode(model,texts,prefix,batch_size=16):
    return model.encode([prefix+t for t in texts],batch_size=batch_size,normalize_embeddings=True,
                        show_progress_bar=True,convert_to_numpy=True)
