import pygame
import random
import sys

# ----------------------------
# 設定
# ----------------------------
pygame.init()
WIDTH, HEIGHT = 900, 500
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("チャリ走風ランナー（Pygame）")

#背景画像の追加
BG_IMG = pygame.image.load("幕末維新電.png").convert()
BG_IMG = pygame.transform.scale(BG_IMG, (WIDTH, HEIGHT))

# プレイヤー画像の読み込み（画像ファイルは同じフォルダに置く）
PLAYER_IMG = pygame.image.load("レッドバロン新.png").convert_alpha()
PLAYER_IMG = pygame.transform.scale(PLAYER_IMG, (100, 86))


FPS = 60
CLOCK = pygame.time.Clock()

# 色
WHITE = (255,255,255)
BLACK = (0,0,0)
SKY = (135, 206, 235)
GROUND = (80, 60, 40)
PLAYER_COLOR = (200, 30, 30)
OBST_COLOR = (20, 20, 20)
COIN_COLOR = (255, 200, 0)

# ゲームパラメータ
GROUND_Y = HEIGHT - 80
SCROLL_SPEED = 5  # 初期スクロール速度（px/frame）
SPEED_INCREASE_RATE = 0.0005  # スコア（距離）に応じて速度増加

# フォント
FONT = pygame.font.SysFont("meiryo", 24)
BIG_FONT = pygame.font.SysFont("meiryo", 48)

# サウンド（ファイルがあれば好きなファイル名を指定する）
# もしファイルが無い場合はコメントアウトしても動きます
try:
    JUMP_SOUND = pygame.mixer.Sound("jump.wav")
    HIT_SOUND = pygame.mixer.Sound("hit.wav")
    COIN_SOUND = pygame.mixer.Sound("coin.wav")
except Exception:
    JUMP_SOUND = None
    HIT_SOUND = None
    COIN_SOUND = None

# ----------------------------
# プレイヤークラス（自転車）
# ----------------------------
class Player:
    def __init__(self, x, y):
        # 当たり判定は矩形で管理（見た目は自転車）
        self.x = x
        self.y = y
        self.image =  PLAYER_IMG #画像の大きさを当たり判定に変更
        self.width,self.height = self.image.get_size()
        self.vy = 0
        self.on_ground = True
        self.jump_count = 0
        self.max_jumps = 2
        self.alive = True
        self.ducking = False
        self.color = PLAYER_COLOR

        # アニメーション用
        self.frame = 0
        self.frame_timer = 0

    @property
    def rect(self):
        # しゃがんだら高さを小さくする
        h = self.height // 2 if self.ducking else self.height
        return pygame.Rect(self.x, self.y - h, self.width, h)

    def jump(self):
        if self.jump_count < self.max_jumps:
            self.vy = -12  # 初速
            self.jump_count += 1
            self.on_ground = False
            if JUMP_SOUND:
                JUMP_SOUND.play()

    def update(self, scroll_speed):
        # 重力
        self.vy += 0.6
        self.y += self.vy

        # 地面判定
        base_h = self.height // 2 if self.ducking else self.height
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
            self.jump_count = 0

        # 簡易アニメーション（フレーム増加で車輪を回すような表示にできる）
        self.frame_timer += 1
        if self.frame_timer > 6:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % 4

    def draw(self, surf):
        r = self.rect


        surf.blit(self.image, (self.x,self.y - self.height // 2 - 35))

        # 自転車本体（四角＋丸の簡易描画）
        #bike_body = pygame.Rect(r.x, r.y + 10, r.width, r.height - 10)
        #pygame.draw.rect(surf, self.color, bike_body, border_radius=6)
        # 車輪
        #wheel_radius = 10
        ##pygame.draw.circle(surf, BLACK, (r.x + 12, r.y + r.height), wheel_radius)
        #pygame.draw.circle(surf, BLACK, (r.x + r.width - 12, r.y + r.height), wheel_radius)

        # 目押しヒント：ジャンプ状態を少し変化表示
        #if not self.on_ground:
         #   pygame.draw.rect(surf, (255,255,255), (r.x + r.width//2 - 4, r.y + 6, 8, 8))


# ----------------------------
# 障害物クラス
# ----------------------------
class Obstacle:
    def __init__(self, x, w, h, typ="block"):
        self.x = x
        self.w = w
        self.h = h
        self.typ = typ
        self.color = OBST_COLOR
        self.passed = False  # プレイヤーを抜けたか
        # y位置は地面に基づく
        self.y = GROUND_Y

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y - self.h), self.w, self.h)

    def update(self, speed):
        self.x -= speed

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)


# ----------------------------
# アイテム（コイン）クラス
# ----------------------------
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.r = 8
        self.collected = False

    @property
    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)

    def update(self, speed):
        self.x -= speed

    def draw(self, surf):
        pygame.draw.circle(surf, COIN_COLOR, (int(self.x), int(self.y)), self.r)


# ----------------------------
# 背景スクロール（地面タイル）
# ----------------------------
class Ground:
    def __init__(self):
        self.tiles = []
        tile_w = 200
        for i in range(6):
            self.tiles.append(pygame.Rect(i*tile_w, GROUND_Y, tile_w, HEIGHT - GROUND_Y))
        self.tile_w = tile_w

    def update(self, speed):
        for t in self.tiles:
            t.x -= speed
        # 先頭タイルが画面左外に行ったら末尾に移動
        if self.tiles and self.tiles[0].right < 0:
            first = self.tiles.pop(0)
            first.x = self.tiles[-1].right
            self.tiles.append(first)

    def draw(self, surf):
        for i,t in enumerate(self.tiles):
            color = GROUND if i%2==0 else (60,40,30)
            pygame.draw.rect(surf, color, t)


# ----------------------------
# ゲーム管理
# ----------------------------
def spawn_obstacle(next_x):
    # 障害物の種類をランダムに。大きさや間隔を変えられる
    r = random.random()
    if r < 0.6:
        # 小ブロック
        w = random.randint(24, 44)
        h = random.randint(24, 48)
        return Obstacle(next_x, w, h, "block")
    elif r < 0.9:
        # 高い柵
        w = random.randint(20, 30)
        h = random.randint(60, 110)
        return Obstacle(next_x, w, h, "tall")
    else:
        # 何も（偶に空）
        return None

def spawn_coin(x):
    # 地面より上に浮かせて配置
    y = GROUND_Y - random.randint(80, 160)
    return Coin(x, y)


def draw_text(surf, text, x, y, font=FONT, col=WHITE):
    surf_text = font.render(text, True, col)
    surf.blit(surf_text, (x,y))


def game_loop():
    # 初期化
    player = Player(140, GROUND_Y - 48)
    ground = Ground()
    obstacles = []
    coins = []
    distance = 0.0
    score = 0
    speed = SCROLL_SPEED
    spawn_timer = 0
    coin_timer = 0
    game_over = False

    # 初期障害物を少し置く
    next_x = WIDTH + 200
    for _ in range(3):
        ob = spawn_obstacle(next_x)
        if ob:
            obstacles.append(ob)
        next_x += random.randint(220, 350)

    # ゲームループ
    running = True
    while running:
        dt = CLOCK.tick(FPS) / 1000.0  # 秒
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # キー入力
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_k) and not game_over:
                    player.jump()
                    player.ducking = False
                if event.key == pygame.K_DOWN:
                    player.ducking = True
                if game_over and event.key == pygame.K_r:
                    return  # リターンして新しいループで再スタート
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    player.ducking = False

        if not game_over:
            # スピードは距離に応じて少しだけ速くなる
            speed += SPEED_INCREASE_RATE

            # 背景移動
            ground.update(speed)

            # プレイヤー更新
            player.update(speed)

            # 障害物更新
            for ob in obstacles:
                ob.update(speed)
            obstacles = [o for o in obstacles if o.x + o.w > -50]  # 画面外消す

            # コイン更新
            for c in coins:
                c.update(speed)
            coins = [c for c in coins if c.x > -50 and not c.collected]

            # 当たり判定：障害物
            for ob in obstacles:
                if player.rect.colliderect(ob.rect):
                    game_over = True
                    player.alive = False
                    if HIT_SOUND:
                        HIT_SOUND.play()
                    break

            # 当たり判定：コイン
            for c in coins:
                if player.rect.colliderect(c.rect) and not c.collected:
                    c.collected = True
                    score += 10
                    if COIN_SOUND:
                        COIN_SOUND.play()

            # スポーン管理
            spawn_timer += 1
            if spawn_timer > max(40, 100 - int(distance/5)):
                # 次の障害物までのX
                spawn_x = WIDTH + random.randint(0, 200)
                ob = spawn_obstacle(spawn_x)
                if ob:
                    obstacles.append(ob)
                spawn_timer = 0

            coin_timer += 1
            if coin_timer > 120:
                coins.append(spawn_coin(WIDTH + random.randint(0,200)))
                coin_timer = 0

            # 距離増加（スクロールに合わせた擬似距離）
            distance += speed * dt
        # 描画
        SCREEN.blit(BG_IMG, (0,0))
        ground.draw(SCREEN)

        # 障害物描画
        for ob in obstacles:
            ob.draw(SCREEN)

        # コイン描画
        for c in coins:
            c.draw(SCREEN)

        # プレイヤー描画
        player.draw(SCREEN)

        # HUD
        draw_text(SCREEN, f"DIST: {int(distance)}m", 10, 10)
        draw_text(SCREEN, f"SCORE: {score}", 10, 36)
        draw_text(SCREEN, f"SPEED: {speed:.1f}", 10, 62)
        draw_text(SCREEN, "SPACE / ↑ / K: ジャンプ  DOWN: しゃがむ  R: リスタート", 200, 10, FONT, (240,240,240))

        # ゲームオーバー表示
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            SCREEN.blit(overlay, (0,0))
            draw_text(SCREEN, "GAME OVER", WIDTH//2 - 120, HEIGHT//2 - 60, BIG_FONT, (255,180,0))
            draw_text(SCREEN, f"距離: {int(distance)}m  スコア: {score}", WIDTH//2 - 180, HEIGHT//2, FONT, (255,255,255))
            draw_text(SCREEN, "Rでリスタート / ESCで終了", WIDTH//2 - 140, HEIGHT//2 + 40, FONT, (200,200,200))

        pygame.display.flip()

    return

# ----------------------------
# ゲーム全体のループ（リスタート対応）
# ----------------------------
while True:
    game_loop()

