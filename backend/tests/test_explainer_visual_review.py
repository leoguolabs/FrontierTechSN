import asyncio
import copy
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from backend import explainer_visual_review as review
from backend.pipeline.opencli import OpenCLIError, OpenCLIResult
from backend.pipeline import multimodal_review, opencli_session


SCENE = {"id": "scene-001", "narration": "She lifts the box.",
         "visual_prompt": "A line-drawn person lifting a box."}


@pytest.fixture(autouse=True)
def close_review_sessions(monkeypatch):
    close = AsyncMock()
    monkeypatch.setattr(opencli_session, "close_opencli_site_sessions", close)
    return close


def payload():
    return {"image_received": True, "reviews": [{"id": "scene-001", "checks": [
        {"criterion": name, "verdict": "pass", "evidence": "The box rests against both hands.", "repair": ""}
        for name in review.CHECKS]}]}


@pytest.mark.parametrize("fault", ["missing_image", "wrong_scene", "missing_check", "duplicate_check",
                                  "no_evidence", "contradictory_pass", "no_repair"])
def test_incomplete_or_contradictory_reviews_fail_closed(fault):
    value = payload()
    row = value["reviews"][0]
    if fault == "missing_image": value["image_received"] = "true"
    if fault == "wrong_scene": row["id"] = "scene-002"
    if fault == "missing_check": row["checks"].pop()
    if fault == "duplicate_check": row["checks"][-1] = copy.deepcopy(row["checks"][0])
    if fault == "no_evidence": row["checks"][0]["evidence"] = ""
    if fault == "contradictory_pass": row["checks"][0]["repair"] = "Fix the detached hands"
    if fault == "no_repair": row["checks"][0]["verdict"] = "fail"
    with pytest.raises(ValueError):
        review.validate_review(value, "scene-001")


@pytest.mark.parametrize("verdict", ["fail", "uncertain"])
def test_failure_or_uncertainty_rejects_otherwise_passing_image(verdict):
    value = payload()
    value["reviews"][0]["checks"][2].update(verdict=verdict, repair="Show contact between hands and box")
    assert review.validate_review(value, "scene-001")["passed"] is False


@pytest.mark.parametrize("verdict", ["fail", "uncertain"])
def test_omitted_repair_is_only_allowed_for_pass(verdict):
    value = payload()
    value["reviews"][0]["checks"][0]["verdict"] = verdict
    del value["reviews"][0]["checks"][0]["repair"]
    with pytest.raises(ValueError, match="omitted visible evidence or repair"):
        review.validate_review(value, "scene-001")


@pytest.mark.parametrize("repair", [None, [], 0])
def test_explicit_invalid_pass_repair_remains_invalid(repair):
    value = payload()
    value["reviews"][0]["checks"][0]["repair"] = repair
    with pytest.raises(ValueError, match="omitted visible evidence or repair"):
        review.validate_review(value, "scene-001")


def test_review_cache_is_bound_to_pixels_scene_and_rules(tmp_path, monkeypatch):
    calls = []

    async def provider(args, **kwargs):
        calls.append(args)
        assert "--file" in args and args[args.index("--file") + 1] == str(tmp_path / "image.png")
        assert args[args.index("--site-session") + 1] == "persistent"
        assert kwargs["site_session_namespace"].endswith("-gemini")
        return OpenCLIResult(tuple(args), 0, json.dumps(payload()), "")

    monkeypatch.setattr(review, "run_opencli", provider)
    rules = ["Objects must be coherent."]
    monkeypatch.setattr(review, "visual_logic_rules", lambda: rules[0])

    async def run():
        image = tmp_path / "image.png"
        image.write_bytes(b"test pixels one")
        scene = copy.deepcopy(SCENE)
        first, path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        assert first["passed"] and path.is_file()
        assert await review.review_image(image, scene, {}, tmp_path, lambda _: None) == (first, path)
        assert len(calls) == 1
        image.write_bytes(b"different pixels")
        await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        scene["narration"] = "She drops the box."
        await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        rules[0] += " Gravity must be coherent."
        await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        assert len(calls) == 4
        await review.review_image(image, scene, {"character_description": "Thin line limbs"}, tmp_path, lambda _: None)
        assert len(calls) == 5
        scene["on_screen_text"] = "11:47 PM"
        await review.review_image(image, scene, {"character_description": "Thin line limbs"}, tmp_path, lambda _: None)
        assert len(calls) == 6
        # Review revisions must retain every original provider response.
        assert len(list(tmp_path.glob("response-explainer_logic-*-gemini.json"))) == 6
    asyncio.run(run())


def test_valid_rejection_never_asks_fallback_for_a_better_verdict(tmp_path, monkeypatch):
    calls = []
    value = payload()
    value["reviews"][0]["checks"][0].update(verdict="fail", repair="Use a consistent perspective")

    async def provider(args, **kwargs):
        calls.append(args[0])
        return OpenCLIResult(tuple(args), 0, json.dumps(value), "")

    monkeypatch.setattr(review, "run_opencli", provider)
    monkeypatch.setattr(review.config, "AV_SYNC_REVIEW_FALLBACK_PROVIDER", "chatgpt")
    image = tmp_path / "image.png"
    image.write_bytes(b"pixels")
    result, _ = asyncio.run(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
    assert result["passed"] is False and calls == ["gemini"]


def test_clipboard_review_separates_page_direction_from_surface_visibility():
    scene = {**SCENE, "visual_prompt": "Overhead view of a teacher holding a clipboard."}
    prompt = review.review_prompt(scene, {})
    assert "bottom edge is normally nearer the reader" in prompt
    assert "does not require the holder to read its front" in prompt
    assert "Do not invent a reading action for a blank, unused prop" in prompt
    assert "rotating that sheet 180 degrees would invert it" in prompt
    assert "Still reject a visibly backward surface" in prompt
    assert "use uncertain if the necessary geometry is unreadable" in prompt
    # This is a review correction; unrelated scenes keep their cache contract.
    assert "Clipboard reading geometry:" not in review.review_prompt(SCENE, {})


@pytest.mark.parametrize("description", [
    "A worker dragging text into a chat window, clipboard icon mid-transfer.",
    "A researcher holding a clipboard beside a table with four cards.",
    "Laboratory icons including a clipboard with a checklist.",
])
def test_overhead_geometry_does_not_invalidate_unrelated_clipboard_scenes(description):
    scene = {**SCENE, "visual_prompt": description}
    assert "Clipboard reading geometry:" not in review.review_prompt(scene, {})


def test_classroom_review_requires_traced_anatomy_without_relaxing_verdicts():
    scene = {**SCENE, "visual_prompt":
             "Students at their desks writing while a teacher checks their notebooks."}
    prompt = review.review_prompt(scene, {})
    assert "shoulder-to-sleeve-to-elbow-to-wrist-to-hand" in prompt
    assert "Absent cast shadows" in prompt
    assert "Still reject demonstrable extra limbs" in prompt
    value = payload()
    value["reviews"][0]["checks"][2].update(
        verdict="fail", evidence="Three distinct connected arms are visible.",
        repair="Remove the third arm.")
    assert not review.validate_review(value, SCENE["id"])["passed"]


@pytest.mark.parametrize("description", [
    "Students at desks while a researcher stands at the front.",
    "Students at spaced desks in an exam hall.",
    "A teacher holding a notebook beside one student.",
    "Students watching a teacher at a blackboard.",
])
def test_classroom_anatomy_preserves_other_review_contracts(description):
    scene = {**SCENE, "visual_prompt": description}
    assert "Multi-person desk anatomy:" not in review.review_prompt(scene, {})


def test_easel_printout_review_revision_rechecks_same_pixels_and_retains_rejection(
        tmp_path, monkeypatch):
    scene = {**SCENE, "visual_prompt":
             "A researcher props a printout of question-card icons against an easel."}
    image = tmp_path / "image.png"
    image.write_bytes(b"unchanged candidate pixels")
    rejected = payload()
    rejected["reviews"][0]["checks"][1].update(
        verdict="fail", evidence="The mast disappears behind the opaque board.",
        repair="Expose the hidden mast.")
    calls = []
    corrected_prompt = review.review_prompt
    old_prompt = corrected_prompt(SCENE, {})

    async def provider(args, **kwargs):
        calls.append(args)
        return OpenCLIResult(tuple(args), 0, json.dumps(rejected), "")

    monkeypatch.setattr(review, "run_opencli", provider)

    async def run():
        monkeypatch.setattr(review, "review_prompt", lambda *_: old_prompt)
        before, before_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        original_receipt = before_path.read_bytes()
        monkeypatch.setattr(review, "review_prompt", corrected_prompt)
        after, after_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        assert before_path != after_path
        assert before_path.read_bytes() == original_receipt
        assert before["image_sha256"] == after["image_sha256"]
        # A prompt correction never overrides the provider's fail or adds a fallback.
        assert not before["passed"] and not after["passed"]
        assert len(calls) == 2
        assert await review.review_image(image, scene, {}, tmp_path, lambda _: None) == (after, after_path)
        assert len(calls) == 2

    asyncio.run(run())
    prompt = corrected_prompt(scene, {})
    assert "parts occluded by the opaque sheet" in prompt
    assert "enumerate the visible shoulder-to-sleeve-to-elbow-to-wrist-to-hand" in prompt
    assert "Do not assume either interpretation solely from the prompt" in prompt
    assert "use uncertain when a required relationship" in prompt


@pytest.mark.parametrize("description", [
    "A researcher draws a diagram on an easel.",
    "A printout lies flat on a desk.",
    "A magnifying-glass icon overlaps question cards on a screen.",
])
def test_easel_printout_correction_preserves_other_review_contracts(description):
    scene = {**SCENE, "visual_prompt": description}
    assert "Easel and printout geometry:" not in review.review_prompt(scene, {})


@pytest.mark.parametrize("description", [
    "A two-bar chart; a presenter's pencil points at the tall human bar.",
    "A complete arm bends from shoulder through elbow and wrist; its pencil points at an empty box.",
])
def test_pointing_review_rechecks_same_pixels_and_preserves_failure(tmp_path, monkeypatch, description):
    scene = {**SCENE, "visual_prompt": description}
    image = tmp_path / "image.png"
    image.write_bytes(b"unchanged chart presenter")
    rejected = payload()
    rejected["reviews"][0]["checks"][1].update(
        verdict="fail", evidence="Three distinct shoulder-to-hand chains are visible.",
        repair="Remove the third connected arm.")
    provider = AsyncMock(return_value=OpenCLIResult((), 0, json.dumps(rejected), ""))
    monkeypatch.setattr(review, "run_opencli", provider)
    corrected_prompt = review.review_prompt
    old_prompt = corrected_prompt(SCENE, {})

    async def run():
        monkeypatch.setattr(review, "review_prompt", lambda *_: old_prompt)
        before, before_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        original_receipt = before_path.read_bytes()
        monkeypatch.setattr(review, "review_prompt", corrected_prompt)
        after, after_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        assert before_path != after_path
        assert before_path.read_bytes() == original_receipt
        assert before["image_sha256"] == after["image_sha256"]
        assert not before["passed"] and not after["passed"]
        assert provider.await_count == 2
        assert await review.review_image(image, scene, {}, tmp_path, lambda _: None) == (after, after_path)
        assert provider.await_count == 2

    asyncio.run(run())
    prompt = corrected_prompt(scene, {})
    assert "Count connected limbs, not side labels" in prompt
    assert "without locating a third distinct chain" in prompt
    assert "Still reject a visibly extra arm" in prompt
    assert "use uncertain if the required topology is unreadable" in prompt


@pytest.mark.parametrize("description", [
    "A paper bar chart propped on the easel rail, topped with robot and person icons.",
    "A pencil rests beside a chart on a desk.",
    "A presenter points at a chart with an empty hand.",
    "A pencil points at a notebook.",
    "An arm rests on a desk beside a pencil; its shoulder and wrist are visible.",
    "A pencil points at an empty box beside the figure's arm.",
])
def test_chart_presenter_correction_keeps_unrelated_review_contracts(description):
    prompt = review.review_prompt({**SCENE, "visual_prompt": description}, {})
    assert "Chart presenter anatomy:" not in prompt
    assert "Pointer gesture anatomy:" not in prompt


@pytest.mark.parametrize("verdict", ["fail", "uncertain"])
def test_magnifier_review_rechecks_same_pixels_without_overriding_rejection(
        tmp_path, monkeypatch, verdict):
    scene = {**SCENE, "visual_prompt":
             "A seated character grips a magnifying glass above a flat clipboard."}
    image = tmp_path / "image.png"
    image.write_bytes(b"unchanged magnifier candidate")
    rejected = payload()
    rejected["reviews"][0]["checks"][1].update(
        verdict=verdict, evidence="A background gap separates the wrist and hand.",
        repair="Connect the hand to the visible forearm.")
    provider = AsyncMock(return_value=OpenCLIResult((), 0, json.dumps(rejected), ""))
    monkeypatch.setattr(review, "run_opencli", provider)
    corrected_prompt = review.review_prompt
    old_prompt = corrected_prompt(SCENE, {})

    async def run():
        monkeypatch.setattr(review, "review_prompt", lambda *_: old_prompt)
        before, before_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        original_receipt = before_path.read_bytes()
        monkeypatch.setattr(review, "review_prompt", corrected_prompt)
        after, after_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        assert before_path != after_path
        assert before_path.read_bytes() == original_receipt
        assert image.read_bytes() == b"unchanged magnifier candidate"
        assert before["image_sha256"] == after["image_sha256"]
        assert not before["passed"] and not after["passed"]
        assert after["checks"][1]["verdict"] == verdict
        assert provider.await_count == 2
        assert await review.review_image(image, scene, {}, tmp_path, lambda _: None) == (after, after_path)
        assert provider.await_count == 2

    asyncio.run(run())
    prompt = corrected_prompt(scene, {})
    assert "needs no transverse wrist line" in prompt
    assert "never assume the requested limb count is correct" in prompt
    assert "Reject a demonstrable third chain" in prompt
    assert "use uncertain when required continuity cannot be established" in prompt


@pytest.mark.parametrize("description", [
    "A clipboard and a magnifying-glass icon appear on a screen.",
    "A character holds a pencil above a clipboard, without a magnifier.",
    "A character holds a magnifying glass above an open book.",
])
def test_magnifier_anatomy_preserves_unrelated_review_contracts(description):
    prompt = review.review_prompt({**SCENE, "visual_prompt": description}, {})
    assert "Handheld magnifier anatomy:" not in prompt


@pytest.mark.parametrize("verdict", ["fail", "uncertain", "pass"])
@pytest.mark.parametrize("description", [
    "A worker at a laptop checks its footnote line while holding a pencil.",
    "A worker at a laptop checks a scoreboard with separate pictogram columns.",
    "Close-up of the screen: the same three-column scoreboard, now with filled pictogram rows.",
])
def test_laptop_geometry_review_preserves_old_rejection_and_caches_new_verdict(
        tmp_path, monkeypatch, verdict, description):
    scene = {**SCENE, "visual_prompt": description}
    image = tmp_path / "image.png"
    image.write_bytes(b"unchanged citation laptop candidate")
    corrected_prompt = review.review_prompt
    old_prompt = corrected_prompt(SCENE, {})
    rejection = payload()
    rejection["reviews"][0]["checks"][2].update(
        verdict="fail", evidence="The display faces the camera, away from the reader.",
        repair="Rotate the laptop toward the reader.")
    revised = payload()
    revised["reviews"][0]["checks"][2].update(
        verdict=verdict,
        evidence=("Reader and camera share the palm-rest side of the visible hinge."
                  if verdict == "pass" else "The reader's side of the lid is incompatible or unclear."),
        repair="" if verdict == "pass" else "Show the reader on the palm-rest side.")
    provider = AsyncMock(side_effect=[
        OpenCLIResult((), 0, json.dumps(rejection), ""),
        OpenCLIResult((), 0, json.dumps(revised), ""),
    ])
    monkeypatch.setattr(review, "run_opencli", provider)

    async def run():
        monkeypatch.setattr(review, "review_prompt", lambda *_: old_prompt)
        before, before_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        old_receipt = before_path.read_bytes()
        monkeypatch.setattr(review, "review_prompt", corrected_prompt)
        after, after_path = await review.review_image(image, scene, {}, tmp_path, lambda _: None)
        assert before_path != after_path and before_path.read_bytes() == old_receipt
        assert image.read_bytes() == b"unchanged citation laptop candidate"
        assert before["image_sha256"] == after["image_sha256"]
        assert not before["passed"] and after["passed"] == (verdict == "pass")
        assert after["checks"][2]["verdict"] == verdict
        assert await review.review_image(image, scene, {}, tmp_path, lambda _: None) == (after, after_path)
        assert provider.await_count == 2

    asyncio.run(run())
    prompt = corrected_prompt(scene, {})
    assert "display then faces BOTH reader and camera" in prompt
    assert "partial profile on a round" in prompt
    assert "Require visible incompatible orientation" in prompt
    assert "Preserve genuine backward-display" in prompt
    if "scoreboard" in description:
        assert "Scoreboard laptop geometry:" in prompt
        assert "Check the scoreboard pictograms and separate score rows" in prompt
        assert "Check the footnote and inspection icon relationship" not in prompt
    if "laptop" not in description:
        assert "only if a laptop is depicted" in prompt
        assert "Do not invent off-frame hardware or people" in prompt


def test_scoreboard_screen_review_does_not_require_laptop_hardware():
    prompt = review.review_prompt({**SCENE, "visual_prompt":
                                  "A scoreboard fills a standalone monitor screen."}, {})
    assert "a standalone monitor or screen-only crop need not show a keyboard" in prompt
    assert "screen-only close-up need not invent an unseen reader" in prompt


@pytest.mark.parametrize("description", [
    "A worker faces a laptop displaying an answer card.",
    "A worker reads a footnote on a printed page.",
    "A tablet shows footnotes beside a pencil.",
    "A scoreboard printed on paper lies beside a tablet.",
    "A worker looks at a scoreboard on a desktop monitor.",
])
def test_citation_geometry_preserves_unrelated_review_contracts(description):
    prompt = review.review_prompt({**SCENE, "visual_prompt": description}, {})
    assert "Citation laptop geometry:" not in prompt
    assert "Scoreboard laptop geometry:" not in prompt


def test_rejection_with_omitted_pass_repairs_is_cached_without_fallback(tmp_path, monkeypatch):
    value = payload()
    for check in value["reviews"][0]["checks"]:
        del check["repair"]
    value["reviews"][0]["checks"][0].update(
        verdict="fail", repair="Turn the laptop screen toward the character")
    original = copy.deepcopy(value)
    calls = []

    async def provider(args, **kwargs):
        calls.append(args[0])
        return OpenCLIResult(tuple(args), 0, json.dumps(value), "")

    monkeypatch.setattr(review, "run_opencli", provider)
    monkeypatch.setattr(review.config, "AV_SYNC_REVIEW_FALLBACK_PROVIDER", "chatgpt")
    image = tmp_path / "image.png"
    image.write_bytes(b"pixels")

    async def run():
        first = await review.review_image(image, SCENE, {}, tmp_path, lambda _: None)
        assert await review.review_image(image, SCENE, {}, tmp_path, lambda _: None) == first
        return first[0]

    result = asyncio.run(run())
    assert not result["passed"] and calls == ["gemini"]
    assert result["payload"] == original  # Preserve the provider's original evidence.
    assert all(check["repair"] == "" for check in result["checks"][1:])


def test_unavailable_review_blocks_image_instead_of_passing(tmp_path, monkeypatch):
    calls = []

    async def provider(args, **kwargs):
        calls.append(args[0])
        return OpenCLIResult(tuple(args), 0, json.dumps({"image_received": False, "reviews": []}), "")

    monkeypatch.setattr(review, "run_opencli", provider)
    monkeypatch.setattr(review.config, "AV_SYNC_REVIEW_FALLBACK_PROVIDER", "chatgpt")
    image = tmp_path / "image.png"
    image.write_bytes(b"pixels")
    with pytest.raises(RuntimeError, match="cannot be accepted"):
        asyncio.run(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
    assert calls == ["gemini", "chatgpt"]


def test_submitted_timeout_survives_failed_read_and_resumes_without_new_ask(tmp_path, monkeypatch):
    calls = []
    url = "https://chatgpt.com/c/6aa23493-b274-83ec-a248-e34aa77a2410"
    receipt = OpenCLIResult((), 1, "", "CHATGPT_TURN_PENDING: The prompt was submitted; "
                           "preserve its owned turn and do not replay. Saved conversation:\n"
                           f"    {url}; current URL:\n    {url}; cause: chatgpt ask timed out after 180s")
    value = payload()
    value["reviews"][0]["checks"][0].update(verdict="fail", repair="Correct the perspective")

    async def ask(args, **kwargs):
        calls.append(args[0])
        if args[0] == "gemini": raise RuntimeError("Model unavailable")
        raise OpenCLIError("submitted timeout", result=receipt)

    async def detail(args, **kwargs):
        assert args[:3] == ["chatgpt", "detail", "6aa23493-b274-83ec-a248-e34aa77a2410"]
        saved = json.loads(next(tmp_path.glob("response-*-chatgpt.json")).read_text())
        assert saved["stderr"] == receipt.stderr  # Durable before awaiting recovery.
        return OpenCLIResult(tuple(args), 0, json.dumps([
            {"Role": "User", "Text": review.review_prompt(SCENE, {})},
            {"Role": "Assistant", "Text": json.dumps(value), "Generating": False, "StableSeconds": 12},
        ]), "")

    monkeypatch.setattr(review, "run_opencli", ask)
    monkeypatch.setattr(review.config, "AV_SYNC_REVIEW_FALLBACK_PROVIDER", "chatgpt")
    monkeypatch.setattr(multimodal_review, "run_opencli", AsyncMock(side_effect=RuntimeError("read unavailable")))
    image = tmp_path / "image.png"
    image.write_bytes(b"original pixels")
    with pytest.raises(RuntimeError, match="cannot be accepted"):
        asyncio.run(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
    saved = next(tmp_path.glob("response-*-chatgpt.json")).read_bytes()
    monkeypatch.setattr(multimodal_review, "run_opencli", detail)
    result, _ = asyncio.run(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
    assert result["passed"] is False  # The original denial remains authoritative.
    assert calls == ["gemini", "chatgpt"]
    assert next(tmp_path.glob("response-*-chatgpt.json")).read_bytes() == saved
    assert image.read_bytes() == b"original pixels"


@pytest.mark.parametrize("provider", ["gemini", "chatgpt"])
def test_preemption_closes_exact_review_session_and_preserves_candidate(
    tmp_path, monkeypatch, close_review_sessions, provider,
):
    entered = asyncio.Event()
    closed = asyncio.Event()
    release_cleanup = asyncio.Event()
    calls = []
    image = tmp_path / "image.png"
    image.write_bytes(b"unchanged accepted generation")
    generated = tmp_path / "complete.json"
    generated.write_text('{"provider":"generation evidence"}')

    async def command(args, **kwargs):
        calls.append((args, kwargs))
        if args[0] != provider:
            raise RuntimeError("Gemini unavailable")
        assert args[args.index("--site-session") + 1] == "persistent"
        assert kwargs["site_session_namespace"].endswith("-" + provider)
        entered.set()
        await asyncio.Event().wait()

    async def close(namespace, *, sites):
        if sites == (provider,):
            assert namespace == calls[-1][1]["site_session_namespace"]
            closed.set()
            await release_cleanup.wait()

    monkeypatch.setattr(review, "run_opencli", command)
    monkeypatch.setattr(close_review_sessions, "side_effect", close)
    monkeypatch.setattr(review.config, "AV_SYNC_REVIEW_FALLBACK_PROVIDER", "chatgpt")

    async def run():
        task = asyncio.create_task(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
        await entered.wait()
        task.cancel()
        await closed.wait()
        assert not task.done()  # The worker cannot move on before tab cleanup.
        release_cleanup.set()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert [args[0] for args, _ in calls] == (["gemini"] if provider == "gemini" else ["gemini", "chatgpt"])
    assert image.read_bytes() == b"unchanged accepted generation"
    assert generated.read_text() == '{"provider":"generation evidence"}'
    journals = list(tmp_path.glob(f"review-session-*-{provider}/browser-session-{provider}.json"))
    assert len(journals) == 1
    assert json.loads(journals[0].read_text())["verified"] is True
    assert not list(tmp_path.glob("visual-review-*.json"))
    response = json.loads(next(tmp_path.glob(f"response-explainer_logic-*-{provider}.json")).read_text())
    assert "Review interrupted" in response["stderr"] or provider == "chatgpt"


def test_preemption_during_original_conversation_read_closes_same_session(
    tmp_path, monkeypatch, close_review_sessions,
):
    entered = asyncio.Event()
    calls = []
    image = tmp_path / "image.png"
    image.write_bytes(b"original candidate")
    conversation_id = "00000000-0000-0000-0000-000000000001"

    async def ask(args, **kwargs):
        if args[0] == "gemini":
            raise RuntimeError("Gemini unavailable")
        calls.append((args, kwargs))
        return OpenCLIResult(tuple(args), 0, json.dumps([{"conversationId": conversation_id}]), "")

    async def read(args, **kwargs):
        calls.append((args, kwargs))
        assert args[:3] == ["chatgpt", "detail", conversation_id]
        assert args[args.index("--site-session") + 1] == "persistent"
        assert kwargs["site_session_namespace"] == calls[0][1]["site_session_namespace"]
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(review, "run_opencli", ask)
    monkeypatch.setattr(multimodal_review, "run_opencli", read)
    monkeypatch.setattr(review.config, "AV_SYNC_REVIEW_FALLBACK_PROVIDER", "chatgpt")

    async def run():
        task = asyncio.create_task(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert [args[1] for args, _ in calls] == ["ask", "detail"]
    close_review_sessions.assert_any_await(calls[0][1]["site_session_namespace"], sites=("chatgpt",))
    assert image.read_bytes() == b"original candidate"
    assert not list(tmp_path.glob("visual-review-*.json"))
    receipt = json.loads(next(tmp_path.glob("response-explainer_logic-*-chatgpt.json")).read_text())
    assert conversation_id in receipt["stdout"]


def test_preemption_during_cleanup_reuses_completed_verdict_without_new_request(
    tmp_path, monkeypatch, close_review_sessions,
):
    closing = asyncio.Event()
    release_cleanup = asyncio.Event()
    calls = []
    image = tmp_path / "image.png"
    image.write_bytes(b"original candidate")

    async def command(args, **kwargs):
        calls.append(args)
        return OpenCLIResult(tuple(args), 0, json.dumps(payload()), "")

    async def close(namespace, *, sites):
        closing.set()
        await release_cleanup.wait()

    monkeypatch.setattr(review, "run_opencli", command)
    monkeypatch.setattr(close_review_sessions, "side_effect", close)

    async def run():
        task = asyncio.create_task(review.review_image(image, SCENE, {}, tmp_path, lambda _: None))
        await closing.wait()
        report_path = next(tmp_path.glob("visual-review-*.json"))
        assert json.loads(report_path.read_text())["passed"] is True
        task.cancel()
        release_cleanup.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        result, cached_path = await review.review_image(image, SCENE, {}, tmp_path, lambda _: None)
        assert result["passed"] is True and cached_path == report_path

    asyncio.run(run())
    assert len(calls) == 1
