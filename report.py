from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,zipfile,platform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
p=pd.read_csv(R/'performance.csv');s=json.loads((R/'summary.json').read_text());a=pd.read_csv(R/'data_audit.csv');gaps=pd.read_csv(R/'spot_missing_intervals.csv');ex=pd.DataFrame(json.loads((R/'execution_audit.json').read_text()))
def table(df):
 cols=list(df.columns);lines=['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']
 for _,row in df.iterrows():lines.append('| '+' | '.join(f'{x:.6f}' if isinstance(x,(float,np.floating)) else str(x) for x in row)+' |')
 return '\n'.join(lines)
total=p[p.year=='ALL'];t=total[total.arm=='SPOT_CONFIRMED'];primary=p[(p.arm=='SPOT_CONFIRMED')&(p.hold==15)]
cols=['side','hold','n','gross_bp','net6_bp','net8_bp','net10_bp','trades_per_calendar_day']
report=f'''# CF1 현물·선물 동반 수급 — 전체 Research 검증 완료

2026-10-26 KST. 결론: 모든12설정이6/8/10bp 비용 가정에서 음의 표본 평균. 후보0개, 이번 동반 수급 조건 종료.

## 질문과 고정한 조건

현물의 동방향 수급을 추가하면 선물 수급만 사용했을 때보다 지속적인 가격 움직임을 얻는가? 전후 순서를 식별하는 현물 선행/인과 전략이 아니라 **같은3분 동안의 동반 확인**이다. ETH 가격 선행, 현선물 가격차, 기존 총체결 불균형과 관련된 탐색이다. 독립적으로 입증된 새로운 alpha라고 주장하지 않는다.

1분마다 quote-volume 불균형=2×taker-buy-quote-volume/quote-volume−1. 매수 우위0.2는 매수 체결금액 비중60%에 해당한다. LONG은 선물에서 최근3개의 완전히 종료된 분봉 모두 불균형≥0.2, SHORT는 모두≤−0.2. 이 선물 조건이 false→true가 되는 순간만 후보 사건이다. CF1은 같은3개 현물 분봉에서도 같은 부호 기준을 충족해야 한다. 비교군 FUTURES_ONLY는 이 추가 확인이 없다. 양쪽 모두 현물/선물 데이터가 유효한 동일 시간 모집단을 사용했다. 현물 확인은 비교군 사건의 부분집합이며, 뒤늦은 별도 현물 신호를 추가하지 않았다.

plan.json은 자료 계산 전에 고정하고 SHA256을 저장했다. 보유시간5/15/30분, 주요15분,2방향×2비교군=12설정. 최댓값 선택/threshold 조정/역방향 구조는 시도하지 않았다.

## 집행 및 비용

신호 확정 시각t에서 **t+60초의 선물 시가**로 진입한다. 1분봉 수신 지연을 알 수 없으므로 한 분 전체의 처리 여유를 둔 proxy다. 시가 체결을 보장하거나 실측 지연을 재현하지 않는다. 청산도 entry+hold 시점 시가. 동일방향/설정 포지션 종료 전 신호 무시. LONG과SHORT 별도 평가, 동시 결합 계좌 전략이 아니다. 고정$50초기명목 노출의 비율 손익이며 계좌$50/20배 수익률이 아니다. 손절/분할매매/복리/청산 위험은 모델링하지 않았다.

수수료는 entry/exit 각 실제 명목금액에3bp: 표준 편도6bp에서50%페이백이라는 **계좌 미확인 가정**. 환급 지연에 따른 현금 흐름은 미계산. net6는 fee만 차감, net8은 추가왕복2bp, net10은 추가4bp 차감. 추가 비용은 가정이며 호가 스프레드/Bitget 슬리피지 실측값이 아니다. 이 봉 데이터 gross에는 스프레드 비용이 없다.60%페이백 시나리오는 없다.

모든 설정에 동일한 공통진입 필터: 예정된 최대30분 보유가 다음UTC00/08/16시 funding에 도달하는 경우 및 정각 진입은 제외했다. 지연 청산이 funding을 넘으면 통과 금지로 정했고 실제0건. 따라서 이번 거래 집합에서는 funding을 차감하지 않았다. 이는 전체 시간대를 거래한 전략이 아니다.

## 결과 (단위 bp,1bp=0.01%)

{table(t[cols])}

15분 CF1의 LONG은 선물 단독 대비 net8가+0.539477bp 개선됐으나 여전히−7.798667bp. SHORT는−1.022683bp 악화. 이는 관측 평균 차이이며 통계적으로 유의한 개선이나 현물 수급의 인과효과가 아니다. 각 arm의 포지션 잠금 때문에 거래 시퀀스도 다르다.

같은 원래 사건에서 잠금 없이15분 결과를 비교한 보조진단도 attribution.csv에 저장했다. 중첩된 사건이므로 거래 성과/독립 표본으로 사용하지 않았다. 이 진단에서 현물 확인 LONG gross0.050620bp, 미확인−0.366830bp; SHORT 확인−1.286299bp, 미확인−0.429124bp. 본 시뮬레이션과 보조 진단 모두 비용을 넘어서는 효과를 보여주지 않았다.

## 15분 청산의 연도별 성과

{table(primary[['side','year','n','gross_bp','net6_bp','net8_bp','win8','pf8','trades_per_calendar_day']])}

12개 설정×3개 연도 **36개 모두 net6 평균이 음수**. CF1 인접5/30분도 net8 음수. 연도별+EV/인접 보유시간+EV 조건 실패로 bootstrap/FDR 유의성 판정으로 넘어가지 않았다. 이는 미래 모든 기간에서 반드시 손실이라는 통계적 증명은 아니다. 이미 여러 가설을 사용한 Research이므로 앞으로 양수가 나오더라도 독립 검증이 별도 필요하다.

15분 LONG은 일평균2.42회, SHORT3.30회(거래0일 포함 전체1096일분모). 평균은 매일 기회나 이익을 보장하지 않는다. 해당 방향 활성일은841/925일. LONG은 사전에 정한 평균3회/일 목표에 미달; SHORT는 빈도 기준을 충족했지만 경제성에서 실패했다. 방향별 시뮬레이션을 단순 합산한 포트폴리오 성과는 제공하지 않는다.

## 데이터 품질 / 검증

2020-01-01~2022-12-31 UTC, 공식BTCUSDT현물36개월+USD-M선물36개월. 모든72ZIP의 공식SHA256 CHECKSUM 일치. 기존 선물자료를 재사용하고 현물36파일만 다운로드. 빈 분을 채우지 않았다. 월 경계에서 전략을 강제로 리셋하지 않고 연속3년 그리드에서 계산했다. 마지막에는 공통최대보유시간 범위 밖 진입을 제한했으며2023데이터는 열지 않았다.

- 선물1,578,240행/누락0, 현물1,575,995행/누락2,245분. 누락은{len(gaps)}구간, 최장{int(gaps.minutes.max())}분. spot_missing_intervals.csv에 전체 저장. 누락 원인이 거래소 장애인지 별도로 확정하지 않았다.
- 양쪽 중복/역순/비정상OHLC/음수 또는 부정합volume0. 선물125분,현물139분 quotevolume0은 신호창에서 제외.
- 현물7행의 close timestamp가 표준59,999ms와 달라 신호창에서 제외. 원값은 spot_bad_close_times.csv에 보존.
- 이전 연구의 현물 일별/월별 불일치2021-04-01은 결과 확인 전에 신호 전체 제외. 수정값 합성이나 유리한 소스 선택 없음. 비교군도 같은 제외 적용.
- 미체결 또는 지연청산을 결과에 유리하게 삭제하지 않는 엔진: 실제 missing-entry0/delayed-exit0/unresolved0/funding-cross0.
- 합성테스트4개(인과/부분집합,지연/잠금/수수료,누락청산/SHORT,공통funding제외) 통과. 실제3개중간cutoff에서prefix와전체 신호 일치. 모든 거래의 비중복 및signal+60초 entry/예정보유시간 검증 통과.

전체 캔들 스키마/체크섬 안내: https://github.com/binance/binance-public-data . 각 파일 URL/해시/다운로드 시각은sources.json. 독립 제공자/Bitget 실체결 대조는 하지 않았다. 수익률은 Binance가격proxy이며 Bitget 미래수익이 아니다.

## 결정 / 재현

CF1은 현재 고정 정의로 종료. 수익을 만들려고 기준/보유시간/방향을 변경하지 않는다. 현재 수익 검증 후보0, 새 가설 미선정. 사용자 입금/가격파일/프로그램 설치는 이 검사에 필요하지 않았다. 실제 페이백/수수료의 가린 증빙은 여전히 미확인 비용 가정을 확인하는 데 유용하다.

Validation2023–24/OOS2025+미열람. 레버리지/실거래/계정API/거시발표/실시간수집 미실행.

재현: python coflow/test_engine.py → python coflow/run.py → python coflow/audit_detail.py → python coflow/report.py. 원자료72파일을 패키지에 포함하므로 download.py 재실행 불필요. sources.json이 있으면 download.py는 중복 다운로드를 거부한다. 새 설치에는 Python3,NumPy,pandas,matplotlib 필요. 전체per-trade ledgers,분리비교군,연도별표,실패조건,감사와설정 포함.
'''
(R/'REPORT.md').write_text(report)
status='''# CF1 HANDOFF / PROJECT STATUS — 2026-10-26 KST

CF1 COMPLETE, ARCHIVED. Full2020–22BTCspot/futures1m,72officialZIPchecksumvalid. Frozen3successiveminutesimbalance±.2, futuresfalse-to-true control, same3spotconfirmation subset. One-minute latencybuffer;5/15/30min timeexits;no stack; funding windows excluded commonmax30min. 12cells allnet6/8/10negative,36yearcell net6negative. Primary15min CF1L2650gross.201394bp/net6-5.798667/net8-7.798667;S3612gross-1.475695/net6-7.476137/net8-9.476137. Frequency2.418/3.296daily. Noqualifiedstrategy/noCIgate. Long meanlift+.539477bp vscontrol,short-1.022683; not statisticallyestablished orcausal. Unblockeddiagnostic separate/overlapping. Read REPORT.md/performance.csv/summary.json. No rescue/thresholdreverse/retune. Nextjustifiedpremiseunselected.

Data:spotmissing2245min;7badclosetimes;known2021Apr1qualityexclusion predeclared. Noimpute; matchedvalidwindows. Allprices/volumeauditvalid;0unresolved/delayedexit/fundingcross.4unit+3prefixchecks+ledgernonoverlap pass. Sources/rawincluded; reproduction REPORT.md. CurrentrootBTC_RESEARCH_RESUME.md preservesearliercampaigns. Provisional50%rebateonly,no60%;Researchonly,sealed2023+,no leverage/live/privateAPI/collector/macro. Activejobs0 aftersaving.
'''
(R/'HANDOFF.md').write_text(status);(R/'00_PROJECT_STATUS.md').write_text(status)
(R/'environment.json').write_text(json.dumps(dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__),indent=2))
figdir=R/'figures';figdir.mkdir(exist_ok=True)
fig,ax=plt.subplots(1,2,figsize=(11,4))
for side,g in t.groupby('side'):
 ax[0].plot(g.hold,g.net8_bp,marker='o',label=side)
 q=g[g.hold==15].iloc[0];ax[1].plot([6,8,10],[q.net6_bp,q.net8_bp,q.net10_bp],marker='o',label=side)
for x in ax:x.axhline(0,color='black',linewidth=.8);x.legend();x.set_ylabel('Mean return per trade (bp)');x.grid(alpha=.2)
ax[0].set_xlabel('Hold (minutes)');ax[0].set_title('Spot-confirmed: net @ nominal 8bp')
ax[1].set_xlabel('Nominal round-trip cost (bp)');ax[1].set_title('Primary 15-minute exit')
fig.tight_layout();fig.savefig(figdir/'economics.png',dpi=160);plt.close(fig)
manifest={str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in R.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.name!='manifest.json'}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(R.parent/'BTC_Coflow_Research.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(R.rglob('*')):
  if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.relative_to(R.parent))
print('REPORT and package saved', (R.parent/'BTC_Coflow_Research.zip').stat().st_size)
