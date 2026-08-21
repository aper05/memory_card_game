import pygame
import os
import time
from .asset_state import StateManager, AssetManager, SoundManager, MENU, PLAYING, SETTINGS, MODE_SELECT, DIFFICULTY, BOARD_SELECT, LEVEL_COMPLETE, LEADERBOARD, resource_path
from .ui_controls import MainMenu, SettingsScreen, ModeSelectScreen, DifficultySelectScreen, BoardSizeSelectScreen, LevelCompleteScreen, LeaderboardScreen, LEVEL_CONFIGS
from .game import Game
from .backgrounds import create_menu_background

VIRTUAL_WIDTH = 1280
VIRTUAL_HEIGHT = 720


def main():
    pygame.init()
    pygame.mixer.init()

    from . import asset_state
    asset_state.sound_manager = SoundManager()
    sound_manager = asset_state.sound_manager
    sound_manager.set_volume(25)
    sound_manager.play_music()

    screen = pygame.display.set_mode((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Memory Card Game")
    clock = pygame.time.Clock()

    virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    game_settings = {'volume': 25}
    state_manager = StateManager(MENU)
    asset_manager = AssetManager()

    base_dir = os.path.dirname(__file__)
    menu_bg = create_menu_background(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

    main_menu = MainMenu(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager)
    settings_screen = SettingsScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager, game_settings)
    mode_select_screen = ModeSelectScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager, game_settings)
    difficulty_select_screen = DifficultySelectScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager, game_settings)
    board_select_screen = BoardSizeSelectScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager, game_settings)
    level_complete_screen = LevelCompleteScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager, game_settings)
    leaderboard_screen = LeaderboardScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, state_manager)

    current_game = None
    running = True

    def get_scaled_rect():
        real_w, real_h = screen.get_size()
        scale = min(real_w / VIRTUAL_WIDTH, real_h / VIRTUAL_HEIGHT)
        scaled_w = int(VIRTUAL_WIDTH * scale)
        scaled_h = int(VIRTUAL_HEIGHT * scale)
        x = (real_w - scaled_w) // 2
        y = (real_h - scaled_h) // 2
        return pygame.Rect(x, y, scaled_w, scaled_h)

    while running:
        real_w, real_h = screen.get_size()
        dest_rect = get_scaled_rect()
        scale_x = VIRTUAL_WIDTH / dest_rect.width
        scale_y = VIRTUAL_HEIGHT / dest_rect.height
        offset_x = dest_rect.x
        offset_y = dest_rect.y

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                virtual_x = int((event.pos[0] - offset_x) * scale_x)
                virtual_y = int((event.pos[1] - offset_y) * scale_y)
                virtual_pos = (max(0, min(VIRTUAL_WIDTH-1, virtual_x)),
                               max(0, min(VIRTUAL_HEIGHT-1, virtual_y)))
                scaled_event = pygame.event.Event(event.type, {
                    'pos': virtual_pos,
                    'button': event.button if hasattr(event, 'button') else 0,
                    'touch': getattr(event, 'touch', False),
                    'window': event.window if hasattr(event, 'window') else None,
                })
            else:
                scaled_event = event

            if state_manager.current_state == MENU:
                main_menu.handle_event(scaled_event)
            elif state_manager.current_state == SETTINGS:
                settings_screen.handle_event(scaled_event)
            elif state_manager.current_state == MODE_SELECT:
                mode_select_screen.handle_event(scaled_event)
            elif state_manager.current_state == DIFFICULTY:
                difficulty_select_screen.handle_event(scaled_event)
            elif state_manager.current_state == BOARD_SELECT:
                board_select_screen.handle_event(scaled_event)
            elif state_manager.current_state == LEVEL_COMPLETE:
                level_complete_screen.handle_event(scaled_event)
            elif state_manager.current_state == LEADERBOARD:
                leaderboard_screen.handle_event(scaled_event)
            elif state_manager.current_state == PLAYING:
                if current_game is not None:
                    current_game.handle_event(scaled_event)

        if state_manager.current_state == PLAYING and current_game is None:
            current_game = Game(virtual_screen, game_settings, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        if state_manager.current_state == MENU:
            main_menu.update()
        elif state_manager.current_state == SETTINGS:
            settings_screen.update()
        elif state_manager.current_state == MODE_SELECT:
            mode_select_screen.update()
        elif state_manager.current_state == DIFFICULTY:
            difficulty_select_screen.update()
        elif state_manager.current_state == BOARD_SELECT:
            board_select_screen.update()
        elif state_manager.current_state == LEVEL_COMPLETE:
            level_complete_screen.update()
        elif state_manager.current_state == LEADERBOARD:
            leaderboard_screen.update()

        if state_manager.current_state == PLAYING and current_game:
            current_game.update()

            if current_game.game_over and current_game.game_over_shown:
                if game_settings.get('game_mode') == 'level':
                    current_level = game_settings.get('current_level', 1)
                    is_final = current_level >= len(LEVEL_CONFIGS)
                    level_complete_screen.set_level_data(
                        current_level,
                        current_game.moves,
                        time.time() - current_game.start_time,
                        game_settings.get('num_pairs', 15),
                        is_final=is_final
                    )
                    current_game = None
                    state_manager.change_state(LEVEL_COMPLETE)
                    continue

            if current_game and current_game.quit_to_menu:
                current_game = None
                state_manager.change_state(MENU)

        if state_manager.current_state == PLAYING and current_game is None and game_settings.get('game_mode') == 'level':
            current_level = game_settings.get('current_level', 1)
            if 1 <= current_level <= len(LEVEL_CONFIGS):
                config = LEVEL_CONFIGS[current_level - 1]
                game_settings.update(config)

        dt = clock.get_time() / 1000.0
        menu_bg.update(dt)
        menu_bg.draw(virtual_screen)
        if state_manager.current_state == MENU:
            main_menu.draw(virtual_screen)
        elif state_manager.current_state == SETTINGS:
            settings_screen.draw(virtual_screen)
        elif state_manager.current_state == MODE_SELECT:
            mode_select_screen.draw(virtual_screen)
        elif state_manager.current_state == DIFFICULTY:
            difficulty_select_screen.draw(virtual_screen)
        elif state_manager.current_state == BOARD_SELECT:
            board_select_screen.draw(virtual_screen)
        elif state_manager.current_state == LEVEL_COMPLETE:
            level_complete_screen.draw(virtual_screen)
        elif state_manager.current_state == LEADERBOARD:
            leaderboard_screen.draw(virtual_screen)
        elif state_manager.current_state == PLAYING and current_game:
            current_game.draw()

        screen.fill((0, 0, 0))
        scaled_surface = pygame.transform.scale(virtual_screen, dest_rect.size)
        screen.blit(scaled_surface, dest_rect.topleft)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
