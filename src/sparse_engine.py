"""Image-level penalized fits and training-only information criteria; no reference names."""
from lasso_engine import *
import math

IC_TIE=1e-10


def prep(train,names):
    raw=train[names].to_numpy();mean=raw.mean(0);sd=raw.std(0);sd=np.where(sd>0,sd,1)
    ymean=float(train[Y].mean());return np.asfortranarray((raw-mean)/sd),train[Y].to_numpy()-ymean,mean,sd,ymean

def weighted_audit(x,y,beta,weights):
    residual=y[:,None]-x@beta.T;rss=np.mean(residual**2,axis=0);grad=(x.T@residual/len(y)).T
    pen=ALPHAS[:,None]*weights
    scale=np.minimum(1,np.min(pen/np.maximum(abs(grad),np.finfo(float).tiny),axis=1))
    primal=.5*rss+np.sum(pen*abs(beta),axis=1)
    dual=scale*(residual.T@y/len(y))-.5*scale**2*rss;gap=primal-dual
    kkt=np.where(abs(beta)>NONZERO,abs(grad-pen*np.sign(beta)),np.maximum(abs(grad)-pen,0)).max(1)
    tol=1e-8*np.mean(y*y);good=(gap>=-1e-8)&(gap<=tol)&np.isfinite(beta).all(1)
    return gap,kkt,good,tol

def fit(train,names,mask,gamma=None):
    key='lasso' if gamma is None else f'adaptive_{gamma:g}';folder=ROOT/'cache'/key;folder.mkdir(exist_ok=True)
    path=folder/f'{mask:03d}.npz'
    if path.exists() and path.with_suffix('.json').exists():
        with np.load(path) as z:return {k:z[k] for k in z.files}
    x,y,mean,sd,ymean=prep(train,names);n,p=x.shape
    initial=np.linalg.solve(x.T@x/n+np.eye(p),x.T@y/n)
    weights=np.ones(p) if gamma is None else 1/(abs(initial)+1e-8)**gamma
    keep=[];aliases={}
    for j in range(p):
        prior=next((k for k in keep if np.array_equal(x[:,j],x[:,k])),None)
        if prior is None:keep.append(j)
        else:
            assert np.isclose(weights[j],weights[prior],rtol=1e-10,atol=1e-12)
            aliases[j]=prior
    transformed=np.asfortranarray(x[:,keep]/weights[keep]);result=solve(transformed,y)
    beta=np.zeros((len(ALPHAS),p));beta[:,keep]=result['betas']/weights[keep]
    gap,kkt,good,tolerance=weighted_audit(x,y,beta,weights);assert good.all(),(key,mask,ALPHAS[~good])
    arrays=dict(betas=beta,mean=mean,sd=sd,ymean=ymean,ridge_initial=initial,weights=weights,alphas=ALPHAS,
                dual_gap=gap,kkt=kkt,solver=result['solver'])
    np.savez_compressed(path,**arrays)
    record=dict(method=key,gamma=gamma,training_mask=mask,training_regions=sorted(train.Region.unique()),n_images=n,
                initial_ridge_penalty_normalized=1,adaptive_weight_normalization='none',alias_indices=aliases,
                gap_tolerance=tolerance,all_200_verified=True,solver_events=result['logs'])
    path.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    return arrays

def select_lambda(rmse,se,rule):
    minimum=rmse.min();best=int(np.flatnonzero(rmse<=minimum+TIE)[0]);limit=float(minimum+(se[best] if rule=='L2' else 0))
    chosen=int(np.flatnonzero(rmse<=limit+TIE)[0])
    return chosen,dict(minimum_inner_rmse_cm=float(minimum),se_at_minimum_cm=float(se[best]),inner_selection_limit_cm=limit,selected_inner_rmse_cm=float(rmse[chosen]))

class ICScorer:
    def __init__(self,train,names,region):
        self.x,self.y,self.mean,self.sd,self.ymean=prep(train,names)
        self.names=names;self.region=region;self.cache={};self.rows=[];self.coef_rows=[]
    def score(self,subset):
        key=tuple(sorted(subset))
        if key in self.cache:return self.cache[key]
        n=len(self.y);q=len(key);design=np.column_stack([np.ones(n),self.x[:,key]])
        coefficient,_,rank,singular=np.linalg.lstsq(design,self.y+self.ymean,rcond=1e-10)
        residual=self.y+self.ymean-design@coefficient;rss=float(residual@residual)
        logloss=n*np.log(max(rss,np.finfo(float).tiny)/n);bic=float(logloss+(q+1)*np.log(n));K=q+2
        aicc=float(logloss+2*K+2*K*(K+1)/(n-K-1)) if n-K-1>0 else np.inf
        lc=math.lgamma(len(self.names)+1)-math.lgamma(q+1)-math.lgamma(len(self.names)+1-q)
        row=dict(outer_test_region=self.region,model_id=len(self.cache)+1,selected_indices=';'.join(map(str,key)),selected_features=';'.join(self.names[j] for j in key),
                 n_images=n,n_predictors=q,training_RSS=rss,BIC=bic,AICc=aicc,log_choose_p_q=lc,ols_design_rank=int(rank),
                 ols_condition_number=float(singular[0]/singular[-1]),rank_deficient=rank<q+1,rss_log_floor_used=rss==0)
        self.cache[key]=row;self.rows.append(row)
        self.coef_rows.append(dict(outer_test_region=self.region,model_id=row['model_id'],feature='intercept',coefficient=float(coefficient[0])))
        for j,b in zip(key,coefficient[1:]):self.coef_rows.append(dict(outer_test_region=self.region,model_id=row['model_id'],feature=self.names[j],coefficient=float(b)))
        return row

def criterion(row,kind,gamma=None):
    return row['BIC']+2*gamma*row['log_choose_p_q'] if kind=='EBIC' else row[kind]

def backward(scorer,initial,kind,gamma,sid):
    current=tuple(sorted(initial));removed=[];history=[];iteration=0
    row=scorer.score(current);score=criterion(row,kind,gamma)
    history.append(dict(setting_id=sid,outer_test_region=scorer.region,step=0,row_type='initial',current_features=row['selected_features'],current_score=score,accepted=True))
    while len(current)>1:
        iteration+=1;proposals=[]
        for j in current:
            child=tuple(k for k in current if k!=j);info=scorer.score(child);value=criterion(info,kind,gamma)
            proposals.append((value,j,child,info))
        minimum=min(p[0] for p in proposals);best=min((p for p in proposals if p[0]<=minimum+IC_TIE),key=lambda p:p[1])
        improves=best[0]<score-IC_TIE
        for value,j,child,info in proposals:
            history.append(dict(setting_id=sid,outer_test_region=scorer.region,step=iteration,row_type='candidate_deletion',current_features=row['selected_features'],
                                removed_feature=scorer.names[j],candidate_features=info['selected_features'],current_score=score,candidate_score=value,
                                criterion_decrease=score-value,accepted=improves and j==best[1],candidate_model_id=info['model_id']))
        if not improves:break
        score,j,current,row=best;removed.append(j)
    history.append(dict(setting_id=sid,outer_test_region=scorer.region,step=iteration,row_type='stop',current_features=row['selected_features'],current_score=score,
                        accepted=False,stop_reason='one_or_fewer_candidates' if len(current)<=1 else 'no_strict_criterion_decrease'))
    return current,row,removed,history
