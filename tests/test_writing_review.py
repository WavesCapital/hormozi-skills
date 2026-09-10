"""Check metric limits without treating metrics as a substitute for source review."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/hormozi/scripts/plain_language.py'
SPEC = importlib.util.spec_from_file_location('writing_review', SCRIPT)
assert SPEC and SPEC.loader
writing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(writing)


class WritingReviewTests(unittest.TestCase):
    def test_soft_wrap_cannot_game_reading_score(self):
        flat = 'The owner checks the cost of each new lead before the team spends more money.'
        wrapped = flat.replace(' ', '\n')
        left, right = writing.analyze(flat), writing.analyze(wrapped)
        for key in ('words', 'sentences', 'reading_grade_estimate', 'issues'):
            self.assertEqual(left[key], right[key], key)
        self.assertNotEqual(left['checked_text_sha256'], right['checked_text_sha256'])

    def test_paragraph_and_list_boundaries_remain_visible(self):
        value = writing.analyze('Check costs\n\nCheck cash\n\n- Check buyers\n- Check sales')
        self.assertEqual(value['sentences'], 4)
        self.assertEqual(value['words'], 8)

    def test_source_positive_example_keeps_flags_and_requires_judgment(self):
        # Private source Blackbook224 explicitly calls this a good example.
        value = writing.analyze(
            'We borrow money so we can buy bigger stuff (and make more) than we could with our cash alone.'
        )
        self.assertEqual(value['words'], 19)
        self.assertFalse(value['ok'])
        self.assertIn('long_sentences', value['issues'])
        self.assertGreater(value['reading_grade_estimate'], value['target_grade'])
        self.assertEqual(value['quality_status'], 'not_assessed')

    def test_plain_list_and_adjective_flags_are_not_quality_verdicts(self):
        for text, flag in [('Check buyers, costs, and cash.', 'too_many_commas'),
                           ('Your business file is unchanged.', 'passive_voice')]:
            with self.subTest(text=text):
                value = writing.analyze(text)
                self.assertIn(flag, value['issues'])
                self.assertEqual(value['quality_status'], 'not_assessed')

    def test_low_score_cannot_certify_nonsense(self):
        value = writing.analyze('Use bad step. Use bad skill. Track blue. Track debt.')
        self.assertLessEqual(value['reading_grade_estimate'], 3)
        self.assertEqual(value['quality_status'], 'not_assessed')

    def test_empty_or_code_only_is_not_a_clean_prose_pass(self):
        for text in ['', '```python\nprint(1)\n```']:
            with self.subTest(text=text):
                value = writing.analyze(text)
                self.assertFalse(value['ok'])
                self.assertIn('no_prose', value['issues'])


if __name__ == '__main__':
    unittest.main()
