"""Step 01: decode RGB, calculate clipped ExG, and construct three representations."""
from pathlib import Path
import numpy as np
import cv2

def imread(path):
    out=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_COLOR)
    if out is None:raise ValueError('Unreadable image '+str(path))
    return cv2.cvtColor(out,cv2.COLOR_BGR2RGB)

def preprocess(raw):
    raw16=raw.astype(np.int16)
    exg=np.clip(2*raw16[:,:,1]-raw16[:,:,0]-raw16[:,:,2],0,255).astype(np.uint8)
    weight=exg.astype(np.float32)/255.0
    continuous=(raw.astype(np.float32)*weight[:,:,None]).clip(0,255).astype(np.uint8)
    threshold,mask=cv2.threshold(exg,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    otsu=raw*(mask[:,:,None]//255)
    return dict(raw=raw,exg=exg,weight=weight,continuous=continuous,otsu=otsu,otsu_threshold=threshold)

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True,help='Optional inspection output: compressed NPZ for one image')
    a=p.parse_args()
    from _common import check_runtime
    check_runtime('pixels')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('xb') as stream:np.savez_compressed(stream,**preprocess(imread(a.image)))
    print('Preprocessing complete:',a.out)
