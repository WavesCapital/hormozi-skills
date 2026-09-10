"""Check exact-draft identity independently of readability cleanup."""
import hashlib
import importlib.util
import json
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/hormozi/scripts/plain_language.py'
SPEC = importlib.util.spec_from_file_location('writing_identity_subject', SCRIPT)
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class WritingIdentityTests(unittest.TestCase):
    def test_hash_covers_citations_and_line_breaks_before_cleanup(self):
        text = 'Fix the work first.\n\n[Source A, p. 9]'
        variants = [text, text.replace('\n', r'\n'), text + '\n',
                    text.replace('p. 9', 'p. 8'), 'Fix the work first.']
        hashes = [subject.analyze(t)['checked_text_sha256'] for t in variants]
        self.assertEqual(len(hashes), len(set(hashes)))
        self.assertEqual(hashes[0], hashlib.sha256(text.encode('utf-8')).hexdigest())

    def test_ignored_terms_do_not_change_input_identity(self):
        text = 'Check the API. API means the app link.'
        normal = subject.analyze(text)
        ignored = subject.analyze(text, ignored_terms=['API'])
        self.assertEqual(normal['checked_text_sha256'], ignored['checked_text_sha256'])

    def test_cli_stdin_preserves_exact_unicode_and_newlines(self):
        text = 'Keep the buyer’s trust.\n\nFix the work first.\n'
        result = subprocess.run([sys.executable, str(SCRIPT), '--strict'],
                                input=text, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['checked_text_sha256'],
                         hashlib.sha256(text.encode('utf-8')).hexdigest())

    def test_quoted_heredoc_keeps_shell_text_literal(self):
        text = (
            "Keep the buyer’s trust.\n\n"
            "- The fee is $1,000, not $1.\n"
            "- Read `source:book:p0171`.\n\n"
            "Treat $(exit 7), $HOME and \\n as text, not commands.\n"
        )
        command = (
            f"{shlex.quote(sys.executable)} {shlex.quote(str(SCRIPT))} "
            "--target-grade 3 <<'HORMOZI_DRAFT'\n"
            + text + "HORMOZI_DRAFT\n"
        )
        result = subprocess.run(['/bin/sh', '-c', command],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['checked_text_sha256'],
                         hashlib.sha256(text.encode('utf-8')).hexdigest())
        self.assertEqual(receipt['words'], subject.analyze(text)['words'])


if __name__ == '__main__':
    unittest.main()
