"""Optional spatial fitting from the 71 packaged feature matrices."""
import argparse,os,sys
from pathlib import Path
from runtime_check import activate
sys.dont_write_bytecode=True
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    p.add_argument('--condition',default='edge6__continuous',help='One condition_id, or all');p.add_argument('--data-root');p.add_argument('--reference-root');a=p.parse_args()
    if a.data_root:os.environ['RICE_HEIGHT_DATA_ROOT']=str(Path(a.data_root).resolve())
    if a.reference_root:os.environ['RICE_HEIGHT_REFERENCE_ROOT']=str(Path(a.reference_root).resolve())
    runtime=activate()
    out=Path(a.out).resolve()
    if out.exists():raise FileExistsError('Use a new output directory: '+str(out))
    out.mkdir(parents=True);os.environ['RICE_REPRO_OUTPUT']=str(out)
    from common import SPATIAL_INPUTS,SPATIAL_METADATA,SPATIAL_REFERENCE,FEATURES,ID,TARGET,read,csv,js,np,pd,metrics
    from protocol import run
    grid=read(SPATIAL_METADATA/'experiment_grid.csv')
    selected=grid if a.condition=='all' else grid[grid.condition_id==a.condition]
    if selected.empty:raise ValueError('Unknown condition: '+a.condition)
    expected=read(SPATIAL_REFERENCE/'all_image_predictions.csv');reports=[]
    for row in selected.itertuples():
        data=read(SPATIAL_INPUTS/f'{row.condition_id}.csv')
        assert len(data)==92*row.k and data.groupby(['Region',ID]).size().eq(row.k).all()
        assert data.columns.tolist()==['Region',ID,'site_date']+FEATURES+[TARGET]
        pred,_=run(data,out/'runs'/row.condition_id,case=row.condition_id)
        ref=expected[expected.condition_id==row.condition_id];keys=['Region',ID,'site_date',TARGET]
        actual=pred.sort_values(keys).reset_index(drop=True);ref=ref.sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual[keys],ref[keys],check_exact=True)
        delta=float(np.max(abs(actual.prediction-ref.prediction)));assert delta<1e-8,(row.condition_id,delta)
        reports.append(dict(condition_id=row.condition_id,max_abs_prediction_difference=delta,**metrics(pred[TARGET],pred.prediction)))
    csv(reports,out/'metrics.csv');js(dict(status='PASS',conditions=len(reports),runtime=runtime),out/'verification.json')
    print('Spatial reproduction PASS:',len(reports),flush=True)
if __name__=='__main__':main()
