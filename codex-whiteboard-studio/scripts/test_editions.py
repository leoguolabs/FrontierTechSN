"""Regression checks for cross-edition writes and stale delivery export."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build
from export_project import reviewed_video
from production import Production, production


class EditionDeliveryTests(unittest.TestCase):
    def test_long_build_routes_each_artifact_stage_to_long(self):
        with patch("sys.argv", ["build.py", "--edition", "long", "--speech"]), \
                patch.object(build, "run") as run:
            build.main()
        calls = [list(c.args) for c in run.call_args_list]
        routed = [c for c in calls if c[1] not in {
            "scripts/analyze_frames.py", "scripts/compare_frames.py"}]
        self.assertEqual(len(routed), 8)
        for command in routed:
            self.assertIn("--edition", command)
            self.assertEqual(command[command.index("--edition")+1], "long")
        analyze, compare = calls[-2:]
        project = production("long")
        self.assertEqual(analyze[2], project.video)
        self.assertEqual(compare[2], project.video)
        self.assertEqual(compare[compare.index("--definitions")+1],
                         project.root/"content/comparison.json")
        self.assertEqual(compare[compare.index("--timeline")+1],
                         project.root/"media/timeline.json")
        self.assertNotIn(production("short").video, sum(calls, []))

    def test_export_requires_review_of_the_exact_current_video(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/"review").mkdir()
            (root/"media").mkdir()
            project = Production("long", root, "film.mp4")
            project.video.write_bytes(b"reviewed encoded artifact")
            digest = hashlib.sha256(project.video.read_bytes()).hexdigest()
            technical = root/"review/technical-delivery.json"
            review = root/"review/delivery.json"
            technical.write_text(json.dumps({"checks_passed": True, "video_sha256": digest}))
            review.write_text(json.dumps({"complete_frame_review": False, "video_sha256": digest}))
            with self.assertRaisesRegex(ValueError, "complete frame review"):
                reviewed_video(project)
            review.write_text(json.dumps({"complete_frame_review": True, "video_sha256": digest}))
            self.assertEqual(reviewed_video(project), digest)
            project.video.write_bytes(b"new unreviewed encoded artifact")
            with self.assertRaisesRegex(ValueError, "technical verification"):
                reviewed_video(project)


if __name__ == "__main__":
    unittest.main()
