"""Optional TypeSafe research judgments. Disabled by default; no execution adapter.

Contract checked 2026-10-24: https://api.typesafe.ai/openapi.json and
https://docs.typesafe.ai/models.md. Public inference is paid and requires a
separate explicit enable flag plus a server-side TYPESAFE_API_KEY.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
import uuid

ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
PINNED_MODEL = 'jev-1.14.0'
MAX_REQUEST_BYTES = 65536
MAX_RESPONSE_BYTES = 1048576
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_]{0,63}$')
SECRET_KEYS = {'apikey', 'apisecret', 'authorization', 'password', 'privatekey', 'seedphrase', 'recoveryphrase', 'accesstoken', 'refreshtoken', 'sessiontoken', 'bearertoken', 'typesafeapikey', 'headers', 'credentials'}
# Reject common credential syntax even when hidden in an innocent field name.
# Arbitrary unknown strings cannot be classified as secrets; callers must supply
# only a minimized, public research state. The actual server key is checked too.
SECRET_VALUE = re.compile(
    r'(?i)(?:\bbearer\s+[A-Za-z0-9._~+/-]{8,}|'
    r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----|'
    r'\b(?:sk[-_]|gh[pousr]_|github_pat_|xox[baprs]-)[A-Za-z0-9_-]{12,}|'
    r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|'
    r'\b(?:api[-_ ]?key|api[-_ ]?secret|password|private[-_ ]?key|seed[-_ ]?phrase|recovery[-_ ]?phrase|access[-_ ]?token|refresh[-_ ]?token)\s*[:=]\s*\S{4,})')


class JevValidationError(ValueError):
    """Carries an internal fixed code, never provider text or request values."""


@dataclass(frozen=True)
class JevHTTPResponse:
    status: int
    body: bytes


def _fail(code):
    error = JevValidationError(code)
    error._safe_code = code
    raise error


def _strict_json(value, depth=0, budget=None):
    budget = [0] if budget is None else budget
    budget[0] += 1
    if depth > 16 or budget[0] > 10000:
        _fail('json_limits_exceeded')
    if type(value) is str:
        if SECRET_VALUE.search(value):
            _fail('credential_like_json_value')
        return
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            _fail('nonfinite_json_number')
        return
    if type(value) is list:
        for item in value:
            _strict_json(item, depth + 1, budget)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or re.sub(r'[^a-z0-9]', '', key.lower()) in SECRET_KEYS:
                _fail('secret_or_invalid_json_key')
            _strict_json(key, depth + 1, budget)
            _strict_json(item, depth + 1, budget)
        return
    _fail('non_json_value')


def _contains_secret(value, secret):
    if type(value) is str:
        return secret in value
    if type(value) is list:
        return any(_contains_secret(item, secret) for item in value)
    if type(value) is dict:
        return any(secret in key or _contains_secret(item, secret) for key, item in value.items())
    return False


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail('duplicate_provider_json_key')
        result[key] = value
    return result


def _encode(value):
    _strict_json(value)
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, OverflowError):
        _fail('json_encoding_failed')


def _number(value, low, high):
    try:
        return type(value) in (int, float) and math.isfinite(value) and low <= value <= high
    except (OverflowError, ValueError):
        return False


def validate_questions(questions):
    _strict_json(questions)
    if type(questions) is not dict or not 1 <= len(questions) <= 24:
        _fail('question_count_invalid')
    for name, question in questions.items():
        if not ID.fullmatch(name) or type(question) is not dict:
            _fail('question_identity_invalid')
        if set(question) - {'type', 'instructions', 'criteria'}:
            _fail('unexpected_question_fields')
        kind = question.get('type')
        if kind not in ('noul', 'choice', 'score'):
            _fail('question_type_invalid')
        instructions = question.get('instructions')
        if type(instructions) not in (str, dict, list) or not instructions:
            _fail('question_instructions_required')
        criteria = question.get('criteria')
        if kind == 'choice':
            if type(criteria) is not dict or not 2 <= len(criteria) <= 255 or any(type(k) is not str or not k or len(k) > 128 for k in criteria) or any(type(v) not in (str, dict, list) or not v for v in criteria.values()):
                _fail('choice_requires_two_to_255_options')
        elif kind == 'score':
            if type(criteria) is not list or not 2 <= len(criteria) <= 10 or any(type(v) not in (str, dict, list) or not v for v in criteria):
                _fail('score_requires_two_to_ten_described_levels')
        elif criteria is not None and (type(criteria) is not dict or set(criteria) != {'true', 'false'} or any(type(v) not in (str, dict, list) or not v for v in criteria.values())):
            _fail('noul_criteria_invalid')
    return json.loads(_encode(questions))


def _distribution(value, keys):
    if type(value) is not dict or set(value) != set(keys) or any(not _number(p, 0, 1) for p in value.values()):
        _fail('probability_distribution_invalid')
    if abs(sum(value.values()) - 1) > 1e-5:
        _fail('probability_sum_invalid')


def validate_provider_response(payload, questions, pinned_model=PINNED_MODEL):
    if pinned_model != PINNED_MODEL:
        _fail('model_pin_not_supported')
    questions = validate_questions(questions)
    _strict_json(payload)
    if type(payload) is not dict or set(payload) != {'model', 'answers', 'usage'}:
        _fail('response_fields_invalid')
    if payload['model'] != pinned_model:
        _fail('model_version_mismatch')
    answers = payload['answers']
    if type(answers) is not dict or set(answers) != set(questions):
        _fail('response_questions_mismatch')
    for name, question in questions.items():
        answer, kind = answers[name], question['type']
        if type(answer) is not dict or answer.get('type') != kind:
            _fail('answer_type_mismatch')
        fields = {'type', 'noul'} if kind == 'noul' else {'type', 'choice', 'confidence', 'probabilities'} if kind == 'choice' else {'type', 'score', 'confidence', 'probabilities', 'legend'}
        if set(answer) != fields:
            _fail('answer_fields_invalid')
        if kind == 'noul':
            if not _number(answer['noul'], 0, 1):
                _fail('noul_probability_invalid')
            continue
        if not _number(answer['confidence'], 0, 1):
            _fail('native_confidence_invalid')
        criteria = question['criteria']
        keys = criteria.keys() if kind == 'choice' else [str(i) for i in range(len(criteria))]
        _distribution(answer['probabilities'], keys)
        if kind == 'choice':
            chosen = answer['choice']
            if type(chosen) is not str or chosen not in criteria or answer['probabilities'][chosen] + 1e-5 < max(answer['probabilities'].values()):
                _fail('choice_selection_invalid')
        else:
            if not _number(answer['score'], 0, len(criteria) - 1):
                _fail('score_range_invalid')
            legend = {str(i): v for i, v in enumerate(criteria)}
            if _encode(answer['legend']) != _encode(legend):
                _fail('score_legend_mismatch')
            expected = sum(int(key) * p for key, p in answer['probabilities'].items())
            if abs(answer['score'] - expected) > 1e-5:
                _fail('score_expected_value_mismatch')
    usage = payload['usage']
    if type(usage) is not dict or set(usage) != {'input_tokens', 'output_tokens'} or any(type(v) is not int or v < 0 for v in usage.values()):
        _fail('token_usage_invalid')
    return json.loads(_encode(payload))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _post(url, body, headers, timeout):
    # The URL cannot be supplied by callers; credentials cannot cross a redirect.
    if url != ENDPOINT:
        _fail('endpoint_not_allowed')
    request = urllib.request.Request(ENDPOINT, data=body, headers=headers, method='POST')
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            return JevHTTPResponse(response.status, response.read(MAX_RESPONSE_BYTES + 1))
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        return JevHTTPResponse(status, b'')


def request_decisions(state, questions, pinned_model=PINNED_MODEL, *, enabled=False, timeout_seconds=10, transport=None):
    """One optional inference attempt; never retries, trades, signs or moves funds.

    A custom transport has signature (fixed_url, body_bytes, headers, timeout)
    -> JevHTTPResponse. Injected responses are never marked authenticated.
    """
    result = {'status': 'DISABLED', 'provider': 'TypeSafe AI / Jev', 'configured': None, 'configuration_checked': False,
              'connected': False, 'authenticated_roundtrip_verified': False, 'request_id': str(uuid.uuid4()),
              'model': PINNED_MODEL, 'answers': {}, 'usage': None, 'contractProbability': None, 'calibrated': False,
              'execution_enabled': False, 'recommendation': 'WAIT', 'mode': 'PAPER',
              'confidence_scope': 'Native model judgment; not contract win probability or trading calibration.'}
    if type(enabled) is not bool:
        return {**result, 'status': 'INVALID_REQUEST', 'error_code': 'enable_flag_must_be_boolean'}
    if pinned_model != PINNED_MODEL:
        return {**result, 'status': 'INVALID_REQUEST', 'error_code': 'model_pin_not_supported'}
    if not enabled:
        return result
    try:
        if transport is not None and not callable(transport):
            _fail('transport_must_be_callable')
        if not _number(timeout_seconds, .1, 30):
            _fail('timeout_invalid')
        if type(state) not in (str, dict, list):
            _fail('state_shape_invalid')
        questions = validate_questions(questions)
        body = _encode({'model': pinned_model, 'state': state, 'questions': questions})
        if len(body) > MAX_REQUEST_BYTES:
            _fail('request_too_large')
    except JevValidationError as error:
        return {**result, 'status': 'INVALID_REQUEST', 'error_code': getattr(error, '_safe_code', 'validation_failed')}
    key = os.environ.get('TYPESAFE_API_KEY', '')
    result.update({'configured': bool(key), 'configuration_checked': True})
    if not key:
        return {**result, 'status': 'NOT_CONFIGURED'}
    if len(key) > 1024 or any(ord(c) < 33 or ord(c) > 126 for c in key):
        return {**result, 'status': 'INVALID_CONFIGURATION', 'error_code': 'invalid_server_key_shape'}
    if _contains_secret(state, key) or _contains_secret(questions, key):
        return {**result, 'status': 'INVALID_REQUEST', 'error_code': 'credential_in_request_data'}
    result.update({'state_sha256': hashlib.sha256(_encode(state)).hexdigest(), 'questions_sha256': hashlib.sha256(_encode(questions)).hexdigest()})
    headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'MONEY-PAPER-Judge/1.0'}
    started = time.monotonic()
    try:
        sender = _post if transport is None else transport
        response = sender(ENDPOINT, body, headers, timeout_seconds)
        if type(response) is not JevHTTPResponse or type(response.status) is not int or type(response.body) is not bytes:
            _fail('transport_response_invalid')
        if response.status != 200:
            return {**result, 'status': 'HTTP_ERROR', 'http_status': response.status, 'error_code': 'provider_http_error', 'attempts': 1}
        if len(response.body) > MAX_RESPONSE_BYTES:
            _fail('response_too_large')
        if key.encode() in response.body:
            _fail('credential_in_provider_response')
        try:
            payload = json.loads(response.body, parse_constant=lambda _: _fail('nonfinite_provider_json'), object_pairs_hook=_unique_json_object)
        except JevValidationError:
            raise
        except (ValueError, UnicodeError):
            _fail('provider_json_invalid')
        if _contains_secret(payload, key):
            _fail('credential_in_provider_response')
        parsed = validate_provider_response(payload, questions, pinned_model)
        return {**result, **parsed, 'status': 'OK', 'connected': transport is None, 'authenticated_roundtrip_verified': transport is None,
                'transport': 'OFFICIAL_HTTPS' if transport is None else 'INJECTED_UNVERIFIED', 'attempts': 1,
                'latency_ms': round((time.monotonic() - started) * 1000, 3)}
    except JevValidationError as error:
        return {**result, 'status': 'INVALID_RESPONSE', 'error_code': getattr(error, '_safe_code', 'validation_failed'), 'attempts': 1}
    except Exception:
        # Never export exception messages, provider bodies, headers or credentials.
        return {**result, 'status': 'UNAVAILABLE', 'error_code': 'provider_transport_error', 'attempts': 1}
