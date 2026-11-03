"""Manuscript fitting/weighting, recurrence, reference, ablation and date analyses."""
from protocol import *
import image_ml_baseline_analysis as ml
import platform, scipy, sklearn

def summarize(pred):return metrics(pred[TARGET],pred.prediction)
def regional(pred):return pd.DataFrame([dict(region=r,**summarize(g)) for r,g in pred.groupby('Region')])
def save(pred,name,models=None):
    csv(pred,ROOT/'predictions'/f'{name}.csv');csv(regional(pred),ROOT/'results'/f'{name}_regions.csv')
    if models is not None:js(models,ROOT/'models'/f'{name}.json')
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

def run():
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
    reference=[];checks=[]
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
if __name__=='__main__':run()
