import pygame
import sys
import random
import os

# 1. Initialize Pygame & Audio Mixer
pygame.init()
pygame.mixer.init()

# 2. Window Geometry Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Swapped: 2D Memory Game")

# 3. Enhanced 2D Color Palette
FEATHER_GREEN = (46, 175, 70)    
SUN_GOLD = (235, 190, 35)        
DARK_CANOPY = (15, 45, 20)       
WHITE = (255, 255, 255)
GRAY = (85, 100, 85)
RED = (230, 40, 40)
CARD_BACK_BG = (20, 50, 25)      

# 4. Game State Machinery
game_state = "MENU"              
difficulty = "Normal"            
bgm_enabled = True
sfx_enabled = True

# 📐 PERFECT CARD FIT DIMENSIONS 
CARD_WIDTH = 150
CARD_HEIGHT = 130
GAP = 15

# 5. Typography Engine
font_title = pygame.font.SysFont("impact", 55)          
font_ui = pygame.font.SysFont("arial", 22, bold=True)    
font_inst = pygame.font.SysFont("arial", 18)
font_card_back = pygame.font.SysFont("impact", 50) 

# --- 🖼️ BACKGROUND LOADING ---
BACKGROUND_IMG = None
if os.path.exists("background.jpg"):
    try:
        BACKGROUND_IMG = pygame.image.load("background.jpg")
        BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print(f"Error loading background image: {e}")

# --- 🔊 AUDIO INFRASTRUCTURE ---
try:
    pygame.mixer.music.load("nature_bgm.mp3")
    pygame.mixer.music.play(-1) 
    pygame.mixer.music.set_volume(0.2)
    flip_sound = pygame.mixer.Sound("flip_sfx.wav")
    flip_sound.set_volume(0.5)
except Exception as e:
    print(f"❌ AUDIO ERROR: {e}")
    flip_sound = None
# --- 🖼️ BIRD PHOTO ASSET SCALING ---
BIRD_PHOTOS = []
for i in range(8):
    img_loaded = False
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]:
        filename = f"bird{i}{ext}"
        if os.path.exists(filename):
            try:
                img = pygame.image.load(filename)
                img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                BIRD_PHOTOS.append(img)
                img_loaded = True
                break
            except:
                pass
                
    if not img_loaded:
        surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        surf.fill((40, 90, i * 20 + 40))
        BIRD_PHOTOS.append(surf)

class Card:
    def __init__(self, index, x, y):
        self.index = index            
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.is_flipped = False
        self.is_matched = False

cards = []
selected_cards = []
mismatch_timer = 0
victory_timer = 0  # ⏳ Keeps track of the end-of-level display break
round_start_time = 0
total_round_duration = 0 
pause_anchor = 0

def start_new_game():
    global cards, selected_cards, round_start_time, total_round_duration, victory_timer
    cards = []
    selected_cards = []
    victory_timer = 0
    
    if difficulty == "Easy":
        rows, cols = 2, 4 
        total_round_duration = 45000  
    elif difficulty == "Normal":
        rows, cols = 3, 4  
        total_round_duration = 60000 
    elif difficulty == "Hard":
        rows, cols = 4, 4
        total_round_duration = 40000

    num_pairs = (rows * cols) // 2
    card_indices = list(range(num_pairs)) * 2
    random.shuffle(card_indices)     
    
    grid_w = (cols * CARD_WIDTH) + ((cols - 1) * GAP)
    grid_h = (rows * CARD_HEIGHT) + ((rows - 1) * GAP)
    
    start_x = (SCREEN_WIDTH - grid_w) // 2
    start_y = ((SCREEN_HEIGHT - grid_h) // 2) + 40
    
    idx = 0
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (CARD_WIDTH + GAP)
            y = start_y + r * (CARD_HEIGHT + GAP)
            cards.append(Card(card_indices[idx], x, y))
            idx += 1
            
    round_start_time = pygame.time.get_ticks()

def advance_difficulty():
    global difficulty, game_state, round_start_time
    if difficulty == "Easy": 
        difficulty = "Normal"
        start_new_game()
        return
    elif difficulty == "Normal":
        difficulty = "Hard"
        start_new_game()
        return
    elif difficulty == "Hard":
        difficulty = "Done"
        game_state = "VICTORY"
        return

def draw_feather_canopy():
    pygame.draw.rect(screen, DARK_CANOPY, (0, 0, SCREEN_WIDTH, 60))
    feather_width = 50
    for x in range(-10, screen.get_width() + 20, 30):
        p1 = [(x, 35), (x + feather_width//2, 55), (x + feather_width, 35)]
        pygame.draw.polygon(screen, (20, 70, 30), p1)
        p2 = [(x + 5, 32), (x + feather_width//2, 50), (x + feather_width - 5, 32)]
        pygame.draw.polygon(screen, FEATHER_GREEN, p2)

# Global UI Rectangles
btn_settings = pygame.Rect(20, 15, 45, 38)
btn_pause = pygame.Rect(SCREEN_WIDTH - 65, 15, 45, 38)
center_x = SCREEN_WIDTH // 2
center_y = SCREEN_HEIGHT // 2
btn_close_setting = pygame.Rect(center_x + 120, 155, 25, 25)

# Dedicated UI Buttons for Post-game States
btn_retry_gameover = pygame.Rect(center_x - 75, 390, 150, 60)
btn_restart_victory = pygame.Rect(center_x - 75, 390, 150, 60)

# Main Runtime Loop
running = True
while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    current_time = pygame.time.get_ticks()
    
    # Freeze countdown bar during victory celebration pause
    if game_state == "PLAYING" and victory_timer == 0:
        elapsed = current_time - round_start_time
        if total_round_duration - elapsed <= 0:
            game_state = "GAMEOVER"

    # Process mismatch reset delay
    if game_state == "PLAYING" and mismatch_timer > 0 and current_time > mismatch_timer:
        for card in selected_cards:
            card.is_flipped = False
        selected_cards = []
        mismatch_timer = 0

    # Process victory display delay before progressing levels
    if game_state == "PLAYING" and victory_timer > 0:
        if current_time >= victory_timer:
            victory_timer = 0
            advance_difficulty()

    if bgm_enabled and not pygame.mixer.music.get_busy():
        pygame.mixer.music.unpause()
    elif not bgm_enabled and pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()

    for event in range(1): # Mock structure check to mirror clean polling execution
        pass

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click

                # 1. Menu Controls Branch
                if game_state == "MENU":
                    if (center_x - 180) - 65 <= mouse_x <= (center_x - 180) + 65 and 390 <= mouse_y <= 440: 
                        difficulty = "Easy"
                    elif center_x - 65 <= mouse_x <= center_x + 65 and 390 <= mouse_y <= 440: 
                        difficulty = "Normal"
                    elif (center_x + 180) - 65 <= mouse_x <= (center_x + 180) + 65 and 390 <= mouse_y <= 440: 
                        difficulty = "Hard"
                    elif (center_x - 75) <= mouse_x <= (center_x + 75) and 500 <= mouse_y <= 560:
                        game_state = "INSTRUCTIONS"

                # 2. Instruction Controls Branch
                elif game_state == "INSTRUCTIONS":
                    inst_btn = pygame.Rect(center_x - 75, 510, 150, 60)
                    if inst_btn.collidepoint(mouse_x, mouse_y):
                        start_new_game()
                        game_state = "PLAYING"
            
                # 3. Active Gameplay Controls Branch
                elif game_state == "PLAYING" and victory_timer == 0:
                    if btn_settings.collidepoint(mouse_x, mouse_y):
                        pause_anchor = pygame.time.get_ticks()
                        game_state = "SETTINGS"
                    elif btn_pause.collidepoint(mouse_x, mouse_y):
                        pause_anchor = pygame.time.get_ticks()
                        game_state = "PAUSED"
   
                    elif len(selected_cards) < 2:
                        for card in cards:
                            if card.rect.collidepoint(mouse_x, mouse_y) and not card.is_flipped and not card.is_matched:
                                card.is_flipped = True
                                selected_cards.append(card)
                                if flip_sound and sfx_enabled: flip_sound.play()
                                
                                if len(selected_cards) == 2:
                                    if selected_cards[0].index == selected_cards[1].index:
                                        selected_cards[0].is_matched = True
                                        selected_cards[1].is_matched = True
                                        selected_cards = []
                                        if all(c.is_matched for c in cards):
                                            victory_timer = pygame.time.get_ticks() + 1200
                                    else:
                                        delay = 400 if difficulty == "Hard" else 1000
                                        mismatch_timer = pygame.time.get_ticks() + delay

                # 4. Settings Overlay Menu Branch
                elif game_state == "SETTINGS":
                    bgm_rect = pygame.Rect(center_x - 90, 275, 180, 40)
                    sfx_rect = pygame.Rect(center_x - 90, 335, 180, 40)
                    menu_rect = pygame.Rect(center_x - 90, 395, 180, 40)
                    restart_rect = pygame.Rect(center_x - 90, 215, 180, 40)

                    if btn_close_setting.collidepoint(mouse_x, mouse_y):
                        round_start_time += (pygame.time.get_ticks() - pause_anchor) 
                        game_state = "PLAYING"
                    elif restart_rect.collidepoint(mouse_x, mouse_y):
                        start_new_game()
                        game_state = "PLAYING"
                    elif bgm_rect.collidepoint(mouse_x, mouse_y):
                        bgm_enabled = not bgm_enabled
                    elif sfx_rect.collidepoint(mouse_x, mouse_y):
                        sfx_enabled = not sfx_enabled
                    elif menu_rect.collidepoint(mouse_x, mouse_y):
                        game_state = "MENU"

                # 5. Pause Screen Branch
                elif game_state == "PAUSED":
                    resume_btn = pygame.Rect(center_x - 75, 360, 150, 60)
                    if btn_pause.collidepoint(mouse_x, mouse_y) or resume_btn.collidepoint(mouse_x, mouse_y):
                        round_start_time += (pygame.time.get_ticks() - pause_anchor) 
                        game_state = "PLAYING"

                # 6. Post-Game State Branch (Game Over)
                elif game_state == "GAMEOVER":
                    if btn_retry_gameover.collidepoint(mouse_x, mouse_y):
                        difficulty = "Normal"
                        start_new_game()
                        game_state = "MENU"

                # 7. Post-Game State Branch (Victory)
                elif game_state == "VICTORY":
                    if btn_restart_victory.collidepoint(mouse_x, mouse_y):
                        difficulty = "Normal"
                        start_new_game()
                        game_state = "MENU"

    # --- RENDER ENGINE ---
    if BACKGROUND_IMG:
        screen.blit(BACKGROUND_IMG, (0, 0))
    else:
        screen.fill((25, 55, 30))

    if game_state in ["PLAYING", "SETTINGS", "PAUSED"]:
        draw_feather_canopy()

    if game_state == "MENU":
        shadow = font_title.render("SWAPPED MATCH", True, (10, 30, 10))
        screen.blit(shadow, shadow.get_rect(center=(center_x + 3, 243)))
        title_text = font_title.render("SWAPPED MATCH", True, SUN_GOLD)
        screen.blit(title_text, title_text.get_rect(center=(center_x, 240)))
        
        for text, cx, cy in [("EASY", center_x - 180, 415), ("NORMAL", center_x, 415), ("HARD", center_x + 180, 415)]:
            b_color = SUN_GOLD if difficulty == text.capitalize() else DARK_CANOPY
            t_color = DARK_CANOPY if difficulty == text.capitalize() else WHITE
            pygame.draw.rect(screen, b_color, (cx-65, cy-25, 130, 50), border_radius=12)
            txt = font_ui.render(text, True, t_color)
            screen.blit(txt, txt.get_rect(center=(cx, cy)))

        play_btn = pygame.Rect(center_x - 75, 500, 150, 60)
        pygame.draw.rect(screen, DARK_CANOPY, play_btn, border_radius=15)
        pygame.draw.rect(screen, SUN_GOLD, play_btn, width=3, border_radius=15)
        txt_play = font_ui.render("PLAY", True, SUN_GOLD)
        screen.blit(txt_play, txt_play.get_rect(center=play_btn.center))
        
    elif game_state == "INSTRUCTIONS":
        panel_w, panel_h = 660, 320
        panel_rect = pygame.Rect(center_x - (panel_w // 2), 150, panel_w, panel_h)
        pygame.draw.rect(screen, DARK_CANOPY, panel_rect, border_radius=20)
        pygame.draw.rect(screen, SUN_GOLD, panel_rect, width=3, border_radius=20)
        
        head = font_ui.render("GAME INSTRUCTIONS / RULES", True, SUN_GOLD)
        screen.blit(head, head.get_rect(center=(center_x, 185)))
        
        rules = [
            "1. Easy Mode has 8 box cards. Normal has 12, Hard has 16.",
            "2. Click a card to flip it and reveal the hidden Swapped Movie character.",
            "3. Find the matching card. Mismatched cards flip back face down automatically.",
            "4. Challenge: Hard mode features a much faster card flip-back delay!",
            "5. Race against the clock! If the countdown bar reaches zero, you lose.",
            "6. Controls: Use top-left ⚙️ for volume/restart. Use top-right ⏸️ to pause game."
        ]
        curr_y = 225
        for rule in rules:
            r_txt = font_inst.render(rule, True, WHITE)
            screen.blit(r_txt, (center_x - 300, curr_y))
            curr_y += 32
            
        start_btn = pygame.Rect(center_x - 75, 510, 150, 60)
        pygame.draw.rect(screen, DARK_CANOPY, start_btn, border_radius=15)
        pygame.draw.rect(screen, SUN_GOLD, start_btn, width=3, border_radius=15)
        txt_start = font_ui.render("START", True, WHITE)
        screen.blit(txt_start, txt_start.get_rect(center=start_btn.center))
        
    elif game_state in ["PLAYING", "SETTINGS", "PAUSED"]:
        txt_level = font_ui.render(f"LEVEL: {difficulty.upper()}", True, SUN_GOLD)
        screen.blit(txt_level, (95, 22))
        
        if victory_timer > 0:
            time_pct = 1.0
        else:
            elapsed = current_time - round_start_time if game_state == "PLAYING" else pause_anchor - round_start_time
            time_pct = max(0.0, min(1.0, (total_round_duration - elapsed) / total_round_duration))
        
        timer_bar_width = 500
        timer_x = (SCREEN_WIDTH - timer_bar_width) // 2
        pygame.draw.rect(screen, SUN_GOLD, (timer_x, 20, timer_bar_width, 15), border_radius=2)
        
        bar_color = FEATHER_GREEN if time_pct > 0.3 else RED
        pygame.draw.rect(screen, bar_color, (timer_x, 25, int(timer_bar_width * time_pct), 20), border_radius=6)
        pygame.draw.rect(screen, SUN_GOLD, (timer_x, 25, timer_bar_width, 20), width=2, border_radius=6)
        
        pygame.draw.rect(screen, SUN_GOLD if game_state == "SETTINGS" else DARK_CANOPY, btn_settings, border_radius=6)
        txt_gear = font_ui.render("⚙️", True, WHITE if game_state != "SETTINGS" else DARK_CANOPY)
        screen.blit(txt_gear, txt_gear.get_rect(center=btn_settings.center))
        
        pygame.draw.rect(screen, SUN_GOLD if game_state == "PAUSED" else DARK_CANOPY, btn_pause, border_radius=6)
        txt_p_sym = font_ui.render("▶️" if game_state == "PAUSED" else "⏸️", True, WHITE)
        screen.blit(txt_p_sym, txt_p_sym.get_rect(center=btn_pause.center))
        
        for card in cards:
            if card.is_matched or card.is_flipped:
                screen.blit(BIRD_PHOTOS[card.index], card.rect.topleft)
                if card.is_matched:
                    pygame.draw.rect(screen, SUN_GOLD, card.rect, width=3, border_radius=6)
            else:
                pygame.draw.rect(screen, CARD_BACK_BG, card.rect, border_radius=8)
                pygame.draw.rect(screen, SUN_GOLD, card.rect, width=3, border_radius=8)
                inner_rect = card.rect.inflate(-12, -12)
                pygame.draw.rect(screen, FEATHER_GREEN, inner_rect, width=1, border_radius=4)
                q_text = font_card_back.render("?", True, SUN_GOLD)
                screen.blit(q_text, q_text.get_rect(center=card.rect.center))

        if game_state == "SETTINGS":
            dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 160))
            screen.blit(dim, (0,0))
            
            pygame.draw.rect(screen, DARK_CANOPY, (center_x - 150, 150, 300, 340), border_radius=15)
            pygame.draw.rect(screen, SUN_GOLD, (center_x - 150, 150, 300, 340), width=3, border_radius=15)
            
            pygame.draw.rect(screen, DARK_CANOPY, btn_close_setting, border_radius=4)
            txt_x = font_ui.render("X", True, RED)
            screen.blit(txt_x, txt_x.get_rect(center=btn_close_setting.center))
            
            title_s = font_ui.render("GAME SETTINGS", True, WHITE)
            screen.blit(title_s, title_s.get_rect(center=(center_x, 185)))
            
            # Restart
            r_rect = pygame.Rect(center_x - 90, 215, 180, 40)
            pygame.draw.rect(screen, GRAY, r_rect, border_radius=10)
            t_rest = font_ui.render("RESTART", True, WHITE)
            screen.blit(t_rest, t_rest.get_rect(center=r_rect.center))
            
            # BGM
            bgm_c = FEATHER_GREEN if bgm_enabled else GRAY
            bgm_rect = pygame.Rect(center_x - 90, 275, 180, 40)
            pygame.draw.rect(screen, bgm_c, bgm_rect, border_radius=10)
            t_bgm = font_ui.render("BGM: ON" if bgm_enabled else "BGM: OFF", True, DARK_CANOPY if bgm_enabled else WHITE)
            screen.blit(t_bgm, t_bgm.get_rect(center=bgm_rect.center))
            
            # SFX
            sfx_c = FEATHER_GREEN if sfx_enabled else GRAY
            sfx_rect = pygame.Rect(center_x - 90, 335, 180, 40)
            pygame.draw.rect(screen, sfx_c, sfx_rect, border_radius=10)
            t_sfx = font_ui.render("FLIP SFX: ON" if sfx_enabled else "FLIP SFX: OFF", True, DARK_CANOPY if sfx_enabled else WHITE)
            screen.blit(t_sfx, t_sfx.get_rect(center=sfx_rect.center))
            
            # Main Menu
            m_rect = pygame.Rect(center_x - 90, 395, 180, 40)
            pygame.draw.rect(screen, SUN_GOLD, m_rect, border_radius=10)
            t_menu = font_ui.render("MAIN MENU", True, DARK_CANOPY)
            screen.blit(t_menu, t_menu.get_rect(center=m_rect.center))

        elif game_state == "PAUSED":
            dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 180))
            screen.blit(dim, (0,0))
            
            t_pause = font_title.render("GAME PAUSED", True, WHITE)
            screen.blit(t_pause, t_pause.get_rect(center=(center_x, center_y - 40)))
            
            res_rect = pygame.Rect(center_x - 75, 360, 150, 60)
            pygame.draw.rect(screen, SUN_GOLD, res_rect, border_radius=15)
            t_res = font_ui.render("RESUME ▶️", True, DARK_CANOPY)
            screen.blit(t_res, t_res.get_rect(center=res_rect.center))

    elif game_state == "GAMEOVER":
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((20, 35, 20, 230))
        screen.blit(dim, (0,0))
        
        go_txt = font_title.render("GAME OVER", True, RED)
        screen.blit(go_txt, go_txt.get_rect(center=(center_x, center_y - 50)))
        
        lbl_txt = font_ui.render("You ran out of time!", True, WHITE)
        screen.blit(lbl_txt, lbl_txt.get_rect(center=(center_x, center_y + 5)))
        
        pygame.draw.rect(screen, SUN_GOLD, btn_retry_gameover, border_radius=15)
        t_retry = font_ui.render("TRY AGAIN", True, DARK_CANOPY)
        screen.blit(t_retry, t_retry.get_rect(center=btn_retry_gameover.center))

    elif game_state == "VICTORY":
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 50, 25, 235))
        screen.blit(dim, (0,0))

        v_text = font_title.render("CONGRATULATIONS!", True, SUN_GOLD)
        screen.blit(v_text, v_text.get_rect(center=(center_x, center_y - 80)))

        sub_text = font_ui.render("YOU PASSED THE GAME! 🎉🎉", True, WHITE)
        screen.blit(sub_text, sub_text.get_rect(center=(center_x, center_y - 10)))

        pygame.draw.rect(screen, SUN_GOLD, btn_restart_victory, border_radius=15)
        t_restart = font_ui.render("PLAY AGAIN", True, DARK_CANOPY)
        screen.blit(t_restart, t_restart.get_rect(center=btn_restart_victory.center))

    pygame.display.flip()

pygame.quit()
sys.exit()