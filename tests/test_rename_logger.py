import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rename_logger import RenameLogger


class RenameLoggerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logger = RenameLogger(str(self.root))

    def rename(self, name):
        original = self.root / name
        new = self.root / f"renamed_{name}"
        original.write_text(name)
        original.rename(new)
        return original, new

    def test_roundtrip_and_empty_history(self):
        self.assertFalse(self.logger.has_history())
        self.assertEqual(self.logger.undo_last_batch(), (0, 0))
        first = self.rename("first.mp4")
        self.logger.log_batch([first])
        second = self.rename("second.mp4")
        self.logger.log_batch([second])
        self.assertEqual(self.logger.get_last_batch_info()["count"], 1)
        self.assertEqual(self.logger.undo_last_batch(), (1, 0))
        self.assertTrue(first[1].exists())
        self.assertEqual(second[0].read_text(), "second.mp4")
        self.assertEqual(self.logger.undo_last_batch(), (1, 0))
        self.assertEqual(first[0].read_text(), "first.mp4")
        self.assertFalse(first[1].exists())
        self.assertFalse(self.logger.has_history())

    def test_partial_failure_keeps_pending_records_for_retry(self):
        pairs = [self.rename(name) for name in ("a.mp4", "b.mp4", "c.mp4")]
        self.logger.log_batch(pairs)
        pairs[0][0].write_text("conflicting file")
        pairs[2][1].unlink()
        self.assertEqual(self.logger.undo_last_batch(), (1, 2))
        self.assertEqual(pairs[0][0].read_text(), "conflicting file")
        pending = json.loads(self.logger.history_file.read_text())[-1]["renames"]
        self.assertEqual([item["original"] for item in pending],
                         [str(pairs[0][0]), str(pairs[2][0])])
        pairs[0][0].unlink()
        pairs[2][1].write_text("c.mp4")
        self.assertEqual(self.logger.undo_last_batch(), (2, 0))
        self.assertFalse(self.logger.has_history())
        for original, new in pairs:
            self.assertEqual(original.read_text(), original.name)
            self.assertFalse(new.exists())

    def test_case_only_rename_can_be_undone(self):
        original = self.root / "show_S01E01.mp4"
        new = self.root / "Show_S01E01.mp4"
        original.write_text("episode")
        original.rename(new)
        self.logger.log_batch([(original, new)])
        self.assertEqual(self.logger.undo_last_batch(), (1, 0))
        self.assertEqual(original.read_text(), "episode")
        names = {path.name for path in self.root.iterdir()}
        self.assertIn(original.name, names)
        self.assertNotIn(new.name, names)

    def test_dangling_symlink_destination_is_preserved(self):
        original, new = self.rename("a.mp4")
        original.symlink_to(self.root / "missing.mp4")
        self.logger.log_batch([(original, new)])
        self.assertEqual(self.logger.undo_last_batch(), (0, 1))
        self.assertTrue(original.is_symlink())
        self.assertEqual(new.read_text(), "a.mp4")
        self.assertTrue(self.logger.has_history())

    def test_existing_hard_link_is_preserved(self):
        original, new = self.rename("a.mp4")
        os.link(new, original)
        self.logger.log_batch([(original, new)])
        self.assertEqual(self.logger.undo_last_batch(), (0, 1))
        self.assertTrue(original.exists())
        self.assertTrue(new.exists())

    def test_case_only_hard_links_on_case_sensitive_disk_are_preserved(self):
        new = self.root / "Show.mp4"
        original = self.root / "show.mp4"
        new.write_text("episode")
        if original.exists():
            self.skipTest("Case-insensitive disk cannot hold distinct case-only hard links")
        os.link(new, original)
        self.logger.log_batch([(original, new)])
        self.assertEqual(self.logger.undo_last_batch(), (0, 1))
        self.assertTrue(original.exists())
        self.assertTrue(new.exists())

    def test_hard_links_in_different_directories_are_preserved(self):
        other = self.root / "other"
        other.mkdir()
        original = other / "show.mp4"
        new = self.root / "Show.mp4"
        new.write_text("episode")
        os.link(new, original)
        self.logger.log_batch([(original, new)])
        self.assertEqual(self.logger.undo_last_batch(), (0, 1))
        self.assertTrue(original.exists())
        self.assertTrue(new.exists())

    def test_corrupt_history_is_never_overwritten(self):
        pair = self.rename("a.mp4")
        for content in ("{broken", "{}", '[{"renames": [{}]}]',
                        '[{"renames": [{"original": 1, "new": "x"}]}]'):
            with self.subTest(content=content):
                self.logger.history_file.write_text(content)
                for operation in (lambda: self.logger.log_batch([pair]),
                                  self.logger.undo_last_batch,
                                  self.logger.has_history):
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(self.logger.history_file.read_text(), content)
                    self.assertTrue(pair[1].exists())

    def test_failed_atomic_replace_preserves_previous_history(self):
        self.logger.log_batch([self.rename("a.mp4")])
        previous = self.logger.history_file.read_bytes()
        with patch("rename_logger.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.logger.log_batch([self.rename("b.mp4")])
        self.assertEqual(self.logger.history_file.read_bytes(), previous)
        self.assertEqual(list(self.root.glob(".rename_history.json.*")), [])


if __name__ == "__main__":
    unittest.main()
