import concurrent.futures
import sys
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from UI.hybride_UI import PathfindingGUI

def main():
    cols, rows = 36, 22
    starts = [(2, 2), (2, 19), (33, 2)]
    goals = [(33, 19), (33, 2), (2, 19)]
    
    static_obs = set()
    obstacle_density = 0.20  
    for x in range(cols):
        for y in range(rows):
            if random.random() < obstacle_density:
                pos = (x, y)
                if pos not in starts and pos not in goals:
                    static_obs.add(pos)

    app = PathfindingGUI(cols, rows, starts, goals, static_obs)
    app.run()

if __name__ == "__main__":
    main()