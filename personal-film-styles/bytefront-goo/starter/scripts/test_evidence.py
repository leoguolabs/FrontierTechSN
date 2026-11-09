"""Guard editorial links, ordinary episode compatibility and clip boundaries."""
from pathlib import Path
import tempfile
import unittest
from validate_evidence import validate


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'page.png').touch()
        self.shot = dict(id='source', type='document', start=24, end=72, paragraph='p1',
                         relevance='Supports the quantity spoken in p1', role='evidence',
                         source_url='https://example.org/paper', rights='Permission recorded',
                         credit='Source', asset='page.png')

    def plan(self, shots):
        return dict(fps=24, duration_frames=240, shots=shots)

    def test_zero_is_valid_and_regular_scenes_are_ignored(self):
        self.assertEqual(validate(self.plan([dict(scene='host')]), self.root)['shots'], 0)

    def test_nested_episode_keeps_source_link(self):
        nested = dict(scene='evidence', evidence=self.shot, paragraph='p1', start=24, end=72)
        result = validate(self.plan([nested]), self.root)
        self.assertEqual(result['seconds'], 2)
        self.assertTrue(result['editorial_review_needed'])

    def test_overlap_and_missing_relevance_fail(self):
        for shots in ([self.shot, dict(self.shot, id='second', start=71)],
                      [dict(self.shot, relevance='')]):
            with self.assertRaises(ValueError):
                validate(self.plan(shots), self.root)

    def test_half_open_adjacency_is_valid(self):
        self.assertEqual(validate(self.plan([self.shot, dict(self.shot, id='second', start=72, end=96)]), self.root)['shots'], 2)

    def test_external_and_missing_assets_fail(self):
        for asset in ('../page.png', 'absent.png'):
            with self.assertRaises(ValueError):
                validate(self.plan([dict(self.shot, asset=asset)]), self.root)

    def test_highlight_cannot_outlast_shot(self):
        with self.assertRaises(ValueError):
            validate(self.plan([dict(self.shot, highlights=[dict(at=1.8, seconds=.5)])]), self.root)

    def test_chart_needs_basis_and_valid_axes(self):
        chart = dict(self.shot, type='chart', points=[[0, 1], [1, 2]], x_max=1, y_max=2)
        with self.assertRaises(ValueError):
            validate(self.plan([chart]), self.root)
        chart['data_basis'] = '2**n'
        validate(self.plan([chart]), self.root)
        chart['y_max'] = 1
        with self.assertRaises(ValueError):
            validate(self.plan([chart]), self.root)

    def test_illustration_label_and_all_frames_required(self):
        shot = dict(self.shot, type='footage', role='illustration', frames_dir='frames')
        with self.assertRaises(ValueError):
            validate(self.plan([shot]), self.root)
        shot['context_label'] = 'Context illustration'
        with self.assertRaises(ValueError):
            validate(self.plan([shot]), self.root)
        (self.root / 'frames').mkdir()
        for n in range(1, 49):
            (self.root / 'frames' / f'{n:06d}.jpg').touch()
        validate(self.plan([shot]), self.root)


if __name__ == '__main__':
    unittest.main()
