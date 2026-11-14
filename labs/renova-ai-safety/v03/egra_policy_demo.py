"""EGRA v0.3 advisory classification ONLY; no real enforcement or tool calls."""
from dataclasses import dataclass

READ={'read_public','summarize','draft_local','analyze_offline'}
EXTERNAL={'send_message','post_public','deploy','delete_document','modify_document','schedule_task','change_permissions','transfer_funds'}

@dataclass(frozen=True)
class Action:
    operation:str
    origin:str
    user_authorized:bool=False
    scoped:bool=False
    independently_verified:bool=False
    sensitive:bool=False
    high_impact:bool=False


def evaluate(action):
    if action.operation not in READ|EXTERNAL: return ('ESCALATE','UNKNOWN_OPERATION')
    if action.operation in EXTERNAL:
        if action.origin in ('webpage','document','tool_output'): return ('BLOCK','LOW_TRUST_ORIGIN')
        if not action.user_authorized or not action.scoped: return ('BLOCK','MISSING_SCOPED_AUTH')
        if not action.independently_verified: return ('ESCALATE','AUTH_NEEDS_EXTERNAL_VERIFICATION')
    if action.sensitive or action.high_impact:return ('ESCALATE','HUMAN_CHECKPOINT')
    return ('ALLOW','DEMO_ONLY')

if __name__=='__main__':
    assert evaluate(Action('send_message','webpage',True,True,True))[0]=='BLOCK'
    assert evaluate(Action('summarize','authenticated_user'))[0]=='ALLOW'
    print('2 illustrative assertions passed; NO safety efficacy inferred')
