import math
import time
import tracemalloc
import heapq

SQRT2 = math.sqrt(2)

# --- 1. СГЛАЖИВАНИЕ И АНИМАЦИЯ ---
def smooth_path_chaikin(points, iterations=3):
    """Сглаживает углы 90°/45° алгоритмом Чайкина (Corner Cutting)."""
    if len(points) < 3:
        return points

    pts = list(points)
    for _ in range(iterations):
        new_pts = [pts[0]]
        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]

            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])

            new_pts.extend([q, r])
        new_pts.append(pts[-1])
        pts = new_pts
    return pts

def get_partial_path(pts, progress):
    """Возвращает срез точек для анимации прорастания линии."""
    if not pts:
        return []
    if progress >= 1.0:
        return pts

    total_segments = len(pts) - 1
    current_length = total_segments * progress
    idx = int(current_length)
    frac = current_length - idx

    result = pts[:idx + 1]
    if idx < len(pts) - 1 and frac > 0:
        p1 = pts[idx]
        p2 = pts[idx + 1]
        interp_point = (p1[0] + (p2[0] - p1[0]) * frac, p1[1] + (p2[1] - p1[1]) * frac)
        result.append(interp_point)

    return result


# --- 2. НИЖНИЙ УРОВЕНЬ: Space-Time D* Lite ---
class SpaceTimeDStarLite:
    def __init__(self, cols, rows, start, goal, static_obs, dynamic_obs):
        self.cols = cols
        self.rows = rows
        self.start = start
        self.goal = goal
        self.obs = set(static_obs) | set(dynamic_obs)

    def heuristic(self, a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (SQRT2 - 1.0) * min(dx, dy)

    def plan(self, constraints):
        """
        Ищет кратчайший путь с учетом пространственно-временных ограничений CBS.
        constraints: set состояний (x, y, t) или рёбер (u_x, u_y, v_x, v_y, t).
        """
        # (f_score, g_score, x, y, t)
        open_set = [(self.heuristic(self.start, self.goal), 0, self.start[0], self.start[1], 0)]
        came_from = {}
        g_score = {(self.start, 0): 0}

        max_horizon = self.cols * self.rows * 2

        while open_set:
            _, current_g, x, y, t = heapq.heappop(open_set)
            curr_pos = (x, y)

            if curr_pos == self.goal:
                # Сборка пути
                path = []
                curr_state = (curr_pos, t)
                while curr_state in came_from:
                    path.append(curr_state[0])
                    curr_state = came_from[curr_state]
                path.append(self.start)
                return path[::-1]

            if t > max_horizon:
                continue

            # 8 направлений + ожидание на месте
            dx = [0, 0, 1, 0, -1, 1, 1, -1, -1]
            dy = [0, 1, 0, -1, 0, 1, -1, 1, -1]

            for i in range(9):
                nx, ny = x + dx[i], y + dy[i]
                next_pos = (nx, ny)
                next_t = t + 1

                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                if next_pos in self.obs:
                    continue

                # Диагональный запрет срезания углов
                if abs(dx[i]) == 1 and abs(dy[i]) == 1:
                    if (x + dx[i], y) in self.obs or (x, y + dy[i]) in self.obs:
                        continue
                    step_cost = SQRT2
                else:
                    step_cost = 1.0 if (dx[i] != 0 or dy[i] != 0) else 0.8

                # Проверка ограничений CBS (вершинные и рёберные)
                if (nx, ny, next_t) in constraints:
                    continue
                if (x, y, nx, ny, next_t) in constraints:
                    continue

                new_g = current_g + step_cost
                state_key = (next_pos, next_t)

                if new_g < g_score.get(state_key, float('inf')):
                    g_score[state_key] = new_g
                    f_score = new_g + self.heuristic(next_pos, self.goal)
                    came_from[state_key] = ((x, y), t)
                    heapq.heappush(open_set, (f_score, new_g, nx, ny, next_t))

        return []


# --- 3. ВЕРХНИЙ УРОВЕНЬ: CBS ДЕРЕВО КОНФЛИКТОВ ---
class CBSDStarLiteSolver:
    def __init__(self, cols, rows, starts, goals, static_obs, dynamic_obs):
        self.cols = cols
        self.rows = rows
        self.starts = starts
        self.goals = goals
        self.static_obs = static_obs
        self.dynamic_obs = dynamic_obs
        self.num_agents = len(starts)

    def detect_conflict(self, paths):
        """Поиск первого вершинного или рёберного конфликта между агентами."""
        max_len = max((len(p) for p in paths), default=0)
        for t in range(max_len):
            # 1. Вершинные конфликты (Vertex Conflicts)
            pos_map = {}
            for agent_id, path in enumerate(paths):
                pos = path[t] if t < len(path) else (path[-1] if path else None)
                if pos is None:
                    continue
                if pos in pos_map:
                    return {
                        "type": "vertex",
                        "agent1": pos_map[pos],
                        "agent2": agent_id,
                        "pos": pos,
                        "time": t
                    }
                pos_map[pos] = agent_id

            # 2. Рёберные конфликты (Edge Conflicts)
            if t > 0:
                for a1 in range(self.num_agents):
                    for a2 in range(a1 + 1, self.num_agents):
                        p1, p2 = paths[a1], paths[a2]
                        u1 = p1[t - 1] if t - 1 < len(p1) else (p1[-1] if p1 else None)
                        v1 = p1[t] if t < len(p1) else (p1[-1] if p1 else None)
                        u2 = p2[t - 1] if t - 1 < len(p2) else (p2[-1] if p2 else None)
                        v2 = p2[t] if t < len(p2) else (p2[-1] if p2 else None)

                        if u1 and v1 and u2 and v2 and u1 == v2 and v1 == u2:
                            return {
                                "type": "edge",
                                "agent1": a1,
                                "agent2": a2,
                                "u": u1,
                                "v": v1,
                                "time": t
                            }
        return None

    def solve(self):
        tracemalloc.start()
        start_time = time.perf_counter()

        # Базовый узел дерева конфликтов (Constraint Tree Node)
        root_constraints = [set() for _ in range(self.num_agents)]
        root_paths = []

        for i in range(self.num_agents):
            planner = SpaceTimeDStarLite(
                self.cols, self.rows, self.starts[i], self.goals[i],
                self.static_obs, self.dynamic_obs
            )
            p = planner.plan(root_constraints[i])
            root_paths.append(p)

        root_cost = sum(len(p) for p in root_paths)
        # Priority Queue: (cost, id, constraints, paths)
        open_tree = [(root_cost, 0, root_constraints, root_paths)]
        node_id = 1

        solution_paths = []

        while open_tree:
            cost, _, constraints, paths = heapq.heappop(open_tree)
            conflict = self.detect_conflict(paths)

            if not conflict:
                solution_paths = paths
                break

            # Создание дочерних узлов для разрешения конфликта
            if conflict["type"] == "vertex":
                agents = [conflict["agent1"], conflict["agent2"]]
                for a in agents:
                    new_constraints = [set(c) for c in constraints]
                    new_constraints[a].add((conflict["pos"][0], conflict["pos"][1], conflict["time"]))

                    planner = SpaceTimeDStarLite(
                        self.cols, self.rows, self.starts[a], self.goals[a],
                        self.static_obs, self.dynamic_obs
                    )
                    new_path = planner.plan(new_constraints[a])

                    if new_path:
                        new_paths = list(paths)
                        new_paths[a] = new_path
                        new_cost = sum(len(p) for p in new_paths)
                        heapq.heappush(open_tree, (new_cost, node_id, new_constraints, new_paths))
                        node_id += 1

            elif conflict["type"] == "edge":
                agents = [conflict["agent1"], conflict["agent2"]]
                edges = [
                    (conflict["u"][0], conflict["u"][1], conflict["v"][0], conflict["v"][1], conflict["time"]),
                    (conflict["v"][0], conflict["v"][1], conflict["u"][0], conflict["u"][1], conflict["time"])
                ]

                for a, edge in zip(agents, edges):
                    new_constraints = [set(c) for c in constraints]
                    new_constraints[a].add(edge)

                    planner = SpaceTimeDStarLite(
                        self.cols, self.rows, self.starts[a], self.goals[a],
                        self.static_obs, self.dynamic_obs
                    )
                    new_path = planner.plan(new_constraints[a])

                    if new_path:
                        new_paths = list(paths)
                        new_paths[a] = new_path
                        new_cost = sum(len(p) for p in new_paths)
                        heapq.heappush(open_tree, (new_cost, node_id, new_constraints, new_paths))
                        node_id += 1

        exec_time = (time.perf_counter() - start_time) * 1000.0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "paths": solution_paths,
            "exec_time_ms": exec_time,
            "peak_memory_kb": peak_mem / 1024.0
        }