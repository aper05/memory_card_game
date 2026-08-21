import pygame
import time
from asset_state import MENU, SETTINGS, PLAYING, MODE_SELECT, DIFFICULTY, BOARD_SELECT, LEVEL_COMPLETE, LEADERBOARD, load_custom_font
import asset_state

LEVEL_CONFIGS = [
    {'num_pairs': 6, 'board_cols': 4, 'board_rows': 3},
    {'num_pairs': 8, 'board_cols': 4, 'board_rows': 4},
    {'num_pairs': 15, 'board_cols': 5, 'board_rows': 6},
]

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (45, 55, 85)
DARK_GREY = (25, 30, 50)
LIGHT_BLUE = (70, 120, 220)

class Button:
    def __init__(self, x, y, width, height, text, font, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.hovered = False
        self.pressed_time = 0.0
        self.PRESS_DURATION = 0.1
        self.pending_action = None   # function to call after animation

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.action:
                if asset_state.sound_manager:
                    asset_state.sound_manager.play_button()
                self.pressed_time = time.time()
                self.pending_action = self.action   # store, don't call yet
                return True
        return False

    def update(self):
        """Call every frame. Fires the action after the animation finishes."""
        if self.pending_action and time.time() - self.pressed_time >= self.PRESS_DURATION:
            self.pending_action()
            self.pending_action = None   # fire only once

    def draw(self, surface):
        now = time.time()
        elapsed = now - self.pressed_time
        pressing = self.pending_action is not None and elapsed < self.PRESS_DURATION

        # Scale: 1.0 → 0.85 → 1.0
        scale = 1.0
        if pressing:
            t = elapsed / self.PRESS_DURATION
            if t < 0.5:
                scale = 1.0 - 0.15 * (t / 0.5)
            else:
                scale = 0.85 + 0.15 * ((t - 0.5) / 0.5)

        # Flash white for first 0.05s
        if pressing and elapsed < 0.05:
            color = WHITE
        else:
            color = LIGHT_BLUE if self.hovered else GREY

        # Shrink rect around center
        if scale != 1.0:
            w = int(self.rect.width * scale)
            h = int(self.rect.height * scale)
            draw_rect = pygame.Rect(self.rect.centerx - w//2,
                                    self.rect.centery - h//2, w, h)
        else:
            draw_rect = self.rect

        pygame.draw.rect(surface, color, draw_rect, border_radius=10)
        pygame.draw.rect(surface, (80, 100, 160), draw_rect, 2, border_radius=10)

        # Scale text accordingly
        text_surf = self.font.render(self.text, True, WHITE)
        if scale != 1.0:
            text_surf = pygame.transform.scale(
                text_surf,
                (max(1, int(text_surf.get_width() * scale)),
                 max(1, int(text_surf.get_height() * scale)))
            )
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)


class Slider:
    """A slider that can be horizontal or vertical. 100 = top, 0 = bottom for vertical."""
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, font, orientation='horizontal'):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.font = font
        self.orientation = orientation
        self.dragging = False

        if orientation == 'horizontal':
            self.knob_radius = height // 2
            self.knob_x = self._value_to_x(initial_val)
            self.knob_y = self.rect.centery
        else:
            self.knob_radius = width // 2
            self.knob_x = self.rect.centerx
            self.knob_y = self._value_to_y(initial_val)

    def _value_to_x(self, value):
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.left + int(ratio * self.rect.width)

    def _x_to_value(self, x):
        ratio = (x - self.rect.left) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def _value_to_y(self, value):
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.top + int((1 - ratio) * self.rect.height)

    def _y_to_value(self, y):
        ratio = (y - self.rect.top) / self.rect.height
        ratio = max(0.0, min(1.0, ratio))
        return self.min_val + (1 - ratio) * (self.max_val - self.min_val)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self.rect.collidepoint(event.pos) or self._knob_rect().collidepoint(event.pos)
            if hit:
                self.dragging = True
                if self.orientation == 'horizontal':
                    self._set_from_mouse_x(event.pos[0])
                else:
                    self._set_from_mouse_y(event.pos[1])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            if self.orientation == 'horizontal':
                self._set_from_mouse_x(event.pos[0])
            else:
                self._set_from_mouse_y(event.pos[1])
            return True
        return False

    def _set_from_mouse_x(self, mouse_x):
        self.knob_x = max(self.rect.left, min(mouse_x, self.rect.right))
        self.value = round(self._x_to_value(self.knob_x))

    def _set_from_mouse_y(self, mouse_y):
        self.knob_y = max(self.rect.top, min(mouse_y, self.rect.bottom))
        self.value = round(self._y_to_value(self.knob_y))

    def _knob_rect(self):
        if self.orientation == 'horizontal':
            return pygame.Rect(
                self.knob_x - self.knob_radius,
                self.rect.centery - self.knob_radius,
                self.knob_radius * 2,
                self.knob_radius * 2
            )
        else:
            return pygame.Rect(
                self.rect.centerx - self.knob_radius,
                self.knob_y - self.knob_radius,
                self.knob_radius * 2,
                self.knob_radius * 2
            )

    def draw(self, surface):
        if self.orientation == 'horizontal':
            pygame.draw.rect(surface, DARK_GREY, self.rect, border_radius=5)
            filled_rect = self.rect.copy()
            filled_rect.width = self.knob_x - self.rect.left
            pygame.draw.rect(surface, LIGHT_BLUE, filled_rect, border_radius=5)
            pygame.draw.circle(surface, WHITE, (self.knob_x, self.rect.centery), self.knob_radius)
            pygame.draw.circle(surface, BLACK, (self.knob_x, self.rect.centery), self.knob_radius, 2)
            value_text = self.font.render(f"{int(self.value)}%", True, WHITE)
            text_rect = value_text.get_rect(midleft=(self.rect.right + 15, self.rect.centery))
            surface.blit(value_text, text_rect)
        else:
            pygame.draw.rect(surface, DARK_GREY, self.rect, border_radius=5)
            if self.knob_y > self.rect.top:
                filled_rect = pygame.Rect(
                    self.rect.left, self.rect.top,
                    self.rect.width, self.knob_y - self.rect.top
                )
                pygame.draw.rect(surface, LIGHT_BLUE, filled_rect, border_radius=5)
            pygame.draw.circle(surface, WHITE, (self.rect.centerx, self.knob_y), self.knob_radius)
            pygame.draw.circle(surface, BLACK, (self.rect.centerx, self.knob_y), self.knob_radius, 2)
            value_text = self.font.render(f"{int(self.value)}%", True, WHITE)
            text_rect = value_text.get_rect(midtop=(self.rect.centerx, self.rect.bottom + 10))
            surface.blit(value_text, text_rect)


class MainMenu:
    def __init__(self, screen_width, screen_height, state_manager):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(40)
        self.title_font = load_custom_font(80)
        self.title_surf = self.title_font.render("Memory Card Game", True, WHITE)

        btn_width, btn_height = 200, 60
        center_x = screen_width // 2 - btn_width // 2
        start_y = screen_height // 2 - 80
        spacing = 80

        self.start_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "Play", self.font, action=self.start_game
        )
        self.leaderboard_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "High Scores", self.font, action=self.open_leaderboard
        )
        self.settings_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "Settings", self.font, action=self.open_settings
        )
        self.quit_btn = Button(
            center_x, start_y + 3 * spacing, btn_width, btn_height,
            "Quit", self.font, action=self.quit_game
        )
        self.buttons = [self.start_btn, self.leaderboard_btn, self.settings_btn, self.quit_btn]

    def start_game(self):
        self.state_manager.change_state(MODE_SELECT)

    def open_leaderboard(self):
        self.state_manager.change_state(LEADERBOARD)

    def open_settings(self):
        self.state_manager.change_state(SETTINGS)

    def quit_game(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self):
        for btn in self.buttons:
            btn.update()

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def draw(self, surface):
        title_rect = self.title_surf.get_rect(center=(self.screen_width // 2, 60))
        surface.blit(self.title_surf, title_rect)
        for btn in self.buttons:
            btn.draw(surface)


class SettingsScreen:
    def __init__(self, screen_width, screen_height, state_manager, settings):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.settings = settings
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(40)
        self.show_how_to_play = False
        self.howto_fade_start = 0.0

        slider_width = 300
        slider_height = 20
        slider_x = screen_width // 2 - slider_width // 2
        slider_y = 250
        initial_vol = self.settings.get('volume', 100)
        self.volume_slider = Slider(
            slider_x, slider_y, slider_width, slider_height,
            0, 100, initial_vol, self.small_font,
            orientation='horizontal'
        )

        btn_width = 250
        btn_height = 50
        self.how_to_play_btn = Button(
            screen_width // 2 - btn_width // 2,
            slider_y + slider_height + 30,
            btn_width, btn_height,
            "How to Play", self.small_font,
            action=self.open_how_to_play
        )

        self.back_btn = Button(
            screen_width // 2 - btn_width // 2,
            self.how_to_play_btn.rect.bottom + 20,
            btn_width, btn_height,
            "Back", self.font, action=self.go_back
        )

    def open_how_to_play(self):
        self.show_how_to_play = True
        self.howto_fade_start = time.time()

    def close_how_to_play(self):
        self.show_how_to_play = False

    def go_back(self):
        self.state_manager.change_state(MENU)

    def update(self):
        self.how_to_play_btn.update()
        self.back_btn.update()

    def handle_event(self, event):
        if self.show_how_to_play:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                back_rect = pygame.Rect(
                    self.screen_width // 2 - 80,
                    self.screen_height - 100,
                    160, 45
                )
                if back_rect.collidepoint(event.pos):
                    self.close_how_to_play()
                    return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.close_how_to_play()
                return True
            return False

        if self.back_btn.handle_event(event):
            return True
        if self.how_to_play_btn.handle_event(event):
            return True
        if self.volume_slider.handle_event(event):
            self.settings['volume'] = self.volume_slider.value
            if asset_state.sound_manager:
                asset_state.sound_manager.set_volume(self.volume_slider.value)
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_back()
            return True
        return False

    def draw(self, surface):
        title = self.font.render("Settings", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 80))
        surface.blit(title, title_rect)

        label = self.small_font.render("Volume", True, WHITE)
        label_rect = label.get_rect(center=(self.screen_width // 2, 210))
        surface.blit(label, label_rect)

        self.volume_slider.draw(surface)
        self.how_to_play_btn.draw(surface)
        self.back_btn.draw(surface)

        if self.show_how_to_play:
            self._draw_how_to_play_overlay(surface)

    def _draw_how_to_play_overlay(self, surface):
        if self.howto_fade_start == 0:
            self.howto_fade_start = time.time()
        alpha = min(200, int((time.time() - self.howto_fade_start) / 0.4 * 200))
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))

        title_font = load_custom_font(48)
        text_font = load_custom_font(28)
        title = title_font.render("How to Play", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)

        rules = [
            "Flip over two cards at a time.",
            "If they match, they disappear and you score points.",
            "If they don't match, they flip back after a short time.",
            "Find all pairs to win the game!",
            "",
            "--- Game Modes ---",
            "",
            "1 Player: Match all pairs before time runs out.",
            "  Score points by matching cards. Consecutive matches",
            "  increase your combo multiplier. Use hints (3 per game)",
            "  to reveal a matching pair. Board size affects timer.",
            "",
            "2 Player: Take turns flipping two cards each turn.",
            "  If you match, you keep your turn. If not, play passes",
            "  to the other player. The player with the most matches wins.",
            "",
            "VS AI: Compete against the computer.",
            "  Difficulty affects how well the AI remembers cards.",
            "  Easy: AI forgets often. Hard: AI has near-perfect memory.",
            "",
            "Level Mode: Progress through 3 levels of increasing size.",
            "  Earn stars based on how few moves you take.",
            "  3 stars: moves <= pairs + 2",
            "",
            "Zen: No timer, no pressure. Just match pairs at your own pace.",
        ]
        y = 120
        for line in rules:
            text = text_font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(self.screen_width // 2, y))
            surface.blit(text, text_rect)
            y += 35

        back_rect = pygame.Rect(self.screen_width // 2 - 80, self.screen_height - 100, 160, 45)
        pygame.draw.rect(surface, (0, 100, 200), back_rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, back_rect, 2, border_radius=8)
        back_text = self.small_font.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        surface.blit(back_text, back_text_rect)


class ModeSelectScreen:
    def __init__(self, screen_width, screen_height, state_manager, settings):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.settings = settings
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(40)

        btn_width, btn_height = 250, 55
        center_x = screen_width // 2 - btn_width // 2
        start_y = screen_height // 2 - 150
        spacing = 70

        self.one_player_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "1 Player", self.font, action=self.open_board_select_1p
        )
        self.two_player_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "2 Player", self.font, action=self.open_board_select_2p
        )
        self.vs_ai_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "VS AI", self.font, action=self.open_difficulty
        )
        self.level_btn = Button(
            center_x, start_y + 3 * spacing, btn_width, btn_height,
            "Level Mode", self.font, action=self.start_level_mode
        )
        self.zen_btn = Button(
            center_x, start_y + 4 * spacing, btn_width, btn_height,
            "Zen", self.font, action=self.open_board_select_zen
        )
        self.back_btn = Button(
            center_x, start_y + 5 * spacing, btn_width, btn_height,
            "Back", self.font, action=self.go_back
        )

        self.buttons = [self.one_player_btn, self.two_player_btn, self.vs_ai_btn,
                        self.level_btn, self.zen_btn, self.back_btn]

    def open_board_select_1p(self):
        self.settings['game_mode'] = '1player'
        self.state_manager.change_state(BOARD_SELECT)

    def open_board_select_2p(self):
        self.settings['game_mode'] = '2player'
        self.state_manager.change_state(BOARD_SELECT)

    def open_board_select_zen(self):
        self.settings['game_mode'] = 'zen'
        self.state_manager.change_state(BOARD_SELECT)

    def start_level_mode(self):
        self.settings['game_mode'] = 'level'
        self.settings['current_level'] = 1
        config = LEVEL_CONFIGS[0]
        self.settings.update(config)
        self.state_manager.change_state(PLAYING)

    def open_difficulty(self):
        self.state_manager.change_state(DIFFICULTY)

    def go_back(self):
        self.state_manager.change_state(MENU)

    def update(self):
        for btn in self.buttons:
            btn.update()

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_back()
            return True
        return False

    def draw(self, surface):
        title = self.font.render("Select Game Mode", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 80))
        surface.blit(title, title_rect)
        for btn in self.buttons:
            btn.draw(surface)


class DifficultySelectScreen:
    def __init__(self, screen_width, screen_height, state_manager, settings):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.settings = settings
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(40)

        btn_width, btn_height = 250, 60
        center_x = screen_width // 2 - btn_width // 2
        start_y = screen_height // 2 - 80
        spacing = 80

        self.easy_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "Easy", self.font, action=lambda: self.select_difficulty("easy")
        )
        self.medium_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "Medium", self.font, action=lambda: self.select_difficulty("medium")
        )
        self.hard_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "Hard", self.font, action=lambda: self.select_difficulty("hard")
        )
        self.back_btn = Button(
            center_x, start_y + 3 * spacing, btn_width, btn_height,
            "Back", self.font, action=self.go_back
        )

        self.buttons = [self.easy_btn, self.medium_btn, self.hard_btn, self.back_btn]

    def select_difficulty(self, level):
        self.settings['ai_difficulty'] = level
        self.settings['game_mode'] = 'vsai'
        self.state_manager.change_state(PLAYING)

    def go_back(self):
        self.state_manager.change_state(MODE_SELECT)

    def update(self):
        for btn in self.buttons:
            btn.update()

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_back()
            return True
        return False

    def draw(self, surface):
        title = self.font.render("Select AI Difficulty", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 80))
        surface.blit(title, title_rect)
        for btn in self.buttons:
            btn.draw(surface)


class BoardSizeSelectScreen:
    def __init__(self, screen_width, screen_height, state_manager, settings):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.settings = settings
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(40)

        btn_width, btn_height = 300, 60
        center_x = screen_width // 2 - btn_width // 2
        start_y = screen_height // 2 - 120
        spacing = 90

        self.easy_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "Easy (4x3)", self.font, action=lambda: self.select_size("easy", 4, 3, 6)
        )
        self.medium_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "Medium (4x4)", self.font, action=lambda: self.select_size("medium", 4, 4, 8)
        )
        self.hard_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "Hard (5x6)", self.font, action=lambda: self.select_size("hard", 5, 6, 15)
        )
        self.back_btn = Button(
            center_x, start_y + 3 * spacing, btn_width, btn_height,
            "Back", self.font, action=self.go_back
        )

        self.buttons = [self.easy_btn, self.medium_btn, self.hard_btn, self.back_btn]

    def select_size(self, difficulty, cols, rows, pairs):
        self.settings['board_difficulty'] = difficulty
        self.settings['board_cols'] = cols
        self.settings['board_rows'] = rows
        self.settings['num_pairs'] = pairs
        self.state_manager.change_state(PLAYING)

    def go_back(self):
        self.state_manager.change_state(MODE_SELECT)

    def update(self):
        for btn in self.buttons:
            btn.update()

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_back()
            return True
        return False

    def draw(self, surface):
        title = self.font.render("Select Board Size", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 80))
        surface.blit(title, title_rect)
        for btn in self.buttons:
            btn.draw(surface)


class LevelCompleteScreen:
    def __init__(self, screen_width, screen_height, state_manager, settings):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.settings = settings
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(40)
        self.big_font = load_custom_font(80)
        self.star_font = load_custom_font(100)

        btn_width, btn_height = 200, 55
        center_x = screen_width // 2 - btn_width // 2
        start_y = screen_height // 2 + 120
        spacing = 75

        self.next_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "Next Level", self.font, action=self.next_level
        )
        self.retry_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "Retry", self.font, action=self.retry_level
        )
        self.menu_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "Main Menu", self.font, action=self.go_menu
        )

        self.buttons = [self.next_btn, self.retry_btn, self.menu_btn]

        self.level_data = {}
        self.stars = 0
        self.is_final_level = False

    def set_level_data(self, level, moves, time_elapsed, num_pairs, is_final=False):
        self.level_data = {
            'level': level,
            'moves': moves,
            'time': time_elapsed,
            'num_pairs': num_pairs
        }
        par_moves = num_pairs + 2
        if moves <= par_moves:
            self.stars = 3
        elif moves <= par_moves * 2:
            self.stars = 2
        else:
            self.stars = 1
        self.is_final_level = is_final

        if self.is_final_level:
            self.next_btn.text = "You Win!"
        else:
            self.next_btn.text = "Next Level"

    def next_level(self):
        if self.is_final_level:
            self.state_manager.change_state(MENU)
        else:
            current = self.settings.get('current_level', 1)
            next_level = current + 1
            self.settings['current_level'] = next_level
            if next_level <= len(LEVEL_CONFIGS):
                self.settings.update(LEVEL_CONFIGS[next_level - 1])
            self.state_manager.change_state(PLAYING)

    def retry_level(self):
        self.state_manager.change_state(PLAYING)

    def go_menu(self):
        self.state_manager.change_state(MENU)

    def update(self):
        for btn in self.buttons:
            btn.update()

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def draw(self, surface):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((5, 10, 25, 180))
        surface.blit(overlay, (0, 0))

        level = self.level_data.get('level', 1)
        title = self.big_font.render(f"Level {level} Complete!", True, (255, 255, 0))
        title_rect = title.get_rect(center=(self.screen_width // 2, 80))
        surface.blit(title, title_rect)

        star_text = "★" * self.stars + "☆" * (3 - self.stars)
        star_surf = self.star_font.render(star_text, True, (255, 215, 0))
        star_rect = star_surf.get_rect(center=(self.screen_width // 2, 180))
        surface.blit(star_surf, star_rect)

        moves = self.level_data.get('moves', 0)
        time_el = self.level_data.get('time', 0)
        mins = int(time_el // 60)
        secs = int(time_el % 60)

        info_font = self.small_font
        y = 270
        moves_surf = info_font.render(f"Moves: {moves}", True, WHITE)
        surface.blit(moves_surf, moves_surf.get_rect(center=(self.screen_width // 2, y)))
        y += 45
        time_surf = info_font.render(f"Time: {mins:02d}:{secs:02d}", True, WHITE)
        surface.blit(time_surf, time_surf.get_rect(center=(self.screen_width // 2, y)))

        for btn in self.buttons:
            btn.draw(surface)


class LeaderboardScreen:
    def __init__(self, screen_width, screen_height, state_manager):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state_manager = state_manager
        self.font = load_custom_font(60)
        self.small_font = load_custom_font(30)
        self.tiny_font = load_custom_font(24)

        self.back_btn = Button(
            screen_width // 2 - 100, screen_height - 80, 200, 50,
            "Back", self.font, action=self.go_back
        )

        self.categories = [
            ("1 Player - Easy", "1player_6"),
            ("1 Player - Medium", "1player_8"),
            ("1 Player - Hard", "1player_15"),
            ("Level Mode", "level"),
        ]
        self.selected_idx = 0

    def go_back(self):
        self.state_manager.change_state(MENU)

    def update(self):
        self.back_btn.update()

    def handle_event(self, event):
        if self.back_btn.handle_event(event):
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.go_back()
                return True
            elif event.key == pygame.K_UP:
                self.selected_idx = (self.selected_idx - 1) % len(self.categories)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_idx = (self.selected_idx + 1) % len(self.categories)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            y_start = 150
            for i in range(len(self.categories)):
                cat_rect = pygame.Rect(50, y_start + i * 40, 250, 35)
                if cat_rect.collidepoint(event.pos):
                    self.selected_idx = i
                    return True
        return False

    def draw(self, surface):
        from highscores import get_top_scores

        title = self.font.render("High Scores", True, (255, 255, 0))
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)

        cat_label = self.small_font.render("Mode:", True, WHITE)
        surface.blit(cat_label, (50, 115))

        y_start = 150
        for i, (label, key) in enumerate(self.categories):
            color = (100, 150, 255) if i == self.selected_idx else (180, 180, 180)
            text = self.small_font.render(label, True, color)
            surface.blit(text, (50, y_start + i * 40))
            if i == self.selected_idx:
                pygame.draw.rect(surface, color, (45, y_start + i * 40 - 2, 260, 35), 2, border_radius=5)

        _, selected_key = self.categories[self.selected_idx]
        scores = get_top_scores(selected_key.split('_')[0] if '_' not in selected_key else selected_key.rsplit('_', 1)[0],
                                 selected_key.split('_')[-1] if '_' in selected_key else '')

        if selected_key == "level":
            all_scores = {}
            from highscores import load_scores
            raw = load_scores()
            for k, v in raw.items():
                if k.startswith("level"):
                    all_scores[k] = v
            scores = []
            for k in sorted(all_scores.keys()):
                scores.extend(all_scores[k])
            scores.sort(key=lambda x: (-x.get('score', 0), x.get('moves', 9999)))
            scores = scores[:10]

        header_x = 350
        col_offsets = [0, 150, 300, 430]
        headers = ["Score", "Moves", "Time", "Date"]
        for j, h in enumerate(headers):
            hsurf = self.tiny_font.render(h, True, (200, 200, 200))
            surface.blit(hsurf, (header_x + col_offsets[j], 115))

        for i in range(10):
            y = 155 + i * 35
            rank_text = f"{i+1}."
            rank_surf = self.tiny_font.render(rank_text, True, (180, 180, 180))
            surface.blit(rank_surf, (300, y))

            if i < len(scores):
                s = scores[i]
                vals = [
                    str(s.get('score', 0)),
                    str(s.get('moves', 0)),
                    f"{int(s.get('time', 0))//60:02d}:{int(s.get('time', 0))%60:02d}",
                    s.get('date', '')
                ]
                for j, val in enumerate(vals):
                    vsurf = self.tiny_font.render(val, True, WHITE)
                    surface.blit(vsurf, (header_x + col_offsets[j], y))
            else:
                empty = self.tiny_font.render("---", True, (100, 100, 100))
                surface.blit(empty, (header_x, y))

        self.back_btn.draw(surface)