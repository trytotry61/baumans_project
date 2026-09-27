from dstar_lite_UI import PathfindingGUI

def main():
    cols, rows = 36, 22
    start = (2, 2)
    goal = (33, 19)

    # Статические препятствия (имитация стеллажей)
    static_obs = set()
    for y in range(5, 17, 4):
        for x in range(5, 31):
            if x % 6 != 0:
                static_obs.add((x, y))

    app = PathfindingGUI(cols, rows, start, goal, static_obs)
    app.run()

if __name__ == "__main__":
    main()