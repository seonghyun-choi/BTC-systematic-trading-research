from pathlib import Path
import pandas as pd,numpy as np,zipfile,json
R=Path(__file__).resolve().parent
rows=[];bad=[]
for p in sorted((R/'raw/spot').glob('*.zip')):
 with zipfile.ZipFile(p) as z:d=pd.read_csv(z.open(z.namelist()[0]),header=None,usecols=[0,6])
 d=d[pd.to_numeric(d[0],errors='coerce').notna()].apply(pd.to_numeric)
 month=p.stem[-7:];start=pd.Timestamp(month+'-01',tz='UTC');end=start+pd.offsets.MonthBegin(1)
 grid=pd.date_range(start,end,freq='min',inclusive='left').asi8//1000000
 missing=grid[~np.isin(grid,d[0].to_numpy())]
 if len(missing):
  groups=np.split(missing,np.flatnonzero(np.diff(missing)>60000)+1)
  for g in groups:rows.append(dict(start_utc=pd.to_datetime(g[0],unit='ms',utc=True).isoformat(),end_exclusive_utc=pd.to_datetime(g[-1]+60000,unit='ms',utc=True).isoformat(),minutes=len(g)))
 for _,r in d[d[6]!=d[0]+59999].iterrows():bad.append(dict(month=month,open_ms=int(r[0]),close_ms=int(r[6]),expected_close_ms=int(r[0]+59999)))
pd.DataFrame(rows).to_csv(R/'spot_missing_intervals.csv',index=False);pd.DataFrame(bad).to_csv(R/'spot_bad_close_times.csv',index=False)
print(json.dumps(dict(missing_minutes=sum(x['minutes'] for x in rows),intervals=len(rows),max_gap_minutes=max(x['minutes'] for x in rows),bad_close_rows=len(bad))))
