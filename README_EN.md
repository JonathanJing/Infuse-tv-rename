# Infuse TV Rename Tool

Rename TV media to `Show_S01E01.ext`. Supports single seasons, season folders, multi-episode files and matching subtitles. CLI uses the standard library; the optional UI uses Streamlit. Python 3.10+ is recommended.

```bash
python3 tv_rename.py --folder '/path/to/Season 1' --show Friends --season 1 --preview
python3 multi_season_rename.py --folder '/path/to/Friends' --show Friends --preview
python3 dual_episode_rename.py --folder '/path/to/Friends' --show Friends --episodes-per-file 2 --preview
```

Remove `--preview` to execute after CLI confirmation. Existing episode numbers and gaps are preserved by default. Use `--renumber` only to deliberately assign new numbers. The UI also offers an explicit renumber option, start number and manual ordering.

Explicit multi-episode chains are preserved; `E01-E03` becomes `E01E02E03`. A single episode marker plus a configured episodes-per-file count assigns that many episodes starting at the marker. Files without markers use sorted sequential allocation while avoiding occupied numbers; inspect those mappings carefully.

Season folders support `Season 1`, `S01`, `第1季`, and numeric names. Duplicate seasons, overlapping episodes, conflicting targets and mismatched source seasons are rejected. Already-correct names are skipped. Subtitles must share the video stem, with optional language suffixes; for example `Friends.S01E01.1080p.mp4` and `Friends.S01E01.1080p.chs.eng.srt`.

## UI

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

UI/API options include preserving episode titles, source series names, a parenthesized series suffix and using the original filename as the title. See each CLI's `--help` for its supported options.

## Recovery and verification

Successful batches are recorded in `rename_history.json` at the selected root. Use the UI history section or `RenameLogger(root).undo_last_batch()` to restore the last batch. Failed restorations stay in the log for retry; corrupt history is reported rather than overwritten.

Avoid concurrent directory modifications. History is saved after a batch, so forced termination or a failed log write can still require manual recovery. Keep independent backups of important media. Infuse indexing and playback require separate verification.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python example.py
```

The suite includes actual Streamlit AppTest interactions. Install the UI dependencies first; otherwise those tests are skipped. Native directory-dialog responses are mocked in automation.

The standalone MP4-to-MP3 feature, duplicate multi-season example and stale README backup were removed to keep this project focused on TV naming. They remain available in Git history.

See the [Chinese guide](README.md) for architecture and supported formats. [MIT License](LICENSE).
