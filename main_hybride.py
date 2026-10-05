import concurrent.futures
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from UI.hybride_UI import PathfindingGUI

def main():
    cols, rows = 36, 22
    starts = [(2, 2), (2, 19), (33, 2)]
    goals = [(33, 19), (33, 2), (2, 10)]
    
    static_obs = set()
    for y in range(1, 21):
        if y not in (5, 6, 10, 11, 15, 16):  
            static_obs.add((11, y))
            static_obs.add((24, y))
    for x in range(1, 35):
        if x not in (5, 6, 17, 18, 29, 30):  
            static_obs.add((x, 7))
            static_obs.add((x, 14))
    for pos in starts + goals:
        static_obs.discard(pos)

    app = PathfindingGUI(cols, rows, starts, goals, static_obs)
    app.run()

if __name__ == "__main__":
    main()