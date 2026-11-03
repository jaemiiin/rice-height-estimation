"""Final pixel formulas and preprocessing; raw images remain external."""
from common import *
import cv2
from scipy.ndimage import gaussian_filter1d
from simplified_detector import detect_boundaries

def imread(path):
    out=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_COLOR)
    if out is None:raise ValueError('Unreadable image '+str(path))
    return cv2.cvtColor(out,cv2.COLOR_BGR2RGB)

def features(crop,x1,x2,width):
    # Color indices are always evaluated in float64, including powers and sums.
    B=crop[:,:,2].astype(float);G=crop[:,:,1].astype(float);R=crop[:,:,0].astype(float);S=R+G+B
    zeros={}
    def div(num,den,name):
        zeros[name]=int(np.count_nonzero(den==0))
        return np.divide(num,den,out=np.zeros_like(num,dtype=float),where=den!=0)
    r=div(R,S,'r');g=div(G,S,'g');b=div(B,S,'b')
    idx=dict(r=r,g=g,b=b,
        GB=div(G,B,'GB'),BG=div(B,G,'BG'),RB=div(R,B,'RB'),BR=div(B,R,'BR'),GR=div(G,R,'GR'),RGRI=div(R,G,'RGRI'),
        NDRBI=div(R-B,R+B,'NDRBI'),NGBDI=div(G-B,G+B,'NGBDI'),NGRDI=div(G-R,G+R,'NGRDI'),
        WI=div(G-B,abs(R-G),'WI'),KI=div(R,R-B,'KI'),SRrgb=div(R,G+B,'SRrgb'),NDI=div(r-g,r+g+0.01,'NDI'),
        IPCA=0.7582*abs(R-B)-0.1168*abs(R-G)+0.6414*abs(G-B),IPCAS=0.994*abs(R-B)+0.914*abs(G-R)+0.961*abs(G-B),
        NExGR=(2*g-r-b)-(1.4*r-g),GLI=div(2*G-R-B,2*G+R+B,'GLI'),MGRVI=div(G**2-R**2,G**2+R**2,'MGRVI'),
        RGBVI=div(G**2-R*B,G**2+R*B,'RGBVI'),VEG=div(G,(R**0.667)*(B**0.333),'VEG'),
        TCVI=div(1.4*2*(R-B),2*R-G-2*B+255*0.4,'TCVI'),VARI=div(G-R,G+R-B,'VARI'),VARIs=div(G-R,G+R,'VARIs'))
    idx['COM']=0.25*(2*g-r-b)+0.30*((2*g-r-b)-(1.4*r-g))+0.33*(0.441*R-0.811*G+0.385*B+18.78745)+0.12*idx['VEG']
    idx['ChOL_log_sig']=1/(1+np.exp(-(G-R/3-B/3)/255))
    gray=cv2.cvtColor(crop,cv2.COLOR_RGB2GRAY);sx=cv2.Sobel(gray,cv2.CV_64F,1,0,ksize=3);sy=cv2.Sobel(gray,cv2.CV_64F,0,1,ksize=3)
    complexity=np.hypot(sx,sy).sum()/(crop.shape[0]*crop.shape[1]+1e-8)
    start,end=sorted([abs(x1-width/2)/(width/2),abs(x2-width/2)/(width/2)])
    out=dict(start=start,end=end,complexity=complexity/255,mean_R=R.mean()/255,mean_G=G.mean()/255,mean_B=B.mean()/255)
    out.update({k:float(v.mean()) for k,v in idx.items()});out['IPCAS']/=255
    out['SAVIgreen']=float(div(1.5*(g-r),g+r+.5,'SAVIgreen').mean())
    out['OSAVIgreen']=float(div(1.5*(g-r),g+r+.16,'OSAVIgreen').mean())
    out['EVI2green']=float(div(2.5*(g-r),g+2.4*r+1,'EVI2green').mean())
    Ri=crop[:,:,0].astype(np.int32);Gi=crop[:,:,1].astype(np.int32);Bi=crop[:,:,2].astype(np.int32)
    D=14*Ri+4*Gi-13*Bi;numerator=5*(Gi-Ri)
    ev=div(numerator.astype(np.float64),D,'EVIgreen')
    assert (ev[D==0]==0).all() and np.isfinite(ev).all()
    out['EVIgreen']=float(ev.mean())
    assert set(out)==set(FEATURES)|{'NExGR'} and all(np.isfinite(x) for x in out.values())
    return out,zeros


def extract(raw_root, output, verify_only=False, limit=None):
    """Recreate all five final matrices, checking retained coordinates and hashes."""
    import time, platform
    output=Path(output).resolve()
    if output.exists():raise FileExistsError('Choose a new output directory: '+str(output))
    output.mkdir(parents=True)
    assert np.__version__=='1.26.4' and cv2.__version__=='4.11.0', 'Use the recorded pixel environment'
    raw_root=Path(raw_root)
    coords=read(METADATA/'retained_strip_coordinates.csv')
    manifest=read(METADATA/'raw_image_manifest.csv').set_index(['Region',ID])
    cases=['raw','otsu','continuous','matched','full']
    saved={c:read(INPUTS/f'features_{c}.csv') for c in cases}
    saved_extra=read(INPUTS/'fixed_baseline_NExGR_continuous.csv')
    frames={c:[] for c in cases};extra=[];checks=[];started=time.time()
    groups=list(coords.groupby(['Region',ID],sort=True))
    if limit is not None:groups=groups[:limit]
    for i,((region,name),group) in enumerate(groups,1):
        g=group.sort_values('strip_order');first=g.iloc[0];w=int(first.width)
        entry=manifest.loc[(region,name)];path=raw_root/entry.relative_path
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry.sha256, str(path)
        raw=imread(path);assert raw.shape==(int(first.height),w,3)
        raw16=raw.astype(np.int16)
        exg=np.clip(2*raw16[:,:,1]-raw16[:,:,0]-raw16[:,:,2],0,255).astype(np.uint8)
        weight=exg.astype(np.float32)/255.0
        continuous=(raw.astype(np.float32)*weight[:,:,None]).clip(0,255).astype(np.uint8)
        threshold,mask=cv2.threshold(exg,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        otsu=raw*(mask[:,:,None]//255)
        col=exg.sum(axis=0).astype(float);col/=col.max()
        _,_,bounds=detect_boundaries(gaussian_filter1d(col,sigma=20))
        pairs=[(a,b) for a,b in zip(bounds[:-1],bounds[1:]) if max(abs(a-w/2),abs(b-w/2))/(w/2)!=1]
        adaptive=pairs[:3]+pairs[-3:]
        assert len(set(adaptive))==6 and adaptive==list(zip(g.x1.astype(int),g.x2.astype(int)))
        left=np.floor(np.linspace(g.iloc[0].x1,g.iloc[2].x2,4)).astype(int)
        right=np.floor(np.linspace(g.iloc[3].x1,g.iloc[5].x2,4)).astype(int)
        matched=list(zip(left[:-1],left[1:]))+list(zip(right[:-1],right[1:]))
        xx=np.floor(np.linspace(0,w,7)).astype(int);full=list(zip(xx[:-1],xx[1:]))
        assert sum(b-a for a,b in adaptive)==sum(b-a for a,b in matched)
        for case in cases:
            rgb={'raw':raw,'otsu':otsu}.get(case,continuous)
            intervals=matched if case=='matched' else full if case=='full' else adaptive
            vals=[]
            for a,b in intervals:
                v,_=features(rgb[:,a:b],a,b,w)
                meta=dict(Region=region,**{ID:name},site_date=str(first.site_date),shoot_length_cm=float(first[TARGET]))
                row={**meta,**{f:v[f] for f in FEATURES}};vals.append([v[f] for f in FEATURES]);frames[case].append(row)
                if case=='continuous':extra.append({**meta,'NExGR':v['NExGR']})
            expected=saved[case][(saved[case].Region==region)&(saved[case][ID]==name)]
            delta=float(np.max(abs(np.array(vals)-expected[FEATURES].to_numpy())))
            assert delta==0,(case,region,name,delta)
            checks.append(dict(case=case,Region=region,image=name,max_abs_feature_difference=delta))
        print(f'Pixel verification {i}/{len(groups)}; elapsed {time.time()-started:.1f}s',flush=True)
    ex=pd.DataFrame(extra)
    keys=ex[['Region',ID]].drop_duplicates()
    expected=saved_extra.merge(keys,on=['Region',ID],how='inner',sort=False)
    assert np.array_equal(ex.NExGR,expected.NExGR)
    if not verify_only:
        if len(groups)!=92:raise ValueError('Full extraction requires all 92 images')
        for case in cases:csv(pd.DataFrame(frames[case])[['Region',ID,'site_date']+FEATURES+[TARGET]],output/f'features_{case}.csv')
        csv(ex[['Region',ID,'site_date','NExGR',TARGET]],output/'fixed_baseline_NExGR_continuous.csv')
    js(dict(images=len(groups),strips=len(groups)*6,cases=cases,features=37,all_features_bitwise_equal=True,all_coordinates_exact=True,raw_hashes_verified=True,NExGR_bitwise_equal=True,python=platform.python_version(),numpy=np.__version__,opencv=cv2.__version__,seconds=time.time()-started),output/'pixel_verification.json')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-root',required=True);p.add_argument('--out',required=True)
    p.add_argument('--verify-only',action='store_true');p.add_argument('--limit',type=int)
    a=p.parse_args();extract(a.raw_root,a.out,a.verify_only,a.limit)
