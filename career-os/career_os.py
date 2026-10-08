#!/usr/bin/env python3
"""CJGR Career OS Ω: offline-only, privacy-safe job admission gate.
Never submits an application or contacts recruiters.
Store real CVs and application records in private Drive, not this repository.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urlencode, parse_qsl

MIN_BASE_MXN_MONTH = 50000

def canonical(url):
    p = urlsplit(url)
    if p.scheme not in ("https", "http") or not p.netloc:
        raise ValueError("Provide an official HTTP(S) job link")
    query = [(k, v) for k, v in parse_qsl(p.query) if
             k.lower() not in ("gclid", "fbclid") and not k.lower().startswith("utm_")]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/"), urlencode(query), ""))

def assess(job):
    url = canonical(job.get("official_url", ""))
    requirements = [str(x).strip() for x in job.get("must_haves", [])]
    claims = set(str(x).strip().casefold() for x in job.get("reviewed_evidence_tags", []))
    confirmed = [x for x in requirements if x.casefold() in claims]
    missing = [x for x in requirements if x.casefold() not in claims]
    blockers = []
    if job.get("active") is not True: blockers.append("Listing is not verified open")
    if job.get("employer_verified") is not True: blockers.append("Employer not verified")
    if job.get("remote_mexico") is not True: blockers.append("Mexico remote eligibility unverified")
    salary = job.get("guaranteed_published_base_mxn_month")
    if not isinstance(salary, (int, float)) or salary < MIN_BASE_MXN_MONTH:
        blockers.append("Published monthly guaranteed base below/unknown threshold")
    if not job.get("salary_source"): blockers.append("Salary primary source missing")
    if not job.get("source_timestamp"): blockers.append("Verification date missing")
    if not requirements: blockers.append("Exact must-have list missing")
    status = "PENDING_VERIFICATION" if blockers else ("GAP_REVIEW" if missing else "ELIGIBLE_FOR_REVIEW")
    identity = "|".join([str(job.get("company", "")).casefold(),
                         str(job.get("requisition_id") or job.get("role", "")).casefold(), url])
    jid = "CJGR-" + hashlib.sha256(identity.encode()).hexdigest()[:14].upper()
    return {"job_id": jid, "company": job.get("company"), "role": job.get("role"),
            "official_url": url, "status": status, "blockers": blockers,
            "must_have_coverage_pct": round(100 * len(confirmed) / len(requirements), 1)
            if requirements else None, "unsupported_must_haves": missing,
            "caution": "Requirements screening, not likelihood of being hired"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job_json", help="Private, manually-vetted job JSON")
    parser.add_argument("--out", help="Optional private JSON output file")
    args = parser.parse_args()
    job = json.loads(Path(args.job_json).read_text(encoding="utf-8"))
    result = assess(job)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

if __name__ == "__main__":
    main()
