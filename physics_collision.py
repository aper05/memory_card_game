import time


def get_card_under_mouse(mouse_pos, cards):
    for card in cards:
        if not card.is_matched and not card.is_flipped:
            if card.rect.collidepoint(mouse_pos):
                return card
    return None


# ---------- Animation maths ----------

def flip_scale(elapsed, duration):
    if elapsed >= duration:
        return 1.0
    t = elapsed / duration
    if t < 0.5:
        return 1.0 - 2.0 * t
    else:
        return 2.0 * (t - 0.5)


def appear_scale(elapsed, duration):
    """Uniform scale factor for a card appearing (0.0 -> 1.0)."""
    if elapsed <= 0:
        return 0.0
    if elapsed >= duration:
        return 1.0
    return elapsed / duration


def disappear_scale(elapsed, duration):
    """Uniform scale factor for a card disappearing (1.0 -> 0.0)."""
    if elapsed <= 0:
        return 1.0
    if elapsed >= duration:
        return 0.0
    return 1.0 - (elapsed / duration)


def shuffle_scale(elapsed, duration):
    """Scale factor for cards during shuffle animation."""
    if elapsed <= 0:
        return 0.0
    if elapsed >= duration:
        return 1.0
    t = elapsed / duration
    t = t * t * (3 - 2 * t)
    return t


def shuffle_positions(cards, elapsed, duration, center_x, center_y, virtual_width, virtual_height):
    """Calculate shuffle positions for cards. Returns list of (x, y) positions."""
    if elapsed <= 0:
        return [(card.rect.x, card.rect.y) for card in cards]

    t = min(1.0, elapsed / duration)

    positions = []
    for i, card in enumerate(cards):
        if t < 0.4:
            phase_t = t / 0.4
            phase_t = phase_t * phase_t * (3 - 2 * phase_t)
            orig_x, orig_y = card.rect.x, card.rect.y
            offset_x = center_x - orig_x
            offset_y = center_y - orig_y
            spread = 80 * (i - len(cards) / 2)
            target_x = center_x + spread - card.rect.width // 2
            target_y = center_y - card.rect.height // 2
            x = orig_x + (target_x - orig_x) * phase_t
            y = orig_y + (target_y - orig_y) * phase_t
        elif t < 0.7:
            phase_t = (t - 0.4) / 0.3
            spread = 80 * (i - len(cards) / 2)
            x = center_x + spread - card.rect.width // 2
            y = center_y - card.rect.height // 2
            wobble = 15 * (1 - phase_t) * ((i * 7) % 3 - 1)
            y += wobble
        else:
            phase_t = (t - 0.7) / 0.3
            phase_t = phase_t * phase_t * (3 - 2 * phase_t)
            spread = 80 * (i - len(cards) / 2)
            x = center_x + spread - card.rect.width // 2
            y = center_y - card.rect.height // 2
            x = x + (card.rect.x - x) * phase_t
            y = y + (card.rect.y - y) * phase_t

        positions.append((x, y))

    return positions