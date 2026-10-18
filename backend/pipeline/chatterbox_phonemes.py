"""Optional exact complete-source acoustic confirmation of ASR spelling drift."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from backend import config
from scripts.chatterbox_phoneme_evidence import audit_observation, reference_parts


async def confirm(path: Path, text: str, edits: list[dict], directory: Path) -> dict | None:
    if not config.CHATTERBOX_PHONEME_RUNTIME_LIB:
        return None
    runtime = Path(config.CHATTERBOX_PHONEME_RUNTIME_LIB)
    if not runtime.is_dir():
        return None
    try:
        reference_parts(text, edits)
    except (ValueError, KeyError):
        return {'supported': False, 'passed': False}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    target = directory / 'acoustic-phones' / digest
    target.mkdir(parents=True, exist_ok=True)
    observation_path = target / 'observation.json'
    if observation_path.exists():
        try:
            observation = json.loads(observation_path.read_text())
            report = audit_observation(path, text, edits, observation)
        except (ValueError, KeyError) as error:
            raise RuntimeError('Cached acoustic observation is invalid; preserving the completed job') from error
    else:
        env = os.environ.copy()
        env['HF_HUB_OFFLINE'] = '1'
        command = [sys.executable, str(config.PROJECT_ROOT / 'scripts/observe_chatterbox_phones.py'),
                   str(path), str(observation_path), '--runtime-lib', str(runtime)]
        try:
            done = await asyncio.to_thread(subprocess.run, command, cwd=config.PROJECT_ROOT,
                                           env=env, capture_output=True, timeout=180)
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError('Acoustic observation unavailable; preserving the completed job') from error
        if done.returncode or not observation_path.is_file():
            raise RuntimeError('Acoustic observation unavailable; preserving the completed job')
        observation = json.loads(observation_path.read_text())
        report = audit_observation(path, text, edits, observation)
    if report.get('passed') is not True and any(edit.get('kind') == 'model_name' for edit in edits):
        # A CTC observation at the waveform boundary can miss an onset phone.
        # Supply one fixed amount of zero context, never trim or alter speech.
        # The observer receives no source text; the audit recomputes both PCM
        # hashes to prove the complete original samples remain in order.
        (target / 'source-comparison.unpadded.json').write_text(json.dumps(report, indent=2))
        padded_path = target / 'observation.edge-padding.json'
        if not padded_path.exists():
            env = os.environ.copy()
            env['HF_HUB_OFFLINE'] = '1'
            command = [sys.executable, str(config.PROJECT_ROOT / 'scripts/observe_chatterbox_phones.py'),
                       str(path), str(padded_path), '--runtime-lib', str(runtime), '--edge-padding-ms', '250']
            try:
                done = await asyncio.to_thread(subprocess.run, command, cwd=config.PROJECT_ROOT,
                                               env=env, capture_output=True, timeout=180)
            except (OSError, subprocess.SubprocessError) as error:
                raise RuntimeError('Padded acoustic observation unavailable; preserving the completed job') from error
            if done.returncode or not padded_path.is_file():
                raise RuntimeError('Padded acoustic observation unavailable; preserving the completed job')
        try:
            observation = json.loads(padded_path.read_text())
            if not observation.get('input_transform'):
                raise ValueError('Padding evidence is missing')
            report = audit_observation(path, text, edits, observation)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            raise RuntimeError('Padded acoustic observation is invalid; preserving the completed job') from error
    report_path = target / 'source-comparison.json'
    temporary = report_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    temporary.replace(report_path)
    return report
