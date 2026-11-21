#!/usr/bin/env python3
"""Offline validation of a proposed ℛenova federation packet. This does not send, authenticate, or sign anything."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
FIELDS={'packet_id','schema_version','created_at','expires_at','source_node','target_node','project_id','data_classification','mission','requested_operation','source_refs','state','provider_receipt_id','readback_verified'}
def check(p):
    e=[]
    if not isinstance(p,dict):return ['expected JSON object']
    for k in sorted(FIELDS-set(p)):e.append('missing '+k)
    for k in sorted(set(p)-FIELDS):e.append('unexpected '+k)
    if e:return e
    if p['schema_version']!='2.1':e.append('bad version')
    if p['project_id']!='RENOVA-AI-SAFETY-GOVERNANCE':e.append('bad project')
    if not isinstance(p['packet_id'],str) or len(p['packet_id'])<12:e.append('bad packet_id')
    if p['data_classification'] not in ('PUBLIC','INTERNAL','CONFIDENTIAL'):e.append('bad class')
    if p['requested_operation'] not in ('READ','ANALYZE','REVIEW','PROPOSE_PATCH'):e.append('unauthorized operation type')
    if p['state'] not in ('PREPARED','DISPATCHED','ACKNOWLEDGED','REJECTED','EXPIRED'):e.append('bad state')
    if type(p['readback_verified']) is not bool:e.append('bad readback flag')
    if not isinstance(p['mission'],str) or len(p['mission'])<10:e.append('bad mission')
    if not isinstance(p['source_refs'],list) or not p['source_refs'] or not all(isinstance(x,str) and x.startswith('https://') for x in p['source_refs']):e.append('bad refs')
    try:
        start=datetime.fromisoformat(p['created_at'].replace('Z','+00:00'))
        end=datetime.fromisoformat(p['expires_at'].replace('Z','+00:00'))
        if start.utcoffset() is None or end.utcoffset() is None or end<=start or (end-start).total_seconds()>604800:e.append('time window invalid')
    except (ValueError,TypeError,AttributeError):e.append('bad timestamps')
    if p['state']=='ACKNOWLEDGED' and (not isinstance(p['provider_receipt_id'],str) or not p['provider_receipt_id'].strip() or p['readback_verified'] is not True):e.append('no verified ACK')
    if p['state']=='PREPARED' and (p['provider_receipt_id'] is not None or p['readback_verified'] is not False):e.append('unsent packet cannot claim delivery')
    return e
if __name__=='__main__':
    if len(sys.argv)!=2:sys.exit('usage: python validate_packet.py packet.json')
    try:errors=check(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
    except (OSError,ValueError,json.JSONDecodeError) as exc:errors=[str(exc)]
    print(json.dumps({'valid':not errors,'errors':errors,'note':'syntax only; no authentication or actual provider delivery'},ensure_ascii=False))
    sys.exit(bool(errors))
