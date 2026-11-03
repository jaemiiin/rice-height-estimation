"""Re-run all main manuscript models in a new output directory."""
import argparse,os,shutil,sys,time,traceback
from pathlib import Path
from runtime_check import activate
sys.dont_write_bytecode=True
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--data-root');p.add_argument('--reference-root')
    a=p.parse_args()
    if a.data_root:os.environ['RICE_HEIGHT_DATA_ROOT']=str(Path(a.data_root).resolve())
    if a.reference_root:os.environ['RICE_HEIGHT_REFERENCE_ROOT']=str(Path(a.reference_root).resolve())
    runtime=activate();from paths import INPUTS, METADATA, REFERENCE
    package=Path(__file__).resolve().parents[1];out=Path(a.out).resolve()
    if out.exists():raise FileExistsError('Use a new directory: '+str(out))
    out.mkdir(parents=True);(out/'inputs').mkdir()
    for source in INPUTS.glob('*.csv'):shutil.copyfile(source,out/'inputs'/source.name)
    shutil.copyfile(METADATA/'retained_strip_coordinates.csv',out/'inputs/retained_strip_coordinates.csv');os.environ['RICE_REPRO_OUTPUT']=str(out)
    from common import js,read
    js(runtime,out/'runtime.json');started=time.time()
    try:
        import protocol,run_core,run_remaining,run_ridge,run_baselines,collect_results
        protocol.run(read(out/'inputs/features_continuous.csv'),out/'runs/continuous',case='continuous')
        run_core.run();run_remaining.main()
        for unit in ['image','strip']:
            for case in ['raw','otsu','continuous']:run_ridge.run(case,unit)
        run_baselines.run();collect_results.collect()
        from geometry_summary import export_geometry
        export_geometry(out)
        from verify_results import verify
        result=verify(out/'results',REFERENCE);result['seconds']=time.time()-started;js(result,out/'verification.json')
        print('PASS: all main manuscript models reproduced; '+str(out),flush=True)
    except Exception:
        (out/'FAILED.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
if __name__=='__main__':main()
