import os
import sys
import math
import random
import pygame

# ------------- CONFIG BÁSICO -------------
os.environ["SDL_VIDEODRIVER"] = "windows"  # ajuda no VS Code/Windows
pygame.init()
pygame.mixer.init()

WIN_W, WIN_H = 800, 600
FPS = 60
win = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Maduro's Chase")
clock = pygame.time.Clock()

# ------------- ASSETS -------------
IMG = "images"
SND = "songs"

INTRO_IMG_FILE   = os.path.join(IMG, "game_intro.png")
GAMEOVER_IMG_FILE= os.path.join(IMG, "game_over.png")
MAZE_FILE        = os.path.join(IMG, "maze_map.png")
BARREL_FILE      = os.path.join(IMG, "barrel.png")

TRUMP_IDLE_F     = os.path.join(IMG, "trump_idle.png")
TRUMP_SHOT_F     = os.path.join(IMG, "trump_shot.png")
TRUMP_SHOT2_F    = os.path.join(IMG, "trump_shot2.png")

MADURO_IDLE_F    = os.path.join(IMG, "maduros_idle.png")
MADURO_WALK_F    = os.path.join(IMG, "maduros_walk.png")
MADURO_HIT_F     = os.path.join(IMG, "maduros_hit.png")

INTRO_MUSIC      = os.path.join(SND, "intro_song.mp3")
HIT_SOUND_F      = os.path.join(SND, "maduroscream.mp3")

# ------------- HELPERS -------------
def load_scaled(path, size=None, alpha=True):
    surf = pygame.image.load(path)
    surf = surf.convert_alpha() if alpha else surf.convert()
    if size:
        surf = pygame.transform.smoothscale(surf, size)
    return surf

def mask_from_black(surf, tol=25):
    """Gera máscara onde pixels ~pretos são parede."""
    return pygame.mask.from_threshold(surf, (0, 0, 0), (tol, tol, tol))

def is_area_free(mask, rect_w, rect_h, x, y):
    """True se a área (w,h) em (x,y) NÃO colide com paredes."""
    test_mask = pygame.mask.Mask((rect_w, rect_h), True)
    return mask.overlap_area(test_mask, (int(x), int(y))) == 0

def place_non_wall(mask, size, tries=2000, margin=10):
    w, h = size
    for _ in range(tries):
        x = random.randint(margin, WIN_W - w - margin)
        y = random.randint(margin, WIN_H - h - margin)
        if is_area_free(mask, w, h, x, y):
            return pygame.Rect(x, y, w, h)
    # fallback (centro) se não achar
    return pygame.Rect(WIN_W//2 - w//2, WIN_H//2 - h//2, w, h)

def move_with_collision(rect, mover_mask, dx, dy, maze_mask):
    """Move eixo a eixo; impede atravessar paredes."""
    # eixo X
    step_x = int(math.copysign(1, dx)) if dx != 0 else 0
    for _ in range(abs(int(dx))):
        test = rect.move(step_x, 0)
        if maze_mask.overlap(mover_mask, (test.x, test.y)) is None:
            rect = test
        else:
            break
    # eixo Y
    step_y = int(math.copysign(1, dy)) if dy != 0 else 0
    for _ in range(abs(int(dy))):
        test = rect.move(0, step_y)
        if maze_mask.overlap(mover_mask, (test.x, test.y)) is None:
            rect = test
        else:
            break
    # clampa na tela
    rect.x = max(0, min(WIN_W - rect.w, rect.x))
    rect.y = max(0, min(WIN_H - rect.h, rect.y))
    return rect

# ------------- CARREGAR IMAGENS -------------
intro_img    = load_scaled(INTRO_IMG_FILE, (WIN_W, WIN_H), alpha=False)
gameover_img = load_scaled(GAMEOVER_IMG_FILE, (WIN_W, WIN_H), alpha=False)

maze_img_raw = pygame.image.load(MAZE_FILE).convert()
maze_img     = pygame.transform.smoothscale(maze_img_raw, (WIN_W, WIN_H)).convert()
maze_mask    = mask_from_black(maze_img, tol=30)  # tolerância um pouco maior

barrel_img   = load_scaled(BARREL_FILE, (40, 40))
SCALE_CHAR   = (40, 40)
trump_idle   = load_scaled(TRUMP_IDLE_F, SCALE_CHAR)
trump_shot   = load_scaled(TRUMP_SHOT_F, SCALE_CHAR)
trump_shot2  = load_scaled(TRUMP_SHOT2_F, SCALE_CHAR)

maduro_idle  = load_scaled(MADURO_IDLE_F, SCALE_CHAR)
maduro_walk  = load_scaled(MADURO_WALK_F, SCALE_CHAR)
maduro_hit   = load_scaled(MADURO_HIT_F, SCALE_CHAR)

trump_mask   = pygame.mask.from_surface(trump_idle)
maduro_mask  = pygame.mask.from_surface(maduro_idle)

# ------------- SONS -------------
try:
    hit_snd = pygame.mixer.Sound(HIT_SOUND_F)
except Exception:
    hit_snd = None

# ------------- STATE MACHINE -------------
INTRO, GAMEPLAY, GAMEOVER = "intro", "gameplay", "gameover"
state = INTRO

# ------------- ENTIDADES -------------
BULLET_SPEED = 9
TRUMP_SPEED  = 4
MADURO_SPEED = 2

class Bullet:
    def __init__(self, x, y, target):
        self.x = float(x)
        self.y = float(y)
        dx = target[0] - x
        dy = target[1] - y
        dist = math.hypot(dx, dy) or 1.0
        self.vx = (dx / dist) * BULLET_SPEED
        self.vy = (dy / dist) * BULLET_SPEED
        self.w, self.h = 8, 4
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    def update(self, maze_mask):
        self.x += self.vx
        self.y += self.vy
        # colisão com paredes
        bmask = pygame.mask.Mask((self.w, self.h), True)
        if maze_mask.overlap_area(bmask, (int(self.x), int(self.y))) > 0:
            return False
        # fora da tela
        if (self.rect.right < 0 or self.rect.left > WIN_W or
            self.rect.bottom < 0 or self.rect.top > WIN_H):
            return False
        return True
    def draw(self, surf):
        pygame.draw.rect(surf, (255, 60, 60), self.rect)

def spawn_barrels(n=3):
    rects = []
    for _ in range(n):
        r = place_non_wall(maze_mask, barrel_img.get_size(), margin=12)
        rects.append(r)
    return rects

def reset_game():
    global trump_rect, maduro_rect, trump_img, maduro_img
    global bullets, barrels, winner, maduro_alive, last_shot_time

    trump_img = trump_idle
    maduro_img = maduro_walk

    trump_rect  = place_non_wall(maze_mask, trump_img.get_size(), margin=14)
    maduro_rect = place_non_wall(maze_mask, maduro_img.get_size(), margin=14)

    # Evita spawn colado
    while trump_rect.colliderect(maduro_rect):
        maduro_rect = place_non_wall(maze_mask, maduro_img.get_size(), margin=14)

    barrels = spawn_barrels(3)
    bullets = []
    winner = None
    maduro_alive = True
    last_shot_time = 0

# ------------- INTRO/GO SCREENS -------------
def show_intro():
    try:
        pygame.mixer.music.load(INTRO_MUSIC)
        pygame.mixer.music.play(-1)
    except Exception:
        pass

    title_font = pygame.font.SysFont("Arial", 56, bold=True)
    btn_font   = pygame.font.SysFont("Arial", 40, bold=True)
    tip_font   = pygame.font.SysFont("Arial", 22)

    title = title_font.render("Maduro's Chase", True, (255, 255, 255))
    btn_text = btn_font.render("Start Game", True, (255, 255, 255))
    btn_rect = btn_text.get_rect(center=(WIN_W//2, WIN_H//2 + 120))
    pad = 30

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                pygame.mixer.music.stop()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect.inflate(pad*2, pad*2).collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    return

        win.blit(intro_img, (0, 0))
        win.blit(title, (WIN_W//2 - title.get_width()//2, 80))

        hover = btn_rect.inflate(pad*2, pad*2).collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(win, (0, 160, 0) if not hover else (0, 200, 0),
                         btn_rect.inflate(pad*2, pad*2), border_radius=16)
        win.blit(btn_text, btn_rect)

        tip = tip_font.render("Pressione ESPAÇO ou clique em Start Game", True, (255, 255, 0))
        win.blit(tip, (WIN_W//2 - tip.get_width()//2, btn_rect.bottom + 20))
        pygame.display.update()

def show_gameover():
    font = pygame.font.SysFont("Arial", 26, bold=True)
    prompt = font.render("Pressione ENTER para reiniciar", True, (255, 255, 255))
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return
        win.blit(gameover_img, (0, 0))
        win.blit(prompt, (WIN_W//2 - prompt.get_width()//2, WIN_H - 60))
        pygame.display.update()

# ------------- LÓGICA IA MADURO -------------
def step_towards_with_collision(src_rect, target_pos, speed, mover_mask, maze_mask):
    """Anda rumo ao alvo; tenta X->Y, se travar tenta Y->X, depois tenta contornar."""
    tx, ty = target_pos
    vx = tx - src_rect.centerx
    vy = ty - src_rect.centery
    if vx == 0 and vy == 0:
        return src_rect

    dist = math.hypot(vx, vy) or 1.0
    # passo inteiro pra evitar erro de arredondamento com a máscara
    dx = int(round((vx / dist) * speed))
    dy = int(round((vy / dist) * speed))

    old = src_rect.copy()

    # 1) tenta X depois Y
    src_rect = move_with_collision(src_rect, mover_mask, dx, 0, maze_mask)
    src_rect = move_with_collision(src_rect, mover_mask, 0, dy, maze_mask)
    if src_rect.topleft != old.topleft:
        return src_rect

    # 2) tenta Y depois X
    src_rect = old
    src_rect = move_with_collision(src_rect, mover_mask, 0, dy, maze_mask)
    src_rect = move_with_collision(src_rect, mover_mask, dx, 0, maze_mask)
    if src_rect.topleft != old.topleft:
        return src_rect

    # 3) tenta contornar (perpendicular)
    src_rect = old
    # escolhe uma perpendicular aleatória
    alt = random.choice([(speed, 0), (-speed, 0), (0, speed), (0, -speed)])
    src_rect = move_with_collision(src_rect, mover_mask, alt[0], alt[1], maze_mask)
    return src_rect

# ------------- LOOP PRINCIPAL -------------
reset_game()

while True:
    if state == INTRO:
        show_intro()
        reset_game()
        state = GAMEPLAY

    elif state == GAMEPLAY:
        while state == GAMEPLAY:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not winner:
                    # tiro do Trump na direção do clique
                    bx, by = trump_rect.center
                    bullets.append(Bullet(bx, by, event.pos))
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and winner:
                    reset_game()

            # --- INPUT TRUMP (WASD) ---
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_d] - keys[pygame.K_a]) * TRUMP_SPEED
            dy = (keys[pygame.K_s] - keys[pygame.K_w]) * TRUMP_SPEED
            trump_rect = move_with_collision(trump_rect, trump_mask, dx, dy, maze_mask)

            # --- IA MADURO (persegue barril mais próximo) ---
            if maduro_alive and not winner and barrels:
                # alvo: barril mais próximo
                target = min(barrels, key=lambda br: (maduro_rect.centerx - br.centerx)**2 + (maduro_rect.centery - br.centery)**2)
                maduro_rect = step_towards_with_collision(
                    maduro_rect, target.center, MADURO_SPEED, maduro_mask, maze_mask
                )
                # se encostar em QUALQUER barril -> GAME OVER
                for br in barrels:
                    if maduro_rect.colliderect(br):
                        state = GAMEOVER
                        break
                if state == GAMEOVER:
                    break

            # --- BALAS ---
            for b in bullets[:]:
                if not b.update(maze_mask):
                    bullets.remove(b)
                    continue
                # acertou Maduro?
                if maduro_alive and b.rect.colliderect(maduro_rect):
                    maduro_alive = False
                    if hit_snd:
                        hit_snd.play()
                    bullets.remove(b)
                    # trava sprite de hit
                    winner = "Trump"
                    continue

            # --- DESENHO ---
            win.blit(maze_img, (0, 0))

            # barris
            for br in barrels:
                win.blit(barrel_img, br)

            # personagens (Trump sempre aparece!)
            win.blit(trump_idle, trump_rect)
            if maduro_alive:
                win.blit(maduro_walk, maduro_rect)
            else:
                win.blit(maduro_hit, maduro_rect)

            # balas
            for b in bullets:
                b.draw(win)

            # HUD
            font = pygame.font.SysFont("Arial", 22, bold=True)
            hud = font.render("WASD: mover | Clique: atirar | R: reiniciar (após vitória)", True, (255, 255, 255))
            win.blit(hud, (10, 8))

            if winner:
                big = pygame.font.SysFont("Arial", 40, bold=True)
                msg = big.render(f"{winner} venceu!", True, (255, 230, 0))
                win.blit(msg, (WIN_W//2 - msg.get_width()//2, 40))

            pygame.display.update()

    elif state == GAMEOVER:
        show_gameover()
        state = INTRO
