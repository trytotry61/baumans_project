import pygame
import sys
from dstar_lite_core import smooth_path_chaikin, get_partial_path, DStarLite

CELL_SIZE = 26
HUD_HEIGHT = 80

# Тема для единственного агента (D* Lite)
THEME = {"main": (14, 165, 233), "glow": (186, 230, 253), "robot": (2, 132, 199)}

class PathfindingGUI:
    def __init__(self, cols, rows, start, goal, static_obs):
        self.cols = cols
        self.rows = rows
        self.start = start
        self.goal = goal
        self.static_obs = static_obs

        self.width = cols * CELL_SIZE
        self.height = rows * CELL_SIZE + HUD_HEIGHT

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("D* Lite Pathfinding (Python Core)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 15, bold=True)

        self.LINE_GROWTH_SPEED = 0.015  # Скорость "прорастания" линии
        self.ROBOT_SPEED = 0.25         # Скорость движения робота по дугам
        
        self.dstar = DStarLite(cols, rows, start, goal, static_obs)
        
        self.raw_path, self.exec_time, self.peak_mem = self.dstar.initial_solve()
        self.process_path_data()

    def process_path_data(self):
        self.path_reveal_progress = 0.0
        self.robot_idx = 0
        self.robot_sub = 0.0
        
        if not self.raw_path:
            self.smoothed_path = []
            return

        pixel_pts = [(p[0] * CELL_SIZE + CELL_SIZE // 2, HUD_HEIGHT + p[1] * CELL_SIZE + CELL_SIZE // 2) for p in self.raw_path]
        self.smoothed_path = smooth_path_chaikin(pixel_pts, iterations=3)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if my >= HUD_HEIGHT:
                        gx = mx // CELL_SIZE
                        gy = (my - HUD_HEIGHT) // CELL_SIZE
                        pos = (gx, gy)

                        if pos not in self.static_obs and pos != self.start and pos != self.goal:
                            # Мгновенный инкрементальный пересчет D* Lite
                            self.raw_path, self.exec_time, self.peak_mem = self.dstar.toggle_obstacle(pos)
                            self.process_path_data()

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def draw(self):
        self.screen.fill((248, 249, 250))

        # --- HUD ПАНЕЛЬ ---
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, self.width, HUD_HEIGHT))
        pygame.draw.line(self.screen, (226, 232, 240), (0, HUD_HEIGHT), (self.width, HUD_HEIGHT), 2)

        is_found = len(self.raw_path) > 0
        status_txt = f"Пересчет D* Lite: {self.exec_time:.2f} ms | ОЗУ: {self.peak_mem:.1f} KB"
        info_txt = f"Статус: {'Путь оптимизирован' if is_found else 'БЛОКИРОВКА!'} | Клик по карте — динамические препятствия"

        t1 = self.font.render(status_txt, True, (30, 41, 59))
        t2 = self.font.render(info_txt, True, (16, 185, 129) if is_found else (225, 29, 72))
        self.screen.blit(t1, (15, 12))
        self.screen.blit(t2, (15, 38))

        # --- СЕТКА И ПРЕПЯТСТВИЯ ---
        for x in range(self.cols):
            for y in range(self.rows):
                rect = (x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, 1)

                cell = (x, y)
                if cell in self.static_obs:
                    pygame.draw.rect(self.screen, (47, 63, 86), rect)
                elif cell in self.dstar.obs and cell not in self.static_obs:
                    pygame.draw.rect(self.screen, (225, 29, 72), rect)

        # --- ПРОРАСТАНИЕ СГЛАЖЕННОЙ ЛИНИИ ---
        if self.path_reveal_progress < 1.0:
            self.path_reveal_progress = min(1.0, self.path_reveal_progress + self.LINE_GROWTH_SPEED)

        if self.smoothed_path:
            visible_pts = get_partial_path(self.smoothed_path, self.path_reveal_progress)
            if len(visible_pts) > 1:
                pygame.draw.lines(self.screen, THEME["glow"], False, visible_pts, 8)
                pygame.draw.lines(self.screen, THEME["main"], False, visible_pts, 4)

        # --- СТАРТ И ЦЕЛЬ ---
        s_rect = (self.start[0] * CELL_SIZE + 3, HUD_HEIGHT + self.start[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
        g_rect = (self.goal[0] * CELL_SIZE + 3, HUD_HEIGHT + self.goal[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
        pygame.draw.rect(self.screen, (16, 185, 129), s_rect, border_radius=4)
        pygame.draw.rect(self.screen, (139, 92, 246), g_rect, border_radius=4)

        # --- 60 FPS АНИМАЦИЯ РОБОТА ---
        if len(self.smoothed_path) > 1:
            self.robot_sub += self.ROBOT_SPEED
            if self.robot_sub >= 1.0:
                self.robot_sub -= 1.0
                self.robot_idx += 1
                if self.robot_idx >= len(self.smoothed_path) - 1:
                    self.robot_idx = 0  # Зацикливаем движение для визуализации

            p1 = self.smoothed_path[self.robot_idx]
            p2 = self.smoothed_path[self.robot_idx + 1]

            # Линейная интерполяция
            rx = p1[0] + (p2[0] - p1[0]) * self.robot_sub
            ry = p1[1] + (p2[1] - p1[1]) * self.robot_sub

            pygame.draw.circle(self.screen, THEME["robot"], (int(rx), int(ry)), CELL_SIZE // 3)

        pygame.display.flip()