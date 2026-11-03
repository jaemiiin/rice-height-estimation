"""Current G_L2_BIC protocol with unchanged archived solver and selection rules."""
from common import *
import itertools,time,traceback
import sparse_engine as engine
from sklearn.preprocessing import StandardScaler

def run(strips,folder,selection_unit='image',case=''):
    assert selection_unit=='image', 'The final manuscript selects at the image level'
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if (folder/'pooled_metrics.csv').exists():
        return read(folder/'oof_predictions.csv'),read(folder/'fold_results.csv')
    assert np.isfinite(strips[FEATURES+[TARGET]].to_numpy()).all()
    im=images(strips);regions=sorted(strips.Region.unique())
    unit=im
    assert len(unit)==92
    csv(unit,folder/'selection_observations.csv')
    (folder/'cache').mkdir(exist_ok=True);engine.ROOT=folder
    paths={};diagnostics=[];events=[]
    for size in [7,8]:
        for ids in itertools.combinations(range(9),size):
            mask=engine.mask_for(ids);train=unit[unit.Region.isin([regions[i] for i in ids])]
            result=engine.fit(train,FEATURES,mask,None);paths[mask]=result
            metadata=json.loads((folder/'cache/lasso'/f'{mask:03d}.json').read_text(encoding='utf-8'))
            for j,a in enumerate(engine.ALPHAS):diagnostics.append(dict(case=case,selection_unit=selection_unit,training_mask=mask,n_training_selection_rows=len(train),lambda_value=float(a),solver=str(result['solver'][j]),dual_gap=float(result['dual_gap'][j]),max_kkt=float(result['kkt'][j]),gap_tolerance=metadata['gap_tolerance']))
            events.extend([dict(case=case,training_mask=mask,**e) for e in metadata['solver_events']])
        print(case,'completed training paths with',size,'regions',flush=True)
    folds=[];all_preds=[];strip_preds=[];all_history=[];all_curve=[];boundaries=[];models=[]
    for held,region in enumerate(regions):
        outer_mask=511^(1<<held);outer_train=unit[unit.Region!=region];sse=[];counts=[]
        for inner,ir in enumerate(regions):
            if inner==held:continue
            mask=outer_mask^(1<<inner);path=paths[mask]
            validation=outer_train[outer_train.Region==ir]
            prediction=((validation[FEATURES].to_numpy()-path['mean'])/path['sd'])@path['betas'].T+float(path['ymean'])
            sse.append(np.sum((prediction-validation[TARGET].to_numpy()[:,None])**2,axis=0));counts.append(len(validation))
            train_regions=[regions[i] for i in range(9) if mask&(1<<i)]
            assert region not in train_regions and ir not in train_regions
            boundaries.append(dict(case=case,held_region=region,inner_validation_region=ir,training_regions=';'.join(train_regions),n_training_rows=int(unit.Region.isin(train_regions).sum()),selection_unit=selection_unit,held_region_excluded=True,inner_validation_excluded=True))
        rmse,se,_=engine.curve(np.asarray(sse),counts);index,innerinfo=engine.select_lambda(rmse,se,'L2')
        for j,a in enumerate(engine.ALPHAS):all_curve.append(dict(held_region=region,lambda_value=float(a),inner_RMSE=float(rmse[j]),jackknife_SE=float(se[j]),selected=j==index))
        path=paths[outer_mask];initial=tuple(np.flatnonzero(abs(path['betas'][index])>engine.NONZERO))
        scorer=engine.ICScorer(outer_train,FEATURES,region)
        selected,info,removed,history=engine.backward(scorer,initial,'BIC',None,'G_L2_BIC')
        all_history.extend(history)
        chosen=[FEATURES[j] for j in selected]
        train=strips[strips.Region!=region];test=strips[strips.Region==region]
        scaler=StandardScaler().fit(train[FEATURES])
        x=scaler.transform(train[FEATURES]);xt=scaler.transform(test[FEATURES])
        design=np.column_stack([np.ones(len(train)),x[:,selected]])
        beta=np.linalg.pinv(design,rcond=1e-15)@train[TARGET].to_numpy()
        # No held-out response is passed to the transformation or prediction expression.
        predictions=np.column_stack([np.ones(len(test)),xt[:,selected]])@beta
        part=test[['Region',ID,'site_date',TARGET]].copy();part['prediction']=predictions
        strip_preds.append(part)
        pooled=part.groupby(['Region',ID,'site_date'],sort=True,as_index=False).agg({TARGET:'first','prediction':'mean'})
        pooled['error']=pooled.prediction-pooled[TARGET];pooled['abs_error']=abs(pooled.error);all_preds.append(pooled)
        folds.append(dict(case=case,held_region=region,selection_unit=selection_unit,n_selection_training_rows=len(outer_train),lambda_value=float(engine.ALPHAS[index]),lambda_at_lower_boundary=index==199,lambda_at_upper_boundary=index==0,initial_feature_count=len(initial),initial_selected_features=';'.join(FEATURES[j] for j in initial),selected_feature_count=len(selected),selected_features=';'.join(chosen),removal_order=';'.join(FEATURES[j] for j in removed),BIC=info['BIC'],BIC_training_RSS=info['training_RSS'],**innerinfo))
        models.append(dict(held_region=region,selected_features=chosen,scaler_training_regions=sorted(train.Region.unique()),n_fit_strips=len(train),means=scaler.mean_.tolist(),scales=scaler.scale_.tolist(),standardized_coefficients=beta.tolist(),design_rank=int(np.linalg.matrix_rank(design)),n_coefficients=len(beta),design_condition=float(np.linalg.cond(design)),pinv_rcond=1e-15))
        print(case,region,'lambda',float(engine.ALPHAS[index]),'features',len(initial),'->',len(selected),flush=True)
    pred=pd.concat(all_preds,ignore_index=True);fold=pd.DataFrame(folds)
    csv(pred,folder/'oof_predictions.csv');csv(pd.concat(strip_preds,ignore_index=True),folder/'strip_predictions.csv')
    csv(fold,folder/'fold_results.csv');csv(all_curve,folder/'inner_cv_curves.csv');csv(boundaries,folder/'fold_boundary_audit.csv');csv(all_history,folder/'backward_BIC_history.csv')
    csv(diagnostics,folder/'solver_diagnostics.csv');js(events,folder/'solver_events.json');js(models,folder/'fold_models.json')
    csv([dict(feature=f,count=sum(f in set(s.split(';')) for s in fold.selected_features),frequency=sum(f in set(s.split(';')) for s in fold.selected_features)/9) for f in FEATURES],folder/'selection_frequency.csv')
    csv([dict(case=case,region=r,**metrics(g[TARGET],g.prediction)) for r,g in pred.groupby('Region')],folder/'region_metrics.csv')
    csv([dict(case=case,**metrics(pred[TARGET],pred.prediction))],folder/'pooled_metrics.csv')
    return pred,fold

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--out',required=True);parser.add_argument('--unit',default='image',choices=['image']);parser.add_argument('--case',required=True);args=parser.parse_args()
    try:run(read(args.data),Path(args.out),args.unit,args.case)
    except Exception:
        folder=Path(args.out);folder.mkdir(parents=True,exist_ok=True)
        stamp=str(time.time_ns());(folder/('FAILED_'+stamp+'.txt')).write_text(traceback.format_exc(),encoding='utf-8');raise

