"""Re-score OOF records and compare with the current 37-feature manuscript."""
from common import *
MANUSCRIPT={'primary':(.9000,6.67,5.06),'fold_specific_image_OLS':(.8702,7.59,5.87),
 'baseline_elastic':(.8834,7.20,5.53),'ridge_image_continuous':(.8736,7.50,5.66),
 'ridge_strip_continuous':(.9037,6.54,4.94),'baseline_pcr':(.8298,8.70,6.58),
 'baseline_knn':(.7349,10.86,7.92),'baseline_mlp':(.7292,10.97,7.00),
 'baseline_rgb':(.8118,9.15,6.90),'baseline_mean':(-.0065,21.15,19.16)}
def verify(folder=None,reference=None):
    folder=Path(folder or REFERENCE);reference=Path(reference or REFERENCE)
    assert len(FEATURES)==37 and 'NDBGRI' not in FEATURES
    inputs={}
    for case in ['continuous','raw','otsu','matched','full']:
        frame=read(INPUTS/f'features_{case}.csv')
        assert list(frame.columns)==['Region',ID,'site_date']+FEATURES+[TARGET]
        assert frame.shape==(552,41) and frame.groupby(['Region',ID]).size().eq(6).all()
        assert frame.groupby(['Region','site_date'])[TARGET].nunique().eq(1).all()
        assert len(images(frame))==92 and np.isfinite(frame[FEATURES+[TARGET]]).all().all()
        inputs[case]=dict(strips=552,images=92,features=37)
    pred=read(folder/'predictions.csv');expected=read(reference/'predictions.csv');sort=['analysis','Region',ID]
    pred=pred.sort_values(sort).reset_index(drop=True);expected=expected.sort_values(sort).reset_index(drop=True)
    pd.testing.assert_frame_equal(pred.drop(columns='prediction'),expected.drop(columns='prediction'),check_exact=True)
    differences=abs(pred.prediction-expected.prediction);assert differences.max()<1e-8,float(differences.max())
    scores={}
    target=images(read(INPUTS/'features_continuous.csv'))[['Region',ID,'site_date',TARGET]].sort_values(['Region',ID]).reset_index(drop=True)
    for name,g in pred.groupby('analysis'):
        assert len(g)==92 and not g.duplicated(['Region',ID]).any()
        pd.testing.assert_frame_equal(g[target.columns].sort_values(['Region',ID]).reset_index(drop=True),target,check_exact=True)
        scores[name]=metrics(g[TARGET],g.prediction)
    assert len(scores)==24
    for name,values in MANUSCRIPT.items():
        for key,digits,v in zip(['R2','RMSE','MAE'],[4,2,2],values):assert round(scores[name][key],digits)==v,(name,key,scores[name][key],v)
    for row in read(folder/'metrics.csv').to_dict('records'):
        for key in ['R2','RMSE','MAE']:assert abs(row[key]-scores[row['analysis']][key])<1e-10
    comparisons=[]
    for name in ['fold_selected_features.csv','recurrence_counts.csv','reference_coefficients.csv','reference_metrics.csv','ridge_metrics.csv','primary_region_metrics.csv']:
        actual=read(folder/name);saved=read(reference/name)
        if name=='primary_region_metrics.csv':actual=actual.rename(columns={'region':'held_region'})
        columns=[c for c in saved.columns if c in actual.columns]
        assert {'R2','RMSE','MAE'}.issubset(columns) if name in ['reference_metrics.csv','ridge_metrics.csv','primary_region_metrics.csv'] else len(columns)>=2
        keys=[c for c in ['held_region','feature','mode','unit','case'] if c in columns]
        if keys:
            actual=actual.sort_values(keys).reset_index(drop=True)
            saved=saved.sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual[columns],saved[columns],check_exact=False,rtol=0,atol=1e-8);comparisons.append(name)
    folds=read(folder/'fold_selected_features.csv');freq=read(folder/'recurrence_counts.csv')
    assert len(folds)==9 and len(freq)==37
    counts={f:sum(f in s.split(';') for s in folds.selected_features) for f in FEATURES}
    assert all(counts[r.feature]==r.count for r in freq.itertuples())
    assert [f for f in FEATURES if counts[f]==max(counts.values())]==['start','end','complexity','mean_R','MGRVI','COM'] and max(counts.values())==8
    return dict(status='PASS',features=37,inputs=inputs,OOF_analyses=len(scores),OOF_predictions=len(pred),max_abs_prediction_difference=float(differences.max()),compared_result_tables=comparisons,manuscript_rounded_checks=len(MANUSCRIPT)*3,metrics=scores)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--results');p.add_argument('--compare-to');p.add_argument('--report');a=p.parse_args()
    result=verify(a.results,a.compare_to)
    if a.report:js(result,a.report)
    print(json.dumps({k:v for k,v in result.items() if k not in ['metrics','inputs']},ensure_ascii=False,indent=2))
