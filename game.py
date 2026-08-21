import pygame
import random
import os
import time
from ai_logic import AIPlayer
from ui_controls import Slider
import asset_state
from asset_state import resource_path
from physics_collision import get_card_under_mouse, flip_scale, appear_scale, disappear_scale, shuffle_scale, shuffle_positions
from backgrounds import create_gameplay_background, draw_hud_background

CARD_FACES = [
    'A', '2', '3', '4', '5', '6', '7', '8', '9', '10',
    'J', 'Q', 'K', 'red_joker', 'black_joker'
]

TIMER_BY_SIZE = {
    6: 60,
    8: 90,
    15: 120,
}


_card_image_cache = {}


def get_face_filename(face_id):
    if face_id == 'red_joker':
        return 'card_joker_red'
    elif face_id == 'black_joker':
        return 'card_joker_black'
    elif face_id in ['A', 'J', 'Q', 'K']:
        return f'card_spades_{face_id}'
    elif face_id == '10':
        return 'card_spades_10'
    else:
        return f'card_spades_0{face_id}'


class Card:
    def __init__(self, face_id, x, y, width, height, appear_delay=0):
        self.face_id = face_id
        self.rect = pygame.Rect(x, y, width, height)
        self.is_flipped = False
        self.is_matched = False

        self.flipping = False
        self.flip_start = 0.0
        self.flip_duration = 0.2
        self.flip_target = False

        self.appear_start = time.time() + appear_delay
        self.appear_duration = 0.3
        self.appear_progress = 0.0

        self.disappearing = False
        self.disappear_start = 0.0
        self.disappear_duration = 0.25

        self.hint_highlight = False
        self.hint_start = 0.0
        self.hint_duration = 0.8

    def flip(self):
        if not self.is_matched and not self.flipping:
            self.flip_target = not self.is_flipped
            self.flipping = True
            self.flip_start = time.time()
            self.is_flipped = self.flip_target

    def update(self):
        now = time.time()

        if self.flipping:
            if now - self.flip_start >= self.flip_duration:
                self.flipping = False

        if self.appear_progress < 1.0:
            elapsed = now - self.appear_start
            if elapsed >= 0:
                self.appear_progress = min(1.0, elapsed / self.appear_duration)

        if self.disappearing:
            elapsed = now - self.disappear_start
            if elapsed >= self.disappear_duration:
                self.is_matched = True
                self.disappearing = False

        if self.hint_highlight:
            if now - self.hint_start >= self.hint_duration:
                self.hint_highlight = False
                if self.is_flipped and not self.is_matched:
                    self.flip()

    def draw(self, surface, card_back_img, card_front_imgs):
        if self.is_matched:
            return

        if self.is_flipped:
            img = card_front_imgs.get(self.face_id)
            if img is None:
                img = pygame.Surface(self.rect.size)
                img.fill((255, 255, 255))
        else:
            img = card_back_img
            if img is None:
                img = pygame.Surface(self.rect.size)
                img.fill((0, 0, 150))

        scale_x = 1.0
        scale_y = 1.0

        if self.flipping:
            elapsed = time.time() - self.flip_start
            scale_x = flip_scale(elapsed, self.flip_duration)

        if self.appear_progress < 1.0:
            appear = appear_scale(time.time() - self.appear_start, self.appear_duration)
            scale_x *= appear
            scale_y *= appear

        if self.disappearing:
            dis = disappear_scale(time.time() - self.disappear_start, self.disappear_duration)
            scale_x *= dis
            scale_y *= dis

        if scale_x <= 0 or scale_y <= 0:
            return

        w = max(1, int(self.rect.width * scale_x))
        h = max(1, int(self.rect.height * scale_y))
        scaled_img = pygame.transform.scale(img, (w, h))
        dest_rect = scaled_img.get_rect(center=self.rect.center)
        surface.blit(scaled_img, dest_rect.topleft)

        if self.hint_highlight:
            now = time.time()
            pulse = abs((now - self.hint_start) * 4 % 2 - 1)
            highlight_color = (255, 255, 0, int(80 + 80 * pulse))
            highlight = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            highlight.fill(highlight_color)
            surface.blit(highlight, self.rect.topleft)


class Board:
    def __init__(self, virtual_size, num_pairs=15, cards_per_row=6, gap=10):
        self.virtual_width, self.virtual_height = virtual_size
        self.num_pairs = num_pairs
        self.cards_per_row = cards_per_row
        self.gap = gap
        self.cards = []
        self.selected = []
        self.lock = False
        self.anim_type = None
        self.anim_start_time = None
        self.anim_pair = []
        self.need_turn_switch = False
        self.mismatch_sound_played = False

        MAX_CARD_WIDTH = 110
        MAX_CARD_HEIGHT = 140

        total_cards = num_pairs * 2
        total_rows = (total_cards + self.cards_per_row - 1) // self.cards_per_row
        avail_width = self.virtual_width - 2 * 20
        avail_height = self.virtual_height - 2 * 20
        raw_card_width = (avail_width - (self.cards_per_row - 1) * gap) // self.cards_per_row
        raw_card_height = (avail_height - (total_rows - 1) * gap) // total_rows

        self.card_width = min(raw_card_width, MAX_CARD_WIDTH)
        self.card_height = min(raw_card_height, MAX_CARD_HEIGHT)
        self.card_width = max(self.card_width, 80)
        self.card_height = max(self.card_height, 100)

    def create_deck(self):
        deck = []
        for face in CARD_FACES[:self.num_pairs]:
            deck.extend([face, face])
        random.shuffle(deck)
        return deck

    def setup_board(self):
        deck = self.create_deck()
        self.cards = []
        total_cards = len(deck)
        rows = (total_cards + self.cards_per_row - 1) // self.cards_per_row

        grid_width = self.cards_per_row * self.card_width + (self.cards_per_row - 1) * self.gap
        grid_height = rows * self.card_height + (rows - 1) * self.gap

        start_x = (self.virtual_width - grid_width) // 2
        start_y = (self.virtual_height - grid_height) // 2

        for i, face in enumerate(deck):
            row = i // self.cards_per_row
            col = i % self.cards_per_row
            x = start_x + col * (self.card_width + self.gap)
            y = start_y + row * (self.card_height + self.gap)
            card = Card(face, x, y, self.card_width, self.card_height,
                        appear_delay=i * 0.02)
            self.cards.append(card)

    def handle_click(self, mouse_pos):
        if self.lock:
            return False
        card = get_card_under_mouse(mouse_pos, self.cards)
        if card:
            card.flip()
            self.selected.append(card)
            if asset_state.sound_manager:
                asset_state.sound_manager.play_flip()
            return True
        return False

    def flip_card_by_index(self, index):
        if self.lock:
            return False
        card = self.cards[index]
        if not card.is_matched and not card.is_flipped:
            card.flip()
            self.selected.append(card)
            if asset_state.sound_manager:
                asset_state.sound_manager.play_flip()
            return True
        return False

    def check_match(self):
        if len(self.selected) != 2:
            return False
        c1, c2 = self.selected
        if c1.face_id == c2.face_id:
            self.anim_type = 'match'
            self.anim_start_time = time.time()
            self.anim_pair = [c1, c2]
            self.lock = True
            if asset_state.sound_manager:
                asset_state.sound_manager.play_match()
            return True
        else:
            self.anim_type = 'mismatch'
            self.anim_start_time = time.time()
            self.anim_pair = [c1, c2]
            self.lock = True
            self.mismatch_sound_played = False
            return False

    def update(self):
        for card in self.cards:
            card.update()

        if not self.lock:
            return

        if self.anim_type == 'match' and time.time() - self.anim_start_time > 0.5:
            for card in self.anim_pair:
                if not card.disappearing:
                    card.disappearing = True
                    card.disappear_start = time.time()
            self._clear_animation()

        elif self.anim_type == 'mismatch':
            elapsed = time.time() - self.anim_start_time
            if not self.mismatch_sound_played and elapsed > 0.3:
                if asset_state.sound_manager:
                    asset_state.sound_manager.play_mismatch()
                self.mismatch_sound_played = True

            if elapsed > 1.0:
                for card in self.anim_pair:
                    card.flip()
                self.anim_type = 'mismatch_flipback'
                self.anim_start_time = time.time()

        elif self.anim_type == 'mismatch_flipback' and time.time() - self.anim_start_time > 0.25:
            self._clear_animation()
            self.need_turn_switch = True

    def _clear_animation(self):
        self.selected = []
        self.anim_pair = []
        self.anim_type = None
        self.anim_start_time = None
        self.lock = False

    def is_board_complete(self):
        return all(card.is_matched for card in self.cards)


class Game:
    def __init__(self, surface, settings, virtual_size):
        self.screen = surface
        self.virtual_size = virtual_size
        self.settings = settings
        self.mode = settings.get('game_mode', '1player')

        num_pairs = settings.get('num_pairs', 15)
        cols = settings.get('board_cols', 6)

        self.board = Board(virtual_size, num_pairs=num_pairs, cards_per_row=cols)
        self.board.setup_board()

        base_dir = os.path.dirname(__file__)

        self.game_bg = create_gameplay_background(virtual_size[0], virtual_size[1])

        card_back_path = resource_path(os.path.join("assets", "kenney_playing-cards-pack", "PNG", "Cards (large)", "card_back.png"))
        self.card_back = self._load_image(card_back_path, (self.board.card_width, self.board.card_height))

        faces_dir = resource_path(os.path.join("assets", "kenney_playing-cards-pack", "PNG", "Cards (large)"))
        self.card_fronts = {}
        for face in CARD_FACES:
            filename = get_face_filename(face) + ".png"
            path = os.path.join(faces_dir, filename)
            img = self._load_image(path, (self.board.card_width, self.board.card_height))
            self.card_fronts[face] = img

        self.game_over = False
        self.game_over_shown = False
        self.moves = 0

        self.streak = 0
        self.max_streak = 0

        self.hints_remaining = 3
        self.hint_btn_rect = pygame.Rect(virtual_size[0] - 140, 10, 130, 40)
        self.hint_active = False

        self.is_zen = settings.get('game_mode') == 'zen'
        self.is_level_mode = settings.get('game_mode') == 'level'

        if self.mode == '1player' or self.mode == 'zen':
            board_size_key = settings.get('num_pairs', 15)
            self.time_limit = TIMER_BY_SIZE.get(board_size_key, 120)
            self.start_time = time.time()
            self.time_remaining = self.time_limit
            self.score = 0
        elif self.mode == 'level':
            self.time_limit = TIMER_BY_SIZE.get(num_pairs, 120)
            self.start_time = time.time()
            self.time_remaining = self.time_limit
            self.score = 0
            self.current_level = settings.get('current_level', 1)
        elif self.mode == '2player':
            self.current_player = 1
            self.player_scores = {1: 0, 2: 0}
            self.turn_continuation = False
        elif self.mode == 'vsai':
            difficulty = settings.get('ai_difficulty', 'easy')
            self.ai_player = AIPlayer(difficulty)
            self.current_player = 1
            self.player_scores = {1: 0, 2: 0}
            self.turn_continuation = False
            self.ai_turn_state = 'idle'
            self.ai_timer = 0
            self.ai_first_index = None

        self.settings_open = False
        self.show_how_to_play = False
        self.quit_to_menu = False
        self.next_level_ready = False
        self.settings_font = asset_state.load_custom_font(30)
        self.settings_btn_rect = pygame.Rect(10, 10, 120, 40)

        slider_width = 20
        slider_height = 200
        slider_x = virtual_size[0] - 100
        slider_y = (virtual_size[1] - slider_height) // 2
        self.volume_slider = Slider(
            slider_x, slider_y, slider_width, slider_height,
            0, 100, settings.get('volume', 100), self.settings_font,
            orientation='vertical'
        )

        btn_w, btn_h = 220, 45
        gap = 10
        total_height = 4 * btn_h + 3 * gap
        start_y = (virtual_size[1] - total_height) // 2
        btn_x = (virtual_size[0] - btn_w) // 2

        self.how_to_play_btn = pygame.Rect(btn_x, start_y, btn_w, btn_h)
        self.restart_btn = pygame.Rect(btn_x, start_y + btn_h + gap, btn_w, btn_h)
        self.menu_btn = pygame.Rect(btn_x, start_y + 2 * (btn_h + gap), btn_w, btn_h)
        self.quit_btn = pygame.Rect(btn_x, start_y + 3 * (btn_h + gap), btn_w, btn_h)

        self.go_restart_btn = None
        self.go_menu_btn = None
        self.go_quit_btn = None
        self._setup_gameover_buttons()

        self.overlay_alpha = 0.0
        self.overlay_target = 180
        self.overlay_fade_start = 0.0
        self.settings_fade_start = 0.0
        self.howto_fade_start = 0.0
        self.virtual_mouse_pos = (0, 0)

        self.shuffle_state = 'idle'
        self.shuffle_start = 0.0
        self.shuffle_duration = 1.5
        self.shuffle_played = False
        self._start_shuffle()

    def _start_shuffle(self):
        self.shuffle_state = 'shuffling'
        self.shuffle_start = time.time()
        self.shuffle_played = False
        self.board.lock = True

    def _setup_gameover_buttons(self):
        btn_w, btn_h = 200, 50
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (self.virtual_size[0] - total_w) // 2
        y = self.virtual_size[1] - 120
        self.go_restart_btn = pygame.Rect(start_x, y, btn_w, btn_h)
        self.go_menu_btn = pygame.Rect(start_x + btn_w + gap, y, btn_w, btn_h)
        self.go_quit_btn = pygame.Rect(start_x + 2 * (btn_w + gap), y, btn_w, btn_h)

    def _load_image(self, path, size=None):
        cache_key = (path, size)
        if cache_key in _card_image_cache:
            return _card_image_cache[cache_key]
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            _card_image_cache[cache_key] = img
            return img
        except Exception as e:
            print(f"WARNING: Could not load {path} → {e}")
            return None

    def restart(self):
        self.board = Board(self.virtual_size, num_pairs=self.settings.get('num_pairs', 15),
                           cards_per_row=self.settings.get('board_cols', 6))
        self.board.setup_board()
        self.game_over = False
        self.game_over_shown = False
        self.moves = 0
        self.streak = 0
        self.max_streak = 0
        self.hints_remaining = 3
        self.hint_active = False
        self.overlay_alpha = 0.0
        self.next_level_ready = False
        self._start_shuffle()
        if self.mode in ('1player', 'zen', 'level'):
            self.start_time = time.time()
            self.time_remaining = self.time_limit
            self.score = 0
        elif self.mode == '2player':
            self.current_player = 1
            self.player_scores = {1: 0, 2: 0}
            self.turn_continuation = False
        elif self.mode == 'vsai':
            self.current_player = 1
            self.player_scores = {1: 0, 2: 0}
            self.turn_continuation = False
            self.ai_turn_state = 'idle'
            self.ai_timer = 0
            self.ai_first_index = None
            self.ai_player = AIPlayer(self.settings.get('ai_difficulty', 'easy'))
        self.settings_open = False
        self.show_how_to_play = False

    def _activate_hint(self):
        if self.hints_remaining <= 0 or self.hint_active or self.board.lock:
            return
        unmatched = [c for c in self.board.cards if not c.is_matched and not c.is_flipped]
        face_map = {}
        for c in unmatched:
            face_map.setdefault(c.face_id, []).append(c)
        for face, pair in face_map.items():
            if len(pair) >= 2:
                self.hints_remaining -= 1
                self.hint_active = True
                now = time.time()
                pair[0].hint_highlight = True
                pair[0].hint_start = now
                pair[0].flip()
                pair[1].hint_highlight = True
                pair[1].hint_start = now
                pair[1].flip()
                break

    def handle_event(self, event):
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.virtual_mouse_pos = event.pos
        if self.show_how_to_play:
            self._handle_how_to_play_event(event)
            return
        if self.game_over:
            self._handle_gameover_event(event)
            return
        if self.settings_open:
            self._handle_settings_event(event)
            return

        if self.shuffle_state != 'done':
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.settings_open = True
            self.settings_fade_start = time.time()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.settings_btn_rect.collidepoint(event.pos):
                self.settings_open = True
                self.settings_fade_start = time.time()
                return
            if self.mode in ('1player', 'zen', 'level') and self.hints_remaining > 0:
                if self.hint_btn_rect.collidepoint(event.pos):
                    self._activate_hint()
                    return

        if self.game_over:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode in ('1player', 'zen', 'level'):
                self._handle_1p_click(event.pos)
            elif self.mode == '2player':
                self._handle_2p_click(event.pos)
            elif self.mode == 'vsai' and self.current_player == 1:
                self._handle_vsai_human_click(event.pos)

    def _handle_how_to_play_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            vw, vh = self.virtual_size
            panel_h = vh - 80
            back_rect = pygame.Rect(vw // 2 - 80, 20 + panel_h - 52, 160, 40)
            if back_rect.collidepoint(event.pos):
                self.show_how_to_play = False
                self.settings_open = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.show_how_to_play = False
            self.settings_open = True

    def _handle_gameover_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.go_restart_btn and self.go_restart_btn.collidepoint(pos):
                self.restart()
            elif self.go_menu_btn and self.go_menu_btn.collidepoint(pos):
                self.quit_to_menu = True
            elif self.go_quit_btn and self.go_quit_btn.collidepoint(pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _handle_settings_event(self, event):
        if self.volume_slider.handle_event(event):
            self.settings['volume'] = self.volume_slider.value
            if asset_state.sound_manager:
                asset_state.sound_manager.set_volume(self.volume_slider.value)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.how_to_play_btn.collidepoint(pos):
                self.settings_open = False
                self.show_how_to_play = True
                self.howto_fade_start = time.time()
            elif self.restart_btn.collidepoint(pos):
                self.restart()
                self.settings_open = False
            elif self.menu_btn.collidepoint(pos):
                self.quit_to_menu = True
                self.settings_open = False
            elif self.quit_btn.collidepoint(pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            else:
                self.settings_open = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.settings_open = False

    def _handle_1p_click(self, pos):
        if self.board.lock:
            return
        flipped = self.board.handle_click(pos)
        if flipped and len(self.board.selected) == 2:
            self.moves += 1
            match = self.board.check_match()
            if match:
                self.streak += 1
                self.max_streak = max(self.max_streak, self.streak)
                self.score += 5 * self.streak
            else:
                self.streak = 0
            self.hint_active = False

    def _handle_2p_click(self, pos):
        if self.board.lock:
            return
        flipped = self.board.handle_click(pos)
        if flipped and len(self.board.selected) == 2:
            self.moves += 1
            match = self.board.check_match()
            if match:
                self.streak += 1
                self.max_streak = max(self.max_streak, self.streak)
                self.player_scores[self.current_player] += 5 * self.streak
                self.turn_continuation = True
            else:
                self.streak = 0
                self.turn_continuation = False
            self.hint_active = False

    def _handle_vsai_human_click(self, pos):
        if self.board.lock:
            return
        flipped = self.board.handle_click(pos)
        if flipped:
            flipped_card = self.board.selected[-1]
            idx = self.board.cards.index(flipped_card)
            self.ai_player.update_memory([(idx, flipped_card.face_id)])
        if flipped and len(self.board.selected) == 2:
            self.moves += 1
            match = self.board.check_match()
            if match:
                self.streak += 1
                self.max_streak = max(self.max_streak, self.streak)
                self.player_scores[1] += 5 * self.streak
                self.turn_continuation = True
            else:
                self.streak = 0
                self.turn_continuation = False
            self.hint_active = False

    def update(self):
        if self.shuffle_state == 'shuffling':
            elapsed = time.time() - self.shuffle_start
            if not self.shuffle_played and elapsed > 0.1:
                if asset_state.sound_manager:
                    asset_state.sound_manager.play_shuffle()
                self.shuffle_played = True
            if elapsed >= self.shuffle_duration:
                self.shuffle_state = 'done'
                self.board.lock = False
            return

        if self.game_over:
            if not self.game_over_shown:
                if self.overlay_fade_start == 0:
                    self.overlay_fade_start = time.time()
                if self.overlay_alpha < self.overlay_target:
                    elapsed = time.time() - self.overlay_fade_start
                    self.overlay_alpha = min(self.overlay_target, (elapsed / 0.5) * self.overlay_target)
                else:
                    self.game_over_shown = True

                    if self.mode in ('1player', 'zen', 'level'):
                        elapsed_time = time.time() - self.start_time
                        star_count = self._calculate_stars()
                        try:
                            from highscores import save_score
                            save_score(
                                self.mode if self.mode != 'zen' else 'zen',
                                self.settings.get('num_pairs', 15),
                                self.score, self.moves, elapsed_time, star_count
                            )
                        except Exception:
                            pass
            return

        if self.settings_open or self.show_how_to_play:
            return

        self.board.update()
        if self.mode in ('2player', 'vsai') and self.board.need_turn_switch:
            if not self.turn_continuation:
                self.current_player = 2 if self.current_player == 1 else 1
            self.turn_continuation = False
            self.board.need_turn_switch = False
            if self.mode == 'vsai' and self.current_player == 2:
                self.ai_turn_state = 'idle'
                self.ai_timer = time.time() + 0.3

        if self.mode in ('1player', 'zen', 'level') and not self.game_over:
            if not self.is_zen:
                elapsed = time.time() - self.start_time
                self.time_remaining = max(0, self.time_limit - elapsed)
                if self.time_remaining <= 0:
                    self.game_over = True
                    self.overlay_fade_start = time.time()

        if self.mode == 'vsai' and self.current_player == 2 and not self.game_over and not self.board.lock:
            self._update_ai_turn()
        if self.board.is_board_complete() and not self.game_over_shown:
            self.game_over = True
            self.overlay_fade_start = time.time()

    def _calculate_stars(self):
        num_pairs = self.settings.get('num_pairs', 15)
        par_moves = num_pairs + 2
        if self.moves <= par_moves:
            return 3
        elif self.moves <= par_moves * 2:
            return 2
        return 1

    def _update_ai_turn(self):
        now = time.time()
        if self.ai_turn_state == 'idle':
            if now >= self.ai_timer:
                first = self.ai_player.get_first_card(self.board)
                if first is not None:
                    self.board.flip_card_by_index(first)
                    self.ai_player.update_memory([(first, self.board.cards[first].face_id)])
                    self.ai_first_index = first
                    self.ai_turn_state = 'first_flip'
                    self.ai_timer = now + 0.5

        elif self.ai_turn_state == 'first_flip':
            if now >= self.ai_timer:
                second = self.ai_player.get_second_card(self.board, self.ai_first_index)
                if second is not None:
                    self.board.flip_card_by_index(second)
                    self.ai_player.update_memory([(second, self.board.cards[second].face_id)])

                    self.moves += 1
                    match = self.board.check_match()
                    if match:
                        self.streak += 1
                        self.max_streak = max(self.max_streak, self.streak)
                        self.player_scores[2] += 5 * self.streak
                        self.turn_continuation = True
                    else:
                        self.streak = 0
                        self.turn_continuation = False

                self.ai_turn_state = 'idle'
                self.ai_first_index = None

    def draw(self):
        if self.game_bg:
            dt = 1 / 60.0
            self.game_bg.update(dt)
            self.game_bg.draw(self.screen)
        else:
            self.screen.fill((0, 80, 0))

        if self.shuffle_state == 'shuffling':
            elapsed = time.time() - self.shuffle_start
            positions = shuffle_positions(
                self.board.cards, elapsed, self.shuffle_duration,
                self.virtual_size[0] // 2, self.virtual_size[1] // 2,
                self.virtual_size[0], self.virtual_size[1]
            )
            scale = shuffle_scale(elapsed, self.shuffle_duration)
            for i, card in enumerate(self.board.cards):
                x, y = positions[i]
                w = max(1, int(card.rect.width * scale))
                h = max(1, int(card.rect.height * scale))
                img = self.card_back if self.card_back else pygame.Surface((w, h))
                if img:
                    scaled = pygame.transform.scale(img, (w, h))
                    self.screen.blit(scaled, (x, y))
            return

        for card in self.board.cards:
            card.draw(self.screen, self.card_back, self.card_fronts)

        draw_hud_background(self.screen, 5, 50, 200, 230)

        font = asset_state.load_custom_font(36)
        small_font = asset_state.load_custom_font(28)

        if self.mode in ('1player', 'zen', 'level'):
            if not self.is_zen:
                mins = int(self.time_remaining // 60)
                secs = int(self.time_remaining % 60)
                timer_str = f"Time: {mins:02d}:{secs:02d}"
                timer_color = (255, 100, 100) if self.time_remaining <= 15 else (255, 255, 255)
                self.screen.blit(font.render(timer_str, True, timer_color), (10, 60))
            else:
                self.screen.blit(font.render("Zen Mode", True, (150, 200, 255)), (10, 60))

            self.screen.blit(font.render(f"Score: {self.score}", True, (255, 255, 255)), (10, 100))
            self.screen.blit(font.render(f"Moves: {self.moves}", True, (255, 255, 255)), (10, 140))

            if self.streak > 1:
                streak_text = f"Streak: x{self.streak}"
                streak_color = (255, 215, 0) if self.streak < 5 else (255, 100, 100)
                self.screen.blit(font.render(streak_text, True, streak_color), (10, 180))

            pairs_left = sum(1 for c in self.board.cards if not c.is_matched) // 2
            self.screen.blit(small_font.render(f"Pairs left: {pairs_left}", True, (200, 200, 200)), (10, 220))

            if self.is_level_mode:
                lvl_text = f"Level {self.current_level}"
                self.screen.blit(small_font.render(lvl_text, True, (255, 200, 100)), (10, 255))

            if self.mode in ('1player', 'zen', 'level') and self.hints_remaining > 0:
                pygame.draw.rect(self.screen, (25, 35, 65), self.hint_btn_rect, border_radius=5)
                pygame.draw.rect(self.screen, (60, 80, 140), self.hint_btn_rect, 2, border_radius=5)
                hint_text = self.settings_font.render(f"Hint ({self.hints_remaining})", True, (255, 255, 200))
                hint_rect = hint_text.get_rect(center=self.hint_btn_rect.center)
                self.screen.blit(hint_text, hint_rect)

        elif self.mode == '2player':
            turn = "Player 1's Turn" if self.current_player == 1 else "Player 2's Turn"
            self.screen.blit(font.render(turn, True, (255, 255, 255)), (10, 60))
            self.screen.blit(font.render(f"P1 Score: {self.player_scores[1]}", True, (255, 255, 255)), (10, 100))
            self.screen.blit(font.render(f"P2 Score: {self.player_scores[2]}", True, (255, 255, 255)), (10, 140))
            if self.streak > 1:
                self.screen.blit(font.render(f"Streak: x{self.streak}", True, (255, 215, 0)), (10, 180))

        elif self.mode == 'vsai':
            turn = "Your Turn" if self.current_player == 1 else "AI's Turn"
            self.screen.blit(font.render(turn, True, (255, 255, 255)), (10, 60))
            self.screen.blit(font.render(f"You: {self.player_scores[1]}", True, (255, 255, 255)), (10, 100))
            self.screen.blit(font.render(f"AI: {self.player_scores[2]}", True, (255, 255, 255)), (10, 140))

            diff_text = f"AI: {self.settings.get('ai_difficulty', 'easy').capitalize()}"
            diff_font = asset_state.load_custom_font(24)
            diff_surf = diff_font.render(diff_text, True, (255, 255, 255))
            diff_rect = diff_surf.get_rect(topright=(self.screen.get_width() - 20, 20))
            self.screen.blit(diff_surf, diff_rect)

        pygame.draw.rect(self.screen, (30, 40, 70), self.settings_btn_rect, border_radius=5)
        pygame.draw.rect(self.screen, (60, 80, 140), self.settings_btn_rect, 2, border_radius=5)
        btn_text = self.settings_font.render("Settings", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=self.settings_btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)

        if self.show_how_to_play:
            self._draw_how_to_play_overlay()
        elif self.settings_open:
            self._draw_settings_overlay()

        if self.game_over:
            self._draw_game_over()

    def _draw_how_to_play_overlay(self):
        if self.howto_fade_start == 0:
            self.howto_fade_start = time.time()
        alpha = min(220, int((time.time() - self.howto_fade_start) / 0.4 * 220))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        vw, vh = self.virtual_size
        panel_w = min(750, vw - 80)
        panel_h = vh - 80
        panel_x = (vw - panel_w) // 2
        panel_y = 20

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 20, 45, 230), (0, 0, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(panel, (60, 80, 160, 200), (0, 0, panel_w, panel_h), 2, border_radius=16)
        self.screen.blit(panel, (panel_x, panel_y))

        title_font = asset_state.load_custom_font(40)
        header_font = asset_state.load_custom_font(30)
        body_font = asset_state.load_custom_font(24)

        title = title_font.render("How to Play", True, (100, 180, 255))
        title_rect = title.get_rect(center=(vw // 2, panel_y + 28))
        self.screen.blit(title, title_rect)

        underline_y = panel_y + 50
        pygame.draw.line(self.screen, (60, 80, 160), (vw // 2 - 100, underline_y), (vw // 2 + 100, underline_y), 2)

        y = panel_y + 68
        cx = vw // 2
        sp = 26

        sections = [
            {
                "title": None,
                "lines": [
                    ("\u2022  Flip two cards at a time. Match them to score.", (220, 220, 220)),
                    ("\u2022  Unmatched cards flip back after a short time.", (220, 220, 220)),
                    ("\u2022  Find all pairs before time runs out to win!", (220, 220, 220)),
                ],
            },
            {
                "title": "Game Modes",
                "lines": [
                    ("\u25b6  1 Player \u2014 Match pairs against the clock. Use hints to reveal pairs.", (100, 220, 150)),
                    ("     Streaks increase your score combo multiplier.", (170, 170, 170)),
                    ("\u25b6  2 Player \u2014 Take turns flipping cards. Match to keep your turn.", (100, 200, 255)),
                    ("\u25b6  VS AI \u2014 Compete against the computer. Higher difficulty = smarter AI.", (255, 180, 100)),
                    ("\u25b6  Level Mode \u2014 3 levels of increasing size. Earn up to 3 stars.", (255, 200, 100)),
                    ("\u25b6  Zen \u2014 No timer, no pressure. Match pairs at your own pace.", (200, 150, 255)),
                ],
            },
        ]

        for section in sections:
            if section["title"]:
                y += 6
                hdr = header_font.render(section["title"], True, (100, 180, 255))
                hdr_rect = hdr.get_rect(center=(cx, y))
                self.screen.blit(hdr, hdr_rect)
                y += 32
            for text, color in section["lines"]:
                line_surf = body_font.render(text, True, color)
                line_rect = line_surf.get_rect(center=(cx, y))
                self.screen.blit(line_surf, line_rect)
                y += sp

        back_rect = pygame.Rect(vw // 2 - 80, panel_y + panel_h - 52, 160, 40)
        mouse_pos = self.virtual_mouse_pos
        if back_rect.collidepoint(mouse_pos):
            back_color = (50, 90, 180)
            back_border = (100, 140, 220)
        else:
            back_color = (35, 50, 90)
            back_border = (60, 80, 140)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, back_border, back_rect, 2, border_radius=10)
        back_text = self.settings_font.render("Back", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect)

    def _draw_settings_overlay(self):
        if self.settings_fade_start == 0:
            self.settings_fade_start = time.time()
        alpha = min(180, int((time.time() - self.settings_fade_start) / 0.4 * 180))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((5, 10, 25, alpha))
        self.screen.blit(overlay, (0, 0))

        title_font = asset_state.load_custom_font(50)
        title = title_font.render("Settings", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title, title_rect)

        label_font = asset_state.load_custom_font(24)
        label = label_font.render("Volume", True, (255, 255, 255))
        label_rect = label.get_rect(center=(self.volume_slider.rect.centerx, self.volume_slider.rect.top - 20))
        self.screen.blit(label, label_rect)

        self.volume_slider.draw(self.screen)

        self._draw_button(self.how_to_play_btn, "How to Play", (100, 100, 255))
        self._draw_button(self.restart_btn, "Restart", (0, 200, 0))
        self._draw_button(self.menu_btn, "Main Menu", (0, 100, 200))
        self._draw_button(self.quit_btn, "Quit Game", (200, 0, 0))

    def _draw_button(self, rect, text, color):
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 130, 200), rect, 2, border_radius=8)
        text_surf = self.settings_font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def _draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((5, 10, 25, int(self.overlay_alpha)))
        self.screen.blit(overlay, (0, 0))

        big_font = asset_state.load_custom_font(72)
        med_font = asset_state.load_custom_font(50)
        small_font = asset_state.load_custom_font(30)

        if self.mode in ('1player', 'zen', 'level'):
            if self.time_remaining <= 0 and not self.is_zen:
                title = "Time's Up!"
            elif self.board.is_board_complete():
                title = "You Win!"
            else:
                title = "Game Over!"
        elif self.mode == '2player':
            if self.player_scores[1] > self.player_scores[2]:
                title = "Player 1 Wins!"
            elif self.player_scores[2] > self.player_scores[1]:
                title = "Player 2 Wins!"
            else:
                title = "It's a Tie!"
        elif self.mode == 'vsai':
            if self.player_scores[1] > self.player_scores[2]:
                title = "You Win!"
            elif self.player_scores[2] > self.player_scores[1]:
                title = "AI Wins!"
            else:
                title = "It's a Tie!"
        else:
            title = "Game Over!"

        title_surf = big_font.render(title, True, (255, 255, 0))
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surf, title_rect)

        if self.mode in ('1player', 'zen', 'level'):
            score_surf = med_font.render(f"Score: {self.score}", True, (255, 255, 255))
            score_rect = score_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 30))
            self.screen.blit(score_surf, score_rect)

            star_count = self._calculate_stars()
            star_text = "★" * star_count + "☆" * (3 - star_count)
            star_surf = asset_state.load_custom_font(60).render(star_text, True, (255, 215, 0))
            star_rect = star_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 30))
            self.screen.blit(star_surf, star_rect)

        elif self.mode == '2player':
            p1_score_surf = med_font.render(f"Player 1 Score: {self.player_scores[1]}", True, (255, 255, 255))
            p1_score_rect = p1_score_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 30))
            self.screen.blit(p1_score_surf, p1_score_rect)
            p2_score_surf = med_font.render(f"Player 2 Score: {self.player_scores[2]}", True, (255, 255, 255))
            p2_score_rect = p2_score_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 30))
            self.screen.blit(p2_score_surf, p2_score_rect)
        elif self.mode == 'vsai':
            you_surf = med_font.render(f"You: {self.player_scores[1]}", True, (255, 255, 255))
            you_rect = you_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 30))
            self.screen.blit(you_surf, you_rect)
            ai_surf = med_font.render(f"AI: {self.player_scores[2]}", True, (255, 255, 255))
            ai_rect = ai_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 30))
            self.screen.blit(ai_surf, ai_rect)

        if self.mode in ('1player', 'zen', 'level'):
            moves_surf = small_font.render(f"Moves: {self.moves}", True, (255, 255, 255))
            moves_rect = moves_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 80))
            self.screen.blit(moves_surf, moves_rect)
            if not self.is_zen:
                mins_left = int(self.time_remaining // 60)
                secs_left = int(self.time_remaining % 60)
                time_left_str = f"Time Left: {mins_left:02d}:{secs_left:02d}"
                time_left_surf = small_font.render(time_left_str, True, (255, 255, 255))
                time_left_rect = time_left_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 120))
                self.screen.blit(time_left_surf, time_left_rect)

        self._draw_button(self.go_restart_btn, "Restart", (0, 200, 0))
        self._draw_button(self.go_menu_btn, "Main Menu", (0, 100, 200))
        self._draw_button(self.go_quit_btn, "Quit Game", (200, 0, 0))
