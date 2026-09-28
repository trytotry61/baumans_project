import pygame
import sys
import concurrent.futures
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from cores.cbs_core import smooth_path_chaikin, get_partial_path, CBSSolver
CELL_SIZE = 26
HUD_HEIGHT = 80
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
        self.dynamic_obs = set()  
        self.width = cols * CELL_SIZE
        self.height = rows * CELL_SIZE + HUD_HEIGHT
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("CBS Multi-Agent Pathfinding (Python Core)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.LINE_GROWTH_SPEED = 0.008 
        self.path_reveal_progress = 0.0
        self.step_t = 0
        self.frame_counter = 0
        self.recalculate()
    def recalculate(self):
        solver = CBSSolver(self.cols, self.rows, self.starts, self.goals, self.static_obs, self.dynamic_obs)
        res = solver.solve()
        self.raw_paths = res["paths"]
        self.exec_time_ms = res["exec_time_ms"]
        self.peak_memory_kb = res["peak_memory_kb"]
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
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if my >= HUD_HEIGHT:
                        gx = mx // CELL_SIZE
                        gy = (my - HUD_HEIGHT) // CELL_SIZE
                        pos = (gx, gy)
                        if pos not in self.static_obs and pos not in self.starts and pos not in self.goals:
                            if pos in self.dynamic_obs:
                                self.dynamic_obs.remove(pos)
                            else:
                                self.dynamic_obs.add(pos)
                            self.recalculate()

            self.draw()
            self.clock.tick(60)
    def draw(self):
        self.screen.fill((248, 249, 250))
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, self.width, HUD_HEIGHT))
        pygame.draw.line(self.screen, (226, 232, 240), (0, HUD_HEIGHT), (self.width, HUD_HEIGHT), 2)
        is_found = all(len(p) > 0 for p in self.raw_paths) if self.raw_paths else False
        status_txt = f"Время расчёта (CBS): {self.exec_time_ms:.2f} ms | ОЗУ: {self.peak_memory_kb:.1f} KB"
        info_txt = f"Статус: {'Маршруты найдены' if is_found else 'БЛОКИРОВКА!'} | Клик по сетке — установить/убрать препятствие"
        t1 = self.font.render(status_txt, True, (30, 41, 59))
        t2 = self.font.render(info_txt, True, (16, 185, 129) if is_found else (225, 29, 72))
        self.screen.blit(t1, (15, 12))
        self.screen.blit(t2, (15, 38))
        legend_x = self.width - 340
        legend_y = 12
        leg_title = self.font.render("Легенда (Старт / Цель):", True, (100, 116, 139))
        self.screen.blit(leg_title, (legend_x, legend_y))
        for idx in range(len(self.starts)):
            theme = AGENT_THEMES[idx % len(AGENT_THEMES)] 
            item_x = legend_x + (idx * 85)
            item_y = legend_y + 22
            pygame.draw.rect(self.screen, theme["main"], (item_x, item_y + 4, 12, 12), border_radius=2)
            target_box_rect = (item_x + 18, item_y + 4, 12, 12)
            pygame.draw.rect(self.screen, (255, 255, 255), target_box_rect)
            pygame.draw.rect(self.screen, theme["main"], target_box_rect, 2, border_radius=2)
            agent_lbl = self.font.render(f"Р{idx + 1}", True, (30, 41, 59))
            self.screen.blit(agent_lbl, (item_x + 34, item_y))
        for x in range(self.cols):
            for y in range(self.rows):
                rect = (x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, 1)
                cell = (x, y)
                if cell in self.static_obs:
                    pygame.draw.rect(self.screen, (47, 63, 86), rect)
                elif cell in self.dynamic_obs:
                    pygame.draw.rect(self.screen, (225, 29, 72), rect)  # Красный цвет для динамических препятствий
        if self.path_reveal_progress < 1.0:
            self.path_reveal_progress = min(1.0, self.path_reveal_progress + self.LINE_GROWTH_SPEED)
        for idx, smooth_pts in enumerate(self.smoothed_paths):
            if not smooth_pts:
                continue
            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]
            visible_pts = get_partial_path(smooth_pts, self.path_reveal_progress)
            if len(visible_pts) > 1:
                pygame.draw.lines(self.screen, theme["glow"], False, visible_pts, 2)
                pygame.draw.lines(self.screen, theme["main"], False, visible_pts, 8)
            sp, gp = self.starts[idx], self.goals[idx]
            s_rect = (sp[0] * CELL_SIZE + 3, HUD_HEIGHT + sp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            g_rect = (gp[0] * CELL_SIZE + 3, HUD_HEIGHT + gp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            pygame.draw.rect(self.screen, theme["main"], s_rect, border_radius=4)
            pygame.draw.rect(self.screen, theme["main"], g_rect, 2, border_radius=4)
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