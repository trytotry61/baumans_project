import math
import time
import tracemalloc
SQRT2 = math.sqrt(2)
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
    """Возвращает срез точек для анимации прорастания линии от 0.0 до 1.0."""
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
class DStarLite:
    def __init__(self, cols, rows, start, goal, static_obs):
        self.cols = cols
        self.rows = rows
        self.start = tuple(start)
        self.goal = tuple(goal)
        self.obs = set(static_obs)
        self.reset_search()
    def reset_search(self):
        self.U = {}
        self.km = 0
        self.rhs = {}
        self.g = {}
        self.rhs[self.goal] = 0
        self.U[self.goal] = self.calculate_key(self.goal)
    def heuristic(self, a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (SQRT2 - 1.0) * min(dx, dy)
    def calculate_key(self, s):
        g_val = self.g.get(s, float('inf'))
        rhs_val = self.rhs.get(s, float('inf'))
        min_val = min(g_val, rhs_val)
        return (min_val + self.heuristic(self.start, s) + self.km, min_val)
    def get_grid_neighbors(self, u):
        neighbors = []
        dx = [0, 1, 0, -1, 1, 1, -1, -1]
        dy = [1, 0, -1, 0, 1, -1, 1, -1]
        for i in range(8):
            nx, ny = u[0] + dx[i], u[1] + dy[i]
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                neighbors.append((nx, ny))
        return neighbors
    def cost(self, u, v):
        if u in self.obs or v in self.obs:
            return float('inf')
        if abs(u[0] - v[0]) == 1 and abs(u[1] - v[1]) == 1:
            if (u[0], v[1]) in self.obs or (v[0], u[1]) in self.obs:
                return float('inf')
            return SQRT2
        return 1.0
    def update_vertex(self, u):
        if u != self.goal:
            min_rhs = float('inf')
            for v in self.get_grid_neighbors(u):
                min_rhs = min(min_rhs, self.cost(u, v) + self.g.get(v, float('inf')))
            self.rhs[u] = min_rhs
        if u in self.U:
            del self.U[u]
        if self.g.get(u, float('inf')) != self.rhs.get(u, float('inf')):
            self.U[u] = self.calculate_key(u)
    def compute_shortest_path(self):
        while self.U:
            u = min(self.U, key=self.U.get)
            k_old = self.U[u]
            start_key = self.calculate_key(self.start)
            if k_old >= start_key and self.rhs.get(self.start, float('inf')) == self.g.get(self.start, float('inf')):
                break
            del self.U[u]
            k_new = self.calculate_key(u)
            if k_old < k_new:
                self.U[u] = k_new
            elif self.g.get(u, float('inf')) > self.rhs.get(u, float('inf')):
                self.g[u] = self.rhs.get(u, float('inf'))
                for s in self.get_grid_neighbors(u):
                    self.update_vertex(s)
            else:
                self.g[u] = float('inf')
                for s in self.get_grid_neighbors(u) + [u]:
                    self.update_vertex(s)
    def get_path(self):
        path = [self.start]
        curr = self.start
        visited = set([self.start])
        while curr != self.goal:
            min_cost = float('inf')
            next_node = None
            for v in self.get_grid_neighbors(curr):
                c = self.cost(curr, v)
                if c == float('inf'): continue
                val = c + self.g.get(v, float('inf'))
                if val < min_cost:
                    min_cost = val
                    next_node = v   
            if next_node is None or min_cost == float('inf') or next_node in visited:
                return []
            path.append(next_node)
            visited.add(next_node)
            curr = next_node
        return path
    def toggle_obstacle(self, pos):
        if pos == self.start or pos == self.goal:
            return self.get_path()
        if pos in self.obs:
            self.obs.remove(pos)
        else:
            self.obs.add(pos)
        self.reset_search()
        self.compute_shortest_path()
        return self.get_path()
class DStarLiteSolver:
    def __init__(self, cols, rows, starts, goals, static_obs, dynamic_obs=None):
        self.cols = cols
        self.rows = rows
        self.starts = [tuple(s) for s in starts]
        self.goals = [tuple(g) for g in goals]
        self.static_obs = set(static_obs)
        self.dynamic_obs = set(dynamic_obs) if dynamic_obs is not None else set()
        full_obs = self.static_obs | self.dynamic_obs
        self.agents = [
            DStarLite(cols, rows, s, g, full_obs)
            for s, g in zip(self.starts, self.goals)
        ]
    def solve(self):
        tracemalloc.start()
        start_time = time.perf_counter()
        paths = []
        for agent in self.agents:
            agent.compute_shortest_path()
            paths.append(agent.get_path())
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "paths": paths,
            "exec_time_ms": exec_time_ms,
            "peak_memory_kb": peak_mem / 1024.0
        }
    def toggle_obstacle(self, pos):
        tracemalloc.start()
        start_time = time.perf_counter()
        if pos in self.dynamic_obs:
            self.dynamic_obs.remove(pos)
        else:
            self.dynamic_obs.add(pos)
        paths = []
        for agent in self.agents:
            paths.append(agent.toggle_obstacle(pos))
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "paths": paths,
            "exec_time_ms": exec_time_ms,
            "peak_memory_kb": peak_mem / 1024.0
        }