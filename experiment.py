import matplotlib.pyplot as plt
import random
import numpy as np
from main import City, AntColony

def generate_random_cities(n, width=800, height=600):
    """Генерация случайных координат городов"""
    return [City(random.randint(50, width-50), random.randint(50, height-50), i) for i in range(n)]

def run_experiment(city_count=10, ant_count=30, iterations_list=[10, 20, 50, 100, 200, 500], runs_per_setting=5):
    """Запускаеv алгоритм и усредняем результат"""
    cities = generate_random_cities(city_count)
    avg_lengths = []

    for iters in iterations_list:
        lengths = []
        for _ in range(runs_per_setting):
            colony = AntColony(cities, ant_count, iters)
            colony.run()
            lengths.append(colony.best_length)
        avg = np.mean(lengths)
        avg_lengths.append(avg)
        print(f"Итерации: {iters}, средняя длина маршрута: {avg:.2f}")

    return iterations_list, avg_lengths

def plot_results(iterations, lengths):
    """Рисует график зависимости точности от количества итераций"""
    plt.figure(figsize=(8,5))
    plt.plot(iterations, lengths, marker='o', linewidth=2, color='green')
    plt.xlabel("Количество итераций")
    plt.ylabel("Средняя длина маршрута")
    plt.title("Зависимость длины маршрута от количества итераций")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Параметры (кол-во городов, муравьев в итерации, итераций)
    iterations_list, avg_lengths = run_experiment(
        city_count=20,
        ant_count=30,
        iterations_list=[10, 20, 50, 100, 200, 500, 1000, 2000, 5000],
        runs_per_setting=3
    )
    plot_results(iterations_list, avg_lengths)
