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

        # Флаг 
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

        # флаг для масштабирования относительно центра
        self.scale_center_var = tk.BooleanVar(value=True)
        self.scale_center_check = tk.Checkbutton(
            control_frame, text="Масштабирование относительно центра", variable=self.scale_center_var
        )
        self.scale_center_check.pack(fill=tk.X, padx=10)

        self.scale_btn = tk.Button(control_frame, text="Масштабирование", command=self.scale)
        self.scale_btn.pack(fill=tk.X, padx=10, pady=5)

        # Поля для ввода точки (для преобразований относительно заданной точки)
        self.status_label_point = tk.Label(control_frame, text="Точка для преобразований\n(если не относительно центра)", font=("Arial", 10))
        self.status_label_point.pack(pady=5)

        self.x_entry = self.create_labeled_entry(control_frame, "X:")
        self.y_entry = self.create_labeled_entry(control_frame, "Y:")

        self.clear_btn = tk.Button(control_frame, text="Очистить сцену", command=self.clear_scene)
        self.clear_btn.pack(fill=tk.X, padx=10, pady=5)

        self.intersections_button = tk.Button(control_frame, text="Пересечения", command=self.check_polygon_intersections)
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

     #создание поля ввода с меткой
    def create_labeled_entry(self, parent, label_text):  
        frame = tk.Frame(parent)
        frame.pack(padx=10, pady=5, fill=tk.X)
        label = tk.Label(frame, text=label_text)
        label.pack(side=tk.LEFT)
        entry = tk.Entry(frame)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        return entry

    #Получить координаты точки из полей ввода X и Y, если они не пустые
    def get_input_point(self):
        x_text = self.x_entry.get()
        y_text = self.y_entry.get()

        if x_text and y_text:
            try:
                return float(x_text), float(y_text)
            except ValueError:
                self.message_window.insert(tk.END, "Неверный формат координат точки\n")
                return None
        return None

    #Активация режима создания полигона
    def start_creating_polygon(self):
        self.is_creating_polygon = True
        self.current_polygon = []
        self.status_label.config(text="Кликните для добавления точек полигона")

    #Обработка левого клика: выбор полигона или добавление точки
    def handle_left_click(self, event):
        if self.is_creating_polygon:
            self.add_point(event)
        else:
            self.select_polygon(event)

    #Выбор полигона по клику вблизи его вершины или ребра
    def select_polygon(self, event):
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

            # Проверяем расстояние до рёбер
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

    #Вычисление расстояния от точки до отрезка
    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        length_squared = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if length_squared == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / length_squared))
        projection_x = x1 + t * (x2 - x1)
        projection_y = y1 + t * (y2 - y1)
        return ((px - projection_x) ** 2 + (py - projection_y) ** 2) ** 0.5

    #Создание полигонов кликами мышью
    def add_point(self, event):
        x, y = event.x, event.y
        self.current_polygon.append((x, y))

        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")

        # Соединить текущую точку с предыдущей
        if len(self.current_polygon) > 1:
            self.canvas.create_line(
                self.current_polygon[-2], self.current_polygon[-1], fill="black", width=2)

        # Добавить в список полигонов
        if self.current_polygon not in self.polygons:
            self.polygons.append(self.current_polygon)

        self.status_label.config(text=f"Добавлено {len(self.current_polygon)} точек. ПКМ для завершения")

        self.canvas.bind("<Button-3>", self.finish_polygon)

    def finish_polygon(self, event):
        #Завершение и замыкание полигона
        if self.current_polygon:
            if len(self.current_polygon) > 2:
                first_point = self.current_polygon[0]
                last_point = self.current_polygon[-1]
                self.canvas.create_line(last_point, first_point, fill="black", width=2)

            self.selected_polygon = self.current_polygon
            self.current_polygon = []
            self.is_creating_polygon = False
            self.canvas.bind("<Button-3>", self.check_point)
            self.status_label.config(text=f"Полигон с {len(self.selected_polygon)} вершинами выбран")
            self.redraw()

    def clear_scene(self):
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


    def check_point(self, event):
        """Проверка принадлежности точки выбранному полигону и классификация"""
        if not self.selected_polygon:
            self.message_window.delete(1.0, tk.END)
            self.message_window.insert(tk.END, "Выберите полигон для проверки\n")
            return

        x, y = event.x, event.y
        self.message_window.delete(1.0, tk.END)

        # Визуализация проверяемой точки
        self.checked_point_oval = (x - 5, y - 5, x + 5, y + 5)
        self.redraw()

        # Точка на границе рассматривается отдельно от внутренней и внешней
        on_boundary = False
        polygon = self.selected_polygon
        edge_count = 1 if len(polygon) == 2 else len(polygon)
        for i in range(edge_count):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            if self.point_to_segment_distance(x, y, x1, y1, x2, y2) <= 3:
                on_boundary = True
                break

        if on_boundary:
            result = "на границе полигона"
        elif len(polygon) >= 3 and self.is_point_inside_polygon((x, y), polygon):
            result = "внутри полигона"
        else:
            result = "снаружи полигона"

        self.message_window.insert(tk.END, f"Точка ({x}, {y}) {result}\n")

        # Классификация положения точки относительно рёбер выбранного полигона
        if len(polygon) >= 2:
            self.classify_point_position((x, y), polygon)

    def is_point_inside_polygon(self, point, polygon):
        """Проверка принадлежности точки полигону методом луча"""
        if len(polygon) < 3:
            return False

        x, y = point
        inside = False
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            # Луч вправо: ребро учитывается только при пересечении его уровнем y
            if (y1 > y) != (y2 > y):
                x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x < x_cross:
                    inside = not inside
        return inside

    def classify_point_position(self, point, polygon):
        """Классификация положения точки относительно всех рёбер полигона"""
        px, py = point
        edge_count = 1 if len(polygon) == 2 else len(polygon)
        for i in range(edge_count):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            position = self.get_point_position_relative_to_line(px, py, x1, y1, x2, y2)
            line_description = f"Точка ({px}, {py}) относительно ребра ({x1}, {y1})-({x2}, {y2}): {position}\n"
            self.message_window.insert(tk.END, line_description)

    def get_point_position_relative_to_line(self, px, py, x1, y1, x2, y2):
        """Положение точки относительно направленной прямой в экранных координатах"""
        determinant = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        # У Canvas ось Y направлена вниз, поэтому знаки инвертированы.
        if determinant < -1e-7:
            return "Слева"
        elif determinant > 1e-7:
            return "Справа"
        else:
            return "На линии"

    def check_polygon_intersections(self):
        """Проверка пересечений всех рёбер всех полигонов между собой"""
        self.redraw()
        self.message_window.delete(1.0, tk.END)

        intersections_found = False

        for i in range(len(self.polygons)):
            poly1 = self.polygons[i]
            n1 = len(poly1)
            if n1 < 2:
                continue

            for j in range(i, len(self.polygons)):
                poly2 = self.polygons[j]
                n2 = len(poly2)
                if n2 < 2:
                    continue

                # У отрезка две вершины, но только одно ребро.
                for k in range(1 if n1 == 2 else n1):
                    x1, y1 = poly1[k]
                    x2, y2 = poly1[(k + 1) % n1]

                    for l in range(1 if n2 == 2 else n2):
                        if i == j:
                            if k == l or abs(k - l) == 1 or (n1 > 2 and {k, l} == {0, n1 - 1}):
                                continue

                        x3, y3 = poly2[l]
                        x4, y4 = poly2[(l + 1) % n2]

                        intersection_point = self.get_intersection_point(
                            (x1, y1), (x2, y2), (x3, y3), (x4, y4)
                        )

                        if intersection_point is not None:
                            ix, iy = intersection_point
                            self.canvas.create_oval(ix - 5, iy - 5, ix + 5, iy + 5, fill="green", width=2)
                            intersection_info = f"Пересечение:\n"
                            intersection_info += f"Полигон {i}, ребро {k} - Полигон {j}, ребро {l}\n"
                            intersection_info += f"Точка: ({ix:.1f}, {iy:.1f})\n\n"
                            self.message_window.insert(tk.END, intersection_info)
                            intersections_found = True

        if not intersections_found:
            self.message_window.insert(tk.END, "Пересечений не найдено\n")

    def get_intersection_point(self, p1, p2, p3, p4):
        """Точка пересечения двух отрезков (если она единственная)"""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denominator) < 1e-9:
            # Параллельные отрезки. Если они коллинеарны и касаются
            # в одной точке, эту точку тоже считаем пересечением.
            cross = (x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)
            if abs(cross) > 1e-7:
                return None

            def on_segment(p, a, b):
                cross_p = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
                return (abs(cross_p) < 1e-7 and
                        min(a[0], b[0]) - 1e-7 <= p[0] <= max(a[0], b[0]) + 1e-7 and
                        min(a[1], b[1]) - 1e-7 <= p[1] <= max(a[1], b[1]) + 1e-7)

            common = []
            for p in (p1, p2, p3, p4):
                if on_segment(p, p1, p2) and on_segment(p, p3, p4):
                    if not any(abs(p[0] - q[0]) < 1e-7 and abs(p[1] - q[1]) < 1e-7 for q in common):
                        common.append(p)
            # При наложении на отрезке бесконечно много точек,
            # поэтому не выдаём одну из них за единственную точку пересечения.
            return common[0] if len(common) == 1 else None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator

        if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return ix, iy

        return None

    def start_dynamic_intersection(self):
        """Начало режима динамического добавления второго ребра"""
        if not self.selected_polygon or len(self.selected_polygon) != 2:
            self.message_window.insert(tk.END, "Выберите ребро с ровно 2 точками как первое.\n")
            return
        self.status_label.config(text="Кликните для начала второго ребра")
        self.canvas.bind("<Button-1>", self.set_start_point)
        self.canvas.bind("<Button-3>", self.stop_dynamic_intersection)
        self.temp_line = None
        self.intersection_point = None
        self.temp_start_oval = None

    def set_start_point(self, event):
        """Установка начальной точки второго ребра"""
        self.start_point = (event.x, event.y)
        self.temp_start_oval = self.canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="blue")
        self.status_label.config(text="Двигайте мышь, кликните для фиксации")
        self.canvas.bind("<Motion>", self.update_temp_line)
        self.canvas.bind("<Button-1>", self.set_end_point)

    def update_temp_line(self, event):
        """Обновление временной линии и точки пересечения"""
        if self.temp_line:
            self.canvas.delete(self.temp_line)
        if self.intersection_point:
            self.canvas.delete(self.intersection_point)
        x, y = event.x, event.y
        self.temp_line = self.canvas.create_line(self.start_point[0], self.start_point[1], x, y, fill="blue", dash=(4, 4), width=2)
        p1 = self.selected_polygon[0]
        p2 = self.selected_polygon[1]
        p3 = self.start_point
        p4 = (x, y)
        intersect = self.get_intersection_point(p1, p2, p3, p4)
        if intersect is not None:
            ix, iy = intersect
            self.intersection_point = self.canvas.create_oval(ix - 5, iy - 5, ix + 5, iy + 5, fill="red")

    def set_end_point(self, event):
        """Фиксация конечной точки второго ребра"""
        x, y = event.x, event.y
        if self.temp_line:
            self.canvas.delete(self.temp_line)
        if self.intersection_point:
            self.canvas.delete(self.intersection_point)
        if self.temp_start_oval:
            self.canvas.delete(self.temp_start_oval)
        self.canvas.create_oval(self.start_point[0] - 3, self.start_point[1] - 3, self.start_point[0] + 3, self.start_point[1] + 3, fill="black")
        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")
        self.canvas.create_line(self.start_point[0], self.start_point[1], x, y, fill="black", width=2)
        new_polygon = [self.start_point, (x, y)]
        self.polygons.append(new_polygon)
        intersect = self.get_intersection_point(self.selected_polygon[0], self.selected_polygon[1], new_polygon[0], new_polygon[1])
        if intersect is not None:
            ix, iy = intersect
            self.canvas.create_oval(ix - 5, iy - 5, ix + 5, iy + 5, fill="green")
            self.message_window.insert(tk.END, f"Пересечение в ({ix:.1f}, {iy:.1f})\n")
        else:
            self.message_window.insert(tk.END, "Нет единственной точки пересечения\n")
        self.canvas.unbind("<Motion>")
        # Остаёмся в режиме пересечений: следующая пара кликов создаёт новое ребро.
        self.canvas.bind("<Button-1>", self.set_start_point)
        self.canvas.bind("<Button-3>", self.stop_dynamic_intersection)
        self.status_label.config(text="Кликните для начала следующего ребра (ПКМ — выход)")

    def stop_dynamic_intersection(self, event):
        """Выход из режима пересечений по правой кнопке мыши"""
        self.canvas.unbind("<Motion>")
        for item in (self.temp_line, self.intersection_point, self.temp_start_oval):
            if item is not None:
                self.canvas.delete(item)
        self.temp_line = None
        self.intersection_point = None
        self.temp_start_oval = None
        self.canvas.bind("<Button-1>", self.handle_left_click)
        self.canvas.bind("<Button-3>", self.check_point)
        self.status_label.config(text="Режим пересечений завершён")

root = tk.Tk()
app = PolygonEditor(root)
root.mainloop()
