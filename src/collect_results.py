"""Collect current results, with no old-score fallback."""
from common import *
def collect():
    paths={'primary':ROOT/'runs/continuous/oof_predictions.csv'}
    for case in ['raw','otsu','matched','full']:paths['selection_'+case]=ROOT/f'runs/{case}/oof_predictions.csv'
    for unit in ['image','strip']:
        for case in ['raw','otsu','continuous']:paths[f'ridge_{unit}_{case}']=ROOT/f'ridge/{unit}/{case}/oof_predictions.csv'
    for name in ['fold_specific_image_OLS','reference_strip_mean','reference_image_mean','ablation_Color_only','ablation_Color_plus_complexity','ablation_Color_plus_position','baseline_mean','baseline_rgb','baseline_elastic','baseline_pcr','baseline_knn','baseline_mlp']:paths[name]=ROOT/f'predictions/{name}.csv'
    data=images(read(ROOT/'inputs/features_continuous.csv'))
    sites=data.groupby(['Region','site_date'],as_index=False).agg({TARGET:'first'})
    primary=read(paths['primary']);parts=[]
    for region,g in primary.groupby('Region'):
        means=sites[sites.Region!=region].groupby('site_date')[TARGET].mean()
        out=g.copy();out['prediction']=out.site_date.map(means)
        assert out.prediction.notna().all();parts.append(out)
    csv(pd.concat(parts,ignore_index=True)[['Region',ID,'site_date',TARGET,'prediction']],ROOT/'predictions/date_only.csv')
    paths['date_only']=ROOT/'predictions/date_only.csv'
    columns=['analysis','Region',ID,'site_date',TARGET,'prediction']
    pred=pd.concat([read(p)[columns[1:]].assign(analysis=n) for n,p in paths.items()],ignore_index=True)[columns]
    pred=pred.sort_values(['analysis','Region',ID]).reset_index(drop=True)
    csv(pred,ROOT/'results/predictions.csv')
    csv([dict(analysis=n,**metrics(g[TARGET],g.prediction)) for n,g in pred.groupby('analysis')],ROOT/'results/metrics.csv')
    fold=read(ROOT/'runs/continuous/fold_results.csv')
    csv(fold[['held_region','lambda_value','initial_selected_features','selected_features','selected_feature_count','BIC']],ROOT/'results/fold_selected_features.csv')
    csv(read(ROOT/'results/recurrence_all37.csv'),ROOT/'results/recurrence_counts.csv')
    csv(read(ROOT/'results/full_data_coefficients.csv'),ROOT/'results/reference_coefficients.csv')
    csv(pd.concat([read(ROOT/f'ridge/{u}/{c}/pooled_metrics.csv') for u in ['image','strip'] for c in ['raw','otsu','continuous']],ignore_index=True),ROOT/'results/ridge_metrics.csv')
    baselines=read(ROOT/'results/baseline_metrics_without_ridge.csv')
    ridge=read(ROOT/'ridge/image/continuous/pooled_metrics.csv').drop(columns=['case','unit']).assign(Model='Ridge',method='ridge')
    csv(pd.concat([baselines,ridge],ignore_index=True),ROOT/'results/baseline_metrics.csv')
if __name__=='__main__':collect()
