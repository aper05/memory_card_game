import pygame
import time
from asset_state import MENU, SETTINGS, PLAYING, MODE_SELECT, DIFFICULTY, load_custom_font
import asset_state

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (180, 180, 180)
DARK_GREY = (100, 100, 100)
LIGHT_BLUE = (100, 150, 255)

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
        pygame.draw.rect(surface, BLACK, draw_rect, 2, border_radius=10)

        # Scale text accordingly
        text_surf = self.font.render(self.text, True, BLACK)
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
        start_y = screen_height // 2 - 60
        spacing = 80

        self.start_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "Play", self.font, action=self.start_game
        )
        self.settings_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "Settings", self.font, action=self.open_settings
        )
        self.quit_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "Quit", self.font, action=self.quit_game
        )
        self.buttons = [self.start_btn, self.settings_btn, self.quit_btn]

    def start_game(self):
        self.state_manager.change_state(MODE_SELECT)

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
            "1 Player: Score as many points as possible in 120 seconds.",
            "2 Player: Take turns. The player with the most matches wins.",
            "VS AI: Compete against the computer. Difficulty affects AI memory.",
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

        btn_width, btn_height = 250, 60
        center_x = screen_width // 2 - btn_width // 2
        start_y = screen_height // 2 - 100
        spacing = 80

        self.one_player_btn = Button(
            center_x, start_y, btn_width, btn_height,
            "1 Player", self.font, action=lambda: self.select_mode("1player")
        )
        self.two_player_btn = Button(
            center_x, start_y + spacing, btn_width, btn_height,
            "2 Player", self.font, action=lambda: self.select_mode("2player")
        )
        self.vs_ai_btn = Button(
            center_x, start_y + 2 * spacing, btn_width, btn_height,
            "VS AI", self.font, action=self.open_difficulty
        )
        self.back_btn = Button(
            center_x, start_y + 3 * spacing, btn_width, btn_height,
            "Back", self.font, action=self.go_back
        )

        self.buttons = [self.one_player_btn, self.two_player_btn, self.vs_ai_btn, self.back_btn]

    def select_mode(self, mode):
        self.settings['game_mode'] = mode
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