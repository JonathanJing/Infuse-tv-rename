import tempfile
import unittest
from pathlib import Path

from name_utils import extract_date_from_filename, parse_episode_numbers
from tv_rename import TVRenameTool


class EpisodeParserRegressionTests(unittest.TestCase):
    def test_numeric_episode_with_quality_suffix(self):
        for filename, expected in [('03-4K.mp4', [3]), ('12.1080P.mkv', [12]), ('Show.4K.mp4', None)]:
            with self.subTest(filename=filename):
                self.assertEqual(parse_episode_numbers(filename), expected)

    def test_range_endpoints_are_not_silently_discarded(self):
        for filename, expected in [
            ('Show.S01E03-04.mp4', [3, 4]),
            ('Show.S01E03–E05.mp4', [3, 4, 5]),
            ('Show.E03—05.mp4', [3, 4, 5]),
            ('Show.E03-E05.mp4', [3, 4, 5]),
            ('Show.E03E05.mp4', [3, 5]),
            ('Show.E03-E04-E05.mp4', [3, 4, 5]),
            ('Show.S01E03-1080p.mp4', [3]),
        ]:
            with self.subTest(filename=filename):
                self.assertEqual(parse_episode_numbers(filename), expected)

    def test_invalid_ranges_fail_instead_of_returning_partial_numbers(self):
        for filename in [
            'Show.E05-03.mp4', 'Show.E03--E05.mp4',
            'Show.E03-E.mp4', 'Show.E03-05-07.mp4',
            'Show.E03-10000.mp4', 'Show.E03-05E07.mp4',
        ]:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                parse_episode_numbers(filename)

    def test_mixed_separator_dates_are_not_episode_ranges(self):
        for date in ['2026.09-14', '2026 09-14', '2026_09-14', '2026-09-14', '20260914']:
            with self.subTest(date=date):
                filename = f'Show.{date}.mp4'
                self.assertEqual(extract_date_from_filename(filename), '2026-09-14')
                self.assertIsNone(parse_episode_numbers(filename))
                self.assertEqual(parse_episode_numbers(f'Show.{date}.03-04.mp4'), [3, 4])
                self.assertEqual(parse_episode_numbers(f'Show.{date}.S01E07.mp4'), [7])

    def test_standard_naming_keeps_complete_range(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'Show.S01E03-04.mp4'
            source.touch()
            plan = TVRenameTool(directory, 'Show').preview_rename()
            self.assertEqual(plan, [(source, 'Show_S01E03E04.mp4', [3, 4])])


if __name__ == '__main__':
    unittest.main()
