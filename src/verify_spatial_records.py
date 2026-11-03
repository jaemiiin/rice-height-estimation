"""Check all 71 stored spatial inputs and re-score their saved OOF predictions; no fitting."""
from common import *

def verify():
    grid=read(SPATIAL_METADATA/'experiment_grid.csv')
    pred=read(SPATIAL_REFERENCE/'all_image_predictions.csv');saved=read(SPATIAL_REFERENCE/'overall_metrics.csv').set_index('condition_id')
    reference=images(read(INPUTS/'features_continuous.csv'))[['Region',ID,'site_date',TARGET]].sort_values(['Region',ID]).reset_index(drop=True)
    assert len(grid)==71 and grid.spatial.nunique()==29 and grid.condition_id.is_unique
    reports=[]
    for row in grid.itertuples():
        data=read(SPATIAL_INPUTS/f'{row.condition_id}.csv')
        assert data.columns.tolist()==['Region',ID,'site_date']+FEATURES+[TARGET]
        assert len(data)==92*row.k and data.groupby(['Region',ID]).size().eq(row.k).all()
        assert np.isfinite(data[FEATURES+[TARGET]]).all().all()
        actual=images(data)[reference.columns].sort_values(['Region',ID]).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual,reference,check_exact=True)
        p=pred[pred.condition_id==row.condition_id].sort_values(['Region',ID]).reset_index(drop=True)
        pd.testing.assert_frame_equal(p[reference.columns],reference,check_exact=True)
        score=metrics(p[TARGET],p.prediction)
        for key in ['R2','RMSE','MAE']:assert abs(score[key]-saved.loc[row.condition_id,key])<1e-10
        reports.append(row.condition_id)
    return dict(status='PASS',conditions=len(reports),spatial_settings=29,OOF_predictions=len(pred),features=37,refitted=False,checked=reports)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--report');args=parser.parse_args();report=verify()
    if args.report:js(report,args.report)
    print(json.dumps({k:v for k,v in report.items() if k!='checked'},indent=2))
