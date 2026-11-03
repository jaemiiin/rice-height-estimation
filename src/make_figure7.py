"""Render only Figure 7 from the verified 37-feature rerun, in the original style."""
from pathlib import Path
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(Path(os.environ.get('TEMP','/tmp'))/'rice_settings_v1_mpl'))
for variable in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[variable] = '1'

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--results',default=str(PACKAGE/'results/reference'));args=parser.parse_args()
    results=Path(args.results);out=Path(args.out).resolve()
    if out.exists():raise FileExistsError('Use a new directory: '+str(out))
    config = json.loads((PACKAGE / 'config.json').read_text(encoding='utf-8'))
    features = config['feature_order']
    assert len(features) == len(set(features)) == 37 and 'NDBGRI' not in features
    freq = pd.read_csv(results / 'recurrence_counts.csv').set_index('feature').loc[features].reset_index()
    folds = pd.read_csv(results / 'fold_selected_features.csv')
    assert len(folds) == 9 and folds.held_region.nunique() == 9
    expected = [sum(f in s.split(';') for s in folds.selected_features) for f in features]
    assert freq['count'].tolist() == expected
    cmax = int(freq['count'].max())
    out.mkdir(parents=True)

    # Original Figure 7 plotting statements, with only the candidate input changed.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    fig,a=plt.subplots(figsize=(6.6,8.4),layout='constrained');highlight='#218879';other='#b8c8d4'
    a.barh(freq.feature,freq['count'],color=[highlight if n==cmax else other for n in freq['count']]);a.invert_yaxis()
    a.set(xlim=(0,9.55),xticks=range(10),xlabel='Number of regional training folds selecting the feature')
    a.tick_params(axis='y',labelsize=11);a.grid(axis='x',alpha=.10);a.set_axisbelow(True)
    for i,n in enumerate(freq['count']):a.text(n+.10,i,str(n),va='center',fontsize=10)
    a.legend(handles=[Patch(facecolor=highlight,label=f'Maximum recurrence: {cmax} of 9 folds')],loc='lower right',frameon=False,fontsize=9)

    assert len(a.patches) == 37
    assert [t.get_text() for t in a.get_yticklabels()] == features
    fig.savefig(out / 'fig07_selection.pdf', bbox_inches='tight')
    fig.savefig(out / 'fig07_selection.png', bbox_inches='tight', dpi=300)
    plt.close(fig)
    log = dict(figure='Figure 7',candidate_count=37,feature_order=features,
               recurrence_verified_from_nine_folds=True,maximum_recurrence=cmax,
               original_plot_style_preserved=True,NDBGRI_absent=True,
               output_pdf='fig07_selection.pdf',output_png='fig07_selection.png',
               png_dpi=300,pdf_vector_graphics=True)
    (out / 'figure7_validation.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
    print('Figure 7 PDF and 300-dpi PNG saved; 37 feature labels and all recurrence counts verified.')

if __name__ == '__main__':
    main()
