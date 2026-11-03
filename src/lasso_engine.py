"""Name-blind Lasso paths and training-only scaling; no reference-set knowledge."""
import os
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[variable]='1'
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
import hashlib
import itertools
import json
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import lars_path_gram

ALPHAS=np.logspace(-4,1,200)[::-1]
NONZERO=1e-8
TIE=1e-10
Y='shoot_length_cm'

def mask_for(ids):return sum(1<<int(i) for i in ids)


def audit(x,y,betas,alphas=ALPHAS):
    residual=y[:,None]-x@betas.T;rss=np.mean(residual**2,axis=0)
    grad=(x.T@residual/len(y)).T
    scale=np.minimum(1,alphas/np.maximum(abs(grad).max(1),np.finfo(float).tiny))
    primal=.5*rss+alphas*np.sum(abs(betas),axis=1)
    dual=scale*(residual.T@y/len(y))-.5*scale**2*rss
    gap=primal-dual
    kkt=np.where(abs(betas)>NONZERO,abs(grad-alphas[:,None]*np.sign(betas)),np.maximum(abs(grad)-alphas[:,None],0)).max(1)
    tolerance=1e-8*np.mean(y*y)
    good=(gap>=-1e-8)&(gap<=tolerance)&np.isfinite(betas).all(1)
    return gap,kkt,good,tolerance

def qr_active_path(x,y):
    n,p=x.shape;q=x.T@y/n;beta=np.zeros(p);signs=np.zeros(p);rows=[]
    for alpha in ALPHAS:
        for iteration in range(10000):
            active=np.flatnonzero(signs)
            if len(active):
                Q,R=np.linalg.qr(x[:,active],mode='reduced')
                target=np.linalg.solve(R,Q.T@y-np.linalg.solve(R.T,n*alpha*signs[active]))
                crossing=target*signs[active]<=0
                if crossing.any():
                    ratios=beta[active][crossing]/(beta[active][crossing]-target[crossing]);step=float(np.clip(ratios.min(),0,1))
                    beta[active]+=step*(target-beta[active]);drop=active[crossing][ratios<=step+1e-12]
                    beta[drop]=0;signs[drop]=0;continue
                beta[active]=target
            gradient=x.T@(y-x@beta)/n
            violation=np.where(signs==0,abs(gradient)-alpha,-np.inf);j=int(np.argmax(violation))
            if violation[j]<=1e-12*(1+abs(q).max()):break
            signs[j]=np.sign(gradient[j])
        else:raise RuntimeError('QR active-set repair failed')
        rows.append(beta.copy())
    return np.array(rows)

def solve(x,y):
    # All distinct candidates remain eligible. Exact aliases use column-order ties.
    keep=[];aliases={}
    for j in range(x.shape[1]):
        prior=next((k for k in keep if np.array_equal(x[:,j],x[:,k])),None)
        if prior is None:keep.append(j)
        else:aliases[j]=prior
    xx=np.asfortranarray(x[:,keep]);started=time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        knots,_,coef=lars_path_gram(xx.T@y,xx.T@xx,n_samples=len(y),alpha_min=ALPHAS[-1],method='lasso',max_iter=5000,eps=np.finfo(float).eps)
    beta=np.zeros((len(ALPHAS),x.shape[1]))
    beta[:,keep]=np.stack([np.interp(ALPHAS,knots[::-1],row[::-1],left=row[-1],right=0) for row in coef],axis=1)
    solver=np.full(len(ALPHAS),'LARS_interpolation',dtype='U30')
    gap,kkt,good,tolerance=audit(x,y,beta)
    logs=[dict(stage='LARS_warning',message=str(w.message)) for w in caught]
    if not good.all():
        replacement=np.zeros_like(beta);replacement[:,keep]=qr_active_path(xx,y)
        _,_,accepted,_=audit(x,y,replacement);use=(~good)&accepted
        beta[use]=replacement[use];solver[use]='signed_active_QR'
        logs.append(dict(stage='QR_equivalent_repair',n_repaired=int(use.sum())))
        gap,kkt,good,tolerance=audit(x,y,beta)
    if not good.all():raise RuntimeError(f'Failed numerical audit: {ALPHAS[~good].tolist()}')
    path_betas=np.zeros((len(knots),x.shape[1]));path_betas[:,keep]=coef.T
    return dict(betas=beta,solver=solver,dual_gap=gap,kkt=kkt,tolerance=tolerance,aliases=aliases,logs=logs,seconds=time.perf_counter()-started,
                path_alphas=knots,path_betas=path_betas)



def curve(sse,counts):
    total=sse.sum(0);N=sum(counts);rmse=np.sqrt(total/N);G=len(counts)
    best=int(np.flatnonzero(rmse<=rmse.min()+TIE)[0])
    deleted=np.sqrt(np.maximum(total[None,:]-sse,0)/(N-np.asarray(counts)[:,None]))
    se=np.sqrt((G-1)/G*np.sum((deleted-deleted.mean(0))**2,axis=0))
    return rmse,se,best

