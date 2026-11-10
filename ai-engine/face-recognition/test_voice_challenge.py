import unittest

from voice_challenge import (
    normalize_text,
    generate_challenge,
    verify_challenge
)


class VoiceChallengeTests(unittest.TestCase):

    def test_normalization(self):
        self.assertEqual(
            normalize_text("Silver TIGER, opens window!"),
            "silver tiger opens window"
        )

    def test_correct_phrase(self):
        result = verify_challenge(
            "silver tiger opens window",
            "Silver tiger opens window"
        )
        self.assertTrue(result["verified"])

    def test_wrong_phrase(self):
        result = verify_challenge(
            "silver tiger opens window",
            "yellow rabbit closes garden"
        )
        self.assertFalse(result["verified"])

    def test_missing_word(self):
        result = verify_challenge(
            "silver tiger opens window",
            "silver tiger opens"
        )
        self.assertFalse(result["verified"])

    def test_random_challenge(self):
        phrase = generate_challenge()
        self.assertEqual(len(phrase.split()), 4)

    def test_empty_transcript(self):
        result = verify_challenge(
            "silver tiger opens window",
            ""
        )
        self.assertFalse(result["verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
