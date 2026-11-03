"""Four independent selection reruns and all-feature Ridge sensitivities."""
from protocol import *
import importlib.util
def main():
    for case in ['raw','otsu','matched','full']:
        run(read(ROOT/'inputs'/f'features_{case}.csv'),ROOT/'runs'/case,case=case)
    preds={c:read(ROOT/'runs'/c/'oof_predictions.csv') for c in ['raw','otsu','continuous']}
    csv([dict(case=c,**metrics(p[TARGET],p.prediction)) for c,p in preds.items()],ROOT/'results/representation_metrics.csv')
    csv([dict(case=c,region=r,**metrics(g[TARGET],g.prediction)) for c,p in preds.items() for r,g in p.groupby('Region')],ROOT/'results/representation_region_metrics.csv')
    csv([dict(case=c,site_date=d,**metrics(g[TARGET],g.prediction)) for c,p in preds.items() for d,g in p.groupby('site_date')],ROOT/'results/representation_date_metrics.csv')
    csv([dict(partition=c,**metrics((p:=read(ROOT/'runs'/c/'oof_predictions.csv'))[TARGET],p.prediction)) for c in ['continuous','matched','full']],ROOT/'results/partition_metrics.csv')
    print('All four selection reruns completed',flush=True)
if __name__=='__main__':main()
