"""Step 04: nested regional Lasso 1SE and greedy backward BIC on image means."""
from pathlib import Path
if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Analysis output root shared by steps 04-07')
    parser.add_argument('--case', default='continuous', choices=['raw','otsu','continuous','matched','full'])
    args = parser.parse_args()
    os.environ['RICE_REPRO_OUTPUT'] = str(args.out.resolve())
from _common import *

import itertools
import _selection_solver as engine

def select_features(strips,folder,selection_unit='image',case=''):
    assert selection_unit=='image', 'The final manuscript selects at the image level'
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    fingerprint=input_fingerprint(strips)
    signature=folder/'input.sha256'
    if signature.exists():
        assert signature.read_text()==fingerprint, 'Input changed: choose a new output directory'
    else:signature.write_text(fingerprint)
    if (folder/'selection_complete.json').exists():return read(folder/'fold_results.csv')
    validate_features(strips)
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
    folds=[];all_history=[];all_curve=[];boundaries=[]
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
        folds.append(dict(case=case,held_region=region,selection_unit=selection_unit,n_selection_training_rows=len(outer_train),lambda_value=float(engine.ALPHAS[index]),lambda_at_lower_boundary=index==199,lambda_at_upper_boundary=index==0,initial_feature_count=len(initial),initial_selected_features=';'.join(FEATURES[j] for j in initial),selected_feature_count=len(selected),selected_features=';'.join(chosen),removal_order=';'.join(FEATURES[j] for j in removed),BIC=info['BIC'],BIC_training_RSS=info['training_RSS'],**innerinfo))
        print(case,region,'lambda',float(engine.ALPHAS[index]),'features',len(initial),'->',len(selected),flush=True)
    fold=pd.DataFrame(folds)
    csv(fold,folder/'fold_results.csv');csv(all_curve,folder/'inner_cv_curves.csv');csv(boundaries,folder/'fold_boundary_audit.csv');csv(all_history,folder/'backward_BIC_history.csv')
    csv(diagnostics,folder/'solver_diagnostics.csv');js(events,folder/'solver_events.json')
    csv([dict(feature=f,count=sum(f in set(s.split(';')) for s in fold.selected_features),frequency=sum(f in set(s.split(';')) for s in fold.selected_features)/9) for f in FEATURES],folder/'selection_frequency.csv')
    js(dict(case=case,folds=9,input_sha256=fingerprint),folder/'selection_complete.json')
    return fold

if __name__ == '__main__':
    check_runtime()
    select_features(read(ROOT/'inputs'/f'features_{args.case}.csv'),ROOT/'runs'/args.case,case=args.case)
