from hybride_UI import PathfindingGUI

def main():
    cols, rows = 36, 22

    # Задаем 3 роботов с пересекающимися маршрутами
    starts = [(2, 2), (2, 19), (33, 2)]
    goals = [(33, 19), (33, 2), (2, 19)]

    # Статические стеллажи складского помещения
    static_obs = set()
    for y in range(5, 17, 4):
        for x in range(5, 31):
            if x % 6 != 0:
                static_obs.add((x, y))

    app = PathfindingGUI(cols, rows, starts, goals, static_obs)
    app.run()

if __name__ == "__main__":
    main()