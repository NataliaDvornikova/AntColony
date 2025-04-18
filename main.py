import tkinter as tk
import random
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.colors as mcolors

# Параметры феромонов
FEROMON_START = 0.001
EVAPORATION = 0.0001
GRID_SIZE = 100  # условная сетка 100x100

# Максимальные значения для ввода
MAX_ANTS = 500
MAX_ITERATIONS = 5000
MAX_CITIES = 100

class City:
    """
    Класс, описывающий город.
    x, y: координаты.
    index: порядковый номер города.
    """
    def __init__(self, x: float, y: float, index: int):
        self.x = x
        self.y = y
        self.index = index

    def distance(self, other: 'City') -> float:
        """Вычисляет расстояние до другого города."""
        return math.hypot(self.x - other.x, self.y - other.y)

class AntColony:
    """
    Класс, реализующий муравьиный алгоритм для задачи коммивояжера.
    cities: список объектов City.
    ant_count: число муравьев в каждой итерации.
    iterations: число итераций.
    """
    def __init__(self, cities, ant_count: int, iterations: int):
        self.cities = cities
        self.N = len(cities)
        self.ant_count = ant_count
        self.iterations = iterations
        self.pheromone = [[FEROMON_START]*self.N for _ in range(self.N)]
        self.distance = [[cities[i].distance(cities[j]) for j in range(self.N)] for i in range(self.N)]
        self.best_path = None
        self.best_length = float('inf')
        self.lengths_over_time = []
        self.all_paths = []

    def run(self):
        """Запуск алгоритма: N итераций поиска."""
        for _ in range(self.iterations):
            paths = []
            for _ in range(self.ant_count):
                path = self.generate_path()
                length = self.calculate_length(path)
                paths.append((path, length))
                self.spread_pheromones(path, length)
                if length < self.best_length:
                    self.best_length = length
                    self.best_path = path
            self.evaporate()
            self.lengths_over_time.append(self.best_length)
            self.all_paths.append(paths)

    def generate_path(self):
        """Генерация одного пути одним муравьем."""
        path = []
        visited = set()
        current = random.randrange(self.N)
        for _ in range(self.N):
            path.append(current)
            visited.add(current)
            choices = []
            for j in range(self.N):
                if j not in visited:
                    pher = self.pheromone[current][j]
                    dist = self.distance[current][j]
                    choices.append((j, pher / dist))
            if not choices:
                break
            total = sum(p for _, p in choices)
            r = random.random() * total
            acc = 0
            for city, prob in choices:
                acc += prob
                if acc >= r:
                    current = city
                    break
        return path

    def calculate_length(self, path) -> float:
        """Считает длину маршрута замкнутого контура."""
        return sum(self.distance[path[i]][path[(i+1)%self.N]] for i in range(len(path)))

    def spread_pheromones(self, path, length: float):
        """Добавляет феромон вдоль пройденного пути."""
        deposit = FEROMON_START / length
        for i in range(len(path)):
            a, b = path[i], path[(i+1)%len(path)]
            self.pheromone[a][b] += deposit
            self.pheromone[b][a] = self.pheromone[a][b]

    def evaporate(self):
        """Испарение феромонов: уменьшаем концентрацию на всех ребрах."""
        decay = 1 - EVAPORATION
        for i in range(self.N):
            for j in range(self.N):
                self.pheromone[i][j] *= decay

class App:
    """Графический интерфейс для демонстрации алгоритма."""
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Муравьиный алгоритм — TSP")
        self.cities = []
        self.history = []
        self.running = False
        self.colony = None

        self.root.geometry('1000x700')
        self.root.minsize(800,600)

        # карта
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_canvas())
        self.canvas.bind("<Button-1>", self.add_city)

        # панель управления
        control = tk.Frame(root)
        control.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(control, text=f"Кол-во муравьев (max {MAX_ANTS}):", font=(None,12)).pack(pady=2)
        self.ant_entry = tk.Entry(control, font=(None,12)); self.ant_entry.insert(0, "10"); self.ant_entry.pack()
        tk.Label(control, text=f"Итерации (max {MAX_ITERATIONS}):", font=(None,12)).pack(pady=2)
        self.iter_entry = tk.Entry(control, font=(None,12)); self.iter_entry.insert(0, "20"); self.iter_entry.pack()
        tk.Label(control, text=f"Города (max {MAX_CITIES}):", font=(None,12)).pack(pady=2)

        btn_frame = tk.Frame(control); btn_frame.pack(pady=5)
        self.start_btn = tk.Button(btn_frame, text="Старт", command=self.start, font=(None,12))
        self.start_btn.grid(row=0, column=0, padx=5)
        self.stop_btn = tk.Button(btn_frame, text="Стоп", command=self.stop, font=(None,12))
        self.stop_btn.grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Сброс", command=self.clear, font=(None,12)).grid(row=0, column=2, padx=5)

        # график
        self.fig, self.ax = plt.subplots(figsize=(5,4))
        self.ax.set_xlabel("Итерация", fontsize=12)
        self.ax.set_ylabel("Длина лучшего пути", fontsize=12)
        self.line, = self.ax.plot([], [], 'g-', linewidth=2)
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=control)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.length_label = tk.Label(control, text="Оптимальная длина маршрута: -", font=(None,12))
        self.length_label.pack(pady=5)

        self.draw_canvas()

    def draw_grid(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        step_x, step_y = w/GRID_SIZE, h/GRID_SIZE
        self.canvas.delete('grid')
        for i in range(GRID_SIZE+1):
            x, y = i*step_x, i*step_y
            self.canvas.create_line(x,0,x,h, fill="#ddd", tags='grid')
            self.canvas.create_line(0,y,w,y, fill="#ddd", tags='grid')

    def add_city(self, event):
        if self.running or len(self.cities) >= MAX_CITIES:
            return
        idx = len(self.cities)
        self.cities.append(City(event.x, event.y, idx))
        self.draw_canvas()

    def clear(self):
        if self.running:
            return
        self.cities.clear()
        self.history.clear()
        self.colony = None
        self.ax.clear()
        self.ax.set_xlabel("Итерация", fontsize=12)
        self.ax.set_ylabel("Длина лучшего пути", fontsize=12)
        self.line, = self.ax.plot([], [], 'g-', linewidth=2)
        self.length_label.config(text="Оптимальная длина маршрута: -")
        self.canvas_plot.draw()
        self.draw_canvas()

    def draw_canvas(self, best_path=None, show_final=False):
        self.canvas.delete("all")
        self.draw_grid()
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        # визуализация накопленных феромонов (полупрозрачные линии)
        if self.colony:
            pher = self.colony.pheromone
            # определим диапазон
            flat = [pher[i][j] for i in range(self.colony.N) for j in range(self.colony.N)]
            min_p, max_p = min(flat), max(flat)
            for i in range(self.colony.N):
                for j in range(i+1, self.colony.N):
                    p = pher[i][j]
                    if p <= FEROMON_START: continue
                    # нормируем и вычисляем цвет и толщину
                    norm = (p - min_p) / (max_p - min_p)
                    # цвет: от бледно-голубого к насыщенно-синему
                    r = int(255*(1 - norm))
                    g = int(255*(1 - norm))
                    b = 255
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    width = 1 + norm*4
                    # рисуем полупрозрачную линию
                    self.canvas.create_line(
                        self.cities[i].x, self.cities[i].y,
                        self.cities[j].x, self.cities[j].y,
                        fill=color, width=width, stipple='gray50', tags='pher')
        # рисуем города и подписи
        for city in self.cities:
            letter = chr(65 + city.index)
            self.canvas.create_oval(city.x-5, city.y-5, city.x+5, city.y+5, fill="red")
            gx, gy = city.x*GRID_SIZE/w, city.y*GRID_SIZE/h
            self.canvas.create_text(city.x+10, city.y-10,
                                    text=f"{letter} ({gx:.1f},{gy:.1f})",
                                    font=(None,12,'bold'), fill="black")
        # финальный маршрут
        if show_final and best_path:
            for idx in range(len(best_path)):
                a, b = self.cities[best_path[idx]], self.cities[best_path[(idx+1)%len(best_path)]]
                self.canvas.create_line(a.x, a.y, b.x, b.y, fill="red", width=3, tags="final")
                d = a.distance(b)
                mx, my = (a.x+b.x)/2, (a.y+b.y)/2
                self.canvas.create_text(mx, my, text=f"{d:.1f}", font=(None,12), fill="blue")

    def start(self):
        if self.running or len(self.cities)<2:
            return
        ants = min(int(self.ant_entry.get()), MAX_ANTS)
        iters = min(int(self.iter_entry.get()), MAX_ITERATIONS)
        self.running = True
        self.colony = AntColony(self.cities, ants, iters)
        self.colony.run()
        self.history.append(self.colony.lengths_over_time)
        self.animate(self.colony)
        self.draw_canvas(best_path=self.colony.best_path, show_final=True)
        self.length_label.config(text=f"Оптимальная длина маршрута: {self.colony.best_length:.2f}")
        self.update_plot()
        self.running = False

    def stop(self):
        self.running = False

    def animate(self, colony):
        norm = mcolors.Normalize(vmin=min(min(row) for row in colony.pheromone),
                                 vmax=max(max(row) for row in colony.pheromone))
        cmap = plt.cm.Blues
        for paths_it in colony.all_paths:
            if not self.running:
                break
            self.draw_canvas()
            for path, length in paths_it:
                for i in range(len(path)):
                    a, b = colony.cities[path[i]], colony.cities[path[(i+1)%len(path)]]
                    color = mcolors.to_hex(cmap(norm(colony.pheromone[path[i]][path[(i+1)%len(path)]])))
                    dash = None if path == colony.best_path and length == colony.best_length else (4,4)
                    width = 3 if dash is None else 1
                    self.canvas.create_line(a.x, a.y, b.x, b.y, fill=color, width=width, dash=dash, tags="path")
            self.root.update()
            self.root.after(50)

    def update_plot(self):
        x = list(range(1, len(self.history[-1]) + 1))
        y = self.history[-1]
        self.line.set_data(x, y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas_plot.draw()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
