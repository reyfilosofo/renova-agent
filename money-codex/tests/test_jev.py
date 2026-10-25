"""Offline fixtures matching the official OpenAPI0.2.0 shape, not API receipts."""
import copy
import json
import unittest
from unittest.mock import patch
from money_codex.jev import (ENDPOINT, PINNED_MODEL, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES,
                            JevHTTPResponse, JevValidationError, request_decisions,
                            validate_questions, validate_provider_response, _post)

KEY = 'synthetic-unit-test-key-never-a-credential'
QUESTIONS = {
    'worth_reviewing': {'type': 'noul', 'instructions': 'Does this state have enough evidence for paper review?'},
    'regime': {'type': 'choice', 'instructions': 'Which market regime matches the state?', 'criteria': {'trending': 'Persistent direction', 'chop': 'Alternating direction'}},
    'setup_quality': {'type': 'score', 'instructions': 'How well does the evidence match the research setup?', 'criteria': ['No match', 'Partial match', 'Complete match']},
}
PAYLOAD = {
    'model': PINNED_MODEL,
    'answers': {
        'worth_reviewing': {'type': 'noul', 'noul': .72},
        'regime': {'type': 'choice', 'choice': 'trending', 'confidence': .6, 'probabilities': {'trending': .8, 'chop': .2}},
        'setup_quality': {'type': 'score', 'score': 1.3, 'confidence': .45, 'legend': {'0': 'No match', '1': 'Partial match', '2': 'Complete match'}, 'probabilities': {'0': .2, '1': .3, '2': .5}},
    },
    'usage': {'input_tokens': 200, 'output_tokens': 30},
}


class JevTests(unittest.TestCase):
    def call(self, *, payload=None, response=None, state=None, questions=None, **kwargs):
        calls = []
        def transport(url, body, headers, timeout):
            calls.append((url, body, headers, timeout))
            return response or JevHTTPResponse(200, json.dumps(payload if payload is not None else PAYLOAD).encode())
        with patch.dict('os.environ', {'TYPESAFE_API_KEY': KEY}):
            result = request_decisions({'asset': 'BTC', 'unknown': None} if state is None else state,
                                       QUESTIONS if questions is None else questions,
                                       enabled=True, transport=transport, **kwargs)
        self.assertNotIn(KEY, json.dumps(result))
        return result, calls

    def test_default_disabled_never_checks_key_or_calls_network(self):
        with patch('money_codex.jev.os.environ.get', side_effect=AssertionError('must not read env')), patch('money_codex.jev._post', side_effect=AssertionError('network forbidden')):
            result = request_decisions({}, QUESTIONS)
        self.assertEqual(result['status'], 'DISABLED')
        self.assertIsNone(result['configured'])
        self.assertFalse(result['configuration_checked'])
        self.assertFalse(result['connected'])

    def test_missing_key_is_not_connected_and_has_no_network_attempt(self):
        with patch.dict('os.environ', {}, clear=True), patch('money_codex.jev._post', side_effect=AssertionError('network forbidden')):
            result = request_decisions({}, QUESTIONS, enabled=True)
        self.assertEqual(result['status'], 'NOT_CONFIGURED')
        self.assertFalse(result['configured'])
        self.assertFalse(result['authenticated_roundtrip_verified'])

    def test_official_typed_shape_roundtrips_fractional_score_without_pcontract(self):
        result, calls = self.call()
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['answers']['setup_quality']['score'], 1.3)
        self.assertNotIn('confidence', result['answers']['worth_reviewing'])
        self.assertEqual(result['answers']['regime']['confidence'], .6)
        self.assertIsNone(result['contractProbability'])
        self.assertFalse(result['calibrated'])
        self.assertFalse(result['execution_enabled'])
        self.assertEqual(result['recommendation'], 'WAIT')
        self.assertEqual(result['mode'], 'PAPER')
        self.assertFalse(result['authenticated_roundtrip_verified'])
        self.assertFalse(result['connected'])

    def test_post_contract_is_fixed_host_and_bearer_header_not_query_or_payload(self):
        result, calls = self.call(state={'source_url': 'http://169.254.169.254/latest/meta-data/'})
        url, body, headers, timeout = calls[0]
        self.assertEqual(url, ENDPOINT)
        self.assertEqual(headers['Authorization'], 'Bearer ' + KEY)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertNotIn(KEY, url)
        self.assertNotIn(KEY.encode(), body)
        self.assertFalse(any('Danger-Zone' in k for k in headers))
        self.assertEqual(json.loads(body)['model'], PINNED_MODEL)
        self.assertEqual(timeout, 10)

    def test_ssrf_endpoint_changes_rejected_before_opening_a_connection(self):
        with patch('money_codex.jev.urllib.request.build_opener', side_effect=AssertionError('must not open')):
            for url in ['http://169.254.169.254/', 'https://evil.example/v1/systemone', ENDPOINT + '?token=x', ENDPOINT + '/']:
                with self.assertRaises(JevValidationError):
                    _post(url, b'{}', {}, 1)

    def test_aliases_and_unverified_versions_reject_without_network(self):
        for model in ['jev-latest', 'jev-preview', 'jev-1.13.0', 'jev-1.14.1', '', True]:
            result, calls = self.call(pinned_model=model)
            self.assertEqual(result['status'], 'INVALID_REQUEST')
            self.assertEqual(calls, [])

    def test_model_version_drift_rejects_response(self):
        for model in ['jev-latest', 'jev-preview', 'jev-1.13.0', 'jev-1.14.1']:
            body = copy.deepcopy(PAYLOAD); body['model'] = model
            result, calls = self.call(payload=body)
            self.assertEqual(result['status'], 'INVALID_RESPONSE')
            self.assertEqual(result['error_code'], 'model_version_mismatch')
            self.assertEqual(len(calls), 1)

    def test_boolean_nonfinite_and_out_of_range_probabilities_are_rejected(self):
        for probability in [True, False, -.001, 1.001, float('nan'), float('inf'), 10**500]:
            body = copy.deepcopy(PAYLOAD); body['answers']['worth_reviewing']['noul'] = probability
            result, _ = self.call(payload=body)
            self.assertEqual(result['status'], 'INVALID_RESPONSE')

    def test_probabilities_must_have_exact_keys_sum_one_and_selected_maximum(self):
        for probabilities in [{'trending': .9, 'chop': .9}, {'trending': 1}, {'trending': .8, 'other': .2}, {'trending': True, 'chop': 0}, {'trending': .2, 'chop': .8}]:
            body = copy.deepcopy(PAYLOAD); body['answers']['regime']['probabilities'] = probabilities
            result, _ = self.call(payload=body)
            self.assertEqual(result['status'], 'INVALID_RESPONSE')

    def test_score_is_fractional_expectation_with_matching_legend_and_distribution(self):
        for mutate in [lambda a: a.update(score=3), lambda a: a.update(score=True), lambda a: a.update(score=1.2), lambda a: a.update(legend={'0': 'Wrong', '1': 'Partial match', '2': 'Complete match'}), lambda a: a.update(probabilities={'0': .2, '1': .3, '2': .4})]:
            body = copy.deepcopy(PAYLOAD); mutate(body['answers']['setup_quality'])
            result, _ = self.call(payload=body)
            self.assertEqual(result['status'], 'INVALID_RESPONSE')

    def test_wrong_type_extra_answers_missing_answers_and_extra_fields_reject(self):
        variants = []
        for kind in ['noul', 'score', 'choice']:
            body = copy.deepcopy(PAYLOAD); body['answers']['regime']['type'] = kind
            if kind != 'choice': variants.append(body)
        body = copy.deepcopy(PAYLOAD); body['answers']['surprise'] = {'type': 'noul', 'noul': .8}; variants.append(body)
        body = copy.deepcopy(PAYLOAD); del body['answers']['regime']; variants.append(body)
        body = copy.deepcopy(PAYLOAD); body['answers']['worth_reviewing']['confidence'] = .9; variants.append(body)
        body = copy.deepcopy(PAYLOAD); body['tool_call'] = 'BUY'; variants.append(body)
        body = copy.deepcopy(PAYLOAD); body['usage']['input_tokens'] = True; variants.append(body)
        for body in variants:
            result, _ = self.call(payload=body)
            self.assertEqual(result['status'], 'INVALID_RESPONSE')

    def test_invalid_native_confidence_is_not_coerced_or_replaced(self):
        for value in [True, False, -.1, 1.1, '0.9', None]:
            body = copy.deepcopy(PAYLOAD); body['answers']['regime']['confidence'] = value
            result, _ = self.call(payload=body)
            self.assertEqual(result['status'], 'INVALID_RESPONSE')

    def test_single_option_and_single_level_policy_and_oversized_requests_fail_before_network(self):
        for questions in [{}, {'x': {'type': 'choice', 'instructions': 'Pick', 'criteria': {'only': 'Only'}}}, {'x': {'type': 'score', 'instructions': 'Rate', 'criteria': ['Only']}}, {'x': {'type': 'score', 'instructions': 'Rate', 'criteria': ['v'] * 11}}, {'x': {'type': 'choice', 'instructions': 'Pick', 'criteria': {str(i): 'v' for i in range(256)}}}]:
            result, calls = self.call(questions=questions)
            self.assertEqual(result['status'], 'INVALID_REQUEST')
            self.assertFalse(calls)
        result, calls = self.call(state='x' * MAX_REQUEST_BYTES)
        self.assertEqual(result['status'], 'INVALID_REQUEST')
        self.assertFalse(calls)

    def test_invalid_json_secret_keys_and_payload_credentials_never_leave_process(self):
        for state in [{'api_key': 'never-send'}, {'privateKey': 'never-send'}, {'Authorization': 'never-send'}, {'price': float('nan')}, {'note': KEY}, True]:
            result, calls = self.call(state=state)
            self.assertEqual(result['status'], 'INVALID_REQUEST')
            self.assertFalse(calls)

    def test_401_403_429_529_and_redirects_have_no_retry_or_error_body_leak(self):
        for status in [301, 302, 307, 401, 403, 429, 500, 529]:
            result, calls = self.call(response=JevHTTPResponse(status, ('upstream echoed ' + KEY).encode()))
            self.assertEqual(result['status'], 'HTTP_ERROR')
            self.assertEqual(result['http_status'], status)
            self.assertEqual(result['attempts'], 1)
            self.assertEqual(len(calls), 1)
            self.assertFalse(result['connected'])

    def test_oversized_non_json_and_secret_echo_responses_fail_closed(self):
        for body in [b'x' * (MAX_RESPONSE_BYTES + 1), b'not-json', KEY.encode()]:
            result, _ = self.call(response=JevHTTPResponse(200, body))
            self.assertEqual(result['status'], 'INVALID_RESPONSE')
            self.assertEqual(result['answers'], {})

    def test_transport_exception_is_redacted_without_retries(self):
        calls = []
        def bad_transport(*args):
            calls.append(args)
            raise RuntimeError('exception contains ' + KEY)
        with patch.dict('os.environ', {'TYPESAFE_API_KEY': KEY}):
            result = request_decisions({}, QUESTIONS, enabled=True, transport=bad_transport)
        self.assertEqual(result['status'], 'UNAVAILABLE')
        self.assertEqual(len(calls), 1)
        self.assertNotIn(KEY, json.dumps(result))

    def test_question_and_state_hashes_are_reproducible_and_inputs_not_mutated(self):
        questions = copy.deepcopy(QUESTIONS); payload = copy.deepcopy(PAYLOAD)
        a, _ = self.call(questions=questions, payload=payload); b, _ = self.call(questions=questions, payload=payload)
        self.assertEqual(a['state_sha256'], b['state_sha256'])
        self.assertEqual(a['questions_sha256'], b['questions_sha256'])
        self.assertEqual(questions, QUESTIONS)
        self.assertEqual(payload, PAYLOAD)
        self.assertNotEqual(a['request_id'], b['request_id'])



    def test_duplicate_provider_json_keys_reject_at_every_level(self):
        raw = json.dumps(PAYLOAD)
        for body in [raw.replace('"model":', '"model":"jev-1.13.0","model":', 1),
                     raw.replace('"noul": 0.72', '"noul": 0.1,"noul": 0.72'),
                     raw.replace('"input_tokens": 200', '"input_tokens": 1,"input_tokens": 200')]:
            result, calls = self.call(response=JevHTTPResponse(200, body.encode()))
            self.assertEqual(result['status'], 'INVALID_RESPONSE')
            self.assertEqual(result['error_code'], 'duplicate_provider_json_key')
            self.assertEqual(result['answers'], {})
            self.assertEqual(len(calls), 1)

    def test_credential_values_under_innocent_names_are_rejected_before_network(self):
        examples = ['Bearer synthetictoken123456789',
                    'sk-syntheticlongcredential123456789',
                    'ghp_syntheticlongcredential123456789',
                    '-----BEGIN PRIVATE KEY----- synthetic',
                    'api_key=syntheticcredentialvalue',
                    'password: syntheticpasswordvalue']
        for value in examples:
            result, calls = self.call(state={'public_notes': ['Observed source', {'text': value}]})
            self.assertEqual(result['status'], 'INVALID_REQUEST')
            self.assertEqual(result['error_code'], 'credential_like_json_value')
            self.assertEqual(calls, [])
            self.assertNotIn(value, json.dumps(result))
        questions = copy.deepcopy(QUESTIONS)
        questions['regime']['criteria']['trending'] = examples[0]
        result, calls = self.call(questions=questions)
        self.assertEqual(result['status'], 'INVALID_REQUEST')
        self.assertEqual(calls, [])

    def test_actual_key_cannot_escape_detection_via_json_escaping_or_unicode(self):
        escaped_key = 'synthetic"quoted\\credential'
        def forbidden(*args):
            raise AssertionError('request data containing a server key must never leave')
        with patch.dict('os.environ', {'TYPESAFE_API_KEY': escaped_key}):
            for state in [{'note': escaped_key}, {'nested': [{'text': 'prefix ' + escaped_key + ' suffix'}]}, {escaped_key: 'value'}]:
                result = request_decisions(state, QUESTIONS, enabled=True, transport=forbidden)
                self.assertEqual(result['status'], 'INVALID_REQUEST')
                self.assertNotIn(escaped_key, json.dumps(result))
                self.assertNotIn('state_sha256', result)
        # A provider cannot smuggle an echoed key with JSON Unicode escapes.
        escaped_body = json.dumps(PAYLOAD).replace('trending', KEY).replace(KEY, ''.join('\\u%04x' % ord(c) for c in KEY))
        result, _ = self.call(response=JevHTTPResponse(200, escaped_body.encode()))
        self.assertEqual(result['status'], 'INVALID_RESPONSE')
        self.assertEqual(result['error_code'], 'credential_in_provider_response')
        self.assertEqual(result['answers'], {})

    def test_criteria_descriptions_are_strict_and_not_boolean_or_null(self):
        for kind, criteria in [('choice', {'a': True, 'b': 'Description'}),
                               ('choice', {'a': '', 'b': 'Description'}),
                               ('noul', {'true': 'Description', 'false': None})]:
            result, calls = self.call(questions={'q': {'type': kind, 'instructions': 'Review evidence', 'criteria': criteria}})
            self.assertEqual(result['status'], 'INVALID_REQUEST')
            self.assertEqual(calls, [])



    def test_invalid_or_falsy_injected_transport_cannot_fall_through_to_network(self):
        with patch('money_codex.jev._post', side_effect=AssertionError('network forbidden')):
            for transport in [False, 0, '', object()]:
                result = request_decisions({}, QUESTIONS, enabled=True, transport=transport)
                self.assertEqual(result['status'], 'INVALID_REQUEST')
                self.assertEqual(result['error_code'], 'transport_must_be_callable')
            class FalsyTransport:
                def __bool__(self):
                    return False
                def __call__(self, *args):
                    return JevHTTPResponse(200, json.dumps(PAYLOAD).encode())
            with patch.dict('os.environ', {'TYPESAFE_API_KEY': KEY}):
                result = request_decisions({}, QUESTIONS, enabled=True, transport=FalsyTransport())
            self.assertEqual(result['status'], 'OK')
            self.assertFalse(result['connected'])

    def test_transport_validation_exception_text_is_never_exported(self):
        def invalid_transport(*args):
            raise JevValidationError('untrusted provider text ' + KEY)
        with patch.dict('os.environ', {'TYPESAFE_API_KEY': KEY}):
            result = request_decisions({}, QUESTIONS, enabled=True, transport=invalid_transport)
        self.assertEqual(result['status'], 'INVALID_RESPONSE')
        self.assertEqual(result['error_code'], 'validation_failed')
        self.assertNotIn(KEY, json.dumps(result))


if __name__ == '__main__':
    unittest.main()
