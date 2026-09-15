import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from dual_episode_rename import DualEpisodeTVRenameTool
from multi_season_rename import MultiSeasonTVRenameTool
from name_utils import parse_episode_numbers
from rename_logger import RenameLogger
from rename_operations import execute_plans
from tv_rename import TVRenameTool

REPO = Path(__file__).resolve().parents[1]


class RenameWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def files(self, names, folder=None):
        folder = folder or self.root
        folder.mkdir(parents=True, exist_ok=True)
        for name in names:
            (folder / name).write_bytes(name.encode())
        return folder

    def test_missing_episode_preserved_with_torrent_untouched(self):
        self.files(['S02E08.mp4', 'S02E09.torrent', 'S02E10.mp4'])
        tool = TVRenameTool(str(self.root), '菜鸟老警', 2)
        plan = tool.preview_rename()
        self.assertEqual([name for _, name, _ in plan], ['菜鸟老警_S02E08.mp4', '菜鸟老警_S02E10.mp4'])
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        self.assertEqual(tool.execute_rename(plan), (2, 0))
        self.assertEqual((self.root / '菜鸟老警_S02E10.mp4').read_bytes(), before['S02E10.mp4'])
        self.assertEqual((self.root / 'S02E09.torrent').read_bytes(), before['S02E09.torrent'])
        self.assertEqual(tool.execute_rename(tool.preview_rename()), (0, 0))
        self.assertEqual(len(json.loads((self.root / 'rename_history.json').read_text())), 1)
        self.assertEqual(RenameLogger(str(self.root)).undo_last_batch(), (2, 0))
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_pure_numeric_mixed_with_explicit_markers(self):
        self.files(['菜鸟老警S06E01v2.mp4', '06.mp4', '菜鸟老警S06E07.mp4'])
        plan = TVRenameTool(str(self.root), '菜鸟老警', 6).preview_rename()
        self.assertEqual([episodes for _, _, episodes in plan], [[1], [6], [7]])

    def test_subtitle_language_case_and_delimiter_preserved(self):
        self.files(['Show.S01E01.mp4', 'show_s01e01.chs.eng.srt', 'SHOW.S01E01.en.ass'])
        tool = TVRenameTool(str(self.root), 'Show')
        plan = tool.preview_rename()
        self.assertEqual({name for _, name, _ in plan}, {'Show_S01E01.mp4', 'Show_S01E01.chs.eng.srt', 'Show_S01E01.en.ass'})
        self.assertEqual(tool.execute_rename(plan), (3, 0))

    def test_duplicate_versions_rejected_before_changes(self):
        self.files(['S01E01.mp4', 'S01E01.mkv', 'S01E01.srt'])
        with self.assertRaisesRegex(ValueError, '重复集号'):
            TVRenameTool(str(self.root), 'Show').preview_rename()
        self.assertEqual(len(list(self.root.iterdir())), 3)

    def test_season_mismatch_rejected(self):
        self.files(['S02E01.mp4'])
        with self.assertRaisesRegex(ValueError, '季号'):
            TVRenameTool(str(self.root), 'Show', 1).preview_rename()

    def test_explicit_manual_renumber(self):
        self.files(['S02E08.mp4', 'S02E10.mp4'])
        tool = TVRenameTool(str(self.root), 'Show', 1, start_episode=5, renumber=True)
        paths = list(reversed(tool.get_video_files()))
        plan = tool.preview_rename(paths)
        self.assertEqual([(p.name, ep) for p, _, ep in plan], [('S02E10.mp4', [5]), ('S02E08.mp4', [6])])

    def test_multi_episode_chains_ranges_and_fallback(self):
        folder = self.files(['Show.S01E01E02E03.mp4', 'Show.E07-E09.mp4', 'unlabelled.mp4'], self.root / 'S01')
        tool = DualEpisodeTVRenameTool(str(self.root), 'Show', 3)
        plan = tool.preview_season(1, folder)
        self.assertEqual([ep for _, _, ep in plan], [[1, 2, 3], [7, 8, 9], [10, 11, 12]])
        self.assertEqual(tool.execute_rename({1: plan}), {1: (3, 0)})
        self.assertEqual(tool.execute_rename(tool.preview_all_seasons({1: folder})), {1: (0, 0)})

    def test_multi_episode_pack_numbers_can_be_renumbered(self):
        folder = self.files(['01.mp4', '02.mp4'], self.root / 'S01')
        tool = DualEpisodeTVRenameTool(str(self.root), 'Show', 2, renumber=True)
        self.assertEqual([ep for _, _, ep in tool.preview_season(1, folder)], [[1, 2], [3, 4]])

    def test_named_dual_range_is_not_reassigned(self):
        folder = self.files(['Show.03-04.mp4'], self.root / 'S01')
        plan = DualEpisodeTVRenameTool(str(self.root), 'Show').preview_season(1, folder)
        self.assertEqual(plan[0][1], 'Show_S01E03E04.mp4')

    def test_episode_parser_avoids_codec_year_and_extension(self):
        for filename in ['archive2025.mp4', 'Show.1080p.H264.mp4', 'Show.2023-12-01.mp4']:
            with self.subTest(filename=filename):
                self.assertIsNone(parse_episode_numbers(filename))
        for filename, episodes in [('The.Rookie2018.S01E01.mp4', [1]), ('E01E03.mp4', [1, 3]), ('EP09.mp4', [9]), ('第三十一回.mp4', [31]), ('第3集 第4集.mp4', [3, 4])]:
            with self.subTest(filename=filename):
                self.assertEqual(parse_episode_numbers(filename), episodes)
        for filename in ['S01E10000.mp4', 'E03-E01.mp4', 'E01E01.mp4']:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                parse_episode_numbers(filename)

    def test_season_detection_no_year_or_quality_and_no_duplicate(self):
        for name in ['Season 1', '第2季', '3', '1080p', '2025', 'Extras2024']:
            (self.root / name).mkdir()
        tool = MultiSeasonTVRenameTool(str(self.root), 'Show')
        self.assertEqual(list(tool.detect_season_folders()), [1, 2, 3])
        (self.root / 'S01').mkdir()
        with self.assertRaisesRegex(ValueError, '重复季号'):
            tool.detect_season_folders()

    def test_multi_season_invalid_preview_does_not_silently_skip(self):
        self.files(['S01E01.mp4'], self.root / 'S01')
        self.files(['S03E01.mp4'], self.root / 'S02')
        tool = MultiSeasonTVRenameTool(str(self.root), 'Show')
        with self.assertRaisesRegex(ValueError, '第 2 季'):
            tool.preview_all_seasons(tool.detect_season_folders())

    def test_manual_seasons_use_entered_numbers(self):
        (self.root / 'Part A').mkdir()
        (self.root / 'Part B').mkdir()
        tool = MultiSeasonTVRenameTool(str(self.root), 'Show')
        with patch('builtins.input', side_effect=['all', '3', '5']):
            self.assertEqual(list(tool.manual_select_season_folders()), [3, 5])
        with patch('builtins.input', side_effect=['all', '3', '3']), self.assertRaises(ValueError):
            tool.manual_select_season_folders()

    def test_batch_conflict_preflight_leaves_all_sources(self):
        self.files(['one.mp4', 'two.mp4', 'occupied.mp4'])
        plans = {1: [(self.root / 'one.mp4', 'new.mp4')], 2: [(self.root / 'two.mp4', 'occupied.mp4')]}
        with self.assertRaises(FileExistsError):
            execute_plans(self.root, plans)
        self.assertTrue((self.root / 'one.mp4').exists())
        self.assertFalse((self.root / 'new.mp4').exists())

    def test_plan_rejects_path_escape_duplicate_targets_and_dangling_link(self):
        self.files(['one.mp4', 'two.mp4'])
        for target in ['../escape.mp4', '/escape.mp4', 'bad\\name.mp4']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                execute_plans(self.root, {1: [(self.root / 'one.mp4', target)]})
        with self.assertRaises(ValueError):
            execute_plans(self.root, {1: [(self.root / 'one.mp4', 'new.mp4'), (self.root / 'two.mp4', 'NEW.mp4')]})
        (self.root / 'link.mp4').symlink_to(self.root / 'missing.mp4')
        with self.assertRaises(FileExistsError):
            execute_plans(self.root, {1: [(self.root / 'one.mp4', 'link.mp4')]})

    def test_corrupt_history_prevents_first_rename(self):
        self.files(['one.mp4'])
        (self.root / 'rename_history.json').write_text('{bad')
        with self.assertRaises(ValueError):
            execute_plans(self.root, {1: [(self.root / 'one.mp4', 'new.mp4')]})
        self.assertTrue((self.root / 'one.mp4').exists())

    def test_multi_season_one_log_and_full_undo(self):
        self.files(['S01E01.mp4'], self.root / 'S01')
        self.files(['S02E03.mp4'], self.root / 'S02')
        tool = MultiSeasonTVRenameTool(str(self.root), 'Show')
        plans = tool.preview_all_seasons(tool.detect_season_folders())
        self.assertEqual(tool.execute_all_seasons(plans), {1: (1, 0), 2: (1, 0)})
        self.assertEqual(RenameLogger(str(self.root)).get_last_batch_info()['count'], 2)
        self.assertEqual(RenameLogger(str(self.root)).undo_last_batch(), (2, 0))

    def test_all_cli_previews_run_and_show_actual_mappings(self):
        folder = self.files(['S01E01.mp4'], self.root / 'S01')
        for script, directory in [('tv_rename.py', folder), ('multi_season_rename.py', self.root), ('dual_episode_rename.py', self.root)]:
            with self.subTest(script=script):
                result = subprocess.run([sys.executable, str(REPO / script), '--folder', str(directory), '--show', 'Show', '--preview'], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('-> Show_S01E01', result.stdout)
                self.assertTrue((folder / 'S01E01.mp4').exists())
        result = subprocess.run([sys.executable, str(REPO / 'tv_rename.py'), '--folder', str(folder), '--show', 'Show', '--preview', '--season', '2'], capture_output=True, text=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)



if __name__ == '__main__':
    unittest.main()
