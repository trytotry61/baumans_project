import concurrent.futures
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from UI.dstar_lite_UI import PathfindingGUI

def main():
    cols, rows = 36, 22
    starts = [(2, 2), (33, 19)]
    goals = [(33, 19), (2, 2)]
    static_obs = set()
    for y in range(5, 17, 4):
        for x in range(5, 31):
            if x % 6 != 0:
                static_obs.add((x, y))
    app = PathfindingGUI(cols, rows, starts, goals, static_obs)
    app.run()
if __name__ == "__main__":
    main()