import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend import prompts_registry
from backend.pipeline import thumbnail
from backend.pipeline.opencli import OpenCLIError, OpenCLIResult
from backend.tests.test_thumbnail import PNG_FIXTURE


REFUSAL = (
    "We’re so sorry, but the image we created may violate our guardrails "
    "concerning similarity to third-party content. If you think we got it "
    "wrong, please retry or edit your prompt."
)
URL = "https://chatgpt.com/c/rejected1234"


def reject(args, *, wrong_prompt=False):
    state = Path(args[args.index("--state-file") + 1])
    state.write_text(json.dumps({
        "prompt": "Generate an image of: " + ("someone else's prompt" if wrong_prompt else args[2]),
        "stage": "image_wait_failed", "conversationUrl": URL, "beforeUrls": [],
    }))
    diagnostic = {
        "stage": "image_wait_diagnostic", "conversation_url": URL,
        "observation": {
            "terminal_error": "CHATGPT_IMAGE_GENERATION_FAILED", "provider_message": REFUSAL,
        },
    }
    result = OpenCLIResult(tuple(args), 1, "", "[chatgpt/image] " + json.dumps(diagnostic))
    raise OpenCLIError("CHATGPT_IMAGE_GENERATION_FAILED: " + REFUSAL, result=result)


def downloaded(args):
    image = Path(args[args.index("--op") + 1]) / "revised.png"
    image.write_bytes(PNG_FIXTURE)
    return OpenCLIResult(tuple(args), 0, json.dumps([{"file": str(image)}]), "")


@pytest.fixture
def arguments(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("Citi's Nathan Sheets discussed a forecast on Bloomberg. Figures were not disclosed.")
    return dict(task_id="repair-test", task_dir=tmp_path, title="Citi forecast", script_path=script)


def test_repair_ai_receives_actual_error_and_factual_source(arguments):
    captured = {}

    async def chat(system, source, *args, **kwargs):
        captured.update(system=system, source=json.loads(source), args=args)
        return json.dumps({"prompt": "An original editorial forecast document, landscape 16:9.",
                           "rationale": "Remove the imitated broadcast set and exact logos."})

    with (
        patch.object(thumbnail, "_resolve_provider", AsyncMock(return_value=("endpoint", "model", "key"))) as provider,
        patch.object(thumbnail, "_chat", chat),
    ):
        value = asyncio.run(thumbnail.revise_thumbnail_prompt(
            title=arguments["title"], script=arguments["script_path"].read_text(),
            prompt="Reproduce the exact broadcast set and logos", provider_error={"message": REFUSAL},
            revisions=[], provider_id=7, ai_endpoint=None, ai_model=None, log=None,
        ))
    provider.assert_awaited_once_with(7, None, None)
    assert captured["source"]["provider_error"]["message"] == REFUSAL
    assert "Figures were not disclosed" in captured["source"]["audio_script"]
    assert "Do not substitute a confusing lookalike" in captured["system"]
    assert value["rationale"].startswith("Remove")
    assert prompts_registry.get_spec("thumbnail_repair").file == "thumbnail_repair.txt"


def test_terminal_error_revises_once_preserving_original_request(arguments):
    requests = []
    original_state = None

    async def command(args, **kwargs):
        nonlocal original_state
        state = Path(args[args.index("--state-file") + 1])
        requests.append(state)
        if len(requests) == 1:
            try:
                reject(args)
            finally:
                original_state = state.read_bytes()
        assert args[2] == "Original editorial forecast document"
        assert not state.exists()
        return downloaded(args)

    repair = AsyncMock(return_value={"prompt": "Original editorial forecast document",
                                    "rationale": "Address the explicit similarity refusal."})
    with (
        patch.object(thumbnail, "generate_thumbnail_prompt", AsyncMock(return_value="Exact broadcast set")) as director,
        patch.object(thumbnail, "revise_thumbnail_prompt", repair),
        patch.object(thumbnail, "run_opencli", command),
    ):
        artifact = asyncio.run(thumbnail.generate_thumbnail(**arguments))
        again = asyncio.run(thumbnail.generate_thumbnail(**arguments))
    assert artifact == again
    assert requests[0] != requests[1]
    assert requests[0].read_bytes() == original_state
    assert (requests[0].parent / "failure.json").is_file()
    assert json.loads(Path(artifact.manifest_path).read_text())["prompt_revision"] == 1
    assert Path(artifact.prompt_path).read_text().strip() == "Original editorial forecast document"
    repair.assert_awaited_once()
    director.assert_awaited_once()
    assert repair.await_args.kwargs["provider_error"]["message"] == REFUSAL
    assert repair.await_args.kwargs["prompt"] == "Exact broadcast set"


def test_uncertain_revision_resumes_its_checkpoint_without_another_rewrite(arguments):
    calls = []

    async def command(args, **kwargs):
        state = Path(args[args.index("--state-file") + 1])
        calls.append(state)
        if len(calls) == 1:
            reject(args)
        if len(calls) == 2:
            state.write_text(json.dumps({"prompt": "Generate an image of: " + args[2],
                                        "stage": "waiting", "conversationUrl": URL}))
            raise OpenCLIError("timed out while the revised image is still running")
        assert state == calls[1]
        assert state.is_file()
        return downloaded(args)

    repair = AsyncMock(return_value={"prompt": "Original composition", "rationale": "Avoid imitating the broadcast."})
    with (
        patch.object(thumbnail, "generate_thumbnail_prompt", AsyncMock(return_value="Exact broadcast set")),
        patch.object(thumbnail, "revise_thumbnail_prompt", repair),
        patch.object(thumbnail, "run_opencli", command),
    ):
        with pytest.raises(OpenCLIError, match="still running"):
            asyncio.run(thumbnail.generate_thumbnail(**arguments))
        artifact = asyncio.run(thumbnail.generate_thumbnail(**arguments))
    assert Path(artifact.image_path).is_file()
    repair.assert_awaited_once()
    assert len(calls) == 3


def test_repair_limit_persists_across_resume(arguments):
    states = []

    async def command(args, **kwargs):
        states.append(Path(args[args.index("--state-file") + 1]))
        reject(args)

    repair = AsyncMock(side_effect=[
        {"prompt": "Original composition one", "rationale": "First revision"},
        {"prompt": "Original composition two", "rationale": "Second revision"},
    ])
    with (
        patch.object(thumbnail, "generate_thumbnail_prompt", AsyncMock(return_value="Original prompt")),
        patch.object(thumbnail, "revise_thumbnail_prompt", repair),
        patch.object(thumbnail, "run_opencli", command),
    ):
        for _ in range(2):
            with pytest.raises(OpenCLIError, match="CHATGPT_IMAGE_GENERATION_FAILED"):
                asyncio.run(thumbnail.generate_thumbnail(**arguments))
    assert repair.await_count == 2
    assert len(states) == 4
    assert states[-1] == states[-2]  # Re-observe the last request; never reset its budget.
    assert len(set(states)) == 3


def test_unowned_checkpoint_never_authorizes_prompt_replacement(arguments):
    async def command(args, **kwargs):
        reject(args, wrong_prompt=True)

    repair = AsyncMock()
    with (
        patch.object(thumbnail, "generate_thumbnail_prompt", AsyncMock(return_value="Original prompt")),
        patch.object(thumbnail, "revise_thumbnail_prompt", repair),
        patch.object(thumbnail, "run_opencli", command),
        pytest.raises(RuntimeError, match="exact rejected request checkpoint"),
    ):
        asyncio.run(thumbnail.generate_thumbnail(**arguments))
    repair.assert_not_awaited()


@pytest.mark.parametrize("reply", [
    "{}", '["not an object"]', '{"prompt":"Original prompt","rationale":"No change"}',
])
def test_invalid_or_unchanged_ai_repair_does_not_submit(arguments, reply):
    runner = AsyncMock(side_effect=lambda args, **kwargs: reject(args))
    with (
        patch.object(thumbnail, "generate_thumbnail_prompt", AsyncMock(return_value="Original prompt")),
        patch.object(thumbnail, "_resolve_provider", AsyncMock(return_value=("url", "model", "key"))),
        patch.object(thumbnail, "_chat", AsyncMock(return_value=reply)),
        patch.object(thumbnail, "run_opencli", runner),
        pytest.raises(RuntimeError),
    ):
        asyncio.run(thumbnail.generate_thumbnail(**arguments))
    runner.assert_awaited_once()
    assert not list((arguments["task_dir"] / "thumbnail").rglob("prompt-revisions.json"))
