import unittest
import tempfile
import os

import numpy as np

from voice_authentication import (
    normalize_embedding,
    cosine_similarity,
    load_profiles,
    save_profiles
)

from voice_anti_spoofing import assess_audio_quality


class VoiceAuthenticationTests(unittest.TestCase):

    def test_embedding_normalization(self):
        embedding = np.array([3.0, 4.0])

        result = normalize_embedding(embedding)

        self.assertAlmostEqual(
            float(np.linalg.norm(result)),
            1.0,
            places=5
        )

    def test_same_speaker_similarity(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([2.0, 4.0, 6.0])

        score = cosine_similarity(a, b)

        self.assertAlmostEqual(score, 1.0, places=5)

    def test_different_speaker_similarity(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])

        score = cosine_similarity(a, b)

        self.assertAlmostEqual(score, 0.0, places=5)

    def test_invalid_embedding(self):
        with self.assertRaises(ValueError):
            normalize_embedding(np.array([0.0, 0.0]))

    def test_embedding_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            cosine_similarity(
                np.array([1.0, 2.0]),
                np.array([1.0, 2.0, 3.0])
            )

    def test_audio_quality_pass(self):
        audio = (
            0.05 * np.sin(
                2 * np.pi * 220 *
                np.arange(64000) / 16000
            )
        ).astype(np.float32)

        result = assess_audio_quality(audio)

        self.assertTrue(result["passed"])

    def test_empty_audio_rejected(self):
        result = assess_audio_quality(
            np.array([], dtype=np.float32)
        )

        self.assertFalse(result["passed"])

    def test_quiet_audio_rejected(self):
        audio = np.zeros(64000, dtype=np.float32)

        result = assess_audio_quality(audio)

        self.assertFalse(result["passed"])

    def test_profile_save_and_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(
                directory,
                "voice_profiles.json"
            )

            data = {
                "version": 1,
                "profiles": {
                    "TestUser": {
                        "embedding": [0.1, 0.2, 0.3]
                    }
                }
            }

            save_profiles(data, path)
            loaded = load_profiles(path)

            self.assertEqual(
                loaded["profiles"]["TestUser"]["embedding"],
                [0.1, 0.2, 0.3]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
