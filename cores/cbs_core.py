import math
import heapq
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
class SpaceTimeAStar:
    def __init__(self, cols, rows, static_obs, dynamic_obs):
        self.cols = cols
        self.rows = rows
        self.static_obs = static_obs
        self.dynamic_obs = dynamic_obs
    def heuristic(self, a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (SQRT2 - 1.0) * min(dx, dy)
    def is_blocked(self, x, y):
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return True
        return (x, y) in self.static_obs or (x, y) in self.dynamic_obs
    def find_path(self, agent_id, start, goal, constraints):
        open_set = []
        start_state = (start[0], start[1], 0)
        heapq.heappush(open_set, (self.heuristic(start, goal), 0, start_state))
        g_score = {start_state: 0}
        parent = {}
        max_time = self.cols * self.rows * 2
        dx = [0, 1, 0, -1, 1, 1, -1, -1, 0]
        dy = [1, 0, -1, 0, 1, -1, 1, -1, 0]
        while open_set:
            _, current_g, (cx, cy, ct) = heapq.heappop(open_set)
            if (cx, cy) == goal:
                path = []
                curr = (cx, cy, ct)
                while curr in parent:
                    path.append((curr[0], curr[1]))
                    curr = parent[curr]
                path.append(start)
                path.reverse()
                return path
            if ct >= max_time:
                continue
            for i in range(9):
                nx, ny = cx + dx[i], cy + dy[i]
                nt = ct + 1
                if i < 8 and self.is_blocked(nx, ny):
                    continue
                if i < 8 and dx[i] != 0 and dy[i] != 0:
                    if self.is_blocked(cx + dx[i], cy) or self.is_blocked(cx, cy + dy[i]):
                        continue
                v_con = (agent_id, nx, ny, nt, False, -1, -1)
                e_con = (agent_id, nx, ny, nt, True, cx, cy)
                if v_con in constraints or e_con in constraints:
                    continue
                step_cost = SQRT2 if (dx[i] != 0 and dy[i] != 0) else 1.0
                new_g = current_g + step_cost
                next_state = (nx, ny, nt)
                if next_state not in g_score or new_g < g_score[next_state]:
                    g_score[next_state] = new_g
                    parent[next_state] = (cx, cy, ct)
                    f_score = new_g + self.heuristic((nx, ny), goal)
                    heapq.heappush(open_set, (f_score, new_g, next_state))
        return []
class CBSSolver:
    def __init__(self, cols, rows, starts, goals, static_obs, dynamic_obs):
        self.cols = cols
        self.rows = rows
        self.starts = starts
        self.goals = goals
        self.static_obs = static_obs
        self.dynamic_obs = dynamic_obs
    def get_first_conflict(self, paths):
        max_t = max((len(p) for p in paths if p), default=0)
        for t in range(max_t):
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    if not paths[i] or not paths[j]:
                        continue
                    pos_i = paths[i][t] if t < len(paths[i]) else paths[i][-1]
                    pos_j = paths[j][t] if t < len(paths[j]) else paths[j][-1]
                    if pos_i == pos_j:
                        return {"a1": i, "a2": j, "x": pos_i[0], "y": pos_i[1], "t": t, "is_edge": False}
                    if t > 0 and t < len(paths[i]) and t < len(paths[j]):
                        prev_i = paths[i][t - 1]
                        prev_j = paths[j][t - 1]
                        if pos_i == prev_j and pos_j == prev_i:
                            return {
                                "a1": i, "a2": j, "x": pos_i[0], "y": pos_i[1], "t": t,
                                "is_edge": True, "px1": prev_i[0], "py1": prev_i[1],
                                "px2": prev_j[0], "py2": prev_j[1]
                            }
        return None
    def solve(self):
        tracemalloc.start()
        start_time = time.perf_counter()
        low_level = SpaceTimeAStar(self.cols, self.rows, self.static_obs, self.dynamic_obs)
        open_tree = []
        node_id = 0
        root_constraints = set()
        root_paths = []
        for i in range(len(self.starts)):
            p = low_level.find_path(i, self.starts[i], self.goals[i], root_constraints)
            root_paths.append(p)
        root_cost = sum(len(p) for p in root_paths)
        heapq.heappush(open_tree, (root_cost, node_id, root_constraints, root_paths))
        solution_paths = []
        while open_tree:
            cost, _, constraints, paths = heapq.heappop(open_tree)
            conflict = self.get_first_conflict(paths)
            if not conflict:
                solution_paths = paths
                break
            for a in [conflict["a1"], conflict["a2"]]:
                new_constraints = set(constraints)
                if not conflict["is_edge"]:
                    new_constraints.add((a, conflict["x"], conflict["y"], conflict["t"], False, -1, -1))
                else:
                    px = conflict["px1"] if a == conflict["a1"] else conflict["px2"]
                    py = conflict["py1"] if a == conflict["a1"] else conflict["py2"]
                    new_constraints.add((a, conflict["x"], conflict["y"], conflict["t"], True, px, py))
                new_paths = list(paths)
                new_paths[a] = low_level.find_path(a, self.starts[a], self.goals[a], new_constraints)
                if new_paths[a]:
                    new_cost = sum(len(p) for p in new_paths)
                    node_id += 1
                    heapq.heappush(open_tree, (new_cost, node_id, new_constraints, new_paths))
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "paths": solution_paths,
            "exec_time_ms": exec_time_ms,
            "peak_memory_kb": peak_mem / 1024.0
        }