"""Step 06: image-level and regional metrics, manuscript comparisons, and output tables."""
from pathlib import Path
if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Analysis output root shared by steps 04-07')
    args = parser.parse_args()
    os.environ['RICE_REPRO_OUTPUT'] = str(args.out.resolve())
from _common import *

MANUSCRIPT={'primary':(.9000,6.67,5.06),'fold_specific_image_OLS':(.8702,7.59,5.87),
 'baseline_elastic':(.8834,7.20,5.53),'ridge_image_continuous':(.8736,7.50,5.66),
 'ridge_strip_continuous':(.9037,6.54,4.94),'baseline_pcr':(.8298,8.70,6.58),
 'baseline_knn':(.7349,10.86,7.92),'baseline_mlp':(.7292,10.97,7.00),
 'baseline_rgb':(.8118,9.15,6.90),'baseline_mean':(-.0065,21.15,19.16)}

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

def export_geometry(ROOT):
    coords=read(ROOT/'inputs/retained_strip_coordinates.csv');shifts=[];coverage=[]
    for (region,name),g in coords.groupby(['Region',ID],sort=True):
        g=g.sort_values('strip_order');w=int(g.iloc[0].width)
        coverage.append(float((g.x2-g.x1).sum()/w))
        for side,j in [('left',0),('right',3)]:
            edges=np.floor(np.linspace(g.iloc[j].x1,g.iloc[j+2].x2,4)).astype(int)
            for k in [1,2]:shifts.append(dict(side=side,pixels=abs(int(g.iloc[j+k-1].x2)-int(edges[k])),width=w))
    sh=pd.DataFrame(shifts);summary=[]
    for side in ['all','left','right']:
        g=sh if side=='all' else sh[sh.side==side]
        for unit,x in [('pixels',g.pixels),('image_width_fraction',g.pixels/g.width)]:
            summary.append(dict(side=side,unit=unit,n=len(x),median=float(np.median(x)),mean=float(np.mean(x)),p95=float(np.quantile(x,.95)),max=float(np.max(x))))
    csv(summary,ROOT/'results/partition_boundary_summary.csv')
    cov=[]
    for case in ['continuous','full','matched']:
        x=np.ones(92) if case=='full' else np.array(coverage)
        cov.append(dict(partition=case,n_images=92,mean=float(x.mean()),median=float(np.median(x)),min=float(x.min()),max=float(x.max())))
    csv(cov,ROOT/'results/partition_coverage_summary.csv')

def evaluate(all_analyses=False):
    """Score actual predictions; expected values are verification targets only."""
    check_runtime()
    for case in ['raw','otsu','continuous','matched','full']:
        validate_features(read(ROOT/'inputs'/f'features_{case}.csv'))
    if all_analyses:
        collect();export_geometry(ROOT)
        pred=read(ROOT/'results/predictions.csv')
    else:
        pred=read(ROOT/'runs/continuous/oof_predictions.csv').assign(analysis='primary')
    scores={};target=images(read(ROOT/'inputs/features_continuous.csv'))[['Region',ID,'site_date',TARGET]].sort_values(['Region',ID]).reset_index(drop=True)
    for name,g in pred.groupby('analysis'):
        assert len(g)==92 and not g.duplicated(['Region',ID]).any()
        pd.testing.assert_frame_equal(g[target.columns].sort_values(['Region',ID]).reset_index(drop=True),target,check_exact=True)
        scores[name]=metrics(g[TARGET],g.prediction)
    if all_analyses:assert len(scores)==24
    checks=[]
    for name,expected in MANUSCRIPT.items():
        if name not in scores:continue
        for key,digits,value in zip(['R2','RMSE','MAE'],[4,2,2],expected):
            checks.append(dict(analysis=name,metric=key,actual=scores[name][key],reported=value,match=round(scores[name][key],digits)==value))
    report=dict(status='PASS' if all(c['match'] for c in checks) else 'MISMATCH',analyses=len(scores),OOF_predictions=len(pred),metrics=scores,rounded_manuscript_checks=checks)
    js(report,ROOT/('verification.json' if all_analyses else 'primary_verification.json'))
    csv([dict(region=r,**metrics(g[TARGET],g.prediction)) for r,g in pred[pred.analysis=='primary'].groupby('Region')],ROOT/'primary_region_metrics.csv')
    print(json.dumps(report,indent=2),flush=True)
    if report['status']!='PASS':raise RuntimeError('Actual results differ from manuscript targets; see the written report')
    return report

if __name__ == '__main__':
    evaluate(all_analyses=(ROOT/'predictions/baseline_mlp.csv').exists())
