import csv
import os
import random
from hybride_core import CBSDStarLiteSolver
def generate_random_scenario(cols, rows, static_obs, num_agents, seed=None):
    if seed is not None:
        random.seed(seed)
    available_cells = [(x, y) for x in range(cols) for y in range(rows) if (x, y) not in static_obs]
    if len(available_cells) < num_agents * 2:
        raise ValueError("Слишком мало места!")
    chosen = random.sample(available_cells, num_agents * 2)
    return chosen[:num_agents], chosen[num_agents:]
def run_benchmark_hybrid(csv_filename="metrics_hybrid.csv", max_agents=10, iterations=5):
    cols, rows = 36, 22
    static_obs = {(x, y) for y in range(5, 17, 4) for x in range(5, 31) if x % 6 != 0}
    dynamic_obs = set()
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Algorithm", "Num_Agents", "Iteration", "Exec_Time_ms", "Peak_Memory_KB", "Sum_of_Costs", "Makespan"])
        print(f"ЗАПУСК БЕНЧМАРКА: CBS-D* Lite (до {max_agents} агентов)")
        for agents_count in range(1, max_agents + 1):
            for i in range(iterations):
                starts, goals = generate_random_scenario(cols, rows, static_obs, agents_count, seed=agents_count * 100 + i)
                solver = CBSDStarLiteSolver(cols, rows, starts, goals, static_obs, dynamic_obs)
                try:
                    res = solver.solve()
                    paths = res["paths"]
                    time_ms, mem_kb = res["exec_time_ms"], res["peak_memory_kb"]
                    sum_costs = sum(len(p) for p in paths)
                    makespan = max((len(p) for p in paths), default=0)
                    writer.writerow(["CBS-D*Lite", agents_count, i + 1, round(time_ms, 3), round(mem_kb, 2), sum_costs, makespan])
                    print(f"[CBS-D*Lite] Агентов: {agents_count} | Итер: {i+1}/{iterations} | Время: {time_ms:.1f}ms | ОЗУ: {mem_kb:.1f}KB")
                except Exception as e:
                    print(f"[CBS-D*Lite] Ошибка (Агентов: {agents_count}, Итер: {i+1}): {e}")

if __name__ == "__main__":
    run_benchmark_hybrid(max_agents=10, iterations=5)