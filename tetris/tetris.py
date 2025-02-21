import pygame
import random

# 初始化 Pygame
pygame.init()

# 简化颜色定义：黑、白、灰
COLORS = [(0, 0, 0), (255, 255, 255), (128, 128, 128)]

# 方块形状定义
SHAPES = [
    [[1, 5, 9, 13], [4, 5, 6, 7]],  # I
    [[4, 5, 9, 10], [2, 6, 5, 9]],  # Z
    [[6, 7, 9, 10], [1, 5, 6, 10]], # S
    [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]], # L
    [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]], # J
    [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]], # T
    [[1, 2, 5, 6]]  # O
]

# 游戏设置
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500
BLOCK_SIZE = 20
FIELD_WIDTH = 10
FIELD_HEIGHT = 20
GAME_AREA_LEFT = 150
NEXT_BLOCK_LEFT = 400
NEXT_BLOCK_TOP = 60
NEXT_BLOCK_SIZE = 80
FPS = 30

# 在游戏设置部分添加游戏状态
GAME_STATES = ["menu", "start", "gameover"]

# 按键重复设置
KEY_REPEAT_DELAY = 200
KEY_REPEAT_INTERVAL = 50
pygame.key.set_repeat(KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()
pygame.mixer.music.load("Tetris/tetris_theme.mp3")
pygame.mixer.music.play(-1)

# 添加字体定义
font = pygame.font.SysFont('Arial', 25, True)

class Game:
    def __init__(self):
        self.field = [[0 for _ in range(FIELD_WIDTH)] for _ in range(FIELD_HEIGHT)]
        self.score = self.lines = 0
        self.level = 1
        self.state = "menu"  # 初始状态改为菜单
        self.figure = self.next = None
        self.new_figure()
        
    def new_figure(self):
        self.figure = self.next if self.next else Figure(3, 0)
        self.next = Figure(3, 0)

    def intersects(self):
        for i, j in self.figure.get_coords():
            if i >= FIELD_HEIGHT or j < 0 or j >= FIELD_WIDTH or self.field[i][j] > 0:
                return True
        return False

    def freeze(self):
        try:
            for i, j in self.figure.get_coords():
                if 0 <= i < FIELD_HEIGHT and 0 <= j < FIELD_WIDTH:  # 添加边界检查
                    self.field[i][j] = 1  # 使用白色(1)作为方块颜色
            
            lines = 0
            for i in range(FIELD_HEIGHT):
                if all(self.field[i]):  # 检查一行是否已满
                    lines += 1
                    # 从当前行开始，每一行都复制上一行的内容
                    for i1 in range(i, 0, -1):
                        self.field[i1] = self.field[i1-1][:]
                    self.field[0] = [0] * FIELD_WIDTH  # 顶部添加新的空行
            
            self.score += lines ** 2
            self.lines += lines
            self.level = self.lines // 10 + 1
            
            if lines:
                pygame.mixer.Sound("cookie_game/click.mp3").play()
            
            self.new_figure()
            if self.intersects():
                self.state = "gameover"
        except Exception as e:
            print(f"Error in freeze: {e}")

    # 添加逆时针旋转方法
    def rotate_counterclockwise(self):
        old_rotation = self.figure.rotation
        self.figure.rotation = (self.figure.rotation - 1) % len(SHAPES[self.figure.type])
        if self.intersects():
            self.figure.rotation = old_rotation

    # 添加快速下落方法
    def drop_down(self):
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

class Figure:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(SHAPES) - 1)
        self.rotation = 0

    def get_coords(self):
        shape = SHAPES[self.type][self.rotation]
        return [(self.y + i, self.x + j) for i in range(4) for j in range(4) if i * 4 + j in shape]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(SHAPES[self.type])

# 创建游戏实例
game = Game()
paused = False
counter = 0

# 在主循环前添加绘制菜单的函数
def draw_menu():
    title = font.render("TETRIS", True, COLORS[1])
    controls = [
        "Controls:",
        "WASD / Arrows - Move",
        "W / Up - Drop Down",
        "J - Rotate Clockwise",
        "K - Rotate Counter-clockwise",
        "P - Pause",
        "R - Restart (when game over)",
        "",
        "Press SPACE to Start"
    ]
    
    title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
    screen.blit(title, title_rect)
    
    for i, text in enumerate(controls):
        control = font.render(text, True, COLORS[1])
        rect = control.get_rect(center=(WINDOW_WIDTH//2, 200 + i*30))
        screen.blit(control, rect)

# 修改主循环
while True:
    counter = (counter + 1) % 100000
    if game.state == "start" and not paused:
        if counter % max(FPS // game.level, 1) == 0:
            game.figure.y += 1
            if game.intersects():
                game.figure.y -= 1
                game.freeze()

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if game.state == "menu" and event.key == pygame.K_SPACE:
                game.state = "start"
            elif game.state == "gameover" and event.key == pygame.K_r:
                game = Game()
            elif event.key == pygame.K_p and game.state == "start":
                paused = not paused
            elif not paused and game.state == "start":
                if event.key in [pygame.K_LEFT, pygame.K_a]:
                    game.figure.x -= 1
                    if game.intersects(): game.figure.x += 1
                if event.key in [pygame.K_RIGHT, pygame.K_d]:
                    game.figure.x += 1
                    if game.intersects(): game.figure.x -= 1
                if event.key in [pygame.K_DOWN, pygame.K_s]:
                    game.figure.y += 1
                    if game.intersects(): game.figure.y -= 1
                if event.key in [pygame.K_UP, pygame.K_w]:
                    game.drop_down()
                if event.key == pygame.K_j:
                    old_rotation = game.figure.rotation
                    game.figure.rotate()
                    if game.intersects(): game.figure.rotation = old_rotation
                if event.key == pygame.K_k:
                    game.rotate_counterclockwise()

    # 绘制游戏界面
    screen.fill(COLORS[0])
    
    if game.state == "menu":
        draw_menu()
    else:
        # 绘制左右边框区域（灰色）
        pygame.draw.rect(screen, COLORS[2], [0, 0, GAME_AREA_LEFT-10, WINDOW_HEIGHT])
        pygame.draw.rect(screen, COLORS[2], [GAME_AREA_LEFT+FIELD_WIDTH*BLOCK_SIZE+10, 0, 
                        WINDOW_WIDTH-(GAME_AREA_LEFT+FIELD_WIDTH*BLOCK_SIZE+10), WINDOW_HEIGHT])
        
        # 绘制游戏区域和预览区域（黑色背景）
        pygame.draw.rect(screen, COLORS[0], [NEXT_BLOCK_LEFT, NEXT_BLOCK_TOP, NEXT_BLOCK_SIZE, NEXT_BLOCK_SIZE])
        
        # 绘制边框（白色）
        pygame.draw.rect(screen, COLORS[1], 
                        [GAME_AREA_LEFT-2, 58, FIELD_WIDTH*BLOCK_SIZE+4, FIELD_HEIGHT*BLOCK_SIZE+4], 2)
        pygame.draw.rect(screen, COLORS[1], [NEXT_BLOCK_LEFT, NEXT_BLOCK_TOP, NEXT_BLOCK_SIZE, NEXT_BLOCK_SIZE], 2)
        screen.blit(font.render("Next:", True, COLORS[1]), [NEXT_BLOCK_LEFT, NEXT_BLOCK_TOP-30])

        # 绘制已固定的方块
        for i in range(FIELD_HEIGHT):
            for j in range(FIELD_WIDTH):
                if game.field[i][j] > 0:
                    pygame.draw.rect(screen, COLORS[1],
                                   [j*BLOCK_SIZE+GAME_AREA_LEFT, i*BLOCK_SIZE+60,
                                    BLOCK_SIZE-1, BLOCK_SIZE-1])

        # 绘制当前方块和预览
        if game.figure:
            # 绘制当前方块
            for i, j in game.figure.get_coords():
                if i >= 0:
                    pygame.draw.rect(screen, COLORS[2],
                                   [j*BLOCK_SIZE+GAME_AREA_LEFT, i*BLOCK_SIZE+60,
                                    BLOCK_SIZE-1, BLOCK_SIZE-1])
            
            # 绘制预览方块（在右上角）
            for i, j in game.next.get_coords():
                if i >= 0:
                    pygame.draw.rect(screen, COLORS[2],
                                   [(j)*BLOCK_SIZE+NEXT_BLOCK_LEFT+10, 
                                    (i)*BLOCK_SIZE+NEXT_BLOCK_TOP+10,
                                    BLOCK_SIZE-1, BLOCK_SIZE-1])

        # 绘制分数和等级（移到左侧区域）
        screen.blit(font.render(f"Score:", True, COLORS[1]), [20, 100])
        screen.blit(font.render(f"{game.score}", True, COLORS[1]), [20, 130])
        screen.blit(font.render(f"Level:", True, COLORS[1]), [20, 180])
        screen.blit(font.render(f"{game.level}", True, COLORS[1]), [20, 210])

        if game.state == "gameover":
            screen.blit(font.render("Game Over! Press R to restart", True, COLORS[1]), [50, 200])
        if paused:
            screen.blit(font.render("PAUSED", True, COLORS[1]), [150, 200])

    pygame.display.flip()
    clock.tick(FPS) 