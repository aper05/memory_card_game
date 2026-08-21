import json
import os
import sys
import platform
from datetime import datetime


def _get_user_data_dir():
    """Get a user-writable directory for storing high scores.
    Works in both development and PyInstaller-packaged builds."""
    app_name = "MemoryCardGame"

    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, app_name)
    elif platform.system() == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
    else:  # Linux / other
        xdg = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
        return os.path.join(xdg, app_name)


def _get_scores_file():
    """Return path to the scores JSON file."""
    if hasattr(sys, '_MEIPASS'):
        # Packaged build: write to user data directory
        data_dir = _get_user_data_dir()
    else:
        # Development: write next to this script
        data_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "highscores.json")


SCORES_FILE = _get_scores_file()


def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_scores(scores):
    os.makedirs(os.path.dirname(SCORES_FILE), exist_ok=True)
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=2)


def save_score(mode, board_size, score, moves, time_elapsed, stars=None):
    scores = load_scores()
    key = f"{mode}_{board_size}"
    if key not in scores:
        scores[key] = []

    entry = {
        'score': score,
        'moves': moves,
        'time': round(time_elapsed, 1),
        'stars': stars,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    scores[key].append(entry)

    scores[key].sort(key=lambda x: (-x.get('score', 0), x.get('moves', 9999), x.get('time', 9999)))
    scores[key] = scores[key][:10]

    save_scores(scores)
    return entry


def get_top_scores(mode, board_size, limit=10):
    scores = load_scores()
    key = f"{mode}_{board_size}"
    return scores.get(key, [])[:limit]
