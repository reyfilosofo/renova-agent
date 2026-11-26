#!/usr/bin/env python3
"""CENTRO T-052: public-safe synthetic CI regression, not empirical validation."""
import csv, json, subprocess, sys, tempfile
from pathlib import Path

VALIDATOR=Path(__file__).resolve().parent.parent/'t051'/'validate_asset_val_004.py'
SHEETS={
 'GATES_README':[['CENTRO GATES']]+[[''] for _ in range(25)],
 'CASE_DICTIONARY':[[],[],[],['Case_ID','Phase','Domain','Family_Internal','Pilot_Only','Confirmatory_Eligible','Leakage_Check'],['DRY-001','SYNTHETIC-DRY-RUN','synthetic','hidden','YES','NO','PASS']],
 'BLIND_SCORING':[[],[],[],['Rating_ID','Case_ID','Rater_ID','Rater_Independent','R1_Novelty_0_4','R2_Transformation_0_4','R3_Viability_0_4','R4_Generativity_0_4','R5_NonDisplacedHarm_0_4','R6_CausalAttribution_0_4','Abstain','Abstain_Reason'],['R-001','DRY-001','ChatGPT','NO','1','1','1','1','1','1','NO','']],
 'R5_HARM':[[],[],[],['Assessment_ID','Case_ID','Actor_Group','Scale','Time_Horizon','Severity_0_4','Externalized','Uncertainty'],['H-001','DRY-001','synthetic actor','local','short','1','NO','LOW']],
 'EXCLUSIONS':[[],[],[],['Exclusion_ID','Case_ID','Phase','Reason_Code','Proposed_Before_Outcome','Decision'],['X-001','DRY-001','SYNTHETIC-DRY-RUN','DUPLICATE-CASE','YES','RETAIN']],
 'MULTIVERSE':[[],[],[],['Spec_ID','Dimension','Level','Value','Role','Confirmatory','Predeclared','Allowed','Notes']]+[[f'MV-{i:03d}','synthetic','level','SESOI pending' if i==26 else 'value','test','NO','YES','NO' if i==26 else 'YES',''] for i in range(1,29)]
}
for i,token in enumerate(['BLOCKED-EXTERNAL','Independent raters','Numeric SESOI','Confirmatory data permission','DENIED','No aggregate score']):
 SHEETS['GATES_README'][i+1]=[token]

def execute(tables):
 with tempfile.TemporaryDirectory(prefix='centro-t052-') as tmp:
  for name,rows in tables.items():
   with (Path(tmp)/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:csv.writer(f).writerows(rows)
  p=subprocess.run([sys.executable,str(VALIDATOR),tmp],text=True,capture_output=True,check=False)
  if not p.stdout.strip():raise RuntimeError(p.stderr)
  return p.returncode,json.loads(p.stdout)

def mutate(index):
 t={k:[r.copy() for r in rows] for k,rows in SHEETS.items()}
 c=t['CASE_DICTIONARY'];r=t['BLIND_SCORING'];h=t['R5_HARM'];e=t['EXCLUSIONS'];m=t['MULTIVERSE'];g=t['GATES_README']
 if index==1:c[4][5]='YES'
 elif index==2:r[4][4]='5'
 elif index==3:r[4][10]='YES'
 elif index==4:r[4][3]='YES'
 elif index==5:h[4][2]=''
 elif index==6:e[4][3]='ADVERSE-RESULT'
 elif index==7:e[4][4]='NO'
 elif index==8:m.pop()
 elif index==9:m[29][7]='YES'
 elif index==10:r[3].append('RCV_Total')
 elif index==11:g[5]=['GATE-REDACTED']
 elif index==12:r[4][1]='DRY-UNKNOWN'
 return t

EXPECTED=['PILOT_LEAK','SCORE_RANGE','ABSTAIN_REASON','AUTHOR_INDEPENDENCE','R5_INCOMPLETE','EXCLUSION_REASON','POST_OUTCOME_EXCLUSION','MULTIVERSE_IDS','EXECUTABLE_BRANCH_COUNT','AGGREGATE_SCORE_FORBIDDEN','GATE_TOKEN_MISSING','ORPHAN_RATING']
def main():
 code,data=execute(SHEETS)
 results=[{'case':'baseline','expected':'PASS','observed':data['status'],'exit_code':code,'codes':[x['code'] for x in data['errors']]}]
 for i,expected in enumerate(EXPECTED,1):
  code,data=execute(mutate(i));codes=[x['code'] for x in data['errors']]
  results.append({'case':f'negative_{i:02d}','expected':expected,'observed':data['status'],'exit_code':code,'codes':codes})
 ok=results[0]['observed']=='PASS' and results[0]['exit_code']==0 and all(x['observed']=='FAIL' and x['exit_code']==1 and x['expected'] in x['codes'] for x in results[1:])
 passed=sum((x['observed']=='PASS' and x['exit_code']==0) if i==0 else (x['observed']=='FAIL' and x['exit_code']==1 and x['expected'] in x['codes']) for i,x in enumerate(results))
 print(json.dumps({'status':'PASS' if ok else 'FAIL','tests':len(results),'passed':passed,'scope':'synthetic-only regression, not canonical live sheet verification or empirical validation','results':results},indent=2))
 return 0 if ok else 1
if __name__=='__main__':sys.exit(main())
