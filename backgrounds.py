import pygame
import random
import math
import time


class Particle:
    def __init__(self, width, height, size_range=(1, 3), speed_range=(0.1, 0.4)):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.size = random.uniform(*size_range)
        self.speed_x = random.uniform(-speed_range[1], speed_range[1])
        self.speed_y = random.uniform(-speed_range[0], speed_range[0])
        self.base_alpha = random.randint(25, 90)
        self.twinkle_speed = random.uniform(0.5, 2.0)
        self.twinkle_offset = random.uniform(0, math.pi * 2)
        self.color_shift = random.uniform(-10, 10)
        self.width = width
        self.height = height

    def update(self, dt):
        self.x += self.speed_x * dt * 60
        self.y += self.speed_y * dt * 60
        if self.x < -5:
            self.x = self.width + 5
        elif self.x > self.width + 5:
            self.x = -5
        if self.y < -5:
            self.y = self.height + 5
        elif self.y > self.height + 5:
            self.y = -5

    def draw(self, surface, time_val):
        twinkle = math.sin(time_val * self.twinkle_speed + self.twinkle_offset)
        current_alpha = max(10, min(120, int(self.base_alpha + twinkle * 25)))
        r = max(0, min(255, int(180 + self.color_shift)))
        g = max(0, min(255, int(200 + self.color_shift)))
        b = 255
        ix, iy = int(self.x), int(self.y)

        if self.size > 2:
            glow_size = int(self.size * 3)
            glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            glow_alpha = max(5, current_alpha // 4)
            pygame.draw.circle(glow, (r, g, b, glow_alpha), (glow_size, glow_size), glow_size)
            pygame.draw.circle(glow, (r, g, b, current_alpha), (glow_size, glow_size), max(1, int(self.size)))
            surface.blit(glow, (ix - glow_size, iy - glow_size))
        else:
            circle_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (r, g, b, current_alpha), (2, 2), max(1, int(self.size)))
            surface.blit(circle_surf, (ix - 2, iy - 2))


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def create_gradient_surface(width, height, center_color, edge_color, center_radius=0.45):
    surface = pygame.Surface((width, height))
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt(cx * cx + cy * cy)
    center_dist = max_dist * center_radius

    num_steps = 120
    for i in range(num_steps):
        r_outer = (i / num_steps) * max_dist
        r_inner = ((i + 1) / num_steps) * max_dist
        t = i / (num_steps - 1)
        t = _smoothstep(t)
        cr = int(center_color[0] + (edge_color[0] - center_color[0]) * t)
        cg = int(center_color[1] + (edge_color[1] - center_color[1]) * t)
        cb = int(center_color[2] + (edge_color[2] - center_color[2]) * t)
        radius = int(r_outer) + 1
        pygame.draw.circle(surface, (cr, cg, cb), (cx, cy), radius)

    return surface


class GameBackground:
    def __init__(self, width, height, variant="menu"):
        self.width = width
        self.height = height
        self.variant = variant
        self.particles = []
        self.static_bg = None
        self.time_offset = random.uniform(0, 100)

        self._create_background()
        self._create_particles()

    def _get_colors(self):
        if self.variant == "menu":
            center = (18, 30, 70)
            edge = (5, 8, 20)
            particle_count = 60
        elif self.variant == "gameplay":
            center = (12, 22, 55)
            edge = (3, 5, 15)
            particle_count = 40
        elif self.variant == "overlay":
            center = (8, 12, 30)
            edge = (2, 3, 10)
            particle_count = 30
        else:
            center = (15, 25, 60)
            edge = (4, 6, 18)
            particle_count = 50
        return center, edge, particle_count

    def _create_background(self):
        center_color, edge_color, _ = self._get_colors()
        self.static_bg = create_gradient_surface(
            self.width, self.height,
            center_color, edge_color,
            center_radius=0.45
        )
        self._add_decorative_elements()

    def _add_decorative_elements(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        cx, cy = self.width // 2, self.height // 2
        glow_radius = int(min(self.width, self.height) * 0.35)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

        for r in range(glow_radius, 0, -3):
            alpha = int(8 * (1 - r / glow_radius))
            color = (30, 50, 100, alpha)
            pygame.draw.circle(glow_surf, color, (glow_radius, glow_radius), r)

        overlay.blit(glow_surf, (cx - glow_radius, cy - glow_radius))

        if self.variant == "menu":
            self._draw_suit_outlines(overlay)
        else:
            self._draw_geometric_pattern(overlay)

        self.static_bg.blit(overlay, (0, 0))

    def _draw_suit_outlines(self, surface):
        suits = ['\u2660', '\u2665', '\u2666', '\u2663']
        suit_positions = [
            (self.width * 0.12, self.height * 0.25),
            (self.width * 0.88, self.height * 0.25),
            (self.width * 0.12, self.height * 0.75),
            (self.width * 0.88, self.height * 0.75),
            (self.width * 0.5, self.height * 0.15),
            (self.width * 0.5, self.height * 0.85),
        ]

        try:
            suit_font = pygame.font.Font(None, 120)
        except Exception:
            return

        for i, (sx, sy) in enumerate(suit_positions):
            suit = suits[i % len(suits)]
            text = suit_font.render(suit, True, (255, 255, 255))
            text.set_alpha(12)
            rect = text.get_rect(center=(int(sx), int(sy)))
            surface.blit(text, rect)

    def _draw_geometric_pattern(self, surface):
        spacing = 80
        for x in range(0, self.width + spacing, spacing):
            for y in range(0, self.height, spacing):
                points = [
                    (x, y - spacing // 4),
                    (x + spacing // 4, y),
                    (x, y + spacing // 4),
                    (x - spacing // 4, y),
                ]
                pygame.draw.aalines(surface, (40, 60, 100), True, points)

    def _create_particles(self):
        _, _, count = self._get_colors()
        for _ in range(count):
            self.particles.append(Particle(self.width, self.height))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)

    def draw(self, target_surface):
        if self.static_bg:
            target_surface.blit(self.static_bg, (0, 0))
        current_time = time.time() + self.time_offset
        for p in self.particles:
            p.draw(target_surface, current_time)


def draw_text_panel(surface, rect, alpha=140, border_color=(60, 80, 140), border_alpha=40):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((5, 10, 25, alpha))
    pygame.draw.rect(panel, (*border_color, border_alpha), panel.get_rect(), 1, border_radius=6)
    surface.blit(panel, rect.topleft)


def draw_hud_background(surface, x, y, width, height, alpha=130):
    panel_rect = pygame.Rect(x - 8, y - 6, width + 16, height + 12)
    draw_text_panel(surface, panel_rect, alpha=alpha, border_color=(40, 60, 120), border_alpha=30)


def create_menu_background(width, height):
    return GameBackground(width, height, variant="menu")


_gameplay_bg_cache = {}

def create_gameplay_background(width, height):
    key = (width, height)
    if key not in _gameplay_bg_cache:
        _gameplay_bg_cache[key] = GameBackground(width, height, variant="gameplay")
    return _gameplay_bg_cache[key]
