import numpy as np
from math import cos, sin, radians
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# =========================================================================
# 1. OBJ файл
# =========================================================================

class OBJModel:
    """Класс для работы с OBJ моделями на основе Polyhedron"""

    def __init__(self, polyhedron=None):
        self.polyhedron = polyhedron

    def load_from_file(self, filename):
        """Загрузка модели из OBJ файла"""
        try:
            vertices = []
            faces = []

            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    if parts[0] == 'v':  # вершина
                        if len(parts) >= 4:
                            vertex = [float(parts[1]), float(parts[2]), float(parts[3])]
                            vertices.append(vertex)

                    elif parts[0] == 'f':  # грань
                        face = []
                        for part in parts[1:]:
                            vertex_index = part.split('/')[0]
                            if vertex_index:
                                face.append(int(vertex_index) - 1)
                        if len(face) >= 3:
                            faces.append(face)

            self.polyhedron = Polyhedron(vertices, faces)
            return True

        except Exception as e:
            print(f"Ошибка загрузки файла: {e}")
            return False

    def save_to_file(self, filename):
        """Сохранение модели в OBJ файл"""
        try:
            if self.polyhedron is None:
                return False

            with open(filename, 'w') as file:
                file.write("# OBJ файл\n")
                file.write("# Создан программой визуализации многогранников\n")

                w = self.polyhedron.V[3, :]
                vertices = np.zeros((3, self.polyhedron.V.shape[1]))
                for i in range(self.polyhedron.V.shape[1]):
                    if abs(w[i]) > 1e-10:
                        vertices[:, i] = self.polyhedron.V[:3, i] / w[i]
                    else:
                        vertices[:, i] = self.polyhedron.V[:3, i]

                for i in range(vertices.shape[1]):
                    vertex = vertices[:, i]
                    file.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")

                for face in self.polyhedron.faces:
                    face_line = "f"
                    for vertex_index in face.indices:
                        face_line += f" {vertex_index + 1}"
                    file.write(face_line + "\n")

            return True

        except Exception as e:
            print(f"Ошибка сохранения файла: {e}")
            return False


def to_h(point3):
    """Возвращает однородный 4x1 вектор из 3D точки (x, y, z)."""
    x, y, z = point3
    return np.array([x, y, z, 1.0], dtype=float)


def from_h(vec4):
    """Возвращает 3D точку из однородного вектора после перспективного деления."""
    w = vec4[3]
    if w == 0:
        raise ZeroDivisionError("Однородная координата w == 0 при дегомогенизации")
    return (vec4[:3] / w)


def normalize(v):
    """Нормализует вектор."""
    n = np.linalg.norm(v)
    if n == 0:
        return v
    return v / n


# --------------------
# Матрицы преобразований (4x4, вектор-столбцы)
# --------------------

def T(dx, dy, dz):
    """Матрица переноса (смещения)."""
    M = np.eye(4)
    M[:3, 3] = [dx, dy, dz]
    return M


def S(sx, sy, sz):
    """Матрица масштабирования."""
    M = np.eye(4)
    M[0, 0], M[1, 1], M[2, 2] = sx, sy, sz
    return M


def Rx(angle_deg):
    """Матрица поворота вокруг оси X."""
    a = radians(angle_deg)
    ca, sa = cos(a), sin(a)
    M = np.eye(4)
    M[1, 1], M[1, 2] = ca, -sa
    M[2, 1], M[2, 2] = sa, ca
    return M


def Ry(angle_deg):
    """Матрица поворота вокруг оси Y."""
    a = radians(angle_deg)
    ca, sa = cos(a), sin(a)
    M = np.eye(4)
    M[0, 0], M[0, 2] = ca, sa
    M[2, 0], M[2, 2] = -sa, ca
    return M


def Rz(angle_deg):
    """Матрица поворота вокруг оси Z."""
    a = radians(angle_deg)
    ca, sa = cos(a), sin(a)
    M = np.eye(4)
    M[0, 0], M[0, 1] = ca, -sa
    M[1, 0], M[1, 1] = sa, ca
    return M


def reflect(plane: str):
    """Отражение относительно координатной плоскости: 'xy', 'yz', или 'xz'."""
    plane = plane.lower()
    if plane == "xy":
        return S(1, 1, -1)
    if plane == "yz":
        return S(-1, 1, 1)
    if plane == "xz":
        return S(1, -1, 1)
    raise ValueError("Плоскость должна быть: 'xy', 'yz', 'xz'")


def rodrigues_axis_angle(axis, angle_deg):
    """Поворот 3x3 вокруг единичной оси на угол в градусах."""
    axis = normalize(np.asarray(axis, dtype=float))
    a = radians(angle_deg)
    c, s = cos(a), sin(a)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]], dtype=float)
    R = np.eye(3) * c + (1 - c) * np.outer(axis, axis) + s * K
    return R


def R_around_line(p1, p2, angle_deg):
    """Матрица поворота 4x4 вокруг произвольной 3D линии p1->p2 на угол."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    axis = p2 - p1
    R3 = rodrigues_axis_angle(axis, angle_deg)
    M = np.eye(4)
    M[:3, :3] = R3
    return T(*p1) @ M @ T(*(-p1))


# --------------------
# Матрицы проекций
# --------------------

def perspective(f=1.5):
    """Простая матрица перспективной проекции (камера смотрит вдоль +Z)."""
    M = np.eye(4)
    M[3, 3] = 0.0
    M[3, 2] = 1.0 / f
    return M


# --------------------
# Класс камеры
# --------------------

class Camera:
    """Класс камеры для 3D визуализации."""

    def __init__(self, position=None, target=None, up=None, fov=60.0, aspect=1.0, near=0.1, far=100.0):
        self.position = np.array(position if position is not None else [0.0, 0.0, 5.0])
        self.target = np.array(target if target is not None else [0.0, 0.0, 0.0])
        self.up = np.array(up if up is not None else [0.0, 1.0, 0.0])
        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far

        self.orbit_radius = np.linalg.norm(self.position - self.target)
        self.orbit_theta = 0.0
        self.orbit_phi = 0.0
        self._update_orbit_angles()

    def _update_orbit_angles(self):
        rel_pos = self.position - self.target
        self.orbit_radius = np.linalg.norm(rel_pos)
        if self.orbit_radius > 0:
            rel_pos_norm = rel_pos / self.orbit_radius
            self.orbit_phi = np.arcsin(np.clip(rel_pos_norm[1], -1.0, 1.0))#вертикальный угол
            self.orbit_theta = np.arctan2(rel_pos_norm[0], rel_pos_norm[2])#горизонтальный угол

    def get_view_direction(self):#направление взгляда камеры
        return normalize(self.target - self.position)

    def get_view_matrix(self):
        forward = normalize(self.target - self.position)#Направление взгляда
        right = normalize(np.cross(forward, self.up))#Правая ось камеры
        true_up = np.cross(right, forward)#Настоящая верхняя ось камеры

        R = np.eye(4)
        R[0, :3] = right
        R[1, :3] = true_up
        R[2, :3] = -forward#поворот системы координат относительно камеры

        T_mat = T(-self.position[0], -self.position[1], -self.position[2])#преобразуем координаты, чтобы в новой системе координат камера находилась в начале
        return R @ T_mat

    def get_projection_matrix(self):
        f = 1.0 / np.tan(np.radians(self.fov / 2.0))#коэффициент перспективного масштабирования
        M = np.zeros((4, 4), dtype=float)
        M[0, 0] = f / max(self.aspect, 1e-6)#определяют ширину и форму области обзора
        M[1, 1] = f
        M[2, 2] = -(self.far + self.near) / (self.far - self.near)
        M[2, 3] = -2 * self.far * self.near / (self.far - self.near)#её ближнюю и дальнюю границы по глубине.
        M[3, 2] = -1.0
        return M

    def orbit_rotate(self, delta_theta, delta_phi):#вращение камеры вокруг неподвижного объекта
        self.orbit_theta += np.radians(delta_theta)
        self.orbit_phi += np.radians(delta_phi)

        max_phi = np.radians(89.0)
        self.orbit_phi = np.clip(self.orbit_phi, -max_phi, max_phi)

        x = self.orbit_radius * np.cos(self.orbit_phi) * np.sin(self.orbit_theta)
        y = self.orbit_radius * np.sin(self.orbit_phi)
        z = self.orbit_radius * np.cos(self.orbit_phi) * np.cos(self.orbit_theta)

        self.position = self.target + np.array([x, y, z])

    def zoom(self, delta):
        self.orbit_radius = max(0.5, self.orbit_radius - delta)
        direction = normalize(self.position - self.target)
        self.position = self.target + direction * self.orbit_radius

    def set_target(self, target):#новую точку, на которую смотрит камера
        self.target = np.array(target)
        self._update_orbit_angles()

    def reset(self, position=None, target=None):#сброс положения камеры
        if position is not None:
            self.position = np.array(position)
        if target is not None:
            self.target = np.array(target)
        self._update_orbit_angles()


def ortho_xy():
    """Ортографическая проекция на плоскость XY (отбрасывание Z)."""
    M = np.eye(4)
    M[2, 2] = 0.0
    return M


def isometric_projection_matrix():
    """Аксонометрическая (изометрическая) проекция."""
    alpha = 35.264389682754654
    beta = 45.0
    R = Rx(alpha) @ Rz(beta)
    return ortho_xy() @ R


# --------------------
# Геометрические классы
# --------------------

class Point:
    """Класс для представления точки в 3D пространстве."""

    def __init__(self, x, y, z):
        self.v = to_h((x, y, z))

    @property
    def xyz(self):
        return from_h(self.v)

    def as_array(self):
        return self.v.copy()


class PolygonFace:
    """Класс для представления грани многогранника."""

    def __init__(self, vertex_indices):
        self.indices = list(vertex_indices)
        self.normal = None

    def compute_normal(self, vertices, object_center=None):
        if len(self.indices) < 3:
            self.normal = np.array([0.0, 0.0, 1.0])
            return

        p0 = vertices[:, self.indices[0]]
        p1 = vertices[:, self.indices[1]]
        p2 = vertices[:, self.indices[2]]

        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)

        norm_length = np.linalg.norm(normal)
        if norm_length > 1e-10:
            normal = normal / norm_length
        else:
            self.normal = np.array([0.0, 0.0, 1.0])
            return

        if object_center is not None:
            face_center = np.mean(vertices[:, self.indices], axis=1)
            outward = face_center - object_center
            if np.dot(normal, outward) < 0:
                normal = -normal

        self.normal = normal


class Polyhedron:
    """Класс для представления многогранника."""

    def __init__(self, vertices, faces):
        self.V = np.array([to_h(p) for p in vertices], dtype=float).T
        self.faces = [PolygonFace(f) for f in faces]
        self.compute_face_normals()

    def compute_face_normals(self):
        vertices_3d = self.V[:3, :] / self.V[3, :]
        center = np.mean(vertices_3d, axis=1)
        for face in self.faces:
            face.compute_normal(vertices_3d, center)

    def copy(self):
        P = Polyhedron([(0, 0, 0)], [[]])
        P.V = self.V.copy()
        P.faces = [PolygonFace(f.indices.copy()) for f in self.faces]
        P.compute_face_normals()
        return P

    def center(self):
        pts = self.V[:3, :] / self.V[3, :]
        return np.mean(pts, axis=1)

    def apply(self, M):
        self.V = M @ self.V
        self.compute_face_normals()
        return self

    def translate(self, dx, dy, dz):
        return self.apply(T(dx, dy, dz))

    def scale(self, sx, sy, sz):
        return self.apply(S(sx, sy, sz))

    def scale_about_center(self, s):
        c = self.center()
        return self.apply(T(*c) @ S(s, s, s) @ T(*(-c)))

    def rotate_x(self, angle_deg):
        return self.apply(Rx(angle_deg))

    def rotate_y(self, angle_deg):
        return self.apply(Ry(angle_deg))

    def rotate_z(self, angle_deg):
        return self.apply(Rz(angle_deg))

    def reflect(self, plane: str):
        return self.apply(reflect(plane))

    def rotate_around_axis_through_center(self, axis: str, angle_deg):
        axis = axis.lower()
        c = self.center()
        R = {'x': Rx, 'y': Ry, 'z': Rz}[axis](angle_deg)
        return self.apply(T(*c) @ R @ T(*(-c)))

    def rotate_around_line(self, p1, p2, angle_deg):
        return self.apply(R_around_line(p1, p2, angle_deg))

    def edges(self):
        es = set()
        if self.faces and len(self.faces[0].indices) > 0:
            for f in self.faces:
                idx = f.indices
                for i in range(len(idx)):
                    a = idx[i]
                    b = idx[(i + 1) % len(idx)]
                    es.add(tuple(sorted((a, b))))
        else:
            pts = (self.V[:3, :] / self.V[3, :]).T
            n = len(pts)
            D = np.linalg.norm(pts[None, :, :] - pts[:, None, :], axis=-1)
            for i in range(n):
                neigh = list(np.argsort(D[i])[1:4])
                for j in neigh:
                    es.add(tuple(sorted((i, j))))
        return sorted(list(es))

    def projected(self, matrix4x4):
        Pv = matrix4x4 @ self.V
        Pv = Pv / Pv[3, :]
        return Pv[0, :], Pv[1, :]


# --------------------
# Правильные многогранники (Платоновы тела)
# --------------------

def tetrahedron():
    V = [(1, 1, 1),
         (1, -1, -1),
         (-1, 1, -1),
         (-1, -1, 1)]
    F = [
        [0, 1, 2],
        [0, 3, 1],
        [0, 2, 3],
        [1, 3, 2]
    ]
    return Polyhedron(V, F)


def hexahedron():
    V = [
        (-1, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, 1, 1),
    ]
    F = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7],
    ]
    return Polyhedron(V, F)


def octahedron():
    V = [
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1),
    ]
    F = [
        [4, 0, 2],
        [4, 2, 1],
        [4, 1, 3],
        [4, 3, 0],
        [5, 2, 0],
        [5, 1, 2],
        [5, 3, 1],
        [5, 0, 3],
    ]
    return Polyhedron(V, F)


# --------------------
# Вспомогательные функции для визуализации
# --------------------

POLY_BUILDERS = {
    'Тетраэдр': tetrahedron,
    'Гексаэдр (куб)': hexahedron,
    'Октаэдр': octahedron,
}


def make_poly(name: str) -> Polyhedron:
    builder = POLY_BUILDERS.get(name)
    if builder is None:
        builder = hexahedron
    return builder()


def project_points(P: Polyhedron, proj_mode: str, f: float = 1.8, view_vector=None, cull_backfaces=False, camera=None):
    """Возвращает 2D проекцию вершин и список рёбер."""
    Q = P.copy()

    if proj_mode == 'camera' and camera is not None:
        view_matrix = camera.get_view_matrix()
        Q = Q.apply(view_matrix)
        if cull_backfaces:
            view_vector = np.array([0.0, 0.0, -1.0])
    elif proj_mode == 'perspective':
        Q = Q.translate(0, 0, 5.0)
    else:
        alpha = 35.264389682754654
        beta = 45.0
        Q = Q.apply(Rx(alpha) @ Rz(beta))

    visible_faces = []
    if cull_backfaces:
        if view_vector is None:
            view_vector = np.array([0.0, 0.0, 1.0])

        view_vector = np.asarray(view_vector, dtype=float)
        view_vector = normalize(view_vector)

        vertices_3d = Q.V[:3, :] / Q.V[3, :]

        for face in Q.faces:
            if face.normal is not None:
                face_center = np.mean(vertices_3d[:, face.indices], axis=1)

                if proj_mode in ['perspective', 'camera']:
                    view_to_face = normalize(face_center)
                else:
                    view_to_face = normalize(view_vector)

                dot_product = np.dot(face.normal, view_to_face)

                if dot_product < 0:
                    visible_faces.append(face)
    else:
        visible_faces = Q.faces

    if proj_mode == 'camera' and camera is not None:
        M = camera.get_projection_matrix()
    elif proj_mode == 'perspective':
        M = perspective(f)
    else:
        M = ortho_xy()

    x, y = Q.projected(M)

    if cull_backfaces:
        es = set()
        for f in visible_faces:
            idx = f.indices
            for i in range(len(idx)):
                a = idx[i]
                b = idx[(i + 1) % len(idx)]
                es.add(tuple(sorted((a, b))))
        edges = sorted(list(es))
    else:
        edges = Q.edges()

    return (x, y, edges)


def to_pixels(x, y, width, height, scale=120.0):
    """Перевод модельных координат в пиксели."""
    x = np.asarray(x)
    y = np.asarray(y)
    cx = width * 0.5
    cy = height * 0.5
    Xs = cx + scale * x
    Ys = cy - scale * y
    return Xs, Ys


# ============================================================================
# Лабораторная 8 — единое окно для отсечения, Z-буфера и камеры.
# ============================================================================
import os


def compute_visible_faces_camera_space(polyhedron, camera, ortho=False):
    """Вернуть модель в координатах камеры и её лицевые грани."""
    q = polyhedron.copy().apply(camera.get_view_matrix())
    verts = q.V[:3] / q.V[3]
    result = []
    for face in q.faces:
        if len(face.indices) < 3:
            continue
        ids = face.indices
        a, b, c = (verts[:, ids[i]] for i in range(3))
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-10:
            continue
        center = np.mean(verts[:, ids], axis=1)
        if np.dot(n, center - np.mean(verts, axis=1)) < 0:
            n = -n
        ray = np.array([0., 0., -1.]) if ortho else center
        if np.dot(n, ray) < 0:
            result.append(face)
    return q, result


from zbuffer import raster_triangle, clear_buffers


class Lab8App:
    def __init__(self, root):
        self.root = root
        root.title('3D-модели — отсечение граней, Z-буфер и камера')
        root.geometry('1260x780')
        root.minsize(850, 540)
        self.mode = tk.StringVar(value='zbuffer')
        self.proj = tk.StringVar(value='perspective')
        self.cull = tk.BooleanVar(value=False)
        self.show_edges = tk.BooleanVar(value=False)
        self.use_z = tk.BooleanVar(value=True)
        self.model_name = tk.StringVar(value='Гексаэдр')
        self.view_xyz = [tk.StringVar(value=v) for v in ('0', '0', '-1')]
        self.step = tk.StringVar(value='15')
        self.axis = tk.StringVar(value='y')
        self.scale_factor = tk.StringVar(value='1.2')
        self.move_xyz = [tk.StringVar(value=v) for v in ('0.2', '0', '0')]
        self.cam_speed = tk.StringVar(value='6')
        self.line_xyz = [tk.StringVar(value=x) for x in ('0', '0', '0', '0', '1', '0')]
        self.ref_plane = tk.StringVar(value='xy')
        self.show_normals = tk.BooleanVar(value=False)
        self.cam_pos = tk.StringVar()
        self.drag = None
        self.meshes = []
        self.base_mesh = None
        self.camera = Camera(position=[0, 1.5, 5], target=[0, 0, 0])
        self._create_ui()
        self.load_preset('Гексаэдр')
        root.after(80, self.render)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def _create_ui(self):
        shell = ttk.Frame(self.root)
        shell.pack(fill='both', expand=True)
        sidebar = ttk.Frame(shell, width=270)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        scroll_canvas = tk.Canvas(sidebar, width=254, highlightthickness=0, bg='#f4f6fa')
        scrollbar = ttk.Scrollbar(sidebar, orient='vertical', command=scroll_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        scroll_canvas.pack(side='left', fill='both', expand=True)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        panel = ttk.Frame(scroll_canvas, padding=9)
        window_id = scroll_canvas.create_window((0, 0), window=panel, anchor='nw')
        panel.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig(window_id, width=e.width))
        scroll_canvas.bind('<MouseWheel>', lambda e: scroll_canvas.yview_scroll(-int(e.delta / 120), 'units'))
        self.canvas = tk.Canvas(shell, bg='#f7f9fc', highlightthickness=0)
        self.canvas.pack(side='right', fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.schedule_render())
        self.canvas.bind('<ButtonPress-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag_camera)
        self.canvas.bind('<MouseWheel>', lambda e: self.camera_zoom(1 if e.delta > 0 else -1))
        self.canvas.bind('<Button-4>', lambda e: self.camera_zoom(1))
        self.canvas.bind('<Button-5>', lambda e: self.camera_zoom(-1))

        f = ttk.LabelFrame(panel, text='Модель / сцена', padding=7)
        f.pack(fill='x', pady=4)
        self.model_box = ttk.Combobox(f, textvariable=self.model_name, state='readonly', width=27,
            values=['Чайник (OBJ)', 'Куб (OBJ)', 'Шар (OBJ)', 'Гексаэдр', 'Тетраэдр', 'Октаэдр', 'Перекрытие кубов', 'Три куба в ряд'])
        self.model_box.pack(fill='x', pady=3)
        self.model_box.bind('<<ComboboxSelected>>', lambda e: self.load_preset(self.model_name.get()))
        r = ttk.Frame(f); r.pack(fill='x', pady=2)
        ttk.Button(r, text='Открыть OBJ', command=self.open_obj).pack(side='left', expand=True, fill='x')
        ttk.Button(r, text='Сохранить', command=self.save_obj).pack(side='left', expand=True, fill='x', padx=(5, 0))
        ttk.Button(f, text='Сбросить модель', command=lambda: self.load_preset(self.model_name.get())).pack(fill='x', pady=2)

        f = ttk.LabelFrame(panel, text='Режим отображения', padding=7)
        f.pack(fill='x', pady=4)
        for label, val in [('Каркас', 'wire'), ('Отсечение граней', 'culling'), ('Z-буфер', 'zbuffer'), ('Камера', 'camera')]:
            ttk.Radiobutton(f, text=label, variable=self.mode, value=val, command=self.change_mode).pack(anchor='w')
        ttk.Checkbutton(f, text='Скрывать задние грани', variable=self.cull, command=self.render).pack(anchor='w', pady=(6, 0))
        ttk.Checkbutton(f, text='Показывать рёбра', variable=self.show_edges, command=self.render).pack(anchor='w')
        ttk.Checkbutton(f, text='Нормали граней', variable=self.show_normals, command=self.render).pack(anchor='w')
        ttk.Checkbutton(f, text='Включить Z-буфер', variable=self.use_z, command=self.render).pack(anchor='w')
        ttk.Label(f, text='Проекция:', font=('Arial', 9, 'bold')).pack(anchor='w', pady=(5, 0))
        for label, val in [('Перспективная', 'perspective'), ('Параллельная', 'parallel')]:
            ttk.Radiobutton(f, text=label, variable=self.proj, value=val, command=self.render).pack(anchor='w')

        f = ttk.LabelFrame(panel, text='Вектор обзора (параллельная)', padding=7)
        f.pack(fill='x', pady=4)
        r = ttk.Frame(f); r.pack(fill='x')
        for variable in self.view_xyz:
            ttk.Entry(r, textvariable=variable, width=7).pack(side='left', expand=True, padx=2)
        ttk.Button(f, text='Применить направление', command=self.set_view_vector).pack(fill='x', pady=3)

        f = ttk.LabelFrame(panel, text='Камера', padding=7)
        f.pack(fill='x', pady=4)
        ttk.Label(f, text='Мышь: поворот и масштаб', foreground='#506174').pack(anchor='w')
        for labels, values in [(['◀ Влево', 'Вправо ▶'], [(-10, 0), (10, 0)]),
                               (['▲ Вверх', 'Вниз ▼'], [(0, 10), (0, -10)])]:
            r = ttk.Frame(f); r.pack(fill='x', pady=2)
            for label, (a, b) in zip(labels, values):
                ttk.Button(r, text=label, command=lambda a=a, b=b: self.orbit(a, b)).pack(side='left', fill='x', expand=True)
        r = ttk.Frame(f); r.pack(fill='x', pady=2)
        ttk.Button(r, text='+ Ближе', command=lambda: self.camera_zoom(1)).pack(side='left', expand=True, fill='x')
        ttk.Button(r, text='− Дальше', command=lambda: self.camera_zoom(-1)).pack(side='left', expand=True, fill='x')
        ttk.Button(f, text='Сброс камеры', command=self.reset_camera).pack(fill='x')
        ttk.Label(f, textvariable=self.cam_pos, foreground='#48627d', wraplength=245).pack(anchor='w', pady=4)

        f = ttk.LabelFrame(panel, text='Преобразования объекта', padding=7)
        f.pack(fill='x', pady=4)
        r = ttk.Frame(f); r.pack(fill='x')
        ttk.Label(r, text='Ось').pack(side='left')
        ttk.Combobox(r, textvariable=self.axis, values=['x', 'y', 'z'], width=3, state='readonly').pack(side='left', padx=4)
        ttk.Label(r, text='Угол').pack(side='left')
        ttk.Entry(r, textvariable=self.step, width=6).pack(side='left', padx=4)
        ttk.Button(f, text='Повернуть объект', command=self.rotate_object).pack(fill='x', pady=3)
        r = ttk.Frame(f); r.pack(fill='x', pady=2)
        ttk.Label(r, text='Масштаб').pack(side='left')
        ttk.Entry(r, textvariable=self.scale_factor, width=7).pack(side='left', padx=6)
        ttk.Button(r, text='Применить', command=self.scale_object).pack(side='left', expand=True, fill='x')
        ttk.Label(f, text='Перенос dx, dy, dz').pack(anchor='w')
        r = ttk.Frame(f); r.pack(fill='x')
        for variable in self.move_xyz:
            ttk.Entry(r, textvariable=variable, width=7).pack(side='left', expand=True, padx=2)
        ttk.Button(f, text='Переместить', command=self.translate_object).pack(fill='x', pady=3)
        r = ttk.Frame(f); r.pack(fill='x', pady=2)
        ttk.Label(r, text='Отражение').pack(side='left')
        ttk.Combobox(r, textvariable=self.ref_plane, state='readonly', values=['xy', 'yz', 'xz'], width=5).pack(side='left', padx=5)
        ttk.Button(r, text='Применить', command=self.reflect_object).pack(side='left', fill='x', expand=True)
        ttk.Label(f, text='Ось через две точки: x y z / x y z').pack(anchor='w', pady=(5, 1))
        r = ttk.Frame(f); r.pack(fill='x')
        for variable in self.line_xyz:
            ttk.Entry(r, textvariable=variable, width=4).pack(side='left', expand=True, padx=1)
        ttk.Button(f, text='Вращать вокруг прямой', command=self.rotate_around_line).pack(fill='x', pady=3)

    def change_mode(self):
        if self.mode.get() == 'camera':
            self.proj.set('perspective')
        self.render()

    def _parse(self, var, default):
        try:
            return float(var.get())
        except (ValueError, TypeError):
            return default

    def _bounds(self):
        pts = np.concatenate([(p.V[:3] / p.V[3]).T for p, col in self.meshes], axis=0)
        lo, hi = pts.min(0), pts.max(0)
        return (lo + hi) / 2, max(float(np.linalg.norm(hi - lo)), .01)

    def fit_camera(self):
        center, diameter = self._bounds()#длину диагонали(размер) объёма модели
        self.camera.reset(position=center + np.array([diameter * 1.05, diameter * .30, diameter * .60]), target=center)
        self.update_cam_label()#разместить камеру относительно центра модели^

    def load_obj_file(self, path):
        obj = OBJModel()
        if not obj.load_from_file(path):
            raise ValueError('Не удалось прочитать OBJ')
        return obj.polyhedron

    def load_preset(self, name):
        try:
            folder = os.path.dirname(os.path.abspath(__file__))
            filenames = {
                'Чайник (OBJ)': 'utah_teapot_lowpoly.obj',
                'Куб (OBJ)': 'cube.obj',
                'Шар (OBJ)': 'sphere.obj',
            }
            builders = {
                'Гексаэдр': hexahedron,
                'Тетраэдр': tetrahedron,
                'Октаэдр': octahedron,
            }
            if name == 'Три куба в ряд':
                self.meshes = [
                    (hexahedron().scale(.68, .68, .68).translate(x, 0, 0), color)
                    for x, color in [(-2., (226, 126, 137)), (0., (106, 174, 217)), (2., (109, 193, 146))]
                ]
            elif name == 'Перекрытие кубов':
                self.meshes = [
                    (hexahedron().scale(.83, .83, .83).translate(-.65, 0, -.5), (242, 135, 145)),
                    (hexahedron().scale(.83, .83, .83).rotate_y(26).translate(.1, .3, .4), (118, 194, 242)),
                    (hexahedron().scale(.7, .7, .7).rotate_x(25).translate(.85, -.3, -1), (132, 222, 179)),
                ]
            elif name in filenames:
                self.meshes = [(self.load_obj_file(os.path.join(folder, filenames[name])), (119, 174, 234))]
            elif name in builders:
                self.meshes = [(builders[name](), (119, 174, 234))]
            else:
                return
            self.model_name.set(name)
            self.base_mesh = self.meshes[0][0]
            self.fit_camera()
            self.render()
        except Exception as e:
            messagebox.showerror('Ошибка модели', str(e))

    def open_obj(self):
        path = filedialog.askopenfilename(filetypes=[('Wavefront OBJ', '*.obj')])
        if not path:
            return
        try:
            self.meshes = [(self.load_obj_file(path), (119, 174, 234))]
            self.base_mesh = self.meshes[0][0]
            self.model_name.set('Загружена из OBJ')
            self.fit_camera()
            self.render()
        except Exception as e:
            messagebox.showerror('Ошибка OBJ', str(e))

    def save_obj(self):
        path = filedialog.asksaveasfilename(defaultextension='.obj', filetypes=[('Wavefront OBJ', '*.obj')])
        if path and self.base_mesh is not None:
            if not OBJModel(self.base_mesh).save_to_file(path):
                messagebox.showerror('Ошибка', 'Не удалось сохранить OBJ')

    def update_cam_label(self):
        self.cam_pos.set('Позиция: ' + ', '.join(f'{x:.2f}' for x in self.camera.position) +
                         '\nЦель: ' + ', '.join(f'{x:.2f}' for x in self.camera.target))

    def orbit(self, azimuth, elevation):
        self.camera.orbit_rotate(azimuth, elevation)
        self.update_cam_label()
        self.render()

    #def camera_zoom(self, d):
    #radius = self.camera.orbit_radius
    #self.camera.zoom(d * radius * .12)
    #self.update_cam_label()
    #self.render()
    def camera_zoom(self, d):
        radius = self.camera.orbit_radius
        _, diameter = self._bounds()#размер модели

        min_radius = max(0.5, diameter * 0.65)
        max_radius = diameter * 20.0

        new_radius = np.clip(
            radius - d * radius * 0.12,
            min_radius,
            max_radius
        )

        direction = normalize(self.camera.position - self.camera.target)#направление от цели к камере
        self.camera.orbit_radius = new_radius
        self.camera.position = self.camera.target + direction * new_radius

        self.update_cam_label()
        self.render()


    def reset_camera(self):
        self.fit_camera()
        self.render()

    def start_drag(self, e):
        self.drag = (e.x, e.y)

    def drag_camera(self, e):#вращает камеру при перемещении мыши
        if self.drag:
            dx, dy = e.x - self.drag[0], e.y - self.drag[1]#смещение мыши по двум осям
            self.drag = (e.x, e.y)
            self.orbit(-dx * .45, dy * .45)

    def close(self):
        self.root.destroy()

    def set_view_vector(self):
        try:
            v = np.array([float(s.get()) for s in self.view_xyz])
            if np.linalg.norm(v) < 1e-8:
                raise ValueError
            v = normalize(v)
            center, dia = self._bounds()
            self.camera.reset(position=center - v * dia * 1.7, target=center)
            self.proj.set('parallel')
            self.render()
            self.update_cam_label()
        except ValueError:
            messagebox.showwarning('Вектор обзора', 'Задайте ненулевой числовой вектор')

    def rotate_object(self):
        angle = self._parse(self.step, 15.)
        for model, _ in self.meshes:
            model.rotate_around_axis_through_center(self.axis.get(), angle)
        self.render()

    def scale_object(self):
        k = self._parse(self.scale_factor, 1.2)
        if k <= 0:
            return
        for model, _ in self.meshes:
            model.scale_about_center(k)
        self.render()

    
    def translate_object(self):
        vec = [self._parse(t, 0.) for t in self.move_xyz]

        for model, _ in self.meshes:
            model.translate(*vec)

        self.camera.set_target(self.camera.target + np.array(vec))

        self.update_cam_label()
        self.render()


    def reflect_object(self):
        for model, _ in self.meshes:
            model.reflect(self.ref_plane.get())
        self.render()

    def rotate_around_line(self):
        try:
            coords = [float(v.get()) for v in self.line_xyz]
            if np.linalg.norm(np.array(coords[3:]) - coords[:3]) < 1e-9:
                raise ValueError('Точки оси должны различаться')
            for model, _ in self.meshes:
                model.rotate_around_line(coords[:3], coords[3:], self._parse(self.step, 15.))
            self.render()
        except ValueError as exc:
            messagebox.showwarning('Ось вращения', str(exc))

    def schedule_render(self):
        if not getattr(self, '_render_pending', False):
            self._render_pending = True
            self.root.after(75, self._scheduled)

    def _scheduled(self):
        self._render_pending = False
        self.render()

    def render(self):
        if not self.meshes:
            return
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 15 or height < 15:
            return
        self.camera.aspect = width / height#вычисляем соотношение сторон
        if self.mode.get() == 'camera' and self.proj.get() != 'perspective':
            self.proj.set('perspective')
        perspective_mode = self.proj.get() == 'perspective'
        view = self.camera.get_view_matrix()#видовая матрица
        mode = self.mode.get()
        culling = self.cull.get() or mode == 'culling'
        wire = mode in ('wire', 'culling')
        limit = 1000
        factor = min(1., limit / max(width, height))
        w, h = max(1, int(width * factor)), max(1, int(height * factor))
        rgb, depth_buffer = clear_buffers(w, h)
        wire_segments = []
        self._normal_lines = []
        for obj, base_color in self.meshes:
            vertices = obj.V[:3] / obj.V[3]
            Vcam = view @ obj.V#координаты вершин относительно камеры
            cam = Vcam[:3] / Vcam[3]
            z = -cam[2]
            if perspective_mode:
                projected = self.camera.get_projection_matrix() @ Vcam
                wcoord = projected[3]
                valid = wcoord > self.camera.near#аходятся ли вершины дальше ближней границы видимости камеры
                ndcx = np.divide(projected[0], wcoord, out=np.zeros_like(wcoord), where=valid)
                ndcy = np.divide(projected[1], wcoord, out=np.zeros_like(wcoord), where=valid)#нормализованные координаты проекции
            else:
                _, dia = self._bounds()
                ortho_half_h = max(dia * .72, 0.1)
                ndcx = cam[0] / (ortho_half_h * self.camera.aspect)
                ndcy = cam[1] / ortho_half_h
                valid = z > self.camera.near
            screen = np.column_stack(((ndcx + 1) * w * .5, (1 - ndcy) * h * .5))
            for face in obj.faces:
                ids = face.indices
                if len(ids) < 3 or not np.all(valid[ids]):
                    continue
                n = view[:3, :3] @ face.normal
                norm = np.linalg.norm(n)
                if norm < 1e-10:
                    continue
                n /= norm
                center = np.mean(cam[:, ids], axis=1)
                facing = np.dot(n, np.array([0., 0., -1.]) if not perspective_mode else center) < 0
                if culling and not facing:
                    continue
                if self.show_normals.get() and facing:
                    normal_length = max(self._bounds()[1] * .09, .05)
                    endpoint = center + n * normal_length
                    if perspective_mode:
                    # # Перспективная: умножаем точку на матрицу проекции
                        pp = self.camera.get_projection_matrix() @ np.array([*endpoint, 1.])
                        if pp[3] > self.camera.near: # # точка перед камерой?
                        # # Делим на w (перспективное деление) → переводим в пиксели
                            end_xy = np.array([(pp[0] / pp[3] + 1) * w * .5, (1 - pp[1] / pp[3]) * h * .5])
                        else:
                            end_xy = None
                    else:
                        # # Параллельная проекция: просто масштабируем 
                        end_xy = np.array([(endpoint[0] / (ortho_half_h * self.camera.aspect) + 1) * w * .5,
                                           (1 - endpoint[1] / ortho_half_h) * h * .5])
                    if end_xy is not None:
                        pc = np.mean(screen[ids], axis=0)
                        self._normal_lines.append((pc.copy(), end_xy))
                if wire:
                    for j in range(len(ids)):
                        p0, p1 = screen[ids[j]], screen[ids[(j + 1) % len(ids)]]
                        wire_segments.append((p0, p1))
                    continue
                light = normalize(np.array([-.5, .8, 1.]))
                intensity = .45 + .55 * max(0., np.dot(n, light))
                shade = np.array([int(min(255, x * intensity)) for x in base_color], dtype=np.uint8)
                for j in range(1, len(ids) - 1):
                    tri = [ids[0], ids[j], ids[j + 1]]
                    raster_triangle(screen[tri], z[tri], shade, rgb, depth_buffer,
                                    ztest=self.use_z.get())
                if self.show_edges.get():
                    for j in range(len(ids)):
                        wire_segments.append((screen[ids[j]], screen[ids[(j + 1) % len(ids)]]))
        self.canvas.delete('all')
        if not wire:
            header = f'P6 {w} {h} 255\n'.encode('ascii')
            photo = tk.PhotoImage(data=header + rgb.tobytes(), format='PPM')
            self.canvas.image = photo
            self.canvas.create_image(width / 2, height / 2, image=photo)
        else:
            self.canvas.configure(bg='#f7f9fc')
        if not wire:
            self.canvas.configure(bg='#f7f9fc')
        for p0, p1 in wire_segments:
            self.canvas.create_line(p0[0] / factor, p0[1] / factor, p1[0] / factor, p1[1] / factor,
                                    fill='#277cc0' if wire else '#506879', width=1)
        #Отрисовка стрелок нормалей
        for p0, p1 in self._normal_lines:
            self.canvas.create_line(p0[0] / factor, p0[1] / factor, p1[0] / factor, p1[1] / factor,
                                    fill='#e36c35', width=2, arrow='last')
        modes = {'wire': 'Каркас', 'culling': 'Отсечение граней', 'zbuffer': 'Z-буфер', 'camera': 'Камера'}
        self.canvas.create_text(16, 15, anchor='nw', fill='#64748b',
                                text=f'{self.model_name.get()}   |   {"Перспектива" if perspective_mode else "Параллельная"}   |   {modes[mode]}',
                                font=('Arial', 11))


def main():
    root = tk.Tk()
    Lab8App(root)
    root.mainloop()


if __name__ == '__main__':
    main()