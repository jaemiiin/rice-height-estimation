"""Step 02: ExG profiles, adaptive edge-six strips, and equal-width comparators."""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

def detect_boundaries(smoothed):
    max_peaks, _ = find_peaks(smoothed, prominence=0.02)
    min_peaks, _ = find_peaks(-smoothed, prominence=0.02)
    custom_min = list(min_peaks)

    if len(max_peaks) > 0 and (len(min_peaks) == 0 or max_peaks[0] < min_peaks[0]):
        for i in range(max_peaks[0]):
            if smoothed[i] >= 0.1:
                custom_min.append(i)
                break
    if len(max_peaks) > 0 and (len(min_peaks) == 0 or max_peaks[-1] > min_peaks[-1]):
        for i in range(len(smoothed) - 1, max_peaks[-1], -1):
            if smoothed[i] >= 0.1:
                custom_min.append(i)
                break
    return max_peaks, min_peaks, sorted(custom_min)

def partition(exg):
    w=exg.shape[1]
    col=exg.sum(axis=0).astype(float);col/=col.max()
    smoothed=gaussian_filter1d(col,sigma=20)
    _,_,bounds=detect_boundaries(smoothed)
    pairs=[(a,b) for a,b in zip(bounds[:-1],bounds[1:]) if max(abs(a-w/2),abs(b-w/2))/(w/2)!=1]
    adaptive=pairs[:3]+pairs[-3:]
    assert len(set(adaptive))==6, 'Six distinct usable strips are required'
    left=np.floor(np.linspace(adaptive[0][0],adaptive[2][1],4)).astype(int)
    right=np.floor(np.linspace(adaptive[3][0],adaptive[5][1],4)).astype(int)
    matched=list(zip(left[:-1],left[1:]))+list(zip(right[:-1],right[1:]))
    xx=np.floor(np.linspace(0,w,7)).astype(int);full=list(zip(xx[:-1],xx[1:]))
    assert sum(b-a for a,b in adaptive)==sum(b-a for a,b in matched)
    return dict(adaptive=adaptive,matched=matched,full=full,profile=col,smoothed=smoothed)

if __name__ == '__main__':
    import argparse, json
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preprocessed',type=Path,required=True,help='NPZ produced by step01')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    from _common import check_runtime
    check_runtime('pixels')
    with np.load(a.preprocessed,allow_pickle=False) as z:result=partition(z['exg'])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:
        json.dump({k:[[int(x),int(y)] for x,y in result[k]] for k in ['adaptive','matched','full']},f,indent=2)
    print('Strip detection complete:',a.out)
