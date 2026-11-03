from pathlib import Path
import os,sys,json,hashlib
sys.dont_write_bytecode=True
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from paths import PACKAGE, DATA, INPUTS, METADATA, REFERENCE, SPATIAL_INPUTS, SPATIAL_METADATA, SPATIAL_REFERENCE
ROOT=Path(os.environ.get("RICE_REPRO_OUTPUT",str(PACKAGE/'results/runs/ad-hoc'))).resolve()
os.environ['MPLCONFIGDIR']=str(ROOT/'diagnostics/mplconfig')
import numpy as np
import pandas as pd
TARGET='shoot_length_cm'
ID='파일명'
FEATURES=['start', 'end', 'complexity', 'mean_R', 'mean_G', 'mean_B', 'r', 'g', 'b', 'GB', 'BG', 'RB', 'BR', 'GR', 'RGRI', 'NDRBI', 'NGBDI', 'NGRDI', 'WI', 'KI', 'SRrgb', 'NDI', 'IPCA', 'IPCAS', 'GLI', 'MGRVI', 'RGBVI', 'VEG', 'TCVI', 'VARI', 'VARIs', 'COM', 'ChOL_log_sig', 'SAVIgreen', 'OSAVIgreen', 'EVIgreen', 'EVI2green']
def read(path):return pd.read_csv(path,float_precision='round_trip',dtype={'site_date':str})
def csv(frame,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not isinstance(frame,pd.DataFrame):frame=pd.DataFrame(frame)
    content=frame.to_csv(index=False,float_format='%.17g',na_rep='NA').encode('utf-8-sig')
    if path.exists():
        assert path.read_bytes()==content, 'Refusing to overwrite differing result: '+str(path)
    else:path.write_bytes(content)
def js(obj,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)
    if path.exists():assert path.read_text(encoding='utf-8')==content, 'Refusing to overwrite differing result: '+str(path)
    else:path.write_text(content,encoding='utf-8')
def images(strips):
    out=strips.groupby(['Region',ID,'site_date'],as_index=False,sort=True).agg({**dict.fromkeys(FEATURES,'mean'),TARGET:'first'})
    assert len(out)==92 and out.groupby(['Region','site_date']).ngroups==33
    return out
def metrics(y,p,weights=None):
    y=np.asarray(y,float);p=np.asarray(p,float);w=np.ones(len(y)) if weights is None else np.asarray(weights,float)
    assert np.isfinite(y).all() and np.isfinite(p).all() and np.isfinite(w).all() and (w>0).all()
    error=p-y;mse=np.average(error**2,weights=w);sst=np.sum(w*(y-np.average(y,weights=w))**2)
    return dict(n=len(y),R2=float(1-np.sum(w*error**2)/sst) if sst>0 else None,RMSE=float(np.sqrt(mse)),MAE=float(np.average(abs(error),weights=w)),mean_signed_error=float(np.average(error,weights=w)))
