"""Two prespecified 34-color comparisons using the unmodified Lasso/BIC engines."""
from pathlib import Path
import argparse,itertools,json,os,platform,sys,time
OUT=Path(os.environ['RICE_REPRO_OUTPUT']).resolve()
sys.dont_write_bytecode=True
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.environ['RICE_REPRO_OUTPUT']=str(OUT)


def main():
    
    from runtime_check import activate
    runtime=activate()
    import common as c
    import sparse_engine as engine
    from sklearn.preprocessing import StandardScaler
    np,pd=c.np,c.pd;read,csv,js=c.read,c.csv,c.js;ID,TARGET=c.ID,c.TARGET;KEY=['Region',ID,'site_date']
    config=json.loads((OUT/'experiment_config.json').read_text(encoding='utf-8'));features=config['candidate_features']
    assert len(features)==34 and features==[f for f in c.FEATURES if f not in ['start','end','complexity']]
    gate=json.loads((OUT/'validation/pixel_extraction.json').read_text(encoding='utf-8'));assert gate['status']=='PASS' and gate['images']==92
    data={m:read(OUT/'inputs'/f'features_{m}.csv') for m in 'ABCD'}
    canonical_C=data['D'].groupby(KEY,as_index=False,sort=True).agg({**dict.fromkeys(features,'mean'),TARGET:'first'})
    assert np.allclose(data['C'][features],canonical_C[features],rtol=1e-14,atol=1e-12)
    # Use exactly the published pandas image-mean operation for both C and D selection.
    csv(data['C'],OUT/'validation/C_pixel_runtime_mean.csv');data['C']=canonical_C
    selection_data={m:data[m] for m in 'ABC'};selection_data['D']=canonical_C.copy()
    reference=c.images(read(OUT/'inputs/features_continuous.csv'))[KEY+[TARGET]]
    for m,frame in data.items():
        assert len(frame)==(552 if m=='D' else 92)
        keys=frame[KEY+[TARGET]].drop_duplicates().sort_values(KEY).reset_index(drop=True)
        pd.testing.assert_frame_equal(keys,reference.sort_values(KEY).reset_index(drop=True),check_exact=True)
        assert frame.groupby(['Region','site_date'])[TARGET].nunique().eq(1).all()
        assert np.isfinite(frame[features+[TARGET]]).all().all()
        csv(frame,OUT/'model_inputs'/f'{m}.csv')
    regions=sorted(reference.Region.unique());assert len(regions)==9
    js(dict(runtime=runtime,seed=None,deterministic=True,features=features,regions=regions,selection_source='C in common; own image means in independent'),OUT/'validation/model_runtime.json')
    started=time.time()

    def select(unit,label):
        folder=OUT/'selection'/label;folder.mkdir(parents=True,exist_ok=False);(folder/'cache').mkdir()
        engine.ROOT=folder;paths={};diagnostics=[];boundaries=[];history=[];curves=[];folds=[]
        for size in [7,8]:
            for ids in itertools.combinations(range(9),size):
                mask=engine.mask_for(ids);train=unit[unit.Region.isin([regions[i] for i in ids])]
                result=engine.fit(train,features,mask,None);paths[mask]=result
                meta=json.loads((folder/'cache/lasso'/f'{mask:03d}.json').read_text(encoding='utf-8'))
                for j,alpha in enumerate(engine.ALPHAS):
                    diagnostics.append(dict(training_mask=mask,lambda_value=float(alpha),n_train=len(train),dual_gap=float(result['dual_gap'][j]),max_kkt=float(result['kkt'][j]),gap_tolerance=meta['gap_tolerance'],solver=str(result['solver'][j])))
        selections={}
        for held,region in enumerate(regions):
            outer_mask=511^(1<<held);outer=unit[unit.Region!=region];sse=[];counts=[]
            for inner,ir in enumerate(regions):
                if inner==held:continue
                mask=outer_mask^(1<<inner);path=paths[mask];validation=outer[outer.Region==ir]
                prediction=((validation[features].to_numpy()-path['mean'])/path['sd'])@path['betas'].T+float(path['ymean'])
                sse.append(np.sum((prediction-validation[TARGET].to_numpy()[:,None])**2,axis=0));counts.append(len(validation))
                train_regions=[regions[i] for i in range(9) if mask&(1<<i)]
                assert region not in train_regions and ir not in train_regions
                boundaries.append(dict(held_region=region,inner_validation_region=ir,training_regions=';'.join(train_regions),n_training_images=int(unit.Region.isin(train_regions).sum()),n_validation_images=len(validation),held_out_excluded=True,inner_validation_excluded=True))
            rmse,se,_=engine.curve(np.asarray(sse),counts);index,innerinfo=engine.select_lambda(rmse,se,'L2')
            for j,alpha in enumerate(engine.ALPHAS):curves.append(dict(held_region=region,lambda_value=float(alpha),inner_RMSE=float(rmse[j]),score_variability=float(se[j]),selected=j==index))
            initial=tuple(np.flatnonzero(abs(paths[outer_mask]['betas'][index])>engine.NONZERO))
            scorer=engine.ICScorer(outer,features,region)
            selected,info,removed,hist=engine.backward(scorer,initial,'BIC',None,'G_L2_BIC');history.extend(hist)
            names=[features[j] for j in selected];selections[region]=names
            folds.append(dict(held_region=region,selection_run=label,selection_unit='image',n_training_images=len(outer),lambda_value=float(engine.ALPHAS[index]),selected_feature_count=len(names),selected_features=';'.join(names),initial_selected_features=';'.join(features[j] for j in initial),BIC=info['BIC'],**innerinfo))
            print(label,region,'selected',len(names),flush=True)
        csv(folds,folder/'fold_results.csv');csv(history,folder/'BIC_history.csv');csv(curves,folder/'inner_curves.csv');csv(boundaries,folder/'split_boundaries.csv');csv(diagnostics,folder/'solver_diagnostics.csv')
        csv(unit[KEY+features+[TARGET]],folder/'selection_observations.csv')
        return selections,pd.DataFrame(folds)

    selection_runs={};shared,shared_folds=select(selection_data['C'],'common_C')
    selection_runs['common']={m:(shared,shared_folds) for m in 'ABCD'}
    selection_runs['independent']={m:select(selection_data[m],'independent_'+m) for m in 'ABCD'}
    assert selection_runs['independent']['C'][0]==selection_runs['independent']['D'][0]==shared
    allpred=[];allstrips=[];allselected=[];model_records=[];models={}

    def fit(train,test,names):
        if names:
            scale=StandardScaler().fit(train[names]);x=np.column_stack([np.ones(len(train)),scale.transform(train[names])]);xt=np.column_stack([np.ones(len(test)),scale.transform(test[names])])
            mean=scale.mean_;sd=scale.scale_
        else:
            x=np.ones((len(train),1));xt=np.ones((len(test),1));mean=sd=np.array([])
        coef=np.linalg.pinv(x,rcond=1e-15)@train[TARGET].to_numpy();pred=xt@coef
        beta=coef[1:]/sd;intercept=float(coef[0]-mean@beta)
        raw_pred=intercept+test[names].to_numpy()@beta
        assert np.allclose(pred,raw_pred,rtol=1e-11,atol=1e-8)
        return pred,dict(features=names,mean=mean.tolist(),sd=sd.tolist(),standardized_coefficients=coef.tolist(),raw_beta=beta.tolist(),raw_intercept=intercept,design_rank=int(np.linalg.matrix_rank(x)),n_fit_rows=len(train))

    for analysis in ['common','independent']:
        for m in 'ABCD':
            chosen,folds=selection_runs[analysis][m]
            for fold_index,region in enumerate(regions,1):
                frame=data[m];train=frame[frame.Region!=region];test=frame[frame.Region==region];names=chosen[region]
                pred,model=fit(train,test,names)
                model.update(analysis=analysis,model=m,held_region=region,training_regions=sorted(train.Region.unique()),fitting_unit='strip' if m=='D' else 'image')
                assert region not in model['training_regions']
                models[(analysis,m,region)]=model;model_records.append(model)
                part=test[KEY+[TARGET]].copy();part['prediction']=pred
                if m=='D':allstrips.append(part.assign(analysis=analysis,model=m,fold=fold_index))
                p=part.groupby(KEY,as_index=False,sort=True).agg({TARGET:'first','prediction':'mean'})
                p['analysis']=analysis;p['model']=m;p['fold']=fold_index;p['held_region']=region
                p['site_date_id']=p.Region+'_'+p.site_date.astype(str);p['error']=p.prediction-p[TARGET];p['abs_error']=abs(p.error)
                allpred.append(p)
                row=folds[folds.held_region==region].iloc[0].to_dict();row.update(analysis=analysis,model=m,fold=fold_index,fitting_unit=model['fitting_unit'],n_fit_rows=len(train),selection_source='C' if analysis=='common' else ('D_image_mean' if m=='D' else m))
                allselected.append(row)
    oof=pd.concat(allpred,ignore_index=True);csv(oof,OUT/'oof_predictions.csv');csv(allselected,OUT/'selected_features_by_fold.csv');csv(pd.concat(allstrips,ignore_index=True),OUT/'strip_predictions.csv');js(model_records,OUT/'models/ols_models.json')
    assert len(oof)==8*92 and not oof.duplicated(['analysis','model','Region',ID]).any()
    scores=[];regional=[]
    for (analysis,m),p in oof.groupby(['analysis','model']):
        weights=1/p.groupby(['Region','site_date'])[ID].transform('count');assert np.isclose(weights.sum(),33)
        weighted=c.metrics(p[TARGET],p.prediction,weights)
        scores.append(dict(analysis=analysis,model=m,candidate_features=34,fitting_unit='strip' if m=='D' else 'image',**c.metrics(p[TARGET],p.prediction),site_date_equal_RMSE=weighted['RMSE'],site_date_equal_MAE=weighted['MAE'],site_date_equal_R2=weighted['R2']))
        for region,g in p.groupby('Region'):
            regional.append(dict(analysis=analysis,model=m,region=region,actual_min=float(g[TARGET].min()),actual_max=float(g[TARGET].max()),unique_height_references=g.site_date.nunique(),**c.metrics(g[TARGET],g.prediction)))
    scores=pd.DataFrame(scores);regional=pd.DataFrame(regional)
    csv(scores[scores.analysis=='common'],OUT/'results_common_features.csv');csv(scores[scores.analysis=='independent'],OUT/'results_independent_selection.csv');csv(regional,OUT/'regional_results.csv')
    differences=[];regiondiff=[]
    for analysis in ['common','independent']:
        for left,right in [('A','B'),('B','C'),('C','D'),('A','D')]:
            lp=oof[(oof.analysis==analysis)&(oof.model==left)];rp=oof[(oof.analysis==analysis)&(oof.model==right)]
            lm=c.metrics(lp[TARGET],lp.prediction);rm=c.metrics(rp[TARGET],rp.prediction);wins=0;losses=0
            for region in regions:
                l=lp[lp.Region==region];r=rp[rp.Region==region];lmet=c.metrics(l[TARGET],l.prediction);rmet=c.metrics(r[TARGET],r.prediction)
                delta=lmet['RMSE']-rmet['RMSE'];wins+=delta>1e-10;losses+=delta<-1e-10
                regiondiff.append(dict(analysis=analysis,pair=left+'_vs_'+right,region=region,left_RMSE=lmet['RMSE'],right_RMSE=rmet['RMSE'],RMSE_left_minus_right=delta,MAE_left_minus_right=lmet['MAE']-rmet['MAE'],lower_RMSE_model=right if delta>1e-10 else left if delta<-1e-10 else 'tie'))
            differences.append(dict(analysis=analysis,pair=left+'_vs_'+right,left_RMSE=lm['RMSE'],right_RMSE=rm['RMSE'],RMSE_left_minus_right=lm['RMSE']-rm['RMSE'],MAE_left_minus_right=lm['MAE']-rm['MAE'],regions_favor_right=int(wins),regions_favor_left=int(losses),ties=9-int(wins)-int(losses)))
    csv(differences,OUT/'paired_comparisons.csv');csv(regiondiff,OUT/'regional_comparisons.csv')

    # Identity and dispersion comparisons in common, original feature coordinates.
    identity=[]
    for analysis in ['common','independent']:
        for region in regions:
            cm=models[(analysis,'C',region)];dm=models[(analysis,'D',region)];assert cm['features']==dm['features'];names=cm['features']
            strips=data['D'][data['D'].Region!=region].copy();means=data['C'][data['C'].Region!=region].copy()
            # Original rows are image-contiguous, six consecutive strips per image.
            raw=strips[names].to_numpy().reshape(len(means),6,len(names));xbar=raw.mean(axis=1)
            assert np.allclose(xbar,means[names],rtol=1e-14,atol=1e-12)
            centered=raw-xbar[:,None,:];centerflat=centered.reshape(len(means)*6,len(names))
            M=centerflat.T@centerflat;scale=max(1,float(np.linalg.norm(M,2))) if names else 1
            eigen=np.linalg.eigvalsh(M);mineig=float(eigen.min()) if names else 0
            assert np.allclose(M,M.T,rtol=0,atol=1e-12) and mineig>=-1e-10*scale
            losses={}
            for label,model in [('C',cm),('D',dm)]:
                beta=np.asarray(model['raw_beta']);b=model['raw_intercept'];y=means[TARGET].to_numpy()
                phat=b+raw@beta;imagehat=b+xbar@beta
                lstrip=float(np.sum((phat-y[:,None])**2));limage=float(np.sum((imagehat-y)**2));dispersion=float(np.sum((centered@beta)**2));quadratic=float(beta@M@beta)
                discrepancy=abs(lstrip/6-(limage+quadratic/6))
                assert np.isclose(lstrip/6,limage+quadratic/6,rtol=1e-10,atol=1e-6)
                assert np.isclose(dispersion,quadratic,rtol=1e-10,atol=1e-6)
                losses[label]=dict(L_strip=lstrip,L_image=limage,dispersion=dispersion,identity_abs_error=discrepancy)
            tol=1e-7+1e-9*max(1,losses['C']['dispersion'])
            assert losses['D']['dispersion']<=losses['C']['dispersion']+tol
            assert losses['D']['L_strip']<=losses['C']['L_strip']+1e-6
            assert losses['C']['L_image']<=losses['D']['L_image']+1e-6
            identity.append(dict(analysis=analysis,held_region=region,q=len(names),minimum_M_eigenvalue=mineig,M_PSD_tolerance=1e-10*scale,**{'C_'+k:v for k,v in losses['C'].items()},**{'D_'+k:v for k,v in losses['D'].items()},dispersion_D_not_greater=True))
    csv(identity,OUT/'loss_identity_checks.csv')
    js(dict(status='PASS',runtime=runtime,seconds=time.time()-started,analyses=2,groups=4,OOF_predictions=len(oof),outer_fits=72,selection_runs=5,all_C_D_selection_equal=True,identity_cases=len(identity),all_loss_identity_checks_pass=True),OUT/'validation/model_execution.json')
    print(scores.to_string(index=False),flush=True)

if __name__=='__main__':main()
