"""Step 03: regenerate all five 37-feature matrices directly from images and labels."""
from _common import *
import cv2, time
from step01_preprocessing import imread, preprocess
from step02_strip_detection import partition
from _data import load_ground_truth, check_images

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

def extract(images_root,ground_truth,output):
    runtime=check_runtime('pixels')
    output=Path(output).resolve()
    if output.exists():raise FileExistsError('Choose a new feature output directory: '+str(output))
    labels=load_ground_truth(ground_truth)
    check_images(images_root,labels)
    output.mkdir(parents=True)
    cases=['raw','otsu','continuous','matched','full']
    frames={c:[] for c in cases};extra=[];coords=[];started=time.time()
    for i,entry in enumerate(sorted(labels,key=lambda r:(r['region'],r['image_id'])),1):
        region=entry['region'];name=entry['image_id']
        raw=imread(Path(images_root)/entry['filename']);h,w=raw.shape[:2]
        assert (h,w)==(int(entry['height']),int(entry['width']))
        rep=preprocess(raw);parts=partition(rep['exg'])
        meta=dict(Region=region,**{ID:name},site_date=entry['acquisition_date'].replace('-',''),shoot_length_cm=float(entry['shoot_length_cm']))
        for order,(a,b) in enumerate(parts['adaptive']):
            coords.append({**meta,'strip_order':order,'x1':int(a),'x2':int(b),'width':w,'height':h})
        for case in cases:
            rgb=rep[case] if case in ['raw','otsu'] else rep['continuous']
            intervals=parts[case] if case in ['matched','full'] else parts['adaptive']
            for a,b in intervals:
                v,_=features(rgb[:,a:b],a,b,w)
                frames[case].append({**meta,**{f:v[f] for f in FEATURES}})
                if case=='continuous':extra.append({**meta,'NExGR':v['NExGR']})
        print(f'Features {i}/{len(labels)}; elapsed {time.time()-started:.1f}s',flush=True)
    for case in cases:
        frame=pd.DataFrame(frames[case])[['Region',ID,'site_date']+FEATURES+[TARGET]]
        validate_features(frame);csv(frame,output/f'features_{case}.csv')
    csv(pd.DataFrame(extra)[['Region',ID,'site_date','NExGR',TARGET]],output/'fixed_baseline_NExGR_continuous.csv')
    csv(pd.DataFrame(coords)[['Region',ID,'site_date','strip_order','x1','x2','width','height',TARGET]],output/'retained_strip_coordinates.csv')
    js(dict(images=len(labels),regions=9,site_dates=33,strips=552,features=37,cases=cases,runtime=runtime,seconds=time.time()-started),output/'extraction.json')

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--images',type=Path,default=PACKAGE/'data/images')
    p.add_argument('--ground-truth',type=Path,default=PACKAGE/'data/ground_truth.csv')
    p.add_argument('--out',type=Path,required=True,help='Fresh directory, usually <analysis output>/inputs')
    a=p.parse_args();extract(a.images,a.ground_truth,a.out)
