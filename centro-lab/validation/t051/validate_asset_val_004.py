#!/usr/bin/env python3
"""CENTRO T-051 deterministic validator for ASSET-VAL-004.
No empirical inference. Validates schema/gates only.
Canonical source: Google Sheet 1Ler8mxW0gzjKjAC8XqUVagKXv2nUUuE1tEN_FjGC6K0
"""
import csv, json, sys
from pathlib import Path

REQUIRED = {
 "GATES_README": {"min_rows":26},
 "CASE_DICTIONARY": {"header_row":4,"required":["Case_ID","Phase","Domain","Family_Internal","Pilot_Only","Confirmatory_Eligible","Leakage_Check"]},
 "BLIND_SCORING": {"header_row":4,"required":["Rating_ID","Case_ID","Rater_ID","Rater_Independent","R1_Novelty_0_4","R2_Transformation_0_4","R3_Viability_0_4","R4_Generativity_0_4","R5_NonDisplacedHarm_0_4","R6_CausalAttribution_0_4","Abstain"]},
 "R5_HARM": {"header_row":4,"required":["Assessment_ID","Case_ID","Actor_Group","Scale","Time_Horizon","Severity_0_4","Externalized","Uncertainty"]},
 "EXCLUSIONS": {"header_row":4,"required":["Exclusion_ID","Case_ID","Phase","Reason_Code","Proposed_Before_Outcome","Decision"]},
 "MULTIVERSE": {"header_row":4,"required":["Spec_ID","Dimension","Level","Value","Role","Confirmatory","Predeclared","Allowed"]},
}
SCORE_FIELDS=["R1_Novelty_0_4","R2_Transformation_0_4","R3_Viability_0_4","R4_Generativity_0_4","R5_NonDisplacedHarm_0_4","R6_CausalAttribution_0_4",
"Creativity_0_4","Adaptation_0_4","Innovation_0_4","Resilience_0_4","TransformativeChange_0_4"]

def fail(code,msg,errors): errors.append({"code":code,"message":msg})
def load_csv(p):
    with open(p,newline="",encoding="utf-8-sig") as f: return list(csv.reader(f))
def records(rows, header_row):
    h=rows[header_row-1]
    return [dict(zip(h,r+[""]*(len(h)-len(r)))) for r in rows[header_row:] if any(str(x).strip() for x in r)]

def validate(folder):
    folder=Path(folder); errors=[]; warnings=[]; data={}
    for name,spec in REQUIRED.items():
        p=folder/f"{name}.csv"
        if not p.exists(): fail("MISSING_TAB",name,errors); continue
        rows=load_csv(p); data[name]=rows
        if len(rows)<spec.get("min_rows",0): fail("ROW_COUNT",f"{name}: {len(rows)}",errors)
        if "header_row" in spec:
            h=rows[spec["header_row"]-1] if len(rows)>=spec["header_row"] else []
            for col in spec["required"]:
                if col not in h: fail("MISSING_COLUMN",f"{name}.{col}",errors)
    if errors: return errors,warnings

    cases=records(data["CASE_DICTIONARY"],4)
    ratings=records(data["BLIND_SCORING"],4)
    harms=records(data["R5_HARM"],4)
    exclusions=records(data["EXCLUSIONS"],4)
    mv=records(data["MULTIVERSE"],4)
    case_ids=[x["Case_ID"] for x in cases]
    if len(case_ids)!=len(set(case_ids)): fail("DUP_CASE_ID","Case_ID not unique",errors)
    for c in cases:
        if c["Phase"]=="SYNTHETIC-DRY-RUN" and (c["Pilot_Only"]!="YES" or c["Confirmatory_Eligible"]!="NO"):
            fail("DRY_CONFIRMATORY_LEAK",c["Case_ID"],errors)
        if c["Pilot_Only"]=="YES" and c["Confirmatory_Eligible"]!="NO": fail("PILOT_LEAK",c["Case_ID"],errors)
        if c["Leakage_Check"] not in {"PASS","FAIL","PENDING"}: fail("LEAKAGE_ENUM",c["Case_ID"],errors)

    rating_ids=[x["Rating_ID"] for x in ratings]
    if len(rating_ids)!=len(set(rating_ids)): fail("DUP_RATING_ID","Rating_ID not unique",errors)
    for r in ratings:
        if r["Case_ID"] not in case_ids: fail("ORPHAN_RATING",r["Rating_ID"],errors)
        abstain=r["Abstain"]=="YES"
        for f in SCORE_FIELDS:
            v=r.get(f,"").strip()
            if v:
                try:
                    n=float(v)
                    if not (0<=n<=4): fail("SCORE_RANGE",f"{r['Rating_ID']} {f}={v}",errors)
                except ValueError: fail("SCORE_TYPE",f"{r['Rating_ID']} {f}={v}",errors)
        if abstain and not r.get("Abstain_Reason","").strip(): fail("ABSTAIN_REASON",r["Rating_ID"],errors)
        if r["Rater_ID"]=="ChatGPT" and r["Rater_Independent"]=="YES": fail("AUTHOR_INDEPENDENCE",r["Rating_ID"],errors)

    for h in harms:
        if h["Case_ID"] not in case_ids: fail("ORPHAN_HARM",h["Assessment_ID"],errors)
        for f in ["Actor_Group","Scale","Time_Horizon","Uncertainty"]:
            if not h.get(f,"").strip(): fail("R5_INCOMPLETE",f"{h['Assessment_ID']} {f}",errors)
        try:
            n=float(h["Severity_0_4"])
            if not 0<=n<=4: fail("R5_RANGE",h["Assessment_ID"],errors)
        except: fail("R5_TYPE",h["Assessment_ID"],errors)

    allowed_reasons={"DUPLICATE-CASE","CORRUPTED-MATERIAL","FAILED-MANIPULATION-CHECK","RATER-CONFLICT","MISSING-LONGITUDINAL-ENDPOINT"}
    for e in exclusions:
        if e["Case_ID"] not in case_ids: fail("ORPHAN_EXCLUSION",e["Exclusion_ID"],errors)
        if e["Reason_Code"] not in allowed_reasons: fail("EXCLUSION_REASON",e["Exclusion_ID"],errors)
        if e["Proposed_Before_Outcome"]!="YES": fail("POST_OUTCOME_EXCLUSION",e["Exclusion_ID"],errors)

    ids=[x["Spec_ID"] for x in mv]
    expected=[f"MV-{i:03d}" for i in range(1,29)]
    if ids!=expected: fail("MULTIVERSE_IDS",f"expected MV-001..MV-028 in order; got {ids}",errors)
    executable=[x for x in mv if x["Allowed"]=="YES"]
    blocked=[x for x in mv if x["Allowed"]=="NO"]
    if len(mv)!=28: fail("MULTIVERSE_COUNT",str(len(mv)),errors)
    if len(executable)!=27: fail("EXECUTABLE_BRANCH_COUNT",str(len(executable)),errors)
    if [x["Spec_ID"] for x in blocked]!=["MV-026"]: fail("BLOCKED_BRANCH_SET",str([x["Spec_ID"] for x in blocked]),errors)
    mv26=next((x for x in mv if x["Spec_ID"]=="MV-026"),None)
    if not mv26 or "SESOI" not in (mv26.get("Value","")+mv26.get("Notes","")): fail("SESOI_GATE","MV-026",errors)

    headers=data["BLIND_SCORING"][3]
    forbidden={"RCV_Total","RCV_Total_Score","Aggregate_RCV","ℛ_Score","R_Score"}
    if forbidden.intersection(headers): fail("AGGREGATE_SCORE_FORBIDDEN",str(forbidden.intersection(headers)),errors)

    gates="\n".join(",".join(r) for r in data["GATES_README"])
    for token in ["BLOCKED-EXTERNAL","Independent raters","Numeric SESOI","Confirmatory data permission","DENIED","No aggregate score"]:
        if token not in gates: fail("GATE_TOKEN_MISSING",token,errors)
    return errors,warnings

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: validate_asset_val_004.py <folder-with-six-csv-exports>"); sys.exit(2)
    errors,warnings=validate(sys.argv[1])
    result={"status":"PASS" if not errors else "FAIL","errors":errors,"warnings":warnings}
    print(json.dumps(result,ensure_ascii=False,indent=2)); sys.exit(1 if errors else 0)
