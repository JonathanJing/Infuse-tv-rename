# Infuse TV Series Smart Renaming Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-green.svg)]()

An intelligent TV series renaming tool specifically designed for Infuse media library, supporting single season, multi-season, and multi-episode file batch renaming with both command-line and graphical interfaces.

## ✨ Key Features

### 🎯 Core Functionality
- **Smart Renaming**: Rename files to Infuse standard format `ShowName_S01E01.ext`
- **Multiple Modes**: Support single season, multi-season, multi-episode (like `S01E01E02`) renaming
- **Intelligent Subtitle Handling**: Automatically match subtitle files with same basename, preserve language identifiers (zh/en/chs.eng, etc.)
- **Smart Series Name Extraction**: Automatically extract and preserve series names from original filenames, support parentheses suffix
- **Episode Title Preservation**: Optionally preserve episode titles from original filenames
- **Preview Mode**: Preview results before renaming to ensure accuracy

### 🛡️ Safety Features
- **File Protection**: Automatically skip when target file exists to avoid overwriting
- **Preview Confirmation**: Support preview mode to check results before renaming
- **Extension Preservation**: Fully preserve original file extensions and subtitle language identifiers

### 📁 Folder Structure Support
Automatically recognize various season folder naming formats:
- English formats: `Season 1`, `Season1`, `S01`, `season1`
- Chinese formats: `第1季`, `第2季`
- Numeric formats: `1`, `2`, `3`

## 🏗️ Project Architecture

```
infuse-tv-rename/
├── tv_rename.py              # Single season renaming core module
├── multi_season_rename.py    # Multi-season renaming module
├── dual_episode_rename.py    # Multi-episode file renaming module
├── name_utils.py             # Smart series name extraction tool
├── streamlit_app.py          # Graphical interface
├── example.py                # Usage examples
├── multi_season_example.py   # Multi-season usage examples
├── requirements.txt          # Python dependencies
├── install.sh               # Installation script
├── MULTI_SEASON_GUIDE.md    # Multi-season usage guide
└── README.md                # Project documentation
```

### Core Components

#### 1. TVRenameTool Class (`tv_rename.py`)
- **Function**: Single season renaming processing
- **Features**: Smart episode title extraction, subtitle file matching, multi-episode support
- **Output Format**: `ShowName_S01E01.ext` or `ShowName_S01E01E02.ext`

#### 2. MultiSeasonTVRenameTool Class (`multi_season_rename.py`)  
- **Function**: Multi-season batch renaming
- **Features**: Automatic season folder detection, manual selection mode
- **Supported Formats**: Recognize various season folder naming conventions

#### 3. DualEpisodeTVRenameTool Class (`dual_episode_rename.py`)
- **Function**: Multi-episode file renaming (each file contains multiple episodes)
- **Features**: Smart episode number parsing, support 2-3 combined episode files
- **Output Format**: `ShowName_S01E01E02.ext`

#### 4. Series Name Extraction Tool (`name_utils.py`)
- **Function**: Intelligently extract clean series names from filenames
- **Algorithm**: Remove quality markers, codec info, season/episode markers and other noise
- **Preserve Style**: Maintain original naming style as much as possible

## 🚀 Quick Start

### Requirements
- Python 3.7+
- Operating System: Windows / macOS / Linux

### Installation

```bash
# Clone the project
git clone https://github.com/yourusername/infuse-tv-rename.git
cd infuse-tv-rename

# Install dependencies
pip install -r requirements.txt

# Or use the installation script
chmod +x install.sh
./install.sh
```

### Basic Usage

#### 1. Single Season Renaming
```bash
# Basic usage
python3 tv_rename.py --folder "/path/to/season1" --show "Friends" --season 1

# Preview mode
python3 tv_rename.py --folder "/path/to/season1" --show "Friends" --season 1 --preview
```

#### 2. Multi-Season Batch Renaming
```bash
# Automatic season folder detection
python3 multi_season_rename.py --folder "/path/to/Friends" --show "Friends"

# Manual season folder selection
python3 multi_season_rename.py --folder "/path/to/Friends" --show "Friends" --manual
```

#### 3. Multi-Episode File Renaming
```bash
# Each file contains 2 episodes
python3 dual_episode_rename.py --folder "/path/to/Friends" --show "Friends"

# Preview mode
python3 dual_episode_rename.py --folder "/path/to/Friends" --show "Friends" --preview
```

### Graphical Interface

Launch Streamlit Web interface:
```bash
streamlit run streamlit_app.py
```

**Interface Features:**
- 🖱️ Native folder selection dialog
- 🧠 Smart series name extraction
- ⚙️ Advanced options configuration (preserve episode titles, series name parentheses suffix, etc.)
- 📊 Real-time preview and progress display

## 📖 Usage Examples

### File Structure Example

**Before Renaming:**
```
Friends/
├── Season 1/
│   ├── friends.s01e01.720p.mkv
│   ├── friends.s01e01.chs.srt
│   ├── friends.s01e02.720p.mkv
│   └── friends.s01e02.chs.srt
└── Season 2/
    ├── S02E01 - The One With Ross's New Girlfriend.mp4
    └── S02E01 - The One With Ross's New Girlfriend.zh.srt
```

**After Renaming:**
```
Friends/
├── Season 1/
│   ├── Friends_S01E01.mkv
│   ├── Friends_S01E01.chs.srt
│   ├── Friends_S01E02.mkv
│   └── Friends_S01E02.chs.srt
└── Season 2/
    ├── Friends_S02E01.mp4
    └── Friends_S02E01.zh.srt
```

### Advanced Feature Examples

**Preserve Episode Title:**
```
Input:  ShowName.S01E01.The.Pilot.1080p.mkv
Output: ShowName_S01E01_The Pilot.mkv
```

**Series Name Parentheses Suffix:**
```
Set suffix: 1994
Output: Friends (1994)_S01E01.mkv
```

**Multi-Episode File:**
```
Input:  Show.E01E02.Dual.Episode.mkv  
Output: Show_S01E01E02.mkv
```

## 🎯 Supported File Formats

### Video Formats
`.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm` `.rmvb` `.rm` `.m4v` `.3gp` `.ogv`

### Subtitle Formats
`.srt` `.ass` `.ssa` `.sub`

### Subtitle Language Recognition
Supports automatic recognition and preservation of the following language identifiers:
- Chinese: `zh` `chs` `cht` `chi` `sc` `tc`
- English: `en` `eng`
- Others: `ja` `ko` `es` `fr` `de` `ru` `it` `pt` `pt-br`

## 🔧 Command Line Arguments

### tv_rename.py (Single Season)
| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--folder` | `-f` | TV series folder path | ✅ |
| `--show` | `-s` | Series name | ✅ |
| `--season` | `-n` | Season number (default: 1) | ❌ |
| `--preview` | `-p` | Preview only, don't execute renaming | ❌ |

### multi_season_rename.py (Multi-Season)
| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--folder` | `-f` | Root directory path | ✅ |
| `--show` | `-s` | Series name | ✅ |
| `--manual` | `-m` | Manually select season folders | ❌ |
| `--preview` | `-p` | Preview only, don't execute renaming | ❌ |

### dual_episode_rename.py (Multi-Episode)
| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--folder` | `-f` | Root directory path | ✅ |
| `--show` | `-s` | Series name | ✅ |
| `--preview` | `-p` | Preview only, don't execute renaming | ❌ |

## 🧠 Smart Algorithms

### 1. Subtitle Matching Algorithm
- **Normalized Matching**: Ignore case and delimiter differences
- **Language Suffix Preservation**: Intelligently recognize and preserve subtitle language identifiers
- **Multi-Language Support**: Support multi-language subtitles like `.chs.eng`

### 2. Series Name Extraction Algorithm
- **Noise Filtering**: Remove quality markers (720p, 1080p, etc.)
- **Codec Cleaning**: Remove codec information (x264, HEVC, etc.)
- **Structure Analysis**: Extract series name portion before season/episode markers
- **Smart Preservation**: Maintain original naming style and language characteristics

### 3. Season Folder Recognition
- **Pattern Matching**: Support English, Chinese, numeric and other formats
- **Smart Sorting**: Sort correctly by season numbers
- **Manual Fallback**: Provide manual selection when automatic detection fails

## 💡 Best Practices

### 1. Usage Recommendations
- **Backup Important Files**: Recommend backing up before renaming
- **Use Preview Mode First**: Use `--preview` parameter to check results
- **Check File Order**: Ensure original filename order is correct
- **Verify Season Folders**: Check folder structure in multi-season mode

### 2. File Organization
```
Recommended folder structure:
TV_Shows/
├── Friends/
│   ├── Season 1/
│   ├── Season 2/
│   └── Season 3/
└── Breaking_Bad/
    ├── Season 1/
    ├── Season 2/
    └── Season 3/
```

### 3. Naming Conventions
- Original filenames should preferably contain season/episode info
- Subtitle files should have same basename as video files
- Avoid special characters and overly long paths

## 🔍 Troubleshooting

### Common Issues

**Q: What if automatic season folder detection fails?**
A: Use `--manual` parameter for manual selection, or rename folders to standard formats

**Q: Subtitle files are not renamed correctly?**
A: Ensure subtitle files have consistent base names with video files (ignoring language suffixes)

**Q: Renaming fails with file in use error?**
A: Close programs using the file (like players, editors)

**Q: How to undo renaming operations?**
A: The tool doesn't provide undo functionality, recommend backing up files before renaming

### Error Codes
- **FileNotFoundError**: Folder path doesn't exist
- **NotADirectoryError**: Path is not a valid folder
- **PermissionError**: Insufficient file operation permissions
- **ValueError**: Invalid parameter values

## 🤝 Contributing

Issues and Pull Requests are welcome!

### Development Environment
```bash
git clone https://github.com/yourusername/infuse-tv-rename.git
cd infuse-tv-rename
pip install -r requirements.txt
```

### Code Standards
- Follow PEP 8 coding style
- Add appropriate docstrings
- Write unit tests
- Test all functionality before committing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Thanks to all developers and users who contributed to this project!

---

**For questions or suggestions, please submit an Issue or contact the author**

**⭐ If this project helps you, please give it a Star!**