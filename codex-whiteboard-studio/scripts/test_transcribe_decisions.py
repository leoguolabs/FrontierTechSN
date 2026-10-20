"""A recognizer decision cannot silently transfer to another script or take."""
import hashlib
import unittest

from transcribe import recognizer_for


class RecognizerDecisionTests(unittest.TestCase):
    def setUp(self):
        self.row = {"id": "06", "text": "Use the idea.", "audio_sha256": "take-two"}
        self.decisions = {"06": {
            "source_sha256": hashlib.sha256(self.row["text"].encode()).hexdigest(),
            "audio_sha256": "take-two",
            "model": "reviewed-recognizer",
        }}

    def test_only_the_reviewed_source_and_audio_get_the_selected_recognizer(self):
        self.assertEqual(recognizer_for(self.row, "default", self.decisions),
                         "reviewed-recognizer")
        self.assertEqual(recognizer_for(self.row, "default", {}), "default")

    def test_rewritten_text_rejects_the_old_decision(self):
        with self.assertRaisesRegex(ValueError, "older narration"):
            recognizer_for({**self.row, "text": "Use a new method."},
                           "default", self.decisions)

    def test_a_new_take_requires_its_own_decision(self):
        with self.assertRaisesRegex(ValueError, "another WAV"):
            recognizer_for({**self.row, "audio_sha256": "take-three"},
                           "default", self.decisions)


if __name__ == "__main__":
    unittest.main()
