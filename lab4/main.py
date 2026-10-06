import tkinter as tk
import numpy as np
from math import cos, sin, radians

class PolygonEditor:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Панель управления
        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_label = tk.Label(control_frame, text="Выберите действие", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Поля для ввода смещения
        self.dx_entry = self.create_labeled_entry(control_frame, "dx:")
        self.dy_entry = self.create_labeled_entry(control_frame, "dy:")
        self.translate_btn = tk.Button(
            control_frame, text="Смещение", command=self.translate
        )
        self.translate_btn.pack(fill=tk.X, padx=10, pady=5)

        # Поля для ввода угла поворота
        self.angle_entry = self.create_labeled_entry(control_frame, "Угол (градусы):")

        # Чекбокс для поворота относительно центра
        self.rotate_center_var = tk.BooleanVar(value=True)
        self.rotate_center_check = tk.Checkbutton(
            control_frame, text="Поворот вокруг центра", variable=self.rotate_center_var
        )
        self.rotate_center_check.pack(fill=tk.X, padx=10)

        # Кнопка Поворот
        self.rotate_btn = tk.Button(control_frame, text="Поворот", command=self.rotate)
        self.rotate_btn.pack(fill=tk.X, padx=10, pady=5)

        # Масштабирование
        self.scale_entry = self.create_labeled_entry(control_frame, "Коэффициент масштаба:")

        # Чекбокс для масштабирования относительно центра
        self.scale_center_var = tk.BooleanVar(value=True)
        self.scale_center_check = tk.Checkbutton(
            control_frame, text="Масштабирование относительно центра", variable=self.scale_center_var
        )
        self.scale_center_check.pack(fill=tk.X, padx=10)

        self.scale_btn = tk.Button(control_frame, text="Масштабирование", command=self.scale)
        self.scale_btn.pack(fill=tk.X, padx=10, pady=5)

        # Поля для ввода точки (для преобразований относительно заданной точки)
        self.status_label_point = tk.Label(control_frame,
                                           text="Точка для преобразований\n(если не относительно центра)",
                                           font=("Arial", 10))
        self.status_label_point.pack(pady=5)

        self.x_entry = self.create_labeled_entry(control_frame, "X:")
        self.y_entry = self.create_labeled_entry(control_frame, "Y:")

        self.clear_btn = tk.Button(control_frame, text="Очистить сцену", command=self.clear_scene)
        self.clear_btn.pack(fill=tk.X, padx=10, pady=5)

        self.intersections_button = tk.Button(control_frame, text="Пересечения",
                                              command=self.check_polygon_intersections)
        self.intersections_button.pack(fill=tk.X, padx=10, pady=5)

        # Новая кнопка для динамического пересечения
        self.intersect_btn = tk.Button(control_frame, text="Динамическое пересечение", command=self.start_dynamic_intersection)
        self.intersect_btn.pack(fill=tk.X, padx=10, pady=5)

        # Кнопка для начала создания полигона
        self.create_polygon_btn = tk.Button(control_frame, text="Создать полигон", command=self.start_creating_polygon)
        self.create_polygon_btn.pack(fill=tk.X, padx=10, pady=5)

        self.message_window = tk.Text(control_frame, height=10, width=40)
        self.message_window.pack(padx=10, pady=10)

        self.polygons = []
        self.current_polygon = []
        self.selected_polygon = None
        self.is_creating_polygon = False  # Флаг для режима создания полигона
        self.checked_point_oval = None  # Для хранения координат проверяемой точки

        self.canvas.bind("<Button-1>", self.handle_left_click)
        self.canvas.bind("<Button-3>", self.check_point)

        # Для динамического режима
        self.start_point = None
        self.temp_line = None
        self.intersection_point = None
        self.temp_start_oval = None

    def create_labeled_entry(self, parent, label_text):
        """Функция для создания поля ввода с меткой"""
        frame = tk.Frame(parent)
        frame.pack(padx=10, pady=5, fill=tk.X)
        label = tk.Label(frame, text=label_text)
        label.pack(side=tk.LEFT)
        entry = tk.Entry(frame)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        return entry

    def get_input_point(self):
        """Получить координаты точки из полей ввода X и Y, если они не пустые"""
        x_text = self.x_entry.get()
        y_text = self.y_entry.get()

        if x_text and y_text:
            try:
                return float(x_text), float(y_text)
            except ValueError:
                self.message_window.insert(tk.END, "Неверный формат координат точки\n")
                return None
        return None

    def start_creating_polygon(self):
        """Активация режима создания полигона"""
        self.is_creating_polygon = True
        self.current_polygon = []
        self.status_label.config(text="Кликните для добавления точек полигона")

    def handle_left_click(self, event):
        """Обработка левого клика: выбор полигона или добавление точки"""
        if self.is_creating_polygon:
            self.add_point(event)
        else:
            self.select_polygon(event)

    def select_polygon(self, event):
        """Выбор полигона по клику вблизи его вершины или ребра"""
        x, y = event.x, event.y
        closest_polygon = None
        min_distance = float('inf')

        for polygon in self.polygons:
            # Проверяем расстояние до вершин
            for px, py in polygon:
                distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if distance < min_distance and distance < 10:  # Порог близости 10 пикселей
                    min_distance = distance
                    closest_polygon = polygon

            # Проверяем расстояние до рёбер (для полигонов с ≥2 вершинами)
            if len(polygon) >= 2:
                for i in range(len(polygon)):
                    x1, y1 = polygon[i]
                    x2, y2 = polygon[(i + 1) % len(polygon)]
                    distance = self.point_to_segment_distance(x, y, x1, y1, x2, y2)
                    if distance < min_distance and distance < 10:
                        min_distance = distance
                        closest_polygon = polygon

        if closest_polygon:
            self.selected_polygon = closest_polygon
            self.status_label.config(text=f"Выбран полигон с {len(self.selected_polygon)} вершинами")
            self.redraw()
        else:
            self.selected_polygon = None
            self.status_label.config(text="Полигон не выбран")
            self.redraw()

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Вычисление расстояния от точки до отрезка"""
        length_squared = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if length_squared == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / length_squared))
        projection_x = x1 + t * (x2 - x1)
        projection_y = y1 + t * (y2 - y1)
        return ((px - projection_x) ** 2 + (py - projection_y) ** 2) ** 0.5

    def add_point(self, event):
        """Создание полигонов кликами мышью"""
        x, y = event.x, event.y
        self.current_polygon.append((x, y))

        # Нарисовать вершину
        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")

        # Соединить текущую точку с предыдущей
        if len(self.current_polygon) > 1:
            self.canvas.create_line(
                self.current_polygon[-2], self.current_polygon[-1], fill="black", width=2
            )

        # Добавить в список полигонов
        if self.current_polygon not in self.polygons:
            self.polygons.append(self.current_polygon)

        self.status_label.config(text=f"Добавлено {len(self.current_polygon)} точек. ПКМ для завершения")

        # Правый клик завершает полигон
        self.canvas.bind("<Button-3>", self.finish_polygon)

    def finish_polygon(self, event):
        """Завершение и автоматическое замыкание полигона"""
        if self.current_polygon:
            if len(self.current_polygon) > 2:
                # Замыкаем полигон
                first_point = self.current_polygon[0]
                last_point = self.current_polygon[-1]
                self.canvas.create_line(last_point, first_point, fill="black", width=2)

            # Сохраняем полигон и делаем его текущим выбранным
            self.selected_polygon = self.current_polygon
            self.current_polygon = []
            self.is_creating_polygon = False
            self.canvas.bind("<Button-3>", self.check_point)
            self.status_label.config(text=f"Полигон с {len(self.selected_polygon)} вершинами выбран")
            self.redraw()

    def clear_scene(self):
        """Очистка сцены"""
        self.canvas.delete("all")
        self.polygons.clear()
        self.current_polygon.clear()
        self.selected_polygon = None
        self.is_creating_polygon = False
        self.checked_point_oval = None
        self.canvas.bind("<Button-1>", self.handle_left_click)
        self.canvas.bind("<Button-3>", self.check_point)
        self.status_label.config(text="Сцена очищена")
        self.message_window.delete(1.0, tk.END)
    
     def translate(self):
        """Смещение полигона на dx, dy с использованием матрицы переноса"""
        if not self.selected_polygon:
            self.status_label.config(text="Нет выбранного полигона!")
            return

        try:
            dx = float(self.dx_entry.get() or 0)
            dy = float(self.dy_entry.get() or 0)
        except ValueError:
            self.status_label.config(text="Неверный формат dx или dy!")
            return

        translation_matrix = np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]])

        transformed_polygon = []
        for x, y in self.selected_polygon:
            p = np.array([x, y, 1])
            new_p = translation_matrix @ p

            transformed_polygon.append((new_p[0], new_p[1]))

        self.selected_polygon[:] = transformed_polygon
        
        for i, polygon in enumerate(self.polygons):
            if polygon is self.selected_polygon:
                self.polygons[i] = self.selected_polygon
                break

        self.redraw()
        self.status_label.config(text=f"Смещение на ({dx}, {dy}) выполнено")

    def rotate(self):
        """Поворот полигона вокруг заданной точки или центра"""
        if not self.selected_polygon:
            self.status_label.config(text="Нет выбранного полигона!")
            return

        try:
            angle = radians(float(self.angle_entry.get() or 0))
        except ValueError:
            self.status_label.config(text="Неверный формат угла!")
            return

        if self.rotate_center_var.get():
            point = self.get_polygon_center(self.selected_polygon)
            point_description = "центра"
        else:
            point = self.get_input_point()
            if point is None:
                self.status_label.config(text="Введите координаты точки вращения!")
                return
            point_description = f"точки ({point[0]}, {point[1]})"

        T1 = np.array([[1, 0, -point[0]], [0, 1, -point[1]], [0, 0, 1]])
        R = np.array([[cos(angle), -sin(angle), 0], [sin(angle), cos(angle), 0], [0, 0, 1]])
        T2 = np.array([[1, 0, point[0]], [0, 1, point[1]], [0, 0, 1]])
        M = T2 @ R @ T1

        transformed_polygon = []
        for x, y in self.selected_polygon:
            p = np.array([x, y, 1])
            new_p = M @ p
            transformed_polygon.append((new_p[0], new_p[1]))

        self.selected_polygon[:] = transformed_polygon
        for i, polygon in enumerate(self.polygons):
            if polygon is self.selected_polygon:
                self.polygons[i] = self.selected_polygon
                break

        self.redraw()
        angle_degrees = float(self.angle_entry.get() or 0)
        self.status_label.config(text=f"Поворот на {angle_degrees}° вокруг {point_description}")
    def scale(self):
        """Масштабирование полигона относительно заданной точки или центра"""
        if not self.selected_polygon:
            self.status_label.config(text="Нет выбранного полигона!")
            return

        try:
            s = float(self.scale_entry.get() or 1)
        except ValueError:
            self.status_label.config(text="Неверный формат коэффициента!")
            return

        if self.scale_center_var.get():
            point = self.get_polygon_center(self.selected_polygon)
            point_description = "центра"
        else:
            point = self.get_input_point()
            if point is None:
                self.status_label.config(text="Введите координаты точки масштабирования!")
                return
            point_description = f"точки ({point[0]}, {point[1]})"

        T1 = np.array([[1, 0, -point[0]], [0, 1, -point[1]], [0, 0, 1]])
        S = np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]])
        T2 = np.array([[1, 0, point[0]], [0, 1, point[1]], [0, 0, 1]])
        M = T2 @ S @ T1

        transformed_polygon = []
        for x, y in self.selected_polygon:
            p = np.array([x, y, 1])
            new_p = M @ p
            transformed_polygon.append((new_p[0], new_p[1]))

        self.selected_polygon[:] = transformed_polygon
        for i, polygon in enumerate(self.polygons):
            if polygon is self.selected_polygon:
                self.polygons[i] = self.selected_polygon
                break

        self.redraw()
        self.status_label.config(text=f"Масштабирование ({s}x) относительно {point_description}")

    def get_polygon_center(self, polygon):
        """Вычисление центра полигона (центроид)"""
        if not polygon:
            return (0, 0)
        xs = [x for x, _ in polygon]
        ys = [y for _, y in polygon]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def redraw(self):
        """Перерисовка всех полигонов"""
        self.canvas.delete("all")

        for polygon in self.polygons:
            if len(polygon) == 0:
                continue
            elif len(polygon) == 1:
                x, y = polygon[0]
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")
            elif len(polygon) == 2:
                self.canvas.create_line(polygon[0], polygon[1], fill="black", width=2)
                for x, y in polygon:
                    self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")
            else:
                for i in range(len(polygon)):
                    x1, y1 = polygon[i]
                    x2, y2 = polygon[(i + 1) % len(polygon)]
                    self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                for x, y in polygon:
                    self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")

            if polygon is self.selected_polygon and len(polygon) > 0:
                for x, y in polygon:
                    self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, outline="red", width=2)

        # Перерисовка проверяемой точки, если она существует
        if self.checked_point_oval:
            x1, y1, x2, y2 = self.checked_point_oval
            self.canvas.create_oval(x1, y1, x2, y2, fill="red")
