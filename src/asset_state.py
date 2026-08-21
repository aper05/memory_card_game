import pygame
import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, relative_path)


MENU = "MENU"
PLAYING = "PLAYING"
SETTINGS = "SETTINGS"
GAME_OVER = "GAME_OVER"
MODE_SELECT = "MODE_SELECT"
DIFFICULTY = "DIFFICULTY"
BOARD_SELECT = "BOARD_SELECT"
LEVEL_COMPLETE = "LEVEL_COMPLETE"
LEADERBOARD = "LEADERBOARD"

def load_custom_font(size):
    font_path = resource_path(os.path.join("assets", "font_Pix3M_ccby",
        "_bitmap_font____romulus_by_pix3m-d6aokem.ttf"))
    try:
        return pygame.font.Font(font_path, size)
    except (pygame.error, FileNotFoundError):
        print(f"Warning: Could not load custom font at {font_path}, using default.")
        return pygame.font.Font(None, size)


class AssetManager:
    def __init__(self):
        self.images = {}

    def load_image(self, path, size=None):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            self.images[path] = img
            return img
        except pygame.error as e:
            print(f"Could not load image {path}: {e}")
            fallback = pygame.Surface(size or (100, 100))
            fallback.fill((50, 50, 150))
            return fallback


class StateManager:
    def __init__(self, initial_state):
        self.current_state = initial_state
        self.previous_state = None

    def change_state(self, new_state):
        self.previous_state = self.current_state
        self.current_state = new_state
        print(f"State changed: {self.previous_state} -> {new_state}")


class SoundManager:
    """Loads and plays all game sounds and music."""
    def __init__(self):
        music_path = resource_path(os.path.join("assets", "ver0.05", "chong.ogg"))
        self.music_file = music_path

        sound_paths = {
            'flip': resource_path(os.path.join("assets", "ver0.05", "flip.wav")),
            'button': resource_path(os.path.join("assets", "Chunky UI Sounds Demo", "Chunky UI Sounds Demo", "Tiny Mechanical Switch On.ogg")),
            'match': resource_path(os.path.join("assets", "Chunky UI Sounds Demo", "Chunky UI Sounds Demo", "Digital Glass Success 2.ogg")),
            'mismatch': resource_path(os.path.join("assets", "Chunky UI Sounds Demo", "Chunky UI Sounds Demo", "Mechanical Switch Toggle 1.ogg")),
            'shuffle': resource_path(os.path.join("assets", "ver0.05", "shuffling.wav")),
        }

        self.sounds = {}
        for name, path in sound_paths.items():
            try:
                sound = pygame.mixer.Sound(path)
                self.sounds[name] = sound
                print(f"Loaded sound: {path}")
            except Exception as e:
                print(f"WARNING: Could not load sound {path} → {e}")
                self.sounds[name] = None

        self.volume = 1.0

    def set_volume(self, volume_percent):
        self.volume = volume_percent / 100.0
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)
        pygame.mixer.music.set_volume(self.volume)

    def play_music(self):
        try:
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"WARNING: Could not play music {self.music_file} → {e}")

    def play_flip(self):
        if self.sounds.get('flip'):
            self.sounds['flip'].play()

    def play_button(self):
        if self.sounds.get('button'):
            self.sounds['button'].play()

    def play_match(self):
        if self.sounds.get('match'):
            self.sounds['match'].play()

    def play_mismatch(self):
        if self.sounds.get('mismatch'):
            self.sounds['mismatch'].play()

    def play_shuffle(self):
        if self.sounds.get('shuffle'):
            self.sounds['shuffle'].play()


# Global placeholder – will be replaced in main.py after mixer.init()
sound_manager = None