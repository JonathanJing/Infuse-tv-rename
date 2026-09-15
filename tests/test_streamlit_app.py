"""Exercise real Streamlit widget callbacks, reruns and file operations."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

REPO = Path(__file__).resolve().parents[1]


@unittest.skipIf(AppTest is None, 'Install requirements.txt to test the Streamlit UI')
class StreamlitTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'Demo'
        self.root.mkdir()
        self.app = AppTest.from_file(str(REPO / 'streamlit_app.py'), default_timeout=20).run()
        self.assert_clean()

    def assert_clean(self):
        self.assertFalse(list(self.app.exception))
        self.assertFalse([item.value for item in self.app.error])

    def button(self, label):
        return next(item for item in self.app.button if item.label == label)

    def checkbox(self, label):
        return next(item for item in self.app.checkbox if item.label == label)

    def create_files(self, names, folder=None):
        folder = folder or self.root
        folder.mkdir(exist_ok=True)
        for name in names:
            (folder / name).write_bytes(name.encode())

    def open_folder(self, multi=False):
        if multi:
            self.app.radio[0].set_value('多季模式 (每季一个子文件夹)').run()
        self.app.text_input(key='folder_input').input(str(self.root)).run()
        self.assert_clean()

    def test_auto_name_and_use_extracted_name(self):
        self.create_files(['S01E01.mp4'])
        self.open_folder()
        self.assertEqual(self.app.text_input(key='show_name_input').value, 'Demo')
        self.app.text_input(key='show_name_input').input('Custom').run()
        self.button('🔄 使用提取的剧名').click().run()
        self.assertEqual(self.app.text_input(key='show_name_input').value, 'Demo')
        self.assert_clean()

    def test_browse_callback_updates_widget_before_rerun(self):
        self.create_files(['S01E01.mp4'])
        # Native dialog response is mocked; actual Streamlit callback/rerun is exercised.
        with patch('platform.system', return_value='Darwin'), patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, str(self.root), '')):
            self.button('📂 浏览').click().run()
        self.assertEqual(self.app.text_input(key='folder_input').value, str(self.root))
        self.assertEqual(self.app.text_input(key='show_name_input').value, 'Demo')
        self.assert_clean()

    def test_single_season_preview_rename_and_immediate_undo(self):
        names = ['S01E08.mp4', 'S01E08.chs.eng.srt', 'S01E10.mp4', 'S01E09.torrent']
        self.create_files(names)
        before = {name: (self.root / name).read_bytes() for name in names}
        self.open_folder()
        preview = self.app.dataframe[0].value
        self.assertIn('Demo_S01E10.mp4', list(preview['新文件名']))
        self.button('🔍 仅预览').click().run()
        self.assertEqual(set(p.name for p in self.root.iterdir()), set(names))
        self.button('🔄 执行重命名').click().run()
        self.assert_clean()
        self.assertTrue((self.root / 'Demo_S01E10.mp4').exists())
        self.assertTrue((self.root / 'Demo_S01E08.chs.eng.srt').exists())
        self.assertTrue(any('成功 3' in item.value for item in self.app.success))
        self.button('↩️ 撤销上次重命名').click().run()
        self.assert_clean()
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        self.assertEqual(json.loads((self.root / 'rename_history.json').read_text()), [])

    def test_multi_season_roundtrip(self):
        self.create_files(['S01E01.mp4'], self.root / 'S01')
        self.create_files(['S02E10.mp4'], self.root / 'S02')
        self.open_folder(multi=True)
        self.button('🔄 执行所有重命名').click().run()
        self.assert_clean()
        self.assertTrue((self.root / 'S02' / 'Demo_S02E10.mp4').exists())
        self.button('↩️ 撤销上次重命名').click().run()
        self.assert_clean()
        self.assertTrue((self.root / 'S01' / 'S01E01.mp4').exists())
        self.assertTrue((self.root / 'S02' / 'S02E10.mp4').exists())

    def test_multi_episode_explicit_renumber_roundtrip(self):
        self.create_files(['01.mp4', '02.mp4'], self.root / 'S01')
        self.open_folder(multi=True)
        self.checkbox('🎬 多集模式').set_value(True).run()
        # Ambiguous pack numbers intentionally require explicit renumber.
        self.assertTrue(list(self.app.error))
        self.checkbox('按顺序重新编号').set_value(True).run()
        self.assert_clean()
        self.button('🔄 执行所有重命名').click().run()
        self.assert_clean()
        self.assertTrue((self.root / 'S01' / 'Demo_S01E03E04.mp4').exists())
        self.button('↩️ 撤销上次重命名').click().run()
        self.assert_clean()
        self.assertTrue((self.root / 'S01' / '02.mp4').exists())

    def test_corrupt_history_reports_error_without_mutating_files(self):
        self.create_files(['S01E01.mp4'])
        (self.root / 'rename_history.json').write_text('broken')
        self.app.text_input(key='folder_input').input(str(self.root)).run()
        self.assertTrue(list(self.app.error))
        self.button('🔄 执行重命名').click().run()
        self.assertTrue((self.root / 'S01E01.mp4').exists())
        self.assertEqual((self.root / 'rename_history.json').read_text(), 'broken')

    def test_partial_undo_shows_failure_and_retains_retry(self):
        self.create_files(['S01E01.mp4', 'S01E02.mp4'])
        self.open_folder()
        self.button('🔄 执行重命名').click().run()
        (self.root / 'S01E01.mp4').write_bytes(b'conflict')
        self.button('↩️ 撤销上次重命名').click().run()
        self.assertFalse(list(self.app.exception))
        self.assertTrue(any('恢复完成：成功 1 个文件，失败 1 个文件' == item.value for item in self.app.warning))
        self.assertEqual(len(json.loads((self.root / 'rename_history.json').read_text())[-1]['renames']), 1)
        (self.root / 'S01E01.mp4').unlink()
        self.button('↩️ 撤销上次重命名').click().run()
        self.assert_clean()
        self.assertEqual((self.root / 'S01E01.mp4').read_bytes(), b'S01E01.mp4')


if __name__ == '__main__':
    unittest.main()
