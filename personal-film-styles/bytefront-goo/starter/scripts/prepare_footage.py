"""Prepare a licensed local clip for deterministic 24 fps evidence rendering."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/frame_review'))
from ffmpeg_gate import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--source-in', type=float, default=0)
    parser.add_argument('--frames', type=int, required=True)
    args = parser.parse_args()
    if not args.source.is_file() or args.source_in < 0 or args.frames < 1:
        parser.error('Use an existing source, nonnegative in point and positive frame count')
    args.destination.mkdir(parents=True, exist_ok=False)
    run(['-nostdin', '-hide_banner', '-loglevel', 'error', '-ss', str(args.source_in),
         '-i', str(args.source.resolve()), '-an', '-vf', 'fps=24', '-frames:v', str(args.frames),
         '-q:v', '2', str(args.destination.resolve() / '%06d.jpg')])
    if len(list(args.destination.glob('*.jpg'))) != args.frames:
        raise ValueError('Source is too short; choose a complete action, never pad/freeze to fill time')
    print(f'Prepared {args.frames} frames; source audio is excluded')


if __name__ == '__main__':
    main()
