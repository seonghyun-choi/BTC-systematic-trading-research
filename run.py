from pathlib import Path
import json,hashlib,zipfile
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent
P=json.loads((R/'plan.json').read_text())
MINUTE=60000;FUNDING=8*3600*1000
def window_all(x,n=3):
 out=x.copy()
 for k in range(1,n):out[k:]&=x[:-k];out[:k]=False
 return out
def signals(fi,si,valid):
 v=window_all(valid);prev_v=np.r_[False,v[:-1]];out={}
 for side,sign in [('LONG',1),('SHORT',-1)]:
  fs=window_all(sign*fi>=P['threshold']);ss=window_all(sign*si>=P['threshold'])
  ev=fs&~np.r_[False,fs[:-1]]&v&prev_v
  out[side]=(np.flatnonzero(ev),ss)
 return out
def load_market(market,grid):
 frames=[];audit=[];sources=json.loads((R/'sources.json').read_text())
 for src in [x for x in sources if x['market']==market]:
  path=R/'raw'/market/f"BTCUSDT-1m-{src['month']}.zip";assert hashlib.sha256(path.read_bytes()).hexdigest()==src['sha256']
  with zipfile.ZipFile(path) as z:d=pd.read_csv(z.open(z.namelist()[0]),header=None)
  d=d[pd.to_numeric(d[0],errors='coerce').notna()].apply(pd.to_numeric).reset_index(drop=True)
  t=d[0].to_numpy(dtype=np.int64);assert np.all(np.diff(t)>0) and np.all(t%MINUTE==0)
  m=pd.Timestamp(src['month']+'-01',tz='UTC');lo=m.value//1000000;hi=(m+pd.offsets.MonthBegin(1)).value//1000000
  assert np.all((t>=lo)&(t<hi))
  prices=(d[[1,2,3,4]]>0).all(axis=1)&np.isfinite(d[[1,2,3,4]]).all(axis=1)&(d[2]>=d[[1,3,4]].max(axis=1))&(d[3]<=d[[1,2,4]].min(axis=1))
  volume=(d[5]>=0)&(d[7]>=0)&(d[8]>=0)&(d[9]>=0)&(d[10]>=0)&(d[9]<=d[5]+1e-8)&(d[10]<=d[7]+1e-6)
  clock=(d[6]==d[0]+59999);good=prices&volume&clock&(d[7]>0)&(d[8]>0)
  audit.append(dict(market=market,month=src['month'],rows=len(d),expected_minutes=int((hi-lo)//MINUTE),missing=int((hi-lo)//MINUTE-len(d)),invalid_ohlc=int((~prices).sum()),invalid_volume=int((~volume).sum()),zero_quote_minutes=int((d[7]==0).sum()),bad_close_timestamp=int((~clock).sum()),duplicates=0,out_of_order=0,large_close_jumps_gt5pct=int((d[4].pct_change().abs()>.05).sum())))
  f=pd.DataFrame({'open':d[1].to_numpy(),'imbalance':np.where(good,2*d[10]/d[7]-1,np.nan),'valid':good.to_numpy()},index=t)
  f.loc[~prices.to_numpy(),'open']=np.nan;frames.append(f)
 f=pd.concat(frames);assert f.index.is_unique and f.index.is_monotonic_increasing
 return f.reindex(grid),audit
def eligible(indices,grid):
 entry_idx=indices+2
 in_bounds=entry_idx+max(P['holding_minutes'])<len(grid)
 entry_ms=grid[0]+entry_idx*MINUTE
 next_fund=(entry_ms//FUNDING+1)*FUNDING
 no_funding=(entry_ms%FUNDING!=0)&(entry_ms+max(P['holding_minutes'])*MINUTE<next_fund)
 return in_bounds&no_funding
def trade(indices,confirmed,opens,grid,side,h,arm,lock_positions=True):
 sign=1 if side=='LONG' else -1;lock=-1;rows=[];audit=dict(locked=0,missing_entry=0,delayed_exit=0,unresolved=0,funding_cross=0)
 for i in indices:
  if arm=='SPOT_CONFIRMED' and not confirmed[i]:continue
  signal_ms=int(grid[i]+MINUTE)
  if lock_positions and signal_ms<=lock:audit['locked']+=1;continue
  ei=i+2
  if not np.isfinite(opens[ei]) or opens[ei]<=0:audit['missing_entry']+=1;continue
  xi=ei+h;requested=xi
  while xi<len(opens) and (not np.isfinite(opens[xi]) or opens[xi]<=0):xi+=1
  if xi>=len(opens):
   audit['unresolved']+=1;rows.append(dict(side=side,arm=arm,hold=h,signal_ms=signal_ms,entry_ms=int(grid[ei]),status='unresolved'));break
  delayed=xi-requested;audit['delayed_exit']+=int(delayed>0)
  crossed=grid[xi]>=(grid[ei]//FUNDING+1)*FUNDING;audit['funding_cross']+=int(crossed)
  ratio=opens[xi]/opens[ei];gross=sign*(ratio-1)*10000;fee=3*(1+ratio)
  row=dict(side=side,arm=arm,hold=h,signal_ms=signal_ms,entry_ms=int(grid[ei]),exit_ms=int(grid[xi]),entry=opens[ei],exit=opens[xi],confirmed=bool(confirmed[i]),gross_bp=gross,fee_bp=fee,net6_bp=gross-fee,net8_bp=gross-fee-2,net10_bp=gross-fee-4,exit_delay_minutes=int(delayed),funding_cross=bool(crossed),status='closed')
  rows.append(row);lock=int(grid[xi])
 return rows,audit
def statistics(g,days):
 r=dict(n=len(g),gross_bp=float(g.gross_bp.mean()),fee_bp=float(g.fee_bp.mean()),trades_per_calendar_day=len(g)/days,active_days=int(g.day.nunique()),break_even_fee_bp=2*g.gross_bp.sum()/(1+g.exit/g.entry).sum() if len(g) else np.nan)
 for c in (6,8,10):
  v=g[f'net{c}_bp'];w=v[v>0];loss=v[v<0]
  r.update({f'net{c}_bp':v.mean(),f'median{c}_bp':v.median(),f'win{c}':(v>0).mean(),f'pf{c}':w.sum()/-loss.sum() if len(loss) else np.nan,f'avgwin{c}_bp':w.mean(),f'avgloss{c}_bp':loss.mean()})
 return r
def main():
 assert hashlib.sha256((R/'plan.json').read_bytes()).hexdigest()==(R/'frozen_plan.sha256').read_text().strip()
 grid=pd.date_range('2020-01-01','2023-01-01',freq='min',inclusive='left',tz='UTC').asi8//1000000
 fut,af=load_market('futures',grid);spot,asp=load_market('spot',grid)
 audit=af+asp;pd.DataFrame(audit).to_csv(R/'data_audit.csv',index=False)
 valid=fut.valid.fillna(False).to_numpy(dtype=bool)&spot.valid.fillna(False).to_numpy(dtype=bool)
 for day in P['known_spot_quality_exclusion']:
  start=pd.Timestamp(day,tz='UTC').value//1000000;valid[(grid>=start)&(grid<start+86400*1000)]=False
 fi=fut.imbalance.to_numpy();si=spot.imbalance.to_numpy();sig=signals(fi,si,valid)
 checks=[]
 for date in ['2020-07-01','2021-07-01','2022-07-01']:
  cut=np.searchsorted(grid,pd.Timestamp(date,tz='UTC').value//1000000);prefix=signals(fi[:cut],si[:cut],valid[:cut])
  for side in sig:
   np.testing.assert_array_equal(prefix[side][0],sig[side][0][sig[side][0]<cut]);np.testing.assert_array_equal(prefix[side][1],sig[side][1][:cut])
  checks.append(dict(cutoff=date,prefix_pass=True))
 events=[];trades=[];exec_audit=[];diagnostic=[]
 opens=fut.open.to_numpy()
 for side,(idx,cf) in sig.items():
  ok=eligible(idx,grid);events.extend([dict(side=side,signal_ms=int(grid[i]+MINUTE),confirmed=bool(cf[i]),eligible=bool(e)) for i,e in zip(idx,ok)])
  idx=idx[ok]
  for h in P['holding_minutes']:
   for arm in P['arms']:
    rows,a=trade(idx,cf,opens,grid,side,h,arm);trades+=rows;exec_audit.append(dict(side=side,hold=h,arm=arm,**a))
  rows,a=trade(idx,cf,opens,grid,side,P['primary_hold'],'FUTURES_ONLY',False);diagnostic+=rows
  print('completed',side,'events',len(idx),flush=True)
 ev=pd.DataFrame(events);ev.to_csv(R/'events.csv.gz',index=False)
 tr=pd.DataFrame(trades);tr.to_csv(R/'trades.csv.gz',index=False);d=pd.DataFrame(diagnostic);d.to_csv(R/'unblocked_diagnostic.csv.gz',index=False)
 (R/'execution_audit.json').write_text(json.dumps(exec_audit,indent=2));(R/'prefix_checks.json').write_text(json.dumps(checks,indent=2))
 closed=tr[tr.status=='closed'].copy();dt=pd.to_datetime(closed.entry_ms,unit='ms',utc=True);closed['year']=dt.dt.year;closed['day']=dt.dt.strftime('%Y-%m-%d')
 perf=[];daily=[];all_days=pd.date_range('2020-01-01','2022-12-31',freq='D').strftime('%Y-%m-%d')
 for key,g in closed.groupby(['arm','side','hold']):
  g=g.sort_values('entry_ms');assert (g.entry_ms.to_numpy()[1:]>g.exit_ms.to_numpy()[:-1]).all()
  assert (g.entry_ms==g.signal_ms+MINUTE).all() and (g.exit_ms>=g.entry_ms+key[2]*MINUTE).all()
  for y in ['ALL',2020,2021,2022]:
   part=g if y=='ALL' else g[g.year==y];nd=1096 if y=='ALL' else (366 if y==2020 else 365)
   perf.append(dict(arm=key[0],side=key[1],hold=int(key[2]),year=y,**statistics(part,nd)))
  agg=g.groupby('day').agg(n=('net8_bp','size'),net8_sum_bp=('net8_bp','sum')).reindex(all_days,fill_value=0).reset_index(names='day')
  agg['arm']=key[0];agg['side']=key[1];agg['hold']=key[2];daily.append(agg)
 perf=pd.DataFrame(perf);perf.to_csv(R/'performance.csv',index=False);pd.concat(daily).to_csv(R/'daily.csv.gz',index=False)
 attribution=[]
 d=d[d.status=='closed'].copy();d['year']=pd.to_datetime(d.entry_ms,unit='ms',utc=True).dt.year
 for side,g in d.groupby('side'):
  for y in ['ALL',2020,2021,2022]:
   sub=g if y=='ALL' else g[g.year==y]
   for c in [False,True]:
    a=sub[sub.confirmed==c];attribution.append(dict(side=side,year=y,confirmed=c,n=len(a),gross_bp=a.gross_bp.mean(),net8_bp=a.net8_bp.mean()))
 pd.DataFrame(attribution).to_csv(R/'attribution.csv',index=False)
 totals=perf[perf.year=='ALL'];candidates=[]
 for side in ['LONG','SHORT']:
  a=perf[(perf.arm=='SPOT_CONFIRMED')&(perf.side==side)&(perf.hold==15)];total=a[a.year=='ALL'].iloc[0];years=a[a.year!='ALL']
  b=totals[(totals.arm=='FUTURES_ONLY')&(totals.side==side)&(totals.hold==15)].iloc[0]
  adj=totals[(totals.arm=='SPOT_CONFIRMED')&(totals.side==side)&(totals.hold!=15)]
  counts=[x for x in exec_audit if x['side']==side and x['arm']=='SPOT_CONFIRMED' and x['hold']==15]
  gates=dict(support=bool(total.n>=1000 and (years.n>=100).all()),frequency=bool(total.trades_per_calendar_day>=3 and (years.trades_per_calendar_day>=1).all()),net_positive=bool(total.net8_bp>0 and (years.net8_bp>0).all()),incremental=bool(total.net8_bp>b.net8_bp),neighbors=bool((adj.net8_bp>0).all()),execution=bool(all(x['unresolved']==0 and x['funding_cross']==0 for x in counts)))
  candidates.append(dict(side=side,gates=gates,preliminary_pass=all(gates.values()),net8_lift_bp=float(total.net8_bp-b.net8_bp)))
 summary=dict(settings=len(totals),positive6=int((totals.net6_bp>0).sum()),positive8=int((totals.net8_bp>0).sum()),positive10=int((totals.net10_bp>0).sum()),candidates=candidates,qualified=0,requires_uncertainty=any(x['preliminary_pass'] for x in candidates),unresolved=sum(x['unresolved'] for x in exec_audit),funding_cross=sum(x['funding_cross'] for x in exec_audit))
 (R/'summary.json').write_text(json.dumps(summary,indent=2));print(totals.to_string(index=False));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
