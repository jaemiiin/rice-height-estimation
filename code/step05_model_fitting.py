"""Step 05: strip-level OLS, image-level OLS, and regional held-out predictions."""
from pathlib import Path
if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Analysis output root shared by steps 04-07')
    parser.add_argument('--case', default='continuous', choices=['raw','otsu','continuous','matched','full'])
    args = parser.parse_args()
    os.environ['RICE_REPRO_OUTPUT'] = str(args.out.resolve())
from _common import *

from sklearn.preprocessing import StandardScaler

def fit_selected(strips,folder,case=''):
    """Fit the nine held-region models from step04's saved selections."""
    folder=Path(folder);validate_features(strips)
    signature=folder/'input.sha256'
    assert signature.read_text()==input_fingerprint(strips), 'Selections and fitting inputs differ'
    assert (folder/'selection_complete.json').exists(), 'Run step04 first'
    fold=read(folder/'fold_results.csv');regions=sorted(strips.Region.unique())
    assert len(fold)==9 and sorted(fold.held_region)==regions
    all_preds=[];strip_preds=[];models=[]
    for record in fold.itertuples():
        region=record.held_region
        chosen=record.selected_features.split(';') if pd.notna(record.selected_features) else []
        selected=tuple(FEATURES.index(f) for f in chosen)
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
        models.append(dict(held_region=region,selected_features=chosen,scaler_training_regions=sorted(train.Region.unique()),n_fit_strips=len(train),means=scaler.mean_.tolist(),scales=scaler.scale_.tolist(),standardized_coefficients=beta.tolist(),design_rank=int(np.linalg.matrix_rank(design)),n_coefficients=len(beta),design_condition=float(np.linalg.cond(design)),pinv_rcond=1e-15))
    pred=pd.concat(all_preds,ignore_index=True)
    csv(pred,folder/'oof_predictions.csv');csv(pd.concat(strip_preds,ignore_index=True),folder/'strip_predictions.csv')
    js(models,folder/'fold_models.json')
    csv([dict(case=case,region=r,**metrics(g[TARGET],g.prediction)) for r,g in pred.groupby('Region')],folder/'region_metrics.csv')
    csv([dict(case=case,**metrics(pred[TARGET],pred.prediction))],folder/'pooled_metrics.csv')
    return pred,fold

def run(strips,folder,selection_unit='image',case=''):
    """Shared complete LORO protocol used by the comparison stage."""
    from step04_feature_selection import select_features
    select_features(strips,folder,selection_unit,case)
    return fit_selected(strips,folder,case)

def aggregate(frame):return frame.groupby(['Region',ID,'site_date'],as_index=False,sort=True).agg({**dict.fromkeys(FEATURES,'mean'),TARGET:'first'})

def pred_ols(data,selected,unit='strip',agg='mean'):
    rows=[];models=[]
    for region in sorted(data.Region.unique()):
        train=data[data.Region!=region];test=data[data.Region==region]
        if unit=='image':train=aggregate(train);test=aggregate(test)
        names=selected[region] if isinstance(selected,dict) else selected
        scaler=StandardScaler().fit(train[names]);x=np.column_stack([np.ones(len(train)),scaler.transform(train[names])]);xt=np.column_stack([np.ones(len(test)),scaler.transform(test[names])])
        beta=np.linalg.pinv(x,rcond=1e-15)@train[TARGET].to_numpy()
        out=test[['Region',ID,'site_date',TARGET]].copy();out['prediction']=xt@beta
        rows.append(out.groupby(['Region',ID,'site_date'],sort=True,as_index=False).agg({TARGET:'first','prediction':agg}))
        models.append(dict(held_region=region,features=names,training_regions=sorted(train.Region.unique()),n_training=len(train),unit=unit,aggregation=agg,mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),coefficients=beta.tolist(),pinv_rcond=1e-15))
    return pd.concat(rows,ignore_index=True),models

if __name__ == '__main__':
    check_runtime()
    fit_selected(read(ROOT/'inputs'/f'features_{args.case}.csv'),ROOT/'runs'/args.case,case=args.case)
