import unittest

from modules.wake_listener import contains_wake_word


class WakeListenerTest(unittest.TestCase):
    def test_contains_wake_word_matches_phrase(self):
        self.assertTrue(contains_wake_word("Hey Bujji"))

    def test_contains_wake_word_ignores_case_and_punctuation(self):
        self.assertTrue(contains_wake_word("  hey, bujji!  "))

    def test_contains_wake_word_rejects_unrelated_text(self):
        self.assertFalse(contains_wake_word("Hello there, what time is it?"))

    def test_contains_wake_word_rejects_extra_words(self):
        self.assertFalse(contains_wake_word("Hey Bujji, start the music"))


if __name__ == "__main__":
    unittest.main()