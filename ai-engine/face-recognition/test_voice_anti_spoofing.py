import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import voice_anti_spoofing as vas


class FakeSession:
    def __init__(self, logits):
        self.logits = np.asarray(logits, dtype=np.float32)
        self.received_audio = None

    def get_inputs(self):
        return [SimpleNamespace(name="wav")]

    def run(self, outputs, inputs):
        self.received_audio = inputs["wav"]
        return [self.logits]


class AASISTTests(unittest.TestCase):

    def setUp(self):
        self.audio = (
            0.05 * np.sin(
                2 * np.pi * 220 *
                np.arange(80000) / 16000
            )
        ).astype(np.float32)

    def test_audio_quality(self):
        result = vas.assess_audio_quality(self.audio)
        self.assertTrue(result["passed"])

    def test_empty_audio(self):
        result = vas.assess_audio_quality(
            np.array([], dtype=np.float32)
        )
        self.assertFalse(result["passed"])

    def test_short_audio(self):
        result = vas.assess_audio_quality(
            np.zeros(1000, dtype=np.float32)
        )
        self.assertFalse(result["passed"])

    def test_model_input_shape(self):
        result = vas.prepare_model_audio(self.audio)
        self.assertEqual(result.shape, (1, 64600))

    def test_short_audio_padding(self):
        short_audio = self.audio[:50000]
        result = vas.prepare_model_audio(short_audio)
        self.assertEqual(result.shape, (1, 64600))

    def test_spoof_classification(self):
        fake = FakeSession([[3.0, 0.0]])

        with patch.object(vas, "_session", fake):
            result = vas.detect_spoof(self.audio)

        self.assertTrue(result["is_spoof"])
        self.assertEqual(result["decision"], "SPOOF")

    def test_bonafide_classification(self):
        fake = FakeSession([[0.0, 3.0]])

        with patch.object(vas, "_session", fake):
            result = vas.detect_spoof(self.audio)

        self.assertFalse(result["is_spoof"])
        self.assertEqual(result["decision"], "BONAFIDE")

    def test_invalid_sample_rate(self):
        result = vas.detect_spoof(
            self.audio,
            sample_rate=44100
        )

        self.assertEqual(
            result["decision"],
            "REJECTED_AUDIO_QUALITY"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
