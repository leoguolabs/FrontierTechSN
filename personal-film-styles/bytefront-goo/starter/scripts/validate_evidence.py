"""Check source-to-narration links and half-open frame ranges; an empty plan is valid."""
import argparse
import json
from pathlib import Path


def validate(plan, root):
    fps = plan.get('fps', 24)
    if fps != 24:
        raise ValueError('Evidence must use the Goo delivery cadence of 24 fps')
    end = plan['duration_frames']
    # Accept either a cutaway-only manifest or the normal planned episode.
    shots = []
    for s in plan.get('shots', []):
        if s.get('scene') == 'evidence':
            shots.append(dict(s['evidence'], paragraph=s['paragraph'], start=s['start'], end=s['end']))
        elif 'scene' not in s:
            shots.append(s)
    shots.sort(key=lambda x: x['start'])
    previous = 0
    ids = set()
    for s in shots:
        if s['id'] in ids:
            raise ValueError('Duplicate evidence id: ' + s['id'])
        ids.add(s['id'])
        if not all(isinstance(s[k], int) for k in ('start', 'end')) or not (previous <= s['start'] < s['end'] <= end):
            raise ValueError('Overlapping or invalid range: ' + s['id'])
        previous = s['end']
        for k in ('paragraph', 'relevance', 'source_url', 'rights', 'credit', 'role'):
            if not s.get(k):
                raise ValueError(f'{s["id"]}: missing {k}')
        if s['role'] not in {'evidence', 'illustration', 'context'}:
            raise ValueError('Unknown source role')
        if s['type'] not in {'document', 'chart', 'image', 'footage'}:
            raise ValueError('Unknown evidence type')
        if s['type'] == 'chart':
            if not s.get('data_basis') or not s.get('points'):
                raise ValueError('Chart requires fixed data and its calculation/source')
            if s.get('x_max', 0) <= 0 or s.get('y_max', 0) <= 0:
                raise ValueError('Chart axes must be positive')
            if any(x < 0 or x > s['x_max'] or y < 0 or y > s['y_max'] for x, y in s['points']):
                raise ValueError('Chart data exceeds labelled axes')
        else:
            asset = (root / s['asset']).resolve()
            if not asset.is_relative_to(root.resolve()) or not asset.is_file():
                raise ValueError('Missing or external asset: ' + s['asset'])
        if s['type'] == 'footage' and s['role'] == 'illustration' and not s.get('context_label'):
            raise ValueError('Illustrative footage needs an on-screen context label')
        if s['type'] == 'footage':
            frames = (root / s['frames_dir']).resolve()
            if not frames.is_relative_to(root.resolve()):
                raise ValueError('External footage frame directory')
            if any(not (frames / f'{n:06d}.jpg').is_file() for n in range(1, s['end'] - s['start'] + 1)):
                raise ValueError('Prepare all footage frames at 24 fps before planning/rendering')
        for h in s.get('highlights', []):
            if h['at'] < 0 or h['at'] + h.get('seconds', .55) > (s['end'] - s['start']) / fps:
                raise ValueError('Marker animation extends beyond its shot')
    coverage = sum(s['end'] - s['start'] for s in shots) / end if end else 0
    return {'shots': len(shots), 'seconds': sum(s['end'] - s['start'] for s in shots) / fps,
            'coverage': coverage, 'editorial_review_needed': coverage > .15,
            'note': 'Frequency is a review signal, never a quota. Zero inserts is valid.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('manifest', type=Path)
    p.add_argument('--root', type=Path, default=Path.cwd())
    args = p.parse_args()
    print(json.dumps(validate(json.loads(args.manifest.read_text()), args.root), indent=2))
