import pygame
import sys
import concurrent.futures
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from cores.dstar_lite_core import smooth_path_chaikin, get_partial_path, DStarLiteSolver

CELL_SIZE = 26
HUD_HEIGHT = 80

# Оставляем только нужные цвета: Бирюзовый (0) и Синий (1)
AGENT_THEMES = [
    {"main": (20, 184, 166), "glow": (204, 251, 241), "robot": (13, 148, 136)},  # Бирюзовый
    {"main": (37, 99, 235), "glow": (219, 234, 254), "robot": (29, 78, 216)}     # Синий
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
        pygame.display.set_caption("D* Lite Multi-Agent Pathfinding (Python Core)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.LINE_GROWTH_SPEED = 0.010
        self.ROBOT_SPEED = 0.40
        self.solver = DStarLiteSolver(cols, rows, starts, goals, static_obs)
        res = self.solver.solve()
        self.apply_results(res)

    def apply_results(self, res):
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
        self.agent_states = [{"idx": 0, "sub": 0.0} for _ in range(len(self.starts))]

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
                            res = self.solver.toggle_obstacle(pos)
                            self.apply_results(res)
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

    def draw(self):
        self.screen.fill((248, 249, 250))
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, self.width, HUD_HEIGHT))
        pygame.draw.line(self.screen, (226, 232, 240), (0, HUD_HEIGHT), (self.width, HUD_HEIGHT), 2)
        
        is_found = all(len(p) > 0 for p in self.raw_paths) if self.raw_paths else False
        status_txt = f"Пересчет D* Lite: {self.exec_time_ms:.2f} ms | ОЗУ: {self.peak_memory_kb:.1f} KB"
        info_txt = f"Статус: {'Траектории построены' if is_found else 'БЛОКИРОВКА!'}"
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
            item_x = legend_x + (idx * 115)  # Увеличен отступ для размещения креста
            item_y = legend_y + 22
            pygame.draw.rect(self.screen, theme["main"], (item_x, item_y + 4, 12, 12), border_radius=2)
            target_box_rect = (item_x + 18, item_y + 4, 12, 12)
            pygame.draw.rect(self.screen, (255, 255, 255), target_box_rect)
            pygame.draw.rect(self.screen, theme["main"], target_box_rect, 2, border_radius=2)
            agent_lbl = self.font.render(f"Р{idx + 1}", True, (30, 41, 59))
            self.screen.blit(agent_lbl, (item_x + 34, item_y))

            # Рисуем красный медицинский крест рядом с бирюзовым агентом (индекс 0)
            if idx == 0:
                cross_cx = item_x + 62
                cross_cy = item_y + 10
                red_cross_color = (220, 38, 38)
                pygame.draw.rect(self.screen, red_cross_color, (cross_cx - 6, cross_cy - 2, 12, 4))
                pygame.draw.rect(self.screen, red_cross_color, (cross_cx - 2, cross_cy - 6, 4, 12))

        # Отрисовка сетки и препятствий
        for x in range(self.cols):
            for y in range(self.rows):
                rect = (x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, 1)
                cell = (x, y)
                if cell in self.static_obs:
                    pygame.draw.rect(self.screen, (47, 63, 86), rect)
                elif cell in self.solver.dynamic_obs:
                    pygame.draw.rect(self.screen, (225, 29, 72), rect)
        
        if self.path_reveal_progress < 1.0:
            self.path_reveal_progress = min(1.0, self.path_reveal_progress + self.LINE_GROWTH_SPEED)
        
        # Отрисовка траекторий
        for idx, smooth_pts in enumerate(self.smoothed_paths):
            if not smooth_pts:
                continue
            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]
            visible_pts = get_partial_path(smooth_pts, self.path_reveal_progress)
            if len(visible_pts) > 1:
                pygame.draw.lines(self.screen, theme["glow"], False, visible_pts, 8)
                pygame.draw.lines(self.screen, theme["main"], False, visible_pts, 4)
            sp, gp = self.starts[idx], self.goals[idx]
            s_rect = (sp[0] * CELL_SIZE + 3, HUD_HEIGHT + sp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            g_rect = (gp[0] * CELL_SIZE + 3, HUD_HEIGHT + gp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            pygame.draw.rect(self.screen, theme["main"], s_rect, border_radius=4)
            pygame.draw.rect(self.screen, theme["main"], g_rect, 2, border_radius=4)
        
        # Отрисовка агентов и грузов
        for idx, smooth_pts in enumerate(self.smoothed_paths):
            if len(smooth_pts) < 2:
                continue
            st = self.agent_states[idx]
            st["sub"] += self.ROBOT_SPEED
            if st["sub"] >= 1.0:
                st["sub"] -= 1.0
                st["idx"] += 1
                if st["idx"] >= len(smooth_pts) - 1:
                    st["idx"] = len(smooth_pts) - 2
                    st["sub"] = 1.0
            p1 = smooth_pts[st["idx"]]
            p2 = smooth_pts[st["idx"] + 1]
            rx = p1[0] + (p2[0] - p1[0]) * st["sub"]
            ry = p1[1] + (p2[1] - p1[1]) * st["sub"]
            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]

            # Эффект буксировки груза (только если агент НЕ бирюзовый, т.е. Синий)
            if idx != 0:
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                dist = (dx**2 + dy**2) ** 0.5
                nx, ny = (dx / dist, dy / dist) if dist > 0 else (0, 0)

                cargo_offset = 15
                cargo_x = rx - nx * cargo_offset
                cargo_y = ry - ny * cargo_offset

                # Трос
                pygame.draw.line(self.screen, (100, 116, 139), (int(rx), int(ry)), (int(cargo_x), int(cargo_y)), 2)

                # Коробка (груз)
                box_size = 12
                cargo_rect = pygame.Rect(
                    int(cargo_x - box_size // 2),
                    int(cargo_y - box_size // 2),
                    box_size,
                    box_size
                )
                pygame.draw.rect(self.screen, (217, 119, 6), cargo_rect, border_radius=2)
                pygame.draw.rect(self.screen, (120, 53, 15), cargo_rect, 1, border_radius=2)

            # Отрисовка самого робота поверх элементов
            pygame.draw.circle(self.screen, theme["robot"], (int(rx), int(ry)), CELL_SIZE // 3)
            
        pygame.display.flip()