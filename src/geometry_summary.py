from common import *

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
