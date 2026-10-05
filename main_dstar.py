import concurrent.futures
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from UI.dstar_lite_UI import PathfindingGUI

def main():
    cols, rows = 36, 22
    # Оставляем двух агентов без изменений
    starts = [(2, 2), (33, 19)]
    goals = [(33, 19), (2, 2)]
    
    static_obs = set()

    # Формируем планировку комнат и коридоров (вертикальные стены)
    for y in range(1, 21):
        if y not in (5, 6, 10, 11, 15, 16):  # Дверные проемы / коридоры
            static_obs.add((11, y))
            static_obs.add((24, y))

    # Горизонтальные стены с проходами (коридорами)
    for x in range(1, 35):
        if x not in (5, 6, 17, 18, 29, 30):  # Дверные проемы / коридоры
            static_obs.add((x, 7))
            static_obs.add((x, 14))

    # Убеждаемся, что точки старта и финиша не перекрыты стенами
    for pos in starts + goals:
        static_obs.discard(pos)

    app = PathfindingGUI(cols, rows, starts, goals, static_obs)
    app.run()

if __name__ == "__main__":
    main()