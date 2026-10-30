from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import urllib.request,hashlib,json,shutil
R=Path(__file__).resolve().parent
MONTHS=[f'{y}-{m:02}' for y in (2020,2021,2022) for m in range(1,13)]
def fetch(month):
 name=f'BTCUSDT-1m-{month}.zip';p=R/'raw/spot'/name;p.parent.mkdir(parents=True,exist_ok=True)
 url=f'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/{name}'
 chk=urllib.request.urlopen(url+'.CHECKSUM',timeout=60).read();expected=chk.decode().split()[0]
 if not p.exists():
  with urllib.request.urlopen(url,timeout=60) as response:p.write_bytes(response.read())
 sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==expected,(month,'checksum')
 Path(str(p)+'.CHECKSUM').write_bytes(chk)
 return dict(market='spot',month=month,url=url,sha256=sha,bytes=p.stat().st_size,download_utc=datetime.now(timezone.utc).isoformat(),checksum_verified=True)
def main():
 assert not (R/'sources.json').exists(),'Already downloaded; do not repeat'
 (R/'frozen_plan.sha256').write_text(hashlib.sha256((R/'plan.json').read_bytes()).hexdigest()+'\n')
 sources=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  for row in ex.map(fetch,MONTHS):sources.append(row);print('spot',row['month'],flush=True)
 for month in MONTHS:
  p=R.parent/'retest/raw'/f'BTCUSDT-1m-{month}.zip';c=Path(str(p)+'.CHECKSUM');sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==c.read_text().split()[0]
  target=R/'raw/futures'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);shutil.copyfile(c,str(target)+'.CHECKSUM')
  sources.append(dict(market='futures',month=month,url=f'https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m/{p.name}',sha256=sha,bytes=p.stat().st_size,checksum_verified=True,reused_from='BTC_R1_Retest_Research.zip'))
 (R/'sources.json').write_text(json.dumps(sources,indent=2));print('verified72',flush=True)
if __name__=='__main__':main()
