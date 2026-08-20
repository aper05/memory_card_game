import pygame
import random
import os
import time
from ai_logic import AIPlayer
from ui_controls import Slider
import asset_state
from asset_state import resource_path
from physics_collision import get_card_under_mouse, flip_scale, appear_scale, disappear_scale

CARD_FACES = [
    'A', '2', '3', '4', '5', '6', '7', '8', '9', '10',
    'J', 'Q', 'K', 'red_joker', 'black_joker'
]

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


class Board:
    def __init__(self, virtual_size, cards_per_row=6, gap=10):
        self.virtual_width, self.virtual_height = virtual_size
        self.cards_per_row = cards_per_row
        self.gap = gap
        self.cards = []
        self.selected = []
        self.lock = False
        self.anim_type = None            # 'match', 'mismatch', 'mismatch_flipback'
        self.anim_start_time = None
        self.anim_pair = []
        self.need_turn_switch = False
        self.mismatch_sound_played = False   # track if mismatch sound played

        MAX_CARD_WIDTH = 110
        MAX_CARD_HEIGHT = 140

        total_rows = 30 // self.cards_per_row
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
        for face in CARD_FACES:
            deck.extend([face, face])
        random.shuffle(deck)
        return deck

    def setup_board(self):
        deck = self.create_deck()
        self.cards = []
        total_cards = len(deck)
        rows = total_cards // self.cards_per_row

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
            self.mismatch_sound_played = False   # will play after delay
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
            # Play mismatch sound after a 0.3-second pause
            if not self.mismatch_sound_played and elapsed > 0.3:
                if asset_state.sound_manager:
                    asset_state.sound_manager.play_mismatch()
                self.mismatch_sound_played = True

            # After 1.0 seconds total, start flip‑back animation
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
        self.board = Board(virtual_size)
        self.board.setup_board()

        base_dir = os.path.dirname(__file__)

        bg_path = resource_path(os.path.join("assets", "ver0.05", "background.png"))
        self.game_bg = self._load_image(bg_path, virtual_size)

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

        if self.mode == '1player':
            self.time_limit = 120
            self.start_time = time.time()
            self.time_remaining = self.time_limit
            self.score = 0
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

        # In‑game settings
        self.settings_open = False
        self.show_how_to_play = False
        self.quit_to_menu = False
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

        btn_w, btn_h = 200, 45
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

    def _setup_gameover_buttons(self):
        btn_w, btn_h = 180, 50
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (self.virtual_size[0] - total_w) // 2
        y = self.virtual_size[1] - 120
        self.go_restart_btn = pygame.Rect(start_x, y, btn_w, btn_h)
        self.go_menu_btn = pygame.Rect(start_x + btn_w + gap, y, btn_w, btn_h)
        self.go_quit_btn = pygame.Rect(start_x + 2 * (btn_w + gap), y, btn_w, btn_h)

    def _load_image(self, path, size=None):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except Exception as e:
            print(f"WARNING: Could not load {path} → {e}")
            return None

    def restart(self):
        self.board = Board(self.virtual_size)
        self.board.setup_board()
        self.game_over = False
        self.game_over_shown = False
        self.moves = 0
        self.overlay_alpha = 0.0
        if self.mode == '1player':
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

    # ---------- Event handling ----------
    def handle_event(self, event):
        if self.show_how_to_play:
            self._handle_how_to_play_event(event)
            return
        if self.game_over:
            self._handle_gameover_event(event)
            return
        if self.settings_open:
            self._handle_settings_event(event)
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

        if self.game_over:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode == '1player':
                self._handle_1p_click(event.pos)
            elif self.mode == '2player':
                self._handle_2p_click(event.pos)
            elif self.mode == 'vsai' and self.current_player == 1:
                self._handle_vsai_human_click(event.pos)

    def _handle_how_to_play_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            back_rect = pygame.Rect(self.virtual_size[0]//2 - 80, self.virtual_size[1] - 100, 160, 45)
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
                self.score += 5

    def _handle_2p_click(self, pos):
        if self.board.lock:
            return
        flipped = self.board.handle_click(pos)
        if flipped and len(self.board.selected) == 2:
            self.moves += 1
            match = self.board.check_match()
            if match:
                self.player_scores[self.current_player] += 5
                self.turn_continuation = True
            else:
                self.turn_continuation = False

    def _handle_vsai_human_click(self, pos):
        if self.board.lock:
            return
        flipped = self.board.handle_click(pos)
        if flipped:
            # Tell AI about the revealed card
            flipped_card = self.board.selected[-1]
            idx = self.board.cards.index(flipped_card)
            self.ai_player.update_memory([(idx, flipped_card.face_id)])
        if flipped and len(self.board.selected) == 2:
            self.moves += 1
            match = self.board.check_match()
            if match:
                self.player_scores[1] += 5
                self.turn_continuation = True
            else:
                self.turn_continuation = False

    def update(self):
        if self.game_over:
            if not self.game_over_shown:
                if self.overlay_fade_start == 0:
                    self.overlay_fade_start = time.time()
                if self.overlay_alpha < self.overlay_target:
                    elapsed = time.time() - self.overlay_fade_start
                    self.overlay_alpha = min(self.overlay_target, (elapsed / 0.5) * self.overlay_target)
                else:
                    self.game_over_shown = True
            return

        if self.settings_open or self.show_how_to_play:
            return

        self.board.update()
        if self.mode in ['2player', 'vsai'] and self.board.need_turn_switch:
            if not self.turn_continuation:
                self.current_player = 2 if self.current_player == 1 else 1
            self.turn_continuation = False
            self.board.need_turn_switch = False
            if self.mode == 'vsai' and self.current_player == 2:
                self.ai_turn_state = 'idle'
                self.ai_timer = time.time() + 0.3
        if self.mode == '1player' and not self.game_over:
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
                    self.ai_timer = now + 0.5   # visual pause between flips

        elif self.ai_turn_state == 'first_flip':
            if now >= self.ai_timer:
                second = self.ai_player.get_second_card(self.board, self.ai_first_index)
                if second is not None:
                    self.board.flip_card_by_index(second)
                    self.ai_player.update_memory([(second, self.board.cards[second].face_id)])

                    # IMMEDIATE match check – exactly like human
                    self.moves += 1
                    match = self.board.check_match()
                    if match:
                        self.player_scores[2] += 5
                        self.turn_continuation = True
                    else:
                        self.turn_continuation = False

                # Turn finishes right here – no third state
                self.ai_turn_state = 'idle'
                self.ai_first_index = None
                
    def draw(self):
        if self.game_bg:
            self.screen.blit(self.game_bg, (0, 0))
        else:
            self.screen.fill((0, 80, 0))

        for card in self.board.cards:
            card.draw(self.screen, self.card_back, self.card_fronts)

        font = asset_state.load_custom_font(36)
        if self.mode == '1player':
            mins = int(self.time_remaining // 60)
            secs = int(self.time_remaining % 60)
            timer_str = f"Time: {mins:02d}:{secs:02d}"
            self.screen.blit(font.render(timer_str, True, (255, 255, 255)), (10, 60))
            self.screen.blit(font.render(f"Score: {self.score}", True, (255, 255, 255)), (10, 100))
            self.screen.blit(font.render(f"Moves: {self.moves}", True, (255, 255, 255)), (10, 140))
        elif self.mode == '2player':
            turn = "Player 1's Turn" if self.current_player == 1 else "Player 2's Turn"
            self.screen.blit(font.render(turn, True, (255, 255, 255)), (10, 60))
            self.screen.blit(font.render(f"P1 Score: {self.player_scores[1]}", True, (255, 255, 255)), (10, 100))
            self.screen.blit(font.render(f"P2 Score: {self.player_scores[2]}", True, (255, 255, 255)), (10, 140))
        elif self.mode == 'vsai':
            turn = "Your Turn" if self.current_player == 1 else "AI's Turn"
            self.screen.blit(font.render(turn, True, (255, 255, 255)), (10, 60))
            self.screen.blit(font.render(f"You: {self.player_scores[1]}", True, (255, 255, 255)), (10, 100))
            self.screen.blit(font.render(f"AI: {self.player_scores[2]}", True, (255, 255, 255)), (10, 140))

            if self.mode == 'vsai':
                diff_text = f"AI: {self.settings.get('ai_difficulty', 'easy').capitalize()}"
                diff_font = asset_state.load_custom_font(24)
                diff_surf = diff_font.render(diff_text, True, (255, 255, 255))
                diff_rect = diff_surf.get_rect(topright=(self.screen.get_width() - 20, 20))
                self.screen.blit(diff_surf, diff_rect)

        pygame.draw.rect(self.screen, (70, 70, 70), self.settings_btn_rect, border_radius=5)
        pygame.draw.rect(self.screen, (200, 200, 200), self.settings_btn_rect, 2, border_radius=5)
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
        alpha = min(200, int((time.time() - self.howto_fade_start) / 0.4 * 200))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        title_font = asset_state.load_custom_font(48)
        text_font = asset_state.load_custom_font(28)
        title = title_font.render("How to Play", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.virtual_size[0] // 2, 50))
        self.screen.blit(title, title_rect)

        rules = [
            "Flip over two cards at a time.",
            "If they match, they disappear and you score points.",
            "If they don't match, they flip back after a short time.",
            "Find all pairs to win the game!",
            "",
            "1 Player: Score as many points as possible in 120 seconds.",
            "2 Player: Take turns. The player with the most matches wins.",
            "VS AI: Compete against the computer. Difficulty affects AI memory.",
        ]
        y = 120
        for line in rules:
            text = text_font.render(line, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.virtual_size[0] // 2, y))
            self.screen.blit(text, text_rect)
            y += 35

        back_rect = pygame.Rect(self.virtual_size[0]//2 - 80, self.virtual_size[1] - 100, 160, 45)
        pygame.draw.rect(self.screen, (0, 100, 200), back_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 2, border_radius=8)
        back_text = self.settings_font.render("Back", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect)

    def _draw_settings_overlay(self):
        if self.settings_fade_start == 0:
            self.settings_fade_start = time.time()
        alpha = min(180, int((time.time() - self.settings_fade_start) / 0.4 * 180))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
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
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=8)
        text_surf = self.settings_font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def _draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self.overlay_alpha)))
        self.screen.blit(overlay, (0, 0))

        big_font = asset_state.load_custom_font(72)
        med_font = asset_state.load_custom_font(50)
        small_font = asset_state.load_custom_font(30)

        if self.mode == '1player':
            if self.time_remaining <= 0:
                title = "Time's Up!"
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

        if self.mode == '1player':
            score_surf = med_font.render(f"Score: {self.score}", True, (255, 255, 255))
            score_rect = score_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(score_surf, score_rect)
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

        if self.mode == '1player':
            moves_surf = small_font.render(f"Moves: {self.moves}", True, (255, 255, 255))
            moves_rect = moves_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 80))
            self.screen.blit(moves_surf, moves_rect)
            mins_left = int(self.time_remaining // 60)
            secs_left = int(self.time_remaining % 60)
            time_left_str = f"Time Left: {mins_left:02d}:{secs_left:02d}"
            time_left_surf = small_font.render(time_left_str, True, (255, 255, 255))
            time_left_rect = time_left_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 120))
            self.screen.blit(time_left_surf, time_left_rect)

        # Action buttons
        self._draw_button(self.go_restart_btn, "Restart", (0, 200, 0))
        self._draw_button(self.go_menu_btn, "Main Menu", (0, 100, 200))
        self._draw_button(self.go_quit_btn, "Quit Game", (200, 0, 0))