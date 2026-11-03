"""All 37 predictors, manuscript Ridge solver and alpha/tie rule; no feature selection."""
from common import *
import itertools,time
from image_ml_baseline_analysis import fit_ridge as archived_fit_ridge
CASES=['raw','otsu','continuous'];ALPHAS=np.array([.01,.1,1.,10.,100.])
def fit_path(train):
    raw=train[FEATURES].to_numpy(dtype=float);y=train[TARGET].to_numpy(dtype=float)
    mean=raw.mean(0);sd=raw.std(0);sd[sd==0]=1
    design=np.column_stack([np.ones(len(raw)),(raw-mean)/sd]);coefs=[];gap=[]
    for alpha in ALPHAS:
        penalty=np.eye(len(FEATURES)+1)*alpha;penalty[0,0]=0
        beta=np.linalg.pinv(design.T@design+penalty)@design.T@y
        # Verify against the unmodified actual baseline implementation, training only.
        oracle=archived_fit_ridge(raw,y,raw,alpha)
        assert np.allclose(design@beta,oracle,rtol=0,atol=1e-12)
        coefs.append(beta)
        gap.append(float(np.max(abs((design.T@design+penalty)@beta-design.T@y))))
    return dict(mean=mean,sd=sd,coefs=np.asarray(coefs),alphas=ALPHAS,n_training=np.array(len(train)),normal_equation_residual=np.asarray(gap))
def predict(path,frame):
    x=(frame[FEATURES].to_numpy()-path['mean'])/path['sd']
    return np.column_stack([np.ones(len(frame)),x])@path['coefs'].T
def as_images(frame,predictions):
    temp=frame[['Region',ID,'site_date',TARGET]].copy()
    cols=[f'alpha_{i}' for i in range(len(ALPHAS))]
    temp[cols]=predictions
    return temp.groupby(['Region',ID,'site_date'],sort=True,as_index=False).agg({TARGET:'first',**dict.fromkeys(cols,'mean')})
def run(case,mode):
    folder=ROOT/'ridge'/mode/case;folder.mkdir(parents=True,exist_ok=True);cache=folder/'cache';cache.mkdir(exist_ok=True)
    if (folder/'pooled_metrics.csv').exists():return
    strips=read(ROOT/'inputs'/f'features_{case}.csv')
    unit=images(strips) if mode=='image' else strips
    csv(unit,folder/'training_units.csv');regions=sorted(unit.Region.unique());paths={};meta=[]
    for size in [7,8]:
        for ids in itertools.combinations(range(9),size):
            mask=sum(1<<i for i in ids);names=[regions[i] for i in ids];train=unit[unit.Region.isin(names)]
            p=fit_path(train);paths[mask]=p
            np.savez_compressed(cache/f'{mask:03d}.npz',**p)
            row=dict(mask=mask,training_regions=names,n_training_units=len(train),n_training_images=train.groupby(['Region',ID]).ngroups,unit=mode,all_37_features=FEATURES,intercept_penalized=False)
            js(row,cache/f'{mask:03d}.json');meta.append(row)
    records=[];folds=[];curves=[];boundaries=[];models=[];strip_preds=[];inner_preds=[]
    for held,region in enumerate(regions):
        outer=511^(1<<held);parts=[]
        for inner,ir in enumerate(regions):
            if inner==held:continue
            mask=outer^(1<<inner);path=paths[mask];test=unit[unit.Region==ir]
            prediction=predict(path,test);part=as_images(test,prediction)
            parts.append(part);inner_preds.append(part.assign(held_region=region,inner_validation_region=ir,training_mask=mask))
            names=[regions[j] for j in range(9) if mask&(1<<j)]
            assert region not in names and ir not in names
            boundaries.append(dict(held_region=region,inner_validation_region=ir,training_mask=mask,training_regions=';'.join(names),n_training_units=int(paths[mask]['n_training']),n_validation_images=len(part),held_excluded=True,inner_validation_excluded=True))
        inner_df=pd.concat(parts,ignore_index=True);scores=[];best=None;index=0
        for j,alpha in enumerate(ALPHAS):
            score=metrics(inner_df[TARGET],inner_df[f'alpha_{j}'])['RMSE'];scores.append(score)
            if best is None or score<best:best=score;index=j
        for j,alpha in enumerate(ALPHAS):curves.append(dict(held_region=region,alpha=float(alpha),inner_pooled_image_RMSE=scores[j],selected=j==index))
        path=paths[outer];test=unit[unit.Region==region];predictions=predict(path,test)
        allim=as_images(test,predictions);part=allim[['Region',ID,'site_date',TARGET]].copy();part['prediction']=allim[f'alpha_{index}']
        part['error']=part.prediction-part[TARGET];part['abs_error']=abs(part.error);records.append(part)
        if mode=='strip':
            st=test[['Region',ID,'site_date',TARGET]].copy();st['prediction']=predictions[:,index];strip_preds.append(st)
        folds.append(dict(case=case,unit=mode,held_region=region,selected_alpha=float(ALPHAS[index]),n_training_units=int(path['n_training']),n_validation_images=len(inner_df),n_test_images=len(part),inner_RMSE=float(best),n_features=len(FEATURES),exact_tie_count=int(np.sum(np.asarray(scores)==best))))
        models.append(dict(held_region=region,selected_alpha=float(ALPHAS[index]),training_regions=[r for r in regions if r!=region],mean=path['mean'].tolist(),sd=path['sd'].tolist(),coefficients=path['coefs'][index].tolist(),features=FEATURES,training_unit=mode,n_training_units=int(path['n_training'])))
    d=pd.concat(records,ignore_index=True)
    csv(d,folder/'oof_predictions.csv');csv(folds,folder/'fold_results.csv');csv(curves,folder/'inner_cv_curves.csv');csv(boundaries,folder/'fold_boundary_audit.csv')
    csv(pd.concat(inner_preds,ignore_index=True),folder/'inner_validation_predictions.csv');js(models,folder/'fold_models.json')
    if strip_preds:csv(pd.concat(strip_preds,ignore_index=True),folder/'strip_predictions.csv')
    csv([dict(case=case,unit=mode,**metrics(d[TARGET],d.prediction))],folder/'pooled_metrics.csv')
    csv([dict(region=r,**metrics(g[TARGET],g.prediction)) for r,g in d.groupby('Region')],folder/'region_metrics.csv')
    csv([dict(site_date=r,**metrics(g[TARGET],g.prediction)) for r,g in d.groupby('site_date')],folder/'date_metrics.csv')
    print('Ridge',mode,case,metrics(d[TARGET],d.prediction),'alphas',[r['selected_alpha'] for r in folds],flush=True)
if __name__=='__main__':
    for mode in ['image','strip']:
        for case in CASES:run(case,mode)

