"""Exact dictionary-word boundaries for numeric CamelCase model names."""

import re

from backend.pipeline import tts_pronunciation as pronunciation
from backend.pipeline.tts_word_pronunciation import lexicon


def model_name_spoken(source: str, hints: dict | None = None) -> str:
    """Separate source words and spell digits without inventing a pronunciation.

    Single capitals, unknown words, abbreviations and punctuation are excluded.
    This supports EgoWild2Dex -> Ego Wild two Dex, never GPT4 -> a guessed word.
    """
    parts = re.findall(r'[A-Z][a-z]+|[0-9]+', source)
    if (''.join(parts) != source or len(parts) < 3
            or not any(part.isdigit() for part in parts)
            or any(not lexicon().get(part.casefold()) for part in parts if part.isalpha())):
        raise ValueError('Model name lacks exact independent dictionary word boundaries')
    hints = {} if hints is None else hints
    if not isinstance(hints, dict) or set(hints) - {part for part in parts if part.isalpha()}:
        raise ValueError('Model-name hints must belong to its exact source words')
    from backend.pipeline.tts_word_pronunciation import validate_word_hint
    for word, hint in hints.items():
        if not isinstance(hint, dict):
            raise ValueError('Invalid model-name word hint')
        validate_word_hint(word, hint.get('spoken'), hint.get('phones'))
    return ' '.join(pronunciation.numeric_cue(part) if part.isdigit()
                    else hints.get(part, {}).get('spoken', part) for part in parts)


def repair_edits(text: str, edits: list[dict]) -> list[dict]:
    """Correct only a single capital misclassified at a digit-to-word boundary."""
    corrected = list(edits)
    for match in re.finditer(r'(?<![A-Za-z0-9_])[A-Za-z0-9]+(?![A-Za-z0-9_])', text):
        local = [edit for edit in edits if edit['start'] < match.end() and edit['end'] > match.start()]
        if not local or any(
                edit.get('kind') not in (None, 'initialism')
                or edit['end'] != edit['start'] + 1
                or text[edit['start']:edit['end']] != edit['source']
                or not match.start() < edit['start'] < edit['end'] < match.end()
                or not text[edit['start'] - 1].isdigit()
                or not re.match(r'[a-z]{2,}', text[edit['end']:match.end()])
                for edit in local):
            continue
        if any(p.start() < match.end() and p.end() > match.start()
               for p in pronunciation.PROTECTED_TEXT_RE.finditer(text)):
            continue
        try:
            spoken = model_name_spoken(match[0])
        except ValueError:
            continue
        corrected = [edit for edit in corrected if edit not in local]
        corrected.append({'start': match.start(), 'end': match.end(), 'source': match[0],
                          'spoken': spoken, 'kind': 'model_name'})
    return sorted(corrected, key=lambda edit: edit['start'])
