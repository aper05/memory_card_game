# Memory Card Game

A feature-rich memory card matching game built with Python and Pygame, playable on **Windows**, **macOS**, and **Linux**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.5+-green?logo=pygame&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## Table of Contents

- [Game Overview](#game-overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Game Modes](#game-modes)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [How to Play](#how-to-play)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Building from Source](#building-from-source)
- [Store Publishing Guide](#store-publishing-guide)
- [Credits and Licenses](#credits-and-licenses)
- [Version History](#version-history)
- [Author](#author)

---

## Game Overview

Memory Card Game is a classic card-matching puzzle where players flip cards to find matching pairs. Built entirely in Python using the Pygame library, it features polished visuals, smooth animations, multiple game modes, and an AI opponent.

**Repository:** `https://github.com/aper05/memory_card_game.git`

---

## Features

### Core Gameplay
- **Card Matching Mechanic** - Flip two cards at a time; matching pairs disappear with animation, non-matching pairs flip back after 1 second
- **15 Card Faces** - Ace through King (spades suit), plus red and black jokers
- **Dynamic Board Layout** - Cards arranged in auto-calculated grids centered on screen with configurable gaps
- **Smart Card Sizing** - Auto-calculated card dimensions with min/max bounds (80-110px wide, 100-140px tall)

### 5 Game Modes
| Mode | Description |
|------|-------------|
| **1 Player** | Classic single-player against the clock with streak multipliers |
| **2 Player** | Two human players take turns; matching gives another turn |
| **VS AI** | Compete against an AI opponent with 3 difficulty levels |
| **Level Mode** | 3 progressive levels with star ratings |
| **Zen** | No timer, no pressure - match at your own pace |

### AI Opponent System
- **Memory-based AI** - Maintains rolling memory of recently seen cards (2/4/8 entries by difficulty)
- **Smartness Factor** - 0.4/0.6/0.9 probability to use memory vs. random picks
- **Turn-based State Machine** - AI takes timed turns with animated card flips

### Scoring and Timer
- **Streak Multiplier** - Score = 5 x streak per consecutive match (displayed on HUD)
- **Star Rating** - 1-3 stars based on move efficiency vs. par
- **Countdown Timer** - 60s/90s/120s depending on board size (absent in Zen mode)
- **Timer Warning** - Turns red when 15 seconds remain

### Hint System
- **3 Hints Per Game** - Each reveals a matching pair
- **Visual Feedback** - Pulsing yellow highlight animation on hinted cards

### Animations
- **Card Flip** - 3D-style horizontal scale animation (0.2s)
- **Card Appear** - Staggered fade-in on board setup
- **Card Disappear** - Scale-down on match (0.25s)
- **Shuffle Animation** - Cards converge to center, wobble, then spread with smoothstep easing (1.5s)
- **Button Press** - Scale to 85% with white flash, spring back
- **Overlay Fade-in** - Settings and game-over screens fade in (0.4s)

### Visual Effects
- **Particle System** - Floating twinkling stars with glow
- **Gradient Backgrounds** - Radial gradients with smoothstep transitions
- **Decorative Elements** - Card suit symbols (menu), geometric diamonds (gameplay)
- **HUD Panel** - Semi-transparent panel behind score/timer/moves

### Sound
- **6 Sound Effects** - Card flip, button press, match, mismatch, shuffle
- **Background Music** - Looping chiptune track
- **Volume Control** - Master slider (0-100%)

### UI/UX
- **8-Screen Flow** - Menu, Mode Select, Difficulty, Board Size, Settings, How to Play, Level Complete, Leaderboard
- **In-game Overlay** - Settings accessible via button or ESC/back button
- **HUD** - Timer, score, moves, streak, pairs left, hints, settings
- **Leaderboard** - Top 10 scores per category with persistent storage
- **How to Play** - Detailed tutorial for all 5 game modes
- **Responsive Design** - 1280x720 virtual resolution with aspect-ratio-preserving scaling
- **Custom Font** - Pix3M Romulus bitmap pixel font

---

## System Requirements

### PC (Windows / macOS / Linux)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 7+, macOS 10.13+, Ubuntu 18.04+ | Windows 10+, macOS 12+, Ubuntu 22.04+ |
| **Processor** | 1 GHz | 2 GHz dual-core |
| **Memory** | 256 MB RAM | 512 MB RAM |
| **Storage** | 100 MB available space | 200 MB available space |
| **Graphics** | OpenGL 2.0 compatible | OpenGL 3.0+ |
| **Display** | 800x600 | 1280x720 or higher |
| **Sound** | Any | Any |

---

## Installation

### Pre-built Releases

#### Windows
1. Download `MemoryCardGame-Windows.zip` from [Releases](https://github.com/aper05/memory_card_game/releases)
2. Extract the ZIP file
3. Run `MemoryCardGame.exe`

#### macOS
1. Download `MemoryCardGame-macOS.zip` from [Releases](https://github.com/aper05/memory_card_game/releases)
2. Extract the ZIP file
3. Right-click `MemoryCardGame.app` > Open

#### Linux
1. Download `MemoryCardGame-Linux.zip` from [Releases](https://github.com/aper05/memory_card_game/releases)
2. Extract the ZIP file
3. Make executable: `chmod +x MemoryCardGame`
4. Run: `./MemoryCardGame`

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/aper05/memory_card_game.git
cd memory_card_game

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

---

## How to Play

### Basic Rules
1. Cards are placed face-down on the board
2. Tap/click a card to flip it face-up
3. Flip a second card to try to find a match
4. If the two cards match, they disappear and you score points
5. If they don't match, they flip back face-down after 1 second
6. Match all pairs to win the game

### Controls

| Platform | Action | Input |
|----------|--------|-------|
| PC | Flip card | Left click |
| PC | Open settings | ESC key or settings button |
| PC | Navigate menus | Left click |

### Scoring
- **Base Points** - 5 points per match
- **Streak Bonus** - Consecutive matches multiply points (streak x 5)
- **Star Rating** - Based on total moves vs. par:
  - 3 stars: moves <= par
  - 2 stars: moves <= 2x par
  - 1 star: otherwise

### Difficulty Settings

| Difficulty | Board Size | Pairs | Time Limit |
|------------|-----------|-------|------------|
| Easy | 4x3 | 6 | 60 seconds |
| Medium | 4x4 | 8 | 90 seconds |
| Hard | 5x6 | 15 | 120 seconds |

### AI Difficulty (VS AI Mode)

| Level | Memory Size | Smartness | Description |
|-------|-------------|-----------|-------------|
| Easy | 2 cards | 40% | Mostly random picks |
| Medium | 4 cards | 60% | Remembers some cards |
| Hard | 8 cards | 90% | Remembers most cards |

---

## Technology Stack

### Languages and Frameworks
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core programming language |
| Pygame / pygame-ce | 2.5+ | Game engine, rendering, audio |
| PyInstaller | 6.0+ | Desktop executable packaging |

### Development Tools
| Tool | Purpose |
|------|---------|
| GitHub Actions | CI/CD for automated builds |
| Git | Version control |
| Visual Studio Code | IDE |

### Assets
| Asset | Source | License |
|-------|--------|---------|
| Card Images | Kenney Playing Cards Pack | CC-BY 4.0 |
| Font | Pix3M Romulus Bitmap Font | CC-BY |
| Sound Effects | Chunky UI Sounds Demo | Free for commercial use |
| Background Music | chong.ogg | Free for commercial use |

---

## Project Architecture

### Source Files (2,830 lines of code)

```
memory_card_game/
├── main.py              # Entry point, main loop, event dispatch (175 lines)
├── game.py              # Core game logic, Card/Board/Game classes (1,025 lines)
├── ui_controls.py       # All UI screens, Button/Slider widgets (889 lines)
├── asset_state.py       # StateManager, AssetManager, SoundManager (124 lines)
├── backgrounds.py       # Particle system, gradient backgrounds (215 lines)
├── physics_collision.py # Hit-testing, animation math (90 lines)
├── highscores.py        # JSON-based score persistence (80 lines)
├── ai_logic.py          # AI opponent logic (87 lines)
├── build.py             # Cross-platform build script (145 lines)
├── build.bat            # Windows one-click build
├── requirements.txt     # Python dependencies
├── MemoryCardGame.spec  # PyInstaller configuration
├── assets/              # Game assets (24 files)
│   ├── font_Pix3M_ccby/
│   ├── kenney_playing-cards-pack/
│   ├── Chunky UI Sounds Demo/
│   └── ver0.05/
└── .github/workflows/
    └── build.yml        # CI/CD pipeline (Windows, macOS, Linux)
```

### Design Patterns

- **State Machine** - `StateManager` manages 8 game states with previous-state tracking
- **Virtual Resolution** - 1280x720 rendering scaled to any window/screen size
- **Event-driven Architecture** - All input handled through scaled event dispatch
- **Separated Concerns** - Clean module separation (logic, UI, AI, assets, physics)
- **Global Sound Manager** - Singleton pattern for audio playback
- **Image Caching** - Card images cached to prevent redundant loading
- **Graceful Degradation** - Missing assets produce fallback surfaces/colors, not crashes

### Module Dependency Graph

```
main.py
├── asset_state.py (StateManager, SoundManager, AssetManager)
├── ui_controls.py (All menu screens)
├── game.py (Game class)
│   ├── asset_state.py
│   ├── physics_collision.py (Card hit-testing, animations)
│   ├── backgrounds.py (Gameplay background)
│   ├── ai_logic.py (AI opponent)
│   └── highscores.py (Score persistence)
└── backgrounds.py (Menu background)
```

---

## Building from Source

### Desktop (Windows / macOS / Linux)

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
python build.py

# Build and run
python build.py --run

# Clean build artifacts
python build.py --clean
```

Output: `dist/MemoryCardGame/`

### CI/CD

The project includes GitHub Actions workflows that automatically build for:

| Platform | Trigger | Output |
|----------|---------|--------|
| **PC** | Push to main/master | Windows .exe, macOS .app, Linux binary |

Build artifacts are available as downloadable ZIP files on the Actions page.

---

## Store Publishing Guide

### Steam

#### Requirements
- **Steamworks Developer Account** - $100 fee per game
- **Store Page** - Description, screenshots, trailers, capsule art
- **Build** - Windows, macOS, Linux executables
- **Steam Deck Compatibility** - Optional but recommended

#### Art Assets Needed
| Asset | Size | Purpose |
|-------|------|---------|
| Header Capsule | 460x215 | Store page header |
| Small Capsule | 231x87 | Search results |
| Large Capsule | 616x353 | Store page |
| Library Hero | 1920x620 | Library background |
| Library Logo | 128x128 | Library icon |
| Icon | 128x128 | Taskbar/desktop |
| Screenshots | 1920x1080 min | Store page (at least 5) |

#### Store Listing
```
Title: Memory Card Game
Genre: Casual, Puzzle
Tags: Memory, Puzzle, Card Game, Singleplayer, Multiplayer
Description: [Full game description]
Short Description: Classic card matching with 5 modes, AI opponent, and 2-player support
```

#### Steps
1. Create Steamworks account and pay $100 fee
2. Build executables for Windows, macOS, Linux
3. Upload builds via SteamPipe
4. Create store page with descriptions, screenshots, capsule art
5. Set pricing and release date
6. Submit for Valve review
7. Release

---

### Epic Games Store

#### Requirements
- **Epic Games Developer Account** - Application-based (submit game for review)
- **Build** - Windows executable (primary platform)
- **Store Page** - Description, screenshots, trailers
- **Marketing Materials** - Capsule art, key art, screenshots

#### Art Assets Needed
| Asset | Size | Purpose |
|-------|------|---------|
| Key Art | 3840x2160 | Marketing banner |
| Capsule Art | 256x256 | Store listing |
| Screenshots | 1920x1080 min | Store page (at least 3) |

#### Steps
1. Apply at [Epic Games Developer Portal](https://store.epicgames.com/en-US/publish/)
2. Wait for approval (can take weeks/months)
3. Build Windows executable
4. Upload builds and assets
5. Configure store page and pricing
6. Submit for review
7. Release

---

### itch.io (Indie / Web)

#### Requirements
- Free account (no fees)
- Upload builds for any platform
- Optional: HTML5/web build for browser play

#### Steps
1. Create project at [itch.io](https://itch.io)
2. Upload builds (Windows, macOS, Linux)
3. Add description, screenshots, cover image
4. Set pricing (free or paid)
5. Publish immediately (no review process)

---

### Metadata for All Stores

#### Game Description (Long)
```
Memory Card Game is a classic card-matching puzzle that challenges your 
memory and reflexes. With 5 unique game modes, an intelligent AI opponent, 
and beautiful pixel-art visuals, it offers endless entertainment for players 
of all ages.

Choose from 1 Player, 2 Player, VS AI, Level Mode, or Zen mode. Test your 
memory with 3 difficulty levels and track your progress on the leaderboard. 
Earn stars, build streaks, and master the art of memory!

Features beautiful animations, satisfying sound effects, and a charming 
retro aesthetic. Whether you have 5 minutes or an hour, Memory Card Game 
is the perfect pick-up-and-play experience.
```

#### Game Description (Short)
```
Classic card matching puzzle with 5 game modes, AI opponent, streak 
multipliers, and beautiful pixel-art animations. Play solo, with friends, 
or challenge the AI!
```

#### Keywords
```
memory, cards, matching, puzzle, brain, memory game, card game, 
matching game, concentration, recall, memory training, brain training, 
retro, pixel art, casual, family, kids, singleplayer, multiplayer
```

---

## Credits and Licenses

### Developed By
- **aper05** - Game design, programming, and development

### Third-Party Assets

| Asset | Author | License | Source |
|-------|--------|---------|--------|
| Playing Card Images | Kenney | CC-BY 4.0 | [kenney.nl](https://kenney.nl/assets/playing-cards) |
| Bitmap Font (Romulus) | Pix3M | CC-BY | [pix3m on DeviantArt](https://www.deviantart.com/pix3m) |
| UI Sound Effects | Kenney | CC0 (Public Domain) | [kenney.nl](https://kenney.nl/assets/ui-sounds) |
| Background Music | - | Free for use | Included in ver0.05 assets |

### Technologies
- **Python** - Python Software Foundation (PSF License)
- **Pygame** - Pete Shinners, pygame community (LGPL)
- **pygame-ce** - Community Edition (LGPL)
- **PyInstaller** - Hartmut Goebel, contributors (Apache 2.0)

### License
This project is released under the **MIT License**.
Third-party assets retain their original licenses (see Credits).

---

## Version History

### v1.0.0 (Current)
- Initial release
- 5 game modes (1 Player, 2 Player, VS AI, Level, Zen)
- 3 difficulty levels with configurable board sizes
- AI opponent with memory-based intelligence
- Streak multiplier scoring system
- Star rating for level completion
- Hint system (3 per game)
- Persistent leaderboard with top 10 per category
- Full animation system (flip, appear, disappear, shuffle)
- Particle effects and gradient backgrounds
- Sound effects and background music
- Cross-platform builds (Windows, macOS, Linux)
- CI/CD with GitHub Actions

### v0.1.0 (Development)
- Core card matching mechanic
- Basic UI and menu system
- PyInstaller packaging

---

## Author

**aper05**
- GitHub: [github.com/aper05](https://github.com/aper05)
- Project: [memory_card_game](https://github.com/aper05/memory_card_game)

---

## Support

For bug reports and feature requests, please use the [GitHub Issues](https://github.com/aper05/memory_card_game/issues) page.
