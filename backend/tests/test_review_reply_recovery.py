import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.pipeline import multimodal_review as review
from backend.pipeline.opencli import OpenCLIResult
from backend.pipeline.review_response import ReviewResponseError


def result(value):
    return OpenCLIResult((), 0, json.dumps(value), "")


def pending_result(conversation_id="6aa23493-b274-83ec-a248-e34aa77a2410"):
    url = f"https://chatgpt.com/c/{conversation_id}"
    return OpenCLIResult((), 1, "", "CHATGPT_TURN_PENDING: The prompt was submitted; "
                         "preserve its owned turn and do not replay. Saved conversation:\n"
                         f"    {url}; current URL:\n    {url}; cause: chatgpt ask timed out after 180s")


def test_submitted_timeout_reads_original_negative_verdict(tmp_path):
    payload = {"image_received": True, "reviews": [{"id": "scene-09", "verdict": "mismatch"}]}
    rows = [{"Role": "User", "Text": "Review"},
            {"Role": "Assistant", "Text": json.dumps(payload), "Generating": False, "StableSeconds": 12}]
    call = AsyncMock(return_value=result(rows))
    with patch.object(review, "run_opencli", call):
        recovered = asyncio.run(review._review_result_payload(
            pending_result(), provider="chatgpt", prompt="Review", sheet=tmp_path / "sheet.jpg",
            timeout=120, phase="initial", batch_index=2, attempt=1, log=None,
        ))
    assert recovered == payload
    assert call.await_args.args[0][:3] == ["chatgpt", "detail", "6aa23493-b274-83ec-a248-e34aa77a2410"]


@pytest.mark.parametrize("defect", ["wrong_current_url", "missing_marker", "wrong_prompt", "generating"])
def test_timeout_recovery_still_requires_owned_stable_reply(tmp_path, defect):
    receipt = pending_result()
    rows = [{"Role": "User", "Text": "Review"},
            {"Role": "Assistant", "Text": '{"image_received":true,"reviews":[]}',
             "Generating": False, "StableSeconds": 12}]
    if defect == "wrong_current_url":
        receipt = OpenCLIResult((), 1, "", receipt.stderr.replace("current URL:\n    https://chatgpt.com/c/6aa23493", "current URL:\n    https://chatgpt.com/c/7aa23493"))
    if defect == "missing_marker":
        receipt = OpenCLIResult((), 1, "", receipt.stderr.replace("CHATGPT_TURN_PENDING:", "ERROR:"))
    if defect == "wrong_prompt": rows[0]["Text"] = "Another image"
    if defect == "generating": rows[1]["Generating"] = True
    call = AsyncMock(return_value=result(rows))
    with patch.object(review, "run_opencli", call), pytest.raises(ReviewResponseError):
        asyncio.run(review._review_result_payload(
            receipt, provider="chatgpt", prompt="Review", sheet=tmp_path / "sheet.jpg",
            timeout=120, phase="initial", batch_index=2, attempt=1, log=None,
        ))
    assert call.await_count == (0 if defect in {"wrong_current_url", "missing_marker"} else 1)


def test_unfinished_reply_recovers_the_original_negative_verdict(tmp_path):
    prompt = 'Review this image.\nReturn JSON.'
    payload = {"image_received": True, "reviews": [{"id": "scene-09", "score": 68,
               "verdict": "partial", "issues": ["Missing CPU thesis"]}]}
    receipt = result([{"conversationId": "6aa23493-b274-83ec-a248-e34aa77a2410",
                       "response": '{"image_received":true,"reviews":'}])
    rows = [{"Role": "User", "Text": prompt.replace('\n', ' ')},
            {"Role": "Assistant", "Text": json.dumps(payload), "Generating": False, "StableSeconds": 12}]
    call = AsyncMock(return_value=result(rows))
    with patch.object(review, "run_opencli", call):
        recovered = asyncio.run(review._review_result_payload(
            receipt, provider="chatgpt", prompt=prompt, sheet=tmp_path / 'sheet.jpg',
            timeout=120, phase="initial", batch_index=2, attempt=1, log=None,
        ))
    assert recovered == payload
    assert call.await_count == 1
    assert call.await_args.args[0][:3] == ["chatgpt", "detail", "6aa23493-b274-83ec-a248-e34aa77a2410"]
    assert (tmp_path / 'response-initial-02-attempt-01-chatgpt-detail.json').is_file()


@pytest.mark.parametrize('defect', ['wrong_prompt', 'generating', 'unstable', 'extra_reply', 'ambiguous', 'missing_id'])
def test_recovery_cannot_change_ownership_or_select_a_favorable_answer(tmp_path, defect):
    payload = {"image_received": True, "reviews": []}
    receipt = {"conversationId": "6aa23493-b274-83ec-a248-e34aa77a2410", "response": '{"image_received":'}
    rows = [{"Role": "User", "Text": 'Review'},
            {"Role": "Assistant", "Text": json.dumps(payload), "Generating": False, "StableSeconds": 12}]
    if defect == 'wrong_prompt': rows[0]['Text'] = 'Another request'
    if defect == 'generating': rows[1]['Generating'] = True
    if defect == 'unstable': rows[1]['StableSeconds'] = 2
    if defect == 'extra_reply': rows.append(dict(rows[1]))
    if defect == 'ambiguous': receipt['response'] = json.dumps(payload) + json.dumps(payload)
    if defect == 'missing_id': receipt.pop('conversationId')
    call = AsyncMock(return_value=result(rows))
    with patch.object(review, "run_opencli", call), pytest.raises(ReviewResponseError):
        asyncio.run(review._review_result_payload(
            result([receipt]), provider="chatgpt", prompt='Review', sheet=tmp_path / 'sheet.jpg',
            timeout=120, phase="initial", batch_index=2, attempt=1, log=None,
        ))
    assert call.await_count == (0 if defect in {'ambiguous', 'missing_id'} else 1)
