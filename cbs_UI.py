import pygame
import sys
from cbs_core import smooth_path_chaikin, get_partial_path, CBSSolver

CELL_SIZE = 26
HUD_HEIGHT = 80

# Цветовые темы для агентов
AGENT_THEMES = [
    {"main": (16, 185, 129), "glow": (186, 230, 253), "robot": (5, 150, 105)},
    {"main": (245, 158, 11), "glow": (254, 243, 199), "robot": (217, 119, 6)},
    {"main": (139, 92, 246), "glow": (233, 213, 255), "robot": (124, 58, 237)}
]

class PathfindingGUI:
    def __init__(self, cols, rows, starts, goals, static_obs):
        self.cols = cols
        self.rows = rows
        self.starts = starts
        self.goals = goals
        self.static_obs = static_obs

        self.width = cols * CELL_SIZE
        self.height = rows * CELL_SIZE + HUD_HEIGHT

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("CBS Multi-Agent Pathfinding (Python Core)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 15, bold=True)

        self.LINE_GROWTH_SPEED = 0.008  # Скорость "прорастания" линии
        self.path_reveal_progress = 0.0
        self.step_t = 0
        self.frame_counter = 0

        self.recalculate()

    def recalculate(self):
        solver = CBSSolver(self.cols, self.rows, self.starts, self.goals, self.static_obs, set())
        res = solver.solve()
        
        self.raw_paths = res["paths"]
        self.exec_time_ms = res["exec_time_ms"]
        self.peak_memory_kb = res["peak_memory_kb"]

        # Построение сглаженных траекторий
        self.smoothed_paths = []
        for path in self.raw_paths:
            if not path:
                self.smoothed_paths.append([])
                continue
            pixel_pts = [(p[0] * CELL_SIZE + CELL_SIZE // 2, HUD_HEIGHT + p[1] * CELL_SIZE + CELL_SIZE // 2) for p in path]
            self.smoothed_paths.append(smooth_path_chaikin(pixel_pts, iterations=3))

        self.path_reveal_progress = 0.0
        self.step_t = 0

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.draw()
            self.clock.tick(60)


    def draw(self):
        self.screen.fill((248, 249, 250))

        # --- HUD ПАНЕЛЬ ---
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, self.width, HUD_HEIGHT))
        pygame.draw.line(self.screen, (226, 232, 240), (0, HUD_HEIGHT), (self.width, HUD_HEIGHT), 2)

        is_found = all(len(p) > 0 for p in self.raw_paths) if self.raw_paths else False
        status_txt = f"Время расчёта (Python): {self.exec_time_ms:.2f} ms | ОЗУ: {self.peak_memory_kb:.1f} KB"

        t1 = self.font.render(status_txt, True, (30, 41, 59))
        self.screen.blit(t1, (15, 12))

        # --- СЕТКА И ПРЕПЯТСТВИЯ ---
        for x in range(self.cols):
            for y in range(self.rows):
                rect = (x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, 1)

                cell = (x, y)
                if cell in self.static_obs:
                    pygame.draw.rect(self.screen, (47, 63, 86), rect)

        # --- ПРОРАСТАНИЕ ЛИНИЙ ---
        if self.path_reveal_progress < 1.0:
            self.path_reveal_progress = min(1.0, self.path_reveal_progress + self.LINE_GROWTH_SPEED)

        for idx, smooth_pts in enumerate(self.smoothed_paths):
            if not smooth_pts:
                continue

            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]
            visible_pts = get_partial_path(smooth_pts, self.path_reveal_progress)

            if len(visible_pts) > 1:
                # Внешнее свечение
                pygame.draw.lines(self.screen, theme["glow"], False, visible_pts, 2)
                # Основная плавная линия
                pygame.draw.lines(self.screen, theme["main"], False, visible_pts, 8)

            # Старты и цели
            sp, gp = self.starts[idx], self.goals[idx]
            s_rect = (sp[0] * CELL_SIZE + 3, HUD_HEIGHT + sp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            g_rect = (gp[0] * CELL_SIZE + 3, HUD_HEIGHT + gp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)

            pygame.draw.rect(self.screen, theme["main"], s_rect, border_radius=4)
            pygame.draw.rect(self.screen, theme["main"], g_rect, 2, border_radius=4)

        # --- АНИМАЦИЯ РОБОТОВ ---
        self.frame_counter += 1
        if self.frame_counter % 10 == 0:
            self.step_t += 1

        for idx, raw_path in enumerate(self.raw_paths):
            if not raw_path:
                continue
            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]
            curr_pos = raw_path[min(self.step_t, len(raw_path) - 1)]
            rx = curr_pos[0] * CELL_SIZE + CELL_SIZE // 2
            ry = HUD_HEIGHT + curr_pos[1] * CELL_SIZE + CELL_SIZE // 2

            pygame.draw.circle(self.screen, theme["robot"], (rx, ry), CELL_SIZE // 3)

        pygame.display.flip()