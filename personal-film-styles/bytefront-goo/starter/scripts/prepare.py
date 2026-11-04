"""Prepare provider requests at meaning boundaries. A project contains one language."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def prepare():
    episode = read(CONTENT / 'episode.json')
    if episode['language'] not in ('en', 'zh') or not episode['chapters'] or not episode['shots']:
        raise ValueError('Write chapters, paragraphs and shots in content/episode.json; choose en or zh.')
    jobs, lines, seen = [], [], set()
    def unique(identifier):
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', identifier) or identifier in seen:
            raise ValueError(f'Unsafe or repeated ID {identifier}')
        seen.add(identifier)
    for chapter in episode['chapters']:
        unique(chapter['id'])
        if not chapter['paragraphs'] or not 0 <= chapter.get('activity', .65) <= 1:
            raise ValueError(f'Empty chapter or invalid density: {chapter["id"]}')
        groups = [[]]
        for item in chapter['paragraphs']:
            unique(item['id'])
            text = item['text']
            if text.strip() != text or not text or len(text) > 2000:
                raise ValueError(f'Edit paragraph {item["id"]} at a meaning boundary (1–2000 characters).')
            if len(' '.join(x['text'] for x in groups[-1] + [item])) > 2000:
                groups.append([])
            groups[-1].append(item)
            lines.append(item)
        for n, group in enumerate(groups, 1):
            key = chapter['id'] if len(groups) == 1 else f'{chapter["id"]}-part-{n}'
            if key != chapter['id']:
                unique(key)
            text = ' '.join(x['text'] for x in group)
            jobs.append(dict(id=key, logical_chapter=chapter['id'], text=text,
                             paragraph_ids=[x['id'] for x in group],
                             text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    write(CONTENT/'chapters.json', {'lines': jobs})
    write(CONTENT/'narration.json', {'lines': lines})
    print(f'{len(lines)} paragraphs, {len(jobs)} continuous requests ({episode["language"]}).')

if __name__ == '__main__':
    prepare()
