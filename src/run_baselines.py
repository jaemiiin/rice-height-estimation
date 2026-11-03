"""Current manuscript baselines, including fully converged Elastic Net."""
from run_core import *
import time
def run():
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
                # Same candidate ordering/exact-tie rule as archived inner_select.
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
if __name__=='__main__':run()
