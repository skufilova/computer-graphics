import tkinter as tk
import random
import math


class MountainVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Task 2")

        self.canvas = tk.Canvas(self.root, bg="white", width=800, height=400)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.roughness = tk.DoubleVar(value=0.2)
        self.iterations = tk.IntVar(value=5)
        self.step_delay = tk.IntVar(value=500)

        control_frame = tk.Frame(self.root)
        control_frame.pack()

        tk.Label(control_frame, text="Roughness:").pack(side=tk.LEFT)
        self.roughness_slider = tk.Scale(control_frame, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, variable=self.roughness)
        self.roughness_slider.pack(side=tk.LEFT)

        tk.Label(control_frame, text="Iterations:").pack(side=tk.LEFT)
        self.iterations_slider = tk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL, variable=self.iterations)
        self.iterations_slider.pack(side=tk.LEFT)

        tk.Label(control_frame, text="Step Delay (ms):").pack(side=tk.LEFT)
        self.delay_slider = tk.Scale(control_frame, from_=100, to=2000, orient=tk.HORIZONTAL, variable=self.step_delay)
        self.delay_slider.pack(side=tk.LEFT)

        tk.Button(control_frame, text="Generate", command=self.start_generation).pack(side=tk.LEFT)

        # При открытии окна показываем исходную горизонтальную линию
        self.points = [(0, 0), (1, 0)]
        self.animation_id = None  # Запланированный вызов анимации
        self.canvas.bind("<Configure>", self.on_resize)
        self.root.after_idle(self.draw_mountain)

    def on_resize(self, event):
        self.draw_mountain()

    def midpoint_displacement_step(self, points, roughness):
        #смещаем середину каждого отрезка
        new_points = []
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            length = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
            displacement = random.uniform(-1, 1) * roughness * length
            mid_y += displacement

            new_points.append(p1)
            new_points.append((mid_x, mid_y))

        new_points.append(points[-1])
        return new_points

    def draw_mountain(self):
        self.canvas.delete("all")
        if len(self.points) < 2:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 2 or height <= 2:
            return

        margin = 10

        # Масштабирование по Y
        max_abs_y = max(abs(y) for _, y in self.points)
        y_scale = (height / 2 - margin) / max(1, max_abs_y)

        screen_points = []
        for x, y in self.points:
            screen_x = margin + x * (width - 2 * margin)
            screen_y = height / 2 + y * y_scale
            screen_points.append((screen_x, screen_y))

        for i in range(len(screen_points) - 1):
            self.canvas.create_line(screen_points[i][0], screen_points[i][1], screen_points[i + 1][0], screen_points[i + 1][1], fill="black", width=2)

    def animate_step(self, depth, roughness):
        self.animation_id = None
        if depth <= 0:
            return

        self.points = self.midpoint_displacement_step(self.points, roughness)
        self.draw_mountain()

        if depth > 1:
            self.animation_id = self.root.after(self.step_delay.get(), self.animate_step, depth - 1, roughness)

    def start_generation(self):
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

        self.points = [(0, 0), (1, 0)]
        self.draw_mountain() 

        roughness = self.roughness.get()
        iterations = self.iterations.get()
        self.animation_id = self.root.after(self.step_delay.get(), self.animate_step, iterations, roughness)


if __name__ == "__main__":
    root = tk.Tk()
    app = MountainVisualizer(root)
    root.mainloop()
