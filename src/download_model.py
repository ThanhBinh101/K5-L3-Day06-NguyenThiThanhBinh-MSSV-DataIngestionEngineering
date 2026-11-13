from .embeddings import setup_cache
from .common import ROOT,write_json,now,read_json

def main():
    setup_cache()
    from huggingface_hub import HfApi,snapshot_download
    name='intfloat/multilingual-e5-small'
    snapshot=ROOT / 'artifacts/model_snapshot.json'
    revision=read_json(snapshot)['revision'] if snapshot.exists() else HfApi().model_info(name).sha
    snapshot_download(name,revision=revision,local_dir=str(ROOT / '.local/model'),
        allow_patterns=['*.json','*.safetensors','*.model','*.txt','1_Pooling/*'],
        ignore_patterns=['onnx/*','openvino/*'])
    write_json(ROOT / 'artifacts/model_snapshot.json',{'model':name,'revision':revision,'downloaded_at':now(),'license':'MIT','dimensions':384})

if __name__=='__main__': main()
