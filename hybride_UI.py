import pygame
import sys
from hybride_core import smooth_path_chaikin, get_partial_path, CBSDStarLiteSolver

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
        pygame.display.set_caption("CBS-D* Lite Hybrid MAPF (Python Core)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 15, bold=True)

        self.LINE_GROWTH_SPEED = 0.010
        self.ROBOT_SPEED = 0.40

        self.recalculate()

    def recalculate(self):
        solver = CBSDStarLiteSolver(
            self.cols, self.rows, self.starts, self.goals,
            self.static_obs, self.dynamic_obs
        )
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
                            if pos in self.dynamic_obs:
                                self.dynamic_obs.remove(pos)
                            else:
                                self.dynamic_obs.add(pos)
                            self.recalculate()

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def draw(self):
        self.screen.fill((248, 249, 250))

        # --- HUD ПАНЕЛЬ ---
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, self.width, HUD_HEIGHT))
        pygame.draw.line(self.screen, (226, 232, 240), (0, HUD_HEIGHT), (self.width, HUD_HEIGHT), 2)

        is_found = all(len(p) > 0 for p in self.raw_paths) if self.raw_paths else False
        status_txt = f"Гибрид CBS-D* Lite: {self.exec_time_ms:.2f} ms | ОЗУ: {self.peak_memory_kb:.1f} KB"
        info_txt = f"Статус: {'Траектории без конфликтов ' if is_found else 'БЛОКИРОВКА!'} | Клик — динамическая среда"

        t1 = self.font.render(status_txt, True, (30, 41, 59))
        t2 = self.font.render(info_txt, True, (16, 185, 129) if is_found else (225, 29, 72))
        self.screen.blit(t1, (15, 12))
        self.screen.blit(t2, (15, 38))
        legend_x = self.width - 280
        legend_y = 15
        
        # Заголовок легенды
        # --- ЛЕГЕНДА АГЕНТОВ ---
        legend_x = self.width - 340
        legend_y = 12
        
        # Заголовок легенды
        leg_title = self.font.render("Легенда (Старт / Цель):", True, (100, 116, 139))
        self.screen.blit(leg_title, (legend_x, legend_y))
          
        for idx, theme in enumerate(AGENT_THEMES):
            if idx >= len(self.starts):
                break
            
            # Смещаем каждого агента по горизонтали
            item_x = legend_x + (idx * 105)
            item_y = legend_y + 22

            # 1. Значок старта (закрашенный квадратик)
            pygame.draw.rect(self.screen, theme["main"], (item_x, item_y + 4, 12, 12), border_radius=2)
            
            # 2. Значок цели (пустой квадратик с обводкой)
            # Добавим небольшой контрастный подложечный квадрат или отступ, чтобы обводка не терялась
            target_box_rect = (item_x + 18, item_y + 4, 12, 12)
            pygame.draw.rect(self.screen, (255, 255, 255), target_box_rect) # белая подложка для изоляции цвета
            pygame.draw.rect(self.screen, theme["main"], target_box_rect, 2, border_radius=2)
            
            # Текст с номером агента
            agent_lbl = self.font.render(f"Р{idx + 1}", True, (30, 41, 59))
            self.screen.blit(agent_lbl, (item_x + 36, item_y))
        # --- СЕТКА И ПРЕПЯТСТВИЯ ---
        for x in range(self.cols):
            for y in range(self.rows):
                rect = (x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, 1)

                cell = (x, y)
                if cell in self.static_obs:
                    pygame.draw.rect(self.screen, (47, 63, 86), rect)
                elif cell in self.dynamic_obs:
                    pygame.draw.rect(self.screen, (225, 29, 72), rect)

        # --- ПРОРАСТАНИЕ ЛИНИЙ ---
        if self.path_reveal_progress < 1.0:
            self.path_reveal_progress = min(1.0, self.path_reveal_progress + self.LINE_GROWTH_SPEED)

        for idx, smooth_pts in enumerate(self.smoothed_paths):
            if not smooth_pts:
                continue

            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]
            visible_pts = get_partial_path(smooth_pts, self.path_reveal_progress)

            if len(visible_pts) > 1:
                pygame.draw.lines(self.screen, theme["glow"], False, visible_pts, 8)
                pygame.draw.lines(self.screen, theme["main"], False, visible_pts, 4)

            # Старты и цели
            sp, gp = self.starts[idx], self.goals[idx]
            s_rect = (sp[0] * CELL_SIZE + 3, HUD_HEIGHT + sp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            g_rect = (gp[0] * CELL_SIZE + 3, HUD_HEIGHT + gp[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)

            pygame.draw.rect(self.screen, theme["main"], s_rect, border_radius=4)
            pygame.draw.rect(self.screen, theme["main"], g_rect, 2, border_radius=4)

        # --- ПЛАВНАЯ 60 FPS АНИМАЦИЯ РОБОТОВ ---
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

            # Линейная интерполяция (lerp)
            rx = p1[0] + (p2[0] - p1[0]) * st["sub"]
            ry = p1[1] + (p2[1] - p1[1]) * st["sub"]

            theme = AGENT_THEMES[idx % len(AGENT_THEMES)]
            pygame.draw.circle(self.screen, theme["robot"], (int(rx), int(ry)), CELL_SIZE // 3)

        pygame.display.flip()