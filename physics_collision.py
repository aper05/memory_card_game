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