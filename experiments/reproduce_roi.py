"""Optional 34/35-candidate ROI comparisons, separate from the primary evaluation."""
from pathlib import Path
import argparse, importlib, os, shutil, sys
sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant', choices=['34','35'], required=True)
    p.add_argument('--data-root', type=Path, default=PROJECT / 'data')
    p.add_argument('--reference-root', type=Path, default=PROJECT / 'results/reference')
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    from runtime_check import activate
    activate()
    out = a.out.resolve()
    if out.exists(): raise FileExistsError('Use a new output directory')
    data = a.data_root.resolve(); out.mkdir(parents=True)
    shutil.copytree(data / 'processed' / ('roi'+a.variant), out / 'inputs')
    shutil.copyfile(PROJECT / 'config' / ('roi'+a.variant+'.json'), out / 'experiment_config.json')
    (out / 'validation').mkdir()
    shutil.copyfile(data / 'metadata' / ('roi'+a.variant+'_pixel_validation.json'), out / 'validation/pixel_extraction.json')
    os.environ['RICE_REPRO_OUTPUT'] = str(out)
    importlib.import_module('roi'+a.variant+'_models').main()
    import pandas as pd
    checks=[]
    for name in ['oof_predictions.csv','results_common_features.csv','results_independent_selection.csv','selected_features_by_fold.csv','regional_results.csv','loss_identity_checks.csv']:
        actual=pd.read_csv(out/name,float_precision='round_trip')
        expected=pd.read_csv(a.reference_root/('roi'+a.variant)/name,float_precision='round_trip')
        pd.testing.assert_frame_equal(actual,expected,check_exact=False,rtol=0,atol=1e-8)
        checks.append(name)
    from common import js
    js(dict(status='PASS',variant=a.variant,analyses=8,OOF_predictions=736,compared_tables=checks,fresh_model_fitting=True,fresh_pixel_extraction=False),out/'verification.json')
    print('PASS: optional ROI comparison reproduced')

if __name__ == '__main__': main()
