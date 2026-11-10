"""Step 07: all manuscript comparisons, post hoc references, and sensitivity analyses."""
from pathlib import Path
if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Analysis output root shared by steps 04-07')
    args = parser.parse_args()
    os.environ['RICE_REPRO_OUTPUT'] = str(args.out.resolve())
from _common import *

from step05_model_fitting import run, pred_ols, StandardScaler
import _baseline_models as ml
from _baseline_models import fit_ridge as archived_fit_ridge
import itertools, time
RIDGE_ALPHAS=np.array([.01,.1,1.,10.,100.])

def summarize(pred):return metrics(pred[TARGET],pred.prediction)

def regional(pred):return pd.DataFrame([dict(region=r,**summarize(g)) for r,g in pred.groupby('Region')])

def save(pred,name,models=None):
    csv(pred,ROOT/'predictions'/f'{name}.csv');csv(regional(pred),ROOT/'results'/f'{name}_regions.csv')
    if models is not None:js(models,ROOT/'models'/f'{name}.json')

def run_core():
    data=read(ROOT/'inputs/features_continuous.csv');im=images(data)
    primary=read(ROOT/'runs/continuous/oof_predictions.csv');fold=read(ROOT/'runs/continuous/fold_results.csv')
    selected={r.held_region:r.selected_features.split(';') for r in fold.itertuples()}
    pm=summarize(primary);err=abs(primary.prediction-primary[TARGET])
    for lim in [5,10]:pm[f'within_{lim}_count']=int((err<=lim).sum());pm[f'within_{lim}_percent']=float((err<=lim).mean()*100)
    csv([pm],ROOT/'results/primary_metrics.csv')
    fitunit,models=pred_ols(data,selected,'image');save(fitunit,'fold_specific_image_OLS',models)
    csv([summarize(fitunit)],ROOT/'results/fitting_unit_metrics.csv')
    region=regional(primary).merge(regional(fitunit)[['region','RMSE']].rename(columns={'RMSE':'image_OLS_RMSE'}),on='region')
    csv(region,ROOT/'results/primary_region_metrics.csv')
    w=1/primary.groupby(['Region','site_date'])[ID].transform('count')
    assert np.isclose(w.sum(),33,rtol=0,atol=1e-12)
    csv([dict(evaluation='equal_image',**summarize(primary)),dict(evaluation='equal_site_date',**metrics(primary[TARGET],primary.prediction,w))],ROOT/'results/evaluation_weighting.csv')
    binary=pd.DataFrame([dict(held_region=r,**{f:int(f in selected[r]) for f in FEATURES}) for r in sorted(selected)])
    csv(binary,ROOT/'results/recurrence_binary_9x37.csv')
    counts=binary[FEATURES].sum();cmax=int(counts.max());ref=[f for f in FEATURES if counts[f]==cmax]
    csv([dict(feature=f,count=int(counts[f]),frequency=float(counts[f]/9),maximum_group=f in ref) for f in FEATURES],ROOT/'results/recurrence_all37.csv')
    js(dict(maximum_count=cmax,reference=ref,rule='all features tied at the maximum observed recurrence'),ROOT/'results/reference_definition.json')
    reference=[]
    for unit,agg in [('strip','mean'),('image','mean')]:
        p,models=pred_ols(data,ref,unit,agg);name=f'reference_{unit}_{agg}';save(p,name,models);reference.append(dict(mode=name,**summarize(p)))
    csv(reference,ROOT/'results/reference_metrics.csv')
    scaler=StandardScaler().fit(data[ref]);x=np.column_stack([np.ones(len(data)),scaler.transform(data[ref])]);beta=np.linalg.pinv(x,rcond=1e-15)@data[TARGET].to_numpy()
    slopes=beta[1:]/scaler.scale_;intercept=float(beta[0]-slopes@scaler.mean_)
    csv([dict(feature='intercept',coefficient=intercept)]+[dict(feature=f,coefficient=float(v)) for f,v in zip(ref,slopes)],ROOT/'results/full_data_coefficients.csv')
    assert np.allclose(x@beta,intercept+data[ref].to_numpy()@slopes,rtol=0,atol=1e-11)
    if set(ref)==set(['start','end','complexity','mean_R','MGRVI','COM']):
        abl=[]
        for name,cols in [('Color only',['mean_R','MGRVI','COM']),('Color + complexity',['complexity','mean_R','MGRVI','COM']),('Color + position',['start','end','mean_R','MGRVI','COM']),('Full reference',ref)]:
            p,m=pred_ols(data,cols);save(p,'ablation_'+name.replace(' ','_').replace('+','plus'),m);abl.append(dict(configuration=name,q=len(cols),**summarize(p)))
        csv(abl,ROOT/'results/ablation_metrics.csv')
    else:
        print('Reference configuration changed; predefined six-feature ablation was not rerun as a new reference ablation.',flush=True)
    print('Core complete',pm,'reference',ref,flush=True)

def run_representations():
    for case in ['raw','otsu','matched','full']:
        run(read(ROOT/'inputs'/f'features_{case}.csv'),ROOT/'runs'/case,case=case)
    preds={c:read(ROOT/'runs'/c/'oof_predictions.csv') for c in ['raw','otsu','continuous']}
    csv([dict(case=c,**metrics(p[TARGET],p.prediction)) for c,p in preds.items()],ROOT/'results/representation_metrics.csv')
    csv([dict(case=c,region=r,**metrics(g[TARGET],g.prediction)) for c,p in preds.items() for r,g in p.groupby('Region')],ROOT/'results/representation_region_metrics.csv')
    csv([dict(case=c,site_date=d,**metrics(g[TARGET],g.prediction)) for c,p in preds.items() for d,g in p.groupby('site_date')],ROOT/'results/representation_date_metrics.csv')
    csv([dict(partition=c,**metrics((p:=read(ROOT/'runs'/c/'oof_predictions.csv'))[TARGET],p.prediction)) for c in ['continuous','matched','full']],ROOT/'results/partition_metrics.csv')
    print('All four selection reruns completed',flush=True)

def fit_path(train):
    raw=train[FEATURES].to_numpy(dtype=float);y=train[TARGET].to_numpy(dtype=float)
    mean=raw.mean(0);sd=raw.std(0);sd[sd==0]=1
    design=np.column_stack([np.ones(len(raw)),(raw-mean)/sd]);coefs=[];gap=[]
    for alpha in RIDGE_ALPHAS:
        penalty=np.eye(len(FEATURES)+1)*alpha;penalty[0,0]=0
        beta=np.linalg.pinv(design.T@design+penalty)@design.T@y
        # Verify against the unmodified actual baseline implementation, training only.
        oracle=archived_fit_ridge(raw,y,raw,alpha)
        assert np.allclose(design@beta,oracle,rtol=0,atol=1e-12)
        coefs.append(beta)
        gap.append(float(np.max(abs((design.T@design+penalty)@beta-design.T@y))))
    return dict(mean=mean,sd=sd,coefs=np.asarray(coefs),alphas=RIDGE_ALPHAS,n_training=np.array(len(train)),normal_equation_residual=np.asarray(gap))


def predict(path,frame):
    x=(frame[FEATURES].to_numpy()-path['mean'])/path['sd']
    return np.column_stack([np.ones(len(frame)),x])@path['coefs'].T


def as_images(frame,predictions):
    temp=frame[['Region',ID,'site_date',TARGET]].copy()
    cols=[f'alpha_{i}' for i in range(len(RIDGE_ALPHAS))]
    temp[cols]=predictions
    return temp.groupby(['Region',ID,'site_date'],sort=True,as_index=False).agg({TARGET:'first',**dict.fromkeys(cols,'mean')})


def run_ridge(case,mode):
    folder=ROOT/'ridge'/mode/case;folder.mkdir(parents=True,exist_ok=True);cache=folder/'cache';cache.mkdir(exist_ok=True)
    if (folder/'pooled_metrics.csv').exists():return
    strips=read(ROOT/'inputs'/f'features_{case}.csv')
    unit=images(strips) if mode=='image' else strips
    csv(unit,folder/'training_units.csv');regions=sorted(unit.Region.unique());paths={}
    for size in [7,8]:
        for ids in itertools.combinations(range(9),size):
            mask=sum(1<<i for i in ids);names=[regions[i] for i in ids];train=unit[unit.Region.isin(names)]
            p=fit_path(train);paths[mask]=p
            np.savez_compressed(cache/f'{mask:03d}.npz',**p)
            row=dict(mask=mask,training_regions=names,n_training_units=len(train),n_training_images=train.groupby(['Region',ID]).ngroups,unit=mode,all_37_features=FEATURES,intercept_penalized=False)
            js(row,cache/f'{mask:03d}.json')
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
        for j,alpha in enumerate(RIDGE_ALPHAS):
            score=metrics(inner_df[TARGET],inner_df[f'alpha_{j}'])['RMSE'];scores.append(score)
            if best is None or score<best:best=score;index=j
        for j,alpha in enumerate(RIDGE_ALPHAS):curves.append(dict(held_region=region,alpha=float(alpha),inner_pooled_image_RMSE=scores[j],selected=j==index))
        path=paths[outer];test=unit[unit.Region==region];predictions=predict(path,test)
        allim=as_images(test,predictions);part=allim[['Region',ID,'site_date',TARGET]].copy();part['prediction']=allim[f'alpha_{index}']
        part['error']=part.prediction-part[TARGET];part['abs_error']=abs(part.error);records.append(part)
        if mode=='strip':
            st=test[['Region',ID,'site_date',TARGET]].copy();st['prediction']=predictions[:,index];strip_preds.append(st)
        folds.append(dict(case=case,unit=mode,held_region=region,selected_alpha=float(RIDGE_ALPHAS[index]),n_training_units=int(path['n_training']),n_validation_images=len(inner_df),n_test_images=len(part),inner_RMSE=float(best),n_features=len(FEATURES),exact_tie_count=int(np.sum(np.asarray(scores)==best))))
        models.append(dict(held_region=region,selected_alpha=float(RIDGE_ALPHAS[index]),training_regions=[r for r in regions if r!=region],mean=path['mean'].tolist(),sd=path['sd'].tolist(),coefficients=path['coefs'][index].tolist(),features=FEATURES,training_unit=mode,n_training_units=int(path['n_training'])))
    d=pd.concat(records,ignore_index=True)
    csv(d,folder/'oof_predictions.csv');csv(folds,folder/'fold_results.csv');csv(curves,folder/'inner_cv_curves.csv');csv(boundaries,folder/'fold_boundary_audit.csv')
    csv(pd.concat(inner_preds,ignore_index=True),folder/'inner_validation_predictions.csv');js(models,folder/'fold_models.json')
    if strip_preds:csv(pd.concat(strip_preds,ignore_index=True),folder/'strip_predictions.csv')
    csv([dict(case=case,unit=mode,**metrics(d[TARGET],d.prediction))],folder/'pooled_metrics.csv')
    csv([dict(region=r,**metrics(g[TARGET],g.prediction)) for r,g in d.groupby('Region')],folder/'region_metrics.csv')
    csv([dict(site_date=r,**metrics(g[TARGET],g.prediction)) for r,g in d.groupby('site_date')],folder/'date_metrics.csv')
    print('Ridge',mode,case,metrics(d[TARGET],d.prediction),'alphas',[r['selected_alpha'] for r in folds],flush=True)

def run_baselines():
    strips=read(ROOT/'inputs/features_continuous.csv');im=images(strips)
    extra=read(ROOT/'inputs/fixed_baseline_NExGR_continuous.csv')
    extra=extra.groupby(['Region',ID,'site_date'],as_index=False,sort=True).agg({'NExGR':'mean'})
    im=im.merge(extra,on=['Region',ID,'site_date'],validate='one_to_one',sort=False)
    base=[];params=[];curves=[];innerrows=[];boundaries=[];t=time.time()
    diagnostics=[]
    def elastic(*args):
        state={}
        def capture(frame,event,value):
            if event=='return' and frame.f_code is ml.fit_elastic_net.__code__:
                local=frame.f_locals
                state.update(alpha=float(local['alpha']),n_train=int(local['n']),iterations=int(local['_'])+1,max_iter=int(local['max_iter']),last_delta=float(np.max(abs(local['beta']-local['old']))),tol=float(local['tol']))
        previous=sys.getprofile();sys.setprofile(capture)
        try:prediction=ml.fit_elastic_net(*args)
        finally:sys.setprofile(previous)
        state['converged']=state['last_delta']<state['tol']
        if not state['converged']:raise RuntimeError('Elastic Net did not converge: '+str(state))
        diagnostics.append(state)
        return prediction
    methods=[('Training-set mean','mean',None),('RGB vegetation indices','rgb',None),('Elastic Net','elastic',[.001,.003,.01,.03,.1,.3]),('PCR','pcr',[3,5,8,12,18,24]),('kNN regression','knn',[3,5,7,9,11]),('Small MLP','mlp',None)]
    funcs={'elastic':elastic,'pcr':ml.fit_pcr,'knn':ml.fit_knn}
    for label,method,grid in methods:
        outs=[]
        for r in sorted(im.Region.unique()):
            train=im[im.Region!=r];test=im[im.Region==r];cols=['GLI','MGRVI','RGBVI','NExGR','VARI'] if method=='rgb' else FEATURES
            best=None;param=None
            if grid is not None:
                for v in grid:
                    parts=[]
                    for ir in sorted(train.Region.unique()):
                        tr=train[train.Region!=ir];va=train[train.Region==ir]
                        pr=funcs[method](tr[cols],tr[TARGET],va[cols],v)
                        temp=va[['Region',ID,'site_date',TARGET]].copy();temp['prediction']=pr;parts.append(temp)
                        innerrows.append(temp.assign(method=method,held_region=r,inner_region=ir,parameter=v))
                        assert r not in tr.Region.unique() and ir not in tr.Region.unique()
                    score=summarize(pd.concat(parts,ignore_index=True))['RMSE']
                    curves.append(dict(method=method,held_region=r,parameter=v,RMSE=score))
                    if best is None or score<best:best=score;param=v
                # The first candidate is retained on exact ties.
            if method=='mean':pr=np.repeat(train[TARGET].mean(),len(test))
            elif method=='rgb':pr=ml.fit_ols(train[cols],train[TARGET],test[cols])
            elif method=='mlp':pr=ml.fit_mlp(train[cols].to_numpy(),train[TARGET].to_numpy(),test[cols].to_numpy())
            else:pr=funcs[method](train[cols],train[TARGET],test[cols],param)
            temp=test[['Region',ID,'site_date',TARGET]].copy();temp['prediction']=pr;outs.append(temp)
            params.append(dict(method=method,held_region=r,parameter=param,inner_RMSE=best,n_features=len(cols),features=';'.join(cols)))
            boundaries.append(dict(method=method,held_region=r,training_regions=';'.join(sorted(train.Region.unique())),n_train=len(train),n_test=len(test)))
        p=pd.concat(outs,ignore_index=True);save(p,'baseline_'+method);base.append(dict(Model=label,method=method,**summarize(p)))
        print('Baseline',method,summarize(p),'elapsed',round(time.time()-t,1),flush=True)
    csv(base,ROOT/'results/baseline_metrics_without_ridge.csv');csv(params,ROOT/'models/baseline_parameters.csv');csv(curves,ROOT/'models/baseline_inner_curves.csv');csv(pd.concat(innerrows,ignore_index=True),ROOT/'models/baseline_inner_predictions.csv');csv(boundaries,ROOT/'validation/baseline_outer_splits.csv')
    assert len(diagnostics)==441 and all(d['converged'] for d in diagnostics)
    csv(diagnostics,ROOT/'validation/elastic_net_fit_diagnostics.csv')
    js(dict(algorithm_bodies_unchanged=True,Elastic_Net_max_iter=100000,Elastic_Net_fits=len(diagnostics),Elastic_Net_converged=sum(d['converged'] for d in diagnostics),MLP_input_dimension=len(FEATURES),MLP_hidden=8,MLP_epochs=2500,MLP_seed=7,response_standardized=['elastic','mlp'],RGB_fixed_NExGR_not_rerun=False,all_inner_held_regions_excluded=True,exact_tie_first=True),ROOT/'validation/baselines_complete.json')


def comparisons():
    check_runtime()
    run_core();run_representations()
    for unit in ['image','strip']:
        for case in ['raw','otsu','continuous']:run_ridge(case,unit)
    run_baselines()
    from step06_evaluation import evaluate
    return evaluate(all_analyses=True)

if __name__ == '__main__':comparisons()
