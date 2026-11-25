import numpy as np
from math import cos, sin, radians, sqrt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import colorsys


# =========================================================================
# ЛАБ 7.1 — Загрузка и сохранение OBJ (расширение ЛАБ 9: нормали и UV)
# 1. OBJ файл (расширенный для поддержки нормалей и текстурных координат)
# =========================================================================

class OBJModel:
    """Класс для работы с OBJ моделями на основе Polyhedron"""

    def __init__(self, polyhedron=None):
        self.polyhedron = polyhedron

    def load_from_file(self, filename):
        """Загрузка модели из OBJ файла с поддержкой нормалей и текстурных координат"""
        try:
            vertices = []
            tex_coords = []
            normals = []
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

                    elif parts[0] == 'vt':  # текстурные координаты
                        if len(parts) >= 3:
                            tex_coord = [float(parts[1]), float(parts[2])]
                            tex_coords.append(tex_coord)

                    elif parts[0] == 'vn':  # нормали
                        if len(parts) >= 4:
                            normal = [float(parts[1]), float(parts[2]), float(parts[3])]
                            normals.append(normal)

                    elif parts[0] == 'f':  # грань
                        face_vertices = []
                        face_tex_coords = []
                        face_normals = []

                        for part in parts[1:]:
                            # Обработка формата vertex/texture/normal
                            indices = part.split('/')

                            # Индекс вершины
                            vertex_idx = int(indices[0]) - 1 if indices[0] else -1
                            face_vertices.append(vertex_idx)

                            # Индекс текстурных координат
                            tex_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                            face_tex_coords.append(tex_idx)

                            # Индекс нормали
                            normal_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                            face_normals.append(normal_idx)

                        if len(face_vertices) >= 3:
                            face_data = {
                                'vertices': face_vertices,
                                'tex_coords': face_tex_coords if len(face_tex_coords) == len(face_vertices) else [],
                                'normals': face_normals if len(face_normals) == len(face_vertices) else []
                            }
                            faces.append(face_data)

            # Создаем полиэдр с дополнительными данными
            self.polyhedron = Polyhedron(vertices, faces)

            # Сохраняем текстурные координаты и нормали
            if tex_coords:
                self.polyhedron.tex_coords = tex_coords
            if normals:
                self.polyhedron.normals = normals

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

                # Запись вершин
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

                # Запись текстурных координат (если есть)
                if hasattr(self.polyhedron, 'tex_coords') and self.polyhedron.tex_coords:
                    for tc in self.polyhedron.tex_coords:
                        file.write(f"vt {tc[0]:.6f} {tc[1]:.6f}\n")

                # Запись нормалей (если есть)
                if hasattr(self.polyhedron, 'normals') and self.polyhedron.normals:
                    for normal in self.polyhedron.normals:
                        file.write(f"vn {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")

                # Запись граней
                for face in self.polyhedron.faces:
                    face_line = "f"
                    for i, vertex_index in enumerate(face.indices):
                        if hasattr(face, 'tex_coords') and face.tex_coords and hasattr(face,
                                                                                       'normals') and face.normals:
                            # vertex/texture/normal
                            tex_idx = face.tex_coords[i] + 1 if i < len(face.tex_coords) else ""
                            normal_idx = face.normals[i] + 1 if i < len(face.normals) else ""
                            face_line += f" {vertex_index + 1}/{tex_idx}/{normal_idx}"
                        elif hasattr(face, 'tex_coords') and face.tex_coords:
                            # vertex/texture
                            tex_idx = face.tex_coords[i] + 1 if i < len(face.tex_coords) else ""
                            face_line += f" {vertex_index + 1}/{tex_idx}"
                        elif hasattr(face, 'normals') and face.normals:
                            # vertex//normal
                            normal_idx = face.normals[i] + 1 if i < len(face.normals) else ""
                            face_line += f" {vertex_index + 1}//{normal_idx}"
                        else:
                            # только vertex
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
# ЛАБ 6 — Матрицы аффинных преобразований
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
    R3 = rodrigues_axis_angle(axis, angle_deg)  # 3x3
    M = np.eye(4)
    M[:3, :3] = R3
    return T(*p1) @ M @ T(*(-p1))


# --------------------
# ЛАБ 6 — Перспективная проекция
# Матрицы проекций
# --------------------

def perspective(f=1.5):
    """
    Простая матрица перспективной проекции.
    Камера в начале координат смотрит вдоль +Z; точки сцены должны иметь z > 0.
    """
    M = np.eye(4)
    M[3, 3] = 0.0
    M[3, 2] = 1.0 / f  # w' = z/f  -> x' = x / (z/f) = f*x/z
    return M


# --------------------
# ЛАБ 8.3 — Камера
# Класс камеры
# --------------------

class Camera:
    """
    Класс камеры для 3D визуализации.

    Камера задается:
    - position: положение камеры в мировых координатах
    - target: точка, на которую смотрит камера
    - up: вектор "вверх" камеры
    - fov: поле зрения (field of view) в градусах
    - aspect: соотношение сторон (ширина/высота)
    - near, far: ближняя и дальняя плоскости отсечения
    """

    def __init__(self, position=None, target=None, up=None, fov=60.0, aspect=1.0, near=0.1, far=100.0):
        self.position = np.array(position if position is not None else [0.0, 0.0, 5.0])
        self.target = np.array(target if target is not None else [0.0, 0.0, 0.0])
        self.up = np.array(up if up is not None else [0.0, 1.0, 0.0])
        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far

        # Параметры орбитального вращения
        self.orbit_radius = np.linalg.norm(self.position - self.target)
        self.orbit_theta = 0.0  # угол по горизонтали (азимут)
        self.orbit_phi = 0.0  # угол по вертикали (высота)
        self._update_orbit_angles()

    def _update_orbit_angles(self):
        """Обновляет углы орбиты на основе текущей позиции."""
        rel_pos = self.position - self.target
        self.orbit_radius = np.linalg.norm(rel_pos)
        if self.orbit_radius > 0:
            rel_pos_norm = rel_pos / self.orbit_radius
            # phi - угол от горизонтальной плоскости
            self.orbit_phi = np.arcsin(np.clip(rel_pos_norm[1], -1.0, 1.0))
            # theta - угол в горизонтальной плоскости
            self.orbit_theta = np.arctan2(rel_pos_norm[0], rel_pos_norm[2])

    def get_view_direction(self):
        """Возвращает нормализованный вектор направления обзора (от камеры к цели)."""
        direction = self.target - self.position
        return normalize(direction)

    def get_view_matrix(self):
        """Как в лабораторной № 8: камера направлена вдоль -Z."""
        forward = normalize(self.target - self.position)
        right = normalize(np.cross(forward, self.up))
        true_up = np.cross(right, forward)
        R = np.eye(4)
        R[0, :3] = right
        R[1, :3] = true_up
        R[2, :3] = -forward
        return R @ T(*(-self.position))

    def get_projection_matrix(self):
        """Матрица перспективы из лабораторной № 8."""
        f = 1.0 / np.tan(np.radians(self.fov / 2.0))
        M = np.zeros((4, 4), dtype=float)
        M[0, 0] = f / max(self.aspect, 1e-6)
        M[1, 1] = f
        M[2, 2] = -(self.far + self.near) / (self.far - self.near)
        M[2, 3] = -2 * self.far * self.near / (self.far - self.near)
        M[3, 2] = -1.0
        return M

    def orbit_rotate(self, delta_theta, delta_phi):
        """
        Вращает камеру вокруг целевой точки (орбитальное вращение).

        delta_theta: изменение азимутального угла (в градусах)
        delta_phi: изменение угла высоты (в градусах)
        """
        self.orbit_theta += np.radians(delta_theta)
        self.orbit_phi += np.radians(delta_phi)

        # Ограничиваем угол phi, чтобы избежать переворота
        max_phi = np.radians(89.0)
        self.orbit_phi = np.clip(self.orbit_phi, -max_phi, max_phi)

        # Вычисляем новую позицию на сфере
        x = self.orbit_radius * np.cos(self.orbit_phi) * np.sin(self.orbit_theta)
        y = self.orbit_radius * np.sin(self.orbit_phi)
        z = self.orbit_radius * np.cos(self.orbit_phi) * np.cos(self.orbit_theta)

        self.position = self.target + np.array([x, y, z])

    def zoom(self, delta):
        """
        Приближает/отдаляет камеру от цели.

        delta: изменение расстояния (положительное - приближение, отрицательное - отдаление)
        """
        self.orbit_radius = max(0.5, self.orbit_radius - delta)

        # Обновляем позицию, сохраняя направление
        direction = normalize(self.position - self.target)
        self.position = self.target + direction * self.orbit_radius

    def set_target(self, target):
        """Устанавливает новую целевую точку."""
        self.target = np.array(target)
        self._update_orbit_angles()

    def reset(self, position=None, target=None):
        """Сбрасывает камеру в исходное положение."""
        if position is not None:
            self.position = np.array(position)
        if target is not None:
            self.target = np.array(target)
        self._update_orbit_angles()


# ЛАБ 6 — Аксонометрическая проекция
def ortho_xy():
    """Ортографическая проекция на плоскость XY (отбрасывание Z)."""
    M = np.eye(4)
    M[2, 2] = 0.0
    return M


def isometric_projection_matrix():
    """Аксонометрическая (изометрическая) проекция = поворот + ортографическая проекция."""
    # Классическая изометрия: поворот вокруг Z на 45°, затем вокруг X на ~35.264°
    alpha = 35.264389682754654
    beta = 45.0
    R = Rx(alpha) @ Rz(beta)
    return ortho_xy() @ R


# --------------------
# ЛАБ 6 — Геометрические классы
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

    def __init__(self, vertex_indices, tex_coords=None, normals=None):
        self.indices = list(vertex_indices)
        self.tex_coords = tex_coords if tex_coords else []
        self.normals = normals if normals else []
        self.normal = None  # Вектор нормали грани
        self.vertex_normals = []  # Нормали вершин

    # ЛАБ 8.1 — Нормаль грани
    def compute_normal(self, vertices, object_center=None):
        """
        Вычисляет вектор нормали грани через векторное произведение.
        Гарантирует, что нормаль направлена наружу от центра объекта.

        vertices: массив 3xN координат вершин (уже в 3D, без однородной координаты)
        object_center: центр объекта (для определения направления наружу)
        """
        if len(self.indices) < 3:
            self.normal = np.array([0.0, 0.0, 1.0])
            return

        # Берем первые три вершины грани
        p0 = vertices[:, self.indices[0]]
        p1 = vertices[:, self.indices[1]]
        p2 = vertices[:, self.indices[2]]

        # Два вектора в плоскости грани
        v1 = p1 - p0
        v2 = p2 - p0

        # Векторное произведение дает вектор нормали
        normal = np.cross(v1, v2)

        # Нормализуем
        norm_length = np.linalg.norm(normal)
        if norm_length > 1e-10:
            normal = normal / norm_length
        else:
            self.normal = np.array([0.0, 0.0, 1.0])
            return

        # Для выпуклых многогранников проверяем направление нормали относительно центра
        if object_center is not None:
            # Центр грани
            face_center = np.mean(vertices[:, self.indices], axis=1)
            # Вектор от центра объекта к центру грани
            outward = face_center - object_center

            # Если нормаль направлена внутрь (угол > 90 градусов), переворачиваем её
            if np.dot(normal, outward) < 0:
                normal = -normal

        self.normal = normal


class Polyhedron:
    """Класс для представления многогранника."""

    def __init__(self, vertices, faces):
        """
        vertices: список вершин (кортежи (x,y,z))
        faces: список граней (словари с вершинами, текстурными координатами и нормалями)
        """
        self.V = np.array([to_h(p) for p in vertices], dtype=float).T  # 4xN (столбец = вершина)

        # Создаем список граней
        self.faces = []
        for face_data in faces:
            if isinstance(face_data, dict):
                face = PolygonFace(
                    face_data['vertices'],
                    face_data.get('tex_coords', []),
                    face_data.get('normals', [])
                )
            else:
                face = PolygonFace(face_data)
            self.faces.append(face)

        self.tex_coords = []  # Текстурные координаты
        self.normals = []  # Нормали вершин

        self.compute_face_normals()
        self.compute_vertex_normals()

    # ЛАБ 8.1 — Нормали граней многогранника
    def compute_face_normals(self):
        """Вычисляет нормали для всех граней многогранника."""
        # Получаем 3D координаты вершин (без однородной координаты)
        vertices_3d = self.V[:3, :] / self.V[3, :]

        # Центр объекта
        center = np.mean(vertices_3d, axis=1)

        for face in self.faces:
            face.compute_normal(vertices_3d, center)

    # ЛАБ 9.1 — Нормали вершин
    def compute_vertex_normals(self):
        """Вычисляет нормали вершин как среднее нормалей прилегающих граней."""
        vertices_3d = self.V[:3, :] / self.V[3, :]
        vertex_normals = [np.zeros(3) for _ in range(vertices_3d.shape[1])]
        vertex_face_count = [0 for _ in range(vertices_3d.shape[1])]

        for face in self.faces:
            if face.normal is not None:
                for vertex_idx in face.indices:
                    vertex_normals[vertex_idx] += face.normal
                    vertex_face_count[vertex_idx] += 1

        # Нормализуем нормали вершин
        for i in range(len(vertex_normals)):
            if vertex_face_count[i] > 0:
                vertex_normals[i] = normalize(vertex_normals[i])
            else:
                vertex_normals[i] = np.array([0.0, 0.0, 1.0])

        # Сохраняем нормали вершин в гранях
        for face in self.faces:
            face.vertex_normals = [vertex_normals[idx] for idx in face.indices]

    # --- основные методы ---
    def copy(self):
        """Создает копию многогранника."""
        P = Polyhedron([(0, 0, 0)], [{'vertices': []}])
        P.V = self.V.copy()
        P.faces = []
        for f in self.faces:
            face = PolygonFace(f.indices.copy(), f.tex_coords.copy(), f.normals.copy())
            face.normal = f.normal.copy() if f.normal is not None else None
            face.vertex_normals = [n.copy() for n in f.vertex_normals] if f.vertex_normals else []
            P.faces.append(face)

        P.tex_coords = self.tex_coords.copy() if hasattr(self, 'tex_coords') else []
        P.normals = self.normals.copy() if hasattr(self, 'normals') else []
        P.compute_face_normals()
        P.compute_vertex_normals()
        return P

    def center(self):
        """Вычисляет центр многогранника."""
        pts = self.V[:3, :] / self.V[3, :]
        return np.mean(pts, axis=1)

    # ЛАБ 6 — Матричное преобразование объекта
    def apply(self, M):
        """Применяет матричное преобразование 4x4."""
        self.V = M @ self.V

        # ЛАБ 8.1 и 9.1 — Преобразование нормалей
        # Преобразуем нормали (используем обратную транспонированную матрицу для нормалей)
        M_3x3 = M[:3, :3]
        if np.linalg.det(M_3x3) != 0:
            M_normal = np.linalg.inv(M_3x3).T

            for face in self.faces:
                if face.normal is not None:
                    face.normal = normalize(M_normal @ face.normal)

                # Преобразуем нормали вершин
                if face.vertex_normals:
                    face.vertex_normals = [normalize(M_normal @ n) for n in face.vertex_normals]

        return self

    # ЛАБ 6 — Аффинные преобразования
    # --- удобные методы преобразований (все через матрицы) ---
    def translate(self, dx, dy, dz):
        """Перенос (смещение)."""
        return self.apply(T(dx, dy, dz))

    def scale(self, sx, sy, sz):
        """Масштабирование."""
        return self.apply(S(sx, sy, sz))

    def scale_about_center(self, s):
        c = self.center()
        return self.apply(T(*(-c)) @ S(s, s, s) @ T(*c))

    def rotate_x(self, angle_deg):
        """Поворот вокруг оси X."""
        return self.apply(Rx(angle_deg))

    def rotate_y(self, angle_deg):
        """Поворот вокруг оси Y."""
        return self.apply(Ry(angle_deg))

    def rotate_z(self, angle_deg):
        """Поворот вокруг оси Z."""
        return self.apply(Rz(angle_deg))

    def reflect(self, plane: str):
        """Отражение относительно координатной плоскости."""
        return self.apply(reflect(plane))

    def rotate_around_axis_through_center(self, axis: str, angle_deg):
        axis = axis.lower()
        c = self.center()
        R = {'x': Rx, 'y': Ry, 'z': Rz}[axis](angle_deg)
        return self.apply(T(*(-c)) @ R @ T(*c))

    def rotate_around_line(self, p1, p2, angle_deg):
        """Поворот вокруг произвольной линии."""
        return self.apply(R_around_line(p1, p2, angle_deg))

    # --- вспомогательные методы для ребер ---
    def edges(self):
        """Вычисляет список ребер многогранника."""
        es = set()
        if self.faces and len(self.faces[0].indices) > 0:
            # Строим ребра из граней
            for f in self.faces:
                idx = f.indices
                for i in range(len(idx)):
                    a = idx[i]
                    b = idx[(i + 1) % len(idx)]
                    es.add(tuple(sorted((a, b))))
        else:
            # Резервный метод: соединение ближайших соседей
            pts = (self.V[:3, :] / self.V[3, :]).T
            n = len(pts)
            D = np.linalg.norm(pts[None, :, :] - pts[:, None, :], axis=-1)
            for i in range(n):
                neigh = list(np.argsort(D[i])[1:4])  # 3 ближайших соседа
                for j in neigh:
                    es.add(tuple(sorted((i, j))))
        return sorted(list(es))

    # --- проекция ---
    def projected(self, matrix4x4):
        """Возвращает 2D точки (x,y) после применения матрицы проекции."""
        Pv = matrix4x4 @ self.V
        # Перспективное деление
        Pv = Pv / Pv[3, :]
        # возвращаем только (x,y)
        return Pv[0, :], Pv[1, :]


# --------------------
# ЛАБ 6 — Правильные многогранники
# Правильные многогранники (Платоновы тела)
# --------------------

def tetrahedron():
    """Создает правильный тетраэдр с центром в начале координат."""
    V = [(1, 1, 1),
         (1, -1, -1),
         (-1, 1, -1),
         (-1, -1, 1)]
    F = [
        {'vertices': [0, 1, 2]},
        {'vertices': [0, 3, 1]},
        {'vertices': [0, 2, 3]},
        {'vertices': [1, 3, 2]}
    ]
    return Polyhedron(V, F)


def hexahedron():
    """Правильный гексаэдр (куб) с центром в начале координат и ребром 2."""
    V = [
        (-1, -1, -1),  # 0
        (1, -1, -1),  # 1
        (1, 1, -1),  # 2
        (-1, 1, -1),  # 3
        (-1, -1, 1),  # 4
        (1, -1, 1),  # 5
        (1, 1, 1),  # 6
        (-1, 1, 1),  # 7
    ]
    # 6 квадратных граней (порядок вершин по контуру)
    F = [
        {'vertices': [0, 1, 2, 3]},  # z = -1 (низ)
        {'vertices': [4, 5, 6, 7]},  # z = +1 (верх)
        {'vertices': [0, 1, 5, 4]},  # y = -1
        {'vertices': [1, 2, 6, 5]},  # x = +1
        {'vertices': [2, 3, 7, 6]},  # y = +1
        {'vertices': [3, 0, 4, 7]},  # x = -1
    ]
    return Polyhedron(V, F)


def octahedron():
    """Правильный октаэдр с центром в начале координат и ребром √2."""
    V = [
        (1, 0, 0),  # 0
        (-1, 0, 0),  # 1
        (0, 1, 0),  # 2
        (0, -1, 0),  # 3
        (0, 0, 1),  # 4 (верх)
        (0, 0, -1),  # 5 (низ)
    ]
    # 8 треугольных граней
    F = [
        {'vertices': [4, 0, 2]},
        {'vertices': [4, 2, 1]},
        {'vertices': [4, 1, 3]},
        {'vertices': [4, 3, 0]},
        {'vertices': [5, 2, 0]},
        {'vertices': [5, 1, 2]},
        {'vertices': [5, 3, 1]},
        {'vertices': [5, 0, 3]},
    ]
    return Polyhedron(V, F)


def icosahedron():
    """Икосаэдр, построенный с цилиндра.
    Полюса: (0,0,±sqrt(5)/2); кольца радиуса 1 на z=±1/2, нижнее смещено на 36°.
    Возвращает Polyhedron с явными 20 треугольными гранями.
    """

    def deg(a):
        return np.deg2rad(a)

    z_top, z_bot = +0.5, -0.5
    r = 1.0
    z_pole = np.sqrt(5.0) / 2.0

    V = []
    # верхняя вершина
    V.append((0.0, 0.0, +z_pole))

    # 1..5 — верхнее кольцо (углы 0,72,144,216,288)
    for k in range(5):
        ang = deg(72 * k)
        V.append((r * np.cos(ang), r * np.sin(ang), z_top))

    # 6..10 — нижнее кольцо (углы 36,108,180,252,324)
    for k in range(5):
        ang = deg(36 + 72 * k)
        V.append((r * np.cos(ang), r * np.sin(ang), z_bot))

    # нижняя вершина
    V.append((0.0, 0.0, -z_pole))

    F = []

    # Верхняя «шапка»: 5 треугольников (0, Ti, Ti+1)
    for i in range(5):
        F.append({'vertices': [0, 1 + i, 1 + ((i + 1) % 5)]})

    # Средняя зона: 10 треугольников (по 2 на «сектор»).
    # Важный момент: у вершины верхнего кольца Ti ближайшие нижние — Bi и B(i-1).
    for i in range(5):
        Ti = 1 + i
        Tip1 = 1 + ((i + 1) % 5)
        Bi = 6 + i
        Bim1 = 6 + ((i - 1) % 5)

        # «верхний» из пары (Ti, Bi, B(i-1))
        F.append({'vertices': [Ti, Bi, Bim1]})
        # «нижний» из пары (Bi, Tip1, Ti)
        F.append({'vertices': [Bi, Tip1, Ti]})

    # Нижняя «шапка»: 5 треугольников (11, Bj+1, Bj)
    for j in range(5):
        Bj = 6 + j
        Bjp1 = 6 + ((j + 1) % 5)
        F.append({'vertices': [11, Bjp1, Bj]})

    return Polyhedron(V, F)


def dodecahedron():
    """Додекаэдр как дуал к идущему выше 'цилиндрическому' икосаэдру:
    вершины = центры тяжести треугольных граней икосаэдра,
    грани = пятиугольники, по одному на каждую вершину икосаэдра.
    """
    I = icosahedron()
    # координаты вершин икосаэдра (N x 3)
    V = (I.V[:3, :] / I.V[3, :]).T  # normalization
    faces_I = [f.indices for f in I.faces]  # список где каждый элемент это список индексов точек грани

    # 20 вершин додекаэдра: центроиды треугольников
    D_vertices = [tuple(np.mean(V[idxs], axis=0)) for idxs in faces_I]

    # каждой вершине икосаэдра ставим в соответствие номера граней в которых она используется
    incident = [[] for _ in range(len(V))]
    for fi, tri in enumerate(faces_I):
        for vid in tri:
            incident[vid].append(fi)

    # Построим 12 пятиугольных граней додекаэдра.
    D_faces = []
    for vid, fids in enumerate(incident):
        if len(fids) != 5:
            # на всякий случай пропустим аномалии (их быть не должно)
            continue
        p = V[vid]  # точка-центр «звезды» (вершины икосаэдра)
        n = normalize(p)  # используем направление p как «нормаль» локальной плоскости
        # ортонормированный базис {e1,e2} в плоскости, перпендикулярной n
        tmp = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        e1 = normalize(np.cross(n, tmp))
        e2 = np.cross(n, e1)

        # отсортируем прилегающие центроиды по углу в этой плоскости
        ang_with_id = []
        for fid in fids:
            c = np.mean(V[faces_I[fid]], axis=0)
            d = c - p
            ang = np.arctan2(np.dot(d, e2), np.dot(d, e1))
            ang_with_id.append((ang, fid))
        ang_with_id.sort()  # массив отсортированных по полярному углу точек, чтобы точки брались по кругу

        D_faces.append({'vertices': [fid for ang, fid in ang_with_id]})  # добавляем грань

    return Polyhedron(D_vertices, D_faces)


# --------------------
# ЛАБ 8.2 — Z-буфер
# Класс ZBuffer
# --------------------

class ZBuffer:
    """Класс для реализации z-буфера."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buffer = np.full((height, width), np.inf, dtype=float)
        self.color_buffer = np.zeros((height, width, 3), dtype=float)

    def clear(self):
        """Очищает z-буфер."""
        self.buffer.fill(np.inf)
        self.color_buffer.fill(0.0)

    def test_and_set(self, x, y, z, color):
        """Проверяет и устанавливает пиксель в z-буфере."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if z < self.buffer[y, x]:
                self.buffer[y, x] = z
                self.color_buffer[y, x] = color
                return True
        return False

    def draw_to_canvas(self, canvas):
        """Отрисовывает z-буфер на canvas используя PIL Image для производительности."""
        # Создаем массив изображения из color_buffer
        # Преобразуем float [0,1] в uint8 [0,255]
        image_array = (np.clip(self.color_buffer, 0.0, 1.0) * 255).astype(np.uint8)
        
        # Создаем маску для видимых пикселей (где z < inf)
        mask = self.buffer < np.inf
        
        # Создаем изображение с альфа-каналом (RGBA)
        # Фон будет прозрачным для невидимых пикселей
        height, width = self.buffer.shape
        image_rgba = np.zeros((height, width, 4), dtype=np.uint8)
        image_rgba[:, :, :3] = image_array  # RGB каналы
        image_rgba[:, :, 3] = (mask * 255).astype(np.uint8)  # Альфа-канал
        
        # Создаем PIL Image из массива
        pil_image = Image.fromarray(image_rgba, 'RGBA')
        
        # Конвертируем в PhotoImage для Tkinter
        photo = ImageTk.PhotoImage(pil_image)
        
        # Очищаем canvas и рисуем изображение одним вызовом
        canvas.delete('all')
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        
        # Сохраняем ссылку на изображение, чтобы оно не было удалено сборщиком мусора
        canvas.image = photo

# --------------------
# ЛАБ 9.1 — Источник света и материал
# Классы для освещения и материалов
# --------------------

class Light:
    """Класс для представления источника света."""

    def __init__(self, position, color=(1.0, 1.0, 1.0), intensity=1.0):
        self.position = np.array(position, dtype=float)
        self.color = np.array(color, dtype=float)
        self.intensity = intensity


class Material:
    """Класс для представления материала объекта."""

    def __init__(self, color=(0.8, 0.8, 0.8), ambient=0.2, diffuse=0.7, specular=0.3, shininess=32.0):
        self.color = np.array(color, dtype=float)
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess


# --------------------
# ЛАБ 9 — Модели освещения и интерполяция
# Функции для освещения и шейдинга
# --------------------

# ЛАБ 9.1.1 — Модель Ламберта
def lambert_shading(normal, light_dir, material, light):
    """Вычисляет диффузное освещение по модели Ламберта."""
    # Косинус угла между нормалью и направлением к свету
    cos_theta = max(0.0, np.dot(normal, light_dir))

    # Диффузная составляющая
    diffuse = material.diffuse * cos_theta

    # Цвет с учетом освещения
    ambient_color = material.ambient * material.color
    diffuse_color = diffuse * material.color * light.color * light.intensity

    return ambient_color + diffuse_color


# ЛАБ 9.2 — Модель Фонга для освещения текстуры
def phong_shading(normal, view_dir, light_dir, material, light):
    """Вычисляет освещение по модели Фонга."""
    # Диффузная составляющая (Ламберт)
    cos_theta = max(0.0, np.dot(normal, light_dir))
    diffuse = material.diffuse * cos_theta

    # Зеркальная составляющая (Фонг)
    reflect_dir = 2 * cos_theta * normal - light_dir
    cos_alpha = max(0.0, np.dot(view_dir, reflect_dir))
    specular = material.specular * (cos_alpha ** material.shininess)

    # Цвет с учетом освещения
    ambient_color = material.ambient * material.color
    diffuse_color = diffuse * material.color * light.color * light.intensity
    specular_color = specular * light.color * light.intensity

    return ambient_color + diffuse_color + specular_color


# ЛАБ 9.1.2 — Модель туншейдинга
def toon_shading(normal, light_dir, material, light):
    """Вычисляет цвет по модели туншейдинга."""

    # Косинус угла между нормалью и направлением к свету
    cos_theta = np.maximum(
        0.0, np.sum(normal * light_dir, axis=-1)
    )

    # Пять дискретных уровней освещенности
    intensity = np.select(
        [
            cos_theta > 0.8,
            cos_theta > 0.6,
            cos_theta > 0.4,
            cos_theta > 0.2
        ],
        [1.0, 0.8, 0.6, 0.4],
        default=0.25
    )

    # Фоновая составляющая освещения
    ambient_color = material.ambient * 0.3 * material.color

    # Диффузная составляющая с дискретной интенсивностью
    toon_color = (
        intensity[..., np.newaxis]
        * material.diffuse
        * material.color
        * light.color
        * light.intensity
    )

    return ambient_color + toon_color


# ЛАБ 9.1.1 — Интерполяция цвета
def interpolate_color(colors, weights):
    """Интерполирует цвет между вершинами с барицентрической интерполяцией.
    
    Используется для метода Гуро - интерполяция цвета между цветами вершин.
    """
    result = np.zeros(3, dtype=float)
    for i, color in enumerate(colors):
        result += weights[i] * np.array(color, dtype=float)
    return np.clip(result, 0.0, 1.0)


# ЛАБ 9.1.2 — Интерполяция нормалей
def interpolate_normal(normals, weights):
    """Интерполирует нормали и нормализует результат."""
    normals = np.asarray(normals, dtype=float)
    weights = np.asarray(weights, dtype=float)

    result = weights @ normals

    lengths = np.linalg.norm(result, axis=-1, keepdims=True)
    lengths = np.where(lengths == 0, 1.0, lengths)

    return result / lengths


# ЛАБ 9.2 — Интерполяция текстурных координат
def interpolate_tex_coord(tex_coords, weights):
    """Интерполирует текстурные координаты между вершинами."""
    result = np.zeros(2)
    for i, tex_coord in enumerate(tex_coords):
        # Преобразуем в numpy array если это список
        tex_array = np.array(tex_coord, dtype=float)
        result += weights[i] * tex_array
    return result


# --------------------
# ЛАБ 9.2 — Создание и загрузка текстур
# Функции для текстурирования
# --------------------

def create_checkerboard_texture(width=64, height=64, square_size=8):
    """Создает текстуру шахматной доски."""
    texture = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            if ((x // square_size) + (y // square_size)) % 2 == 0:
                texture[y, x] = [255, 255, 255]  # Белый
            else:
                texture[y, x] = [0, 0, 255]  # Синий
    # Переворачиваем по вертикали, чтобы v=0 соответствовал низу текстуры
    return np.flipud(texture)


def create_gradient_texture(width=64, height=64):
    """Создает градиентную текстуру."""
    texture = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            r = int(255 * x / width)
            g = int(255 * y / height)
            #b = int(255 * (1 - x / width))
            b = 128
            texture[y, x] = [r, g, b]
    # Переворачиваем по вертикали, чтобы v=0 соответствовал низу текстуры
    return np.flipud(texture)


def load_texture_from_file(filename):
    """Загружает текстуру из файла."""
    try:
        image = Image.open(filename)
        # Конвертируем в RGB если нужно (убираем альфа-канал)
        if image.mode in ('RGBA', 'LA'):
            # Создаем белый фон для прозрачных текстур
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])  # Используем альфа-канал как маску
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Переворачиваем изображение по вертикали, так как в PIL y=0 сверху,
        # а в текстурных координатах v=0 снизу
        image = image.transpose(Image.FLIP_TOP_BOTTOM)

        return np.array(image)
    except Exception as e:
        print(f"Ошибка загрузки текстуры: {e}")
        return create_checkerboard_texture()


def get_texture_color(texture, u, v):
    """Получает цвет из текстуры по координатам (u, v)."""
    if texture is None:
        return np.array([1.0, 1.0, 1.0])

    # Гарантируем что u и v - числа с плавающей точкой
    u = float(u)
    v = float(v)

    height, width = texture.shape[:2]

    # Обеспечиваем повторение текстуры
    u = u % 1.0
    v = v % 1.0

    # Преобразуем в координаты текстуры
    # После переворота изображения при загрузке, координаты совпадают:
    # v=0 -> y=0 (низ), v=1 -> y=height-1 (верх)
    x = int(u * (width - 1))
    y = int(v * (height - 1))

    # Обеспечиваем границы
    x = max(0, min(width - 1, x))
    y = max(0, min(height - 1, y))

    # Получаем цвет и нормализуем
    color = texture[y, x]

    # Если текстура имеет 4 канала (RGBA), берем только RGB
    if len(color) >= 3:
        color = color[:3]  # Берем только первые 3 канала

    return color / 255.0


# --------------------
# Функции для растеризации
# --------------------

# ЛАБ 9.1.1 — Растеризация Гуро
def rasterize_triangle_gouraud_zbuffer(zbuffer, vertices_2d, vertices_3d, vertex_colors):
    """Растеризует треугольник с интерполяцией цвета по Гуро и z-буфером (векторно)."""
    if len(vertices_2d) != 3 or len(vertex_colors) != 3:
        return

    points = np.asarray(vertices_2d, dtype=float)
    verts = np.asarray(vertices_3d, dtype=float)
    colors = np.asarray(vertex_colors, dtype=float)
    if not np.all(np.isfinite(points)):
        return

    # Ограничивающий прямоугольник в пикселях
    x0 = max(0, int(np.floor(points[:, 0].min())))
    x1 = min(zbuffer.width, int(np.ceil(points[:, 0].max())) + 1)
    y0 = max(0, int(np.floor(points[:, 1].min())))
    y1 = min(zbuffer.height, int(np.ceil(points[:, 1].max())) + 1)
    if x0 >= x1 or y0 >= y1:
        return

    (ax, ay), (bx, by), (cx, cy) = points
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-10:
        return

    # Сетка центров пикселей
    yy, xx = np.mgrid[y0:y1, x0:x1]
    px = xx + 0.5
    py = yy + 0.5

    # Барицентрические веса сразу для всех пикселей
    w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
    w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
    w2 = 1.0 - w0 - w1

    inside = (w0 >= -1e-7) & (w1 >= -1e-7) & (w2 >= -1e-7)
    if not np.any(inside):
        return

    # Интерполяция глубины
    z = w0 * verts[0, 2] + w1 * verts[1, 2] + w2 * verts[2, 2]

    # Интерполяция цвета (Гуро)
    color = (w0[..., None] * colors[0] +
             w1[..., None] * colors[1] +
             w2[..., None] * colors[2])
    color = np.clip(color, 0.0, 1.0)

    # Тест Z-буфера — векторно
    z_region = zbuffer.buffer[y0:y1, x0:x1]
    visible = inside & (z < z_region)
    if not np.any(visible):
        return

    z_region[visible] = z[visible]
    color_region = zbuffer.color_buffer[y0:y1, x0:x1]
    color_region[visible] = color[visible]

# ЛАБ 9.1.2 — Растеризация Фонга с туншейдингом
def rasterize_triangle_phong_zbuffer(zbuffer, vertices_2d, vertices_3d, vertex_normals, view_dir, light, material, depth_sign=1.0, perspective_correct=False):
    """Шейдинг Фонга с билинейной интерполяцией по полосам выпуклой грани."""
    points = np.asarray(vertices_2d, dtype=float)
    positions = np.asarray(vertices_3d, dtype=float)
    normals = np.asarray(vertex_normals, dtype=float)
    n = len(points)
    if n < 3 or len(normals) != n or len(positions) != n:
        return
    if not (np.all(np.isfinite(points)) and np.all(np.isfinite(positions)) and np.all(np.isfinite(normals))):
        return

    if perspective_correct:
        depth = depth_sign * positions[:, 2]
        if np.any(depth <= 1e-8):
            return
        inv_depth = 1.0 / depth
        positions = positions * inv_depth[:, None]
        normals = normals * inv_depth[:, None]
    else:
        inv_depth = np.ones(n)

    # Разбиваем грань на горизонтальные полосы по высотам вершин.
    # В каждой полосе левая и правая границы являются отрезками.
    levels = np.unique(points[:, 1])
    for top, bottom in zip(levels[:-1], levels[1:]):
        middle = (top + bottom) / 2
        edges = []
        for i in range(n):
            j = (i + 1) % n
            yi, yj = points[i, 1], points[j, 1]
            if min(yi, yj) < middle < max(yi, yj):
                a = (middle - yi) / (yj - yi)
                edges.append((points[i, 0] + a * (points[j, 0] - points[i, 0]), i, j))
        if len(edges) != 2:
            continue
        edges.sort()

        # Четыре угла полосы: слева сверху, справа сверху,
        # слева снизу, справа снизу. Нормали на ребрах не нормализуем.
        corners_x = []
        corners_pos = []
        corners_normal = []
        corners_inv_depth = []
        for height in (top, bottom):
            for _, i, j in edges:
                a = (height - points[i, 1]) / (points[j, 1] - points[i, 1])
                corners_x.append((1 - a) * points[i, 0] + a * points[j, 0])
                corners_pos.append((1 - a) * positions[i] + a * positions[j])
                corners_normal.append((1 - a) * normals[i] + a * normals[j])
                corners_inv_depth.append((1 - a) * inv_depth[i] + a * inv_depth[j])

        # Сетка центров пикселей в пределах полосы.
        min_x = max(0, int(np.ceil(min(corners_x) - 0.5)))
        max_x = min(zbuffer.width, int(np.floor(max(corners_x) - 0.5)) + 1)
        min_y = max(0, int(np.ceil(top - 0.5)))
        max_y = min(zbuffer.height, int(np.ceil(bottom - 0.5)))
        if min_x >= max_x or min_y >= max_y:
            continue
        X, Y = np.meshgrid(np.arange(min_x, max_x), np.arange(min_y, max_y))

        # Первый этап: линейная интерполяция вдоль левого и правого ребер.
        t = (Y + 0.5 - top) / (bottom - top)
        left = (1 - t) * corners_x[0] + t * corners_x[2]
        right = (1 - t) * corners_x[1] + t * corners_x[3]

        # Второй этап: линейная интерполяция между ребрами.
        width = right - left
        mask = (width > 0) & (X + 0.5 >= left) & (X + 0.5 <= right)
        x, y = X[mask], Y[mask]
        if x.size == 0:
            continue
        u = (x + 0.5 - left[mask]) / width[mask]
        t = t[mask]

        # Билинейные веса четырех углов полосы.
        weights = np.stack([
            (1 - u) * (1 - t), u * (1 - t),
            (1 - u) * t, u * t
        ], axis=1)

        # Интерполяция координат и проверка Z-буфера.
        pixel_pos = weights @ np.asarray(corners_pos)
        if perspective_correct:
            pixel_pos /= (weights @ np.asarray(corners_inv_depth))[:, None]
        z = depth_sign * pixel_pos[:, 2]
        visible = z < zbuffer.buffer[y, x]
        x, y, z = x[visible], y[visible], z[visible]
        if x.size == 0:
            continue

        # Билинейная интерполяция нормалей с последующей нормализацией.
        pixel_normals = interpolate_normal(corners_normal, weights[visible])
        light_dirs = light.position - pixel_pos[visible]
        lengths = np.linalg.norm(light_dirs, axis=1, keepdims=True)
        light_dirs = light_dirs / np.where(lengths == 0, 1.0, lengths)

        # Вычисляем цвет каждого видимого пикселя по модели туншейдинга.
        colors = toon_shading(pixel_normals, light_dirs, material, light)
        zbuffer.buffer[y, x] = z
        zbuffer.color_buffer[y, x] = colors

# ЛАБ 9.2 — Растеризация с текстурой
def rasterize_triangle_textured_zbuffer(zbuffer, vertices_2d, vertices_3d, tex_coords, texture, vertex_normals=None, view_dir=None, light=None, material=None, perspective=True):
    """Текстурирование треугольника с Z-буфером и коррекцией перспективы."""
    if len(vertices_2d) != 3 or len(tex_coords) != 3:
        return

    points = np.asarray(vertices_2d, dtype=float)
    verts = np.asarray(vertices_3d, dtype=float)
    uv = np.asarray(tex_coords, dtype=float)
    if not np.all(np.isfinite(points)):
        return

    x0 = max(0, int(np.floor(points[:, 0].min())))
    x1 = min(zbuffer.width, int(np.ceil(points[:, 0].max())) + 1)
    y0 = max(0, int(np.floor(points[:, 1].min())))
    y1 = min(zbuffer.height, int(np.ceil(points[:, 1].max())) + 1)
    if x0 >= x1 or y0 >= y1:
        return

    (ax, ay), (bx, by), (cx, cy) = points
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy) #общий знаменатель
    if abs(den) < 1e-10:
        return

    # Координаты центров всех пикселей прямоугольной области
    yy, xx = np.mgrid[y0:y1, x0:x1]
    px = xx + 0.5
    py = yy + 0.5

    # Барицентрические веса сразу для всех пикселей
    w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
    w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
    w2 = 1.0 - w0 - w1

    # Перспективно-корректная интерполяция глубины
    z_region = zbuffer.buffer[y0:y1, x0:x1]

    valid = (#какие пиксели принадлежат треугольнику
        (w0 >= -1e-7) &
        (w1 >= -1e-7) &
        (w2 >= -1e-7)
    )

    if perspective:
        # Перспективная проекция: интерполяция обратной глубины
        depth_vertices = np.maximum(np.abs(verts[:, 2]), 1e-5)
        inv_depth = 1.0 / depth_vertices

        inv_z = (
            w0 * inv_depth[0] +
            w1 * inv_depth[1] +
            w2 * inv_depth[2]
        )

        valid &= inv_z > 0

        z = np.full_like(inv_z, np.inf)
        z[valid] = 1.0 / inv_z[valid]

    else:
        # Аксонометрия: глубина интерполируется линейно
        z = (
            w0 * verts[0, 2] +
            w1 * verts[1, 2] +
            w2 * verts[2, 2]
        )

    visible = valid & np.isfinite(z) & (z < z_region)

    if not np.any(visible):
        return

    # Дальше обрабатываем только видимые пиксели
    a, b, c = w0[visible], w1[visible], w2[visible]
    zv = z[visible]

    # Перспективно интерполяция UV
    if perspective:
    # Перспективно интерполяция
        u = (
            a * uv[0, 0] * inv_depth[0] +
            b * uv[1, 0] * inv_depth[1] +
            c * uv[2, 0] * inv_depth[2]
        ) * zv

        v = (
            a * uv[0, 1] * inv_depth[0] +
            b * uv[1, 1] * inv_depth[1] +
            c * uv[2, 1] * inv_depth[2]
        ) * zv

    else:
        # Линейная интерполяция для аксонометрии
        u = a * uv[0, 0] + b * uv[1, 0] + c * uv[2, 0]
        v = a * uv[0, 1] + b * uv[1, 1] + c * uv[2, 1]

    # Получение цветов из текстуры сразу для всех пикселей
    if texture is None:
        colors = np.ones((len(u), 3), dtype=float)
    else:
        th, tw = texture.shape[:2]
        tx = (np.clip(u, 0.0, 1.0) * (tw - 1)).astype(int)
        ty = (np.clip(v, 0.0, 1.0) * (th - 1)).astype(int)
        colors = np.asarray(texture[ty, tx, :3], dtype=float) / 255.0

    # Освещение текстуры
    if light is not None and material is not None and vertex_normals is not None:
        normals = np.asarray(vertex_normals, dtype=float)

        # Интерполяция нормалей и нормализация
        n = a[:, None] * normals[0] + b[:, None] * normals[1] + c[:, None] * normals[2]
        n_len = np.linalg.norm(n, axis=1, keepdims=True)
        n = np.divide(n, n_len, out=np.zeros_like(n), where=n_len > 0)

        # Интерполяция положения точки
        pos = a[:, None] * verts[0] + b[:, None] * verts[1] + c[:, None] * verts[2]

        # Направление к источнику света
        ld = np.asarray(light.position, dtype=float) - pos
        ld_len = np.linalg.norm(ld, axis=1, keepdims=True)
        ld = np.divide(ld, ld_len, out=np.zeros_like(ld), where=ld_len > 0)

        cos_theta = np.maximum(0.0, np.sum(n * ld, axis=1))
        diffuse = material.diffuse * cos_theta[:, None]
        light_color = np.asarray(light.color, dtype=float)

        # Фоновое и диффузное освещение
        result = (material.ambient * colors +
                  diffuse * colors * light_color * light.intensity)

        # Зеркальное освещение, если задано направление взгляда
        if view_dir is not None:
            reflection = 2.0 * cos_theta[:, None] * n - ld
            view = np.asarray(view_dir, dtype=float)
            cos_alpha = np.maximum(0.0, reflection @ view)
            specular = material.specular * (cos_alpha ** material.shininess)
            result += specular[:, None] * light_color * light.intensity

        colors = result

    # Запись глубины и цветов только для видимых пикселей
    z_region[visible] = zv
    color_region = zbuffer.color_buffer[y0:y1, x0:x1]
    color_region[visible] = np.clip(colors, 0.0, 1.0)


# --------------------
# Вспомогательные функции для визуализации
# --------------------

POLY_BUILDERS = {
    'Тетраэдр': tetrahedron,
    'Гексаэдр (куб)': hexahedron,
    'Октаэдр': octahedron,
    'Икосаэдр': icosahedron,
}


# ЛАБ 9.2 — UV-координаты для текстурирования
def ensure_texture_coordinates(poly):
    """Задаёт UV-координаты граням, у которых их ещё нет."""

    for face in poly.faces:
        n = len(face.indices)

        if n < 3:
            continue

        # Проверяем, что у грани уже есть UV-координаты для всех вершин и их индексы существуют в общем списке
        if (
            len(face.tex_coords) == n and all(0 <= idx < len(poly.tex_coords) for idx in face.tex_coords)
        ):
            continue

        if n == 3:
            # Треугольная грань
            uv = [
                (0.0, 0.0),
                (1.0, 0.0),
                (0.5, 0.866)
            ]

        elif n == 4:
            # Четырёхугольная грань
            uv = [
                (0.0, 0.0),
                (1.0, 0.0),
                (1.0, 1.0),
                (0.0, 1.0)
            ]

        else:
            # Резервная раскладка для многоугольников
            angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
            uv = [
                (0.5 + 0.5 * np.cos(a),
                 0.5 + 0.5 * np.sin(a))
                for a in angles
            ]

        face.tex_coords = []#индексов UV-координат текущей грани

        for coord in uv:
            index = len(poly.tex_coords)
            poly.tex_coords.append(coord)
            face.tex_coords.append(index)


# ЛАБ 6 — Выбор многогранника
def make_poly(name: str) -> Polyhedron:
    """Создаёт выбранный многогранник без дополнительных поворотов/масштабов."""
    builder = POLY_BUILDERS.get(name)
    if builder is None:
        builder = hexahedron
    return builder()


# ЛАБ 6 и 8 — Проекция и подготовка граней
def project_points(P: Polyhedron, proj_mode: str, f=1.8, view_vector=None,
                   cull_backfaces=False, camera=None):
    """Проекция на экран. Перспективная/Камера используют одно положение камеры.

    Сначала мировые координаты переводятся в координаты камеры, затем
    в нормализованные экранные координаты. Для изометрии — ортографический вид.
    """
    Q = P.copy()
    if proj_mode == 'isometric':
        Q.apply(Rx(35.264389682754654) @ Rz(45.0))
        pts = Q.V[:3] / Q.V[3]
        diameter = max(float(np.linalg.norm(np.ptp(pts, axis=1))), 0.01)
        half_height = diameter * 0.72
        aspect = camera.aspect if camera is not None else 1.0
        x = pts[0] / (half_height * aspect)
        y = pts[1] / half_height
        # Ортографический вид: направление взгляда от объекта вдоль +Z.
        eye = np.array([0.0, 0.0, 1.0])
        valid = np.ones(Q.V.shape[1], dtype=bool)
    else:
        if camera is None:
            raise ValueError('Для перспективы требуется камера')
        Q.apply(camera.get_view_matrix())
        pts = Q.V[:3] / Q.V[3]
        clip = camera.get_projection_matrix() @ Q.V
        w = clip[3]
        valid = np.isfinite(w) & (w > camera.near)
        x = np.divide(clip[0], w, out=np.full_like(w, np.nan), where=valid)
        y = np.divide(clip[1], w, out=np.full_like(w, np.nan), where=valid)
    visible = []
    for face in Q.faces:
        if len(face.indices) < 3 or not np.all(valid[face.indices]):
            continue
        normal = face.normal
        if normal is None:
            continue
    # ЛАБ 8.1 — Отсечение нелицевых граней
        if proj_mode == 'isometric':
            front = np.dot(normal, eye) > 0
        else:
            face_center = np.mean(pts[:, face.indices], axis=1)
            front = np.dot(normal, -face_center) > 0
        if front:
            visible.append(face)
    return x, y, Q.edges(), visible, Q, pts


def to_pixels(x, y, width, height, scale=120.0):
    """Перевод модельных координат в пиксели с фиксированным масштабом и центрированием."""
    x = np.asarray(x)
    y = np.asarray(y)
    cx = width * 0.5
    cy = height * 0.5
    Xs = cx + scale * x
    Ys = cy - scale * y  # переворот оси Y
    return Xs, Ys


# --------------------
# Tkinter-приложение
# --------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Правильные многогранники — Tkinter')

        self.poly_var = tk.StringVar(value='Гексаэдр (куб)')
        self.proj_var = tk.StringVar(value='perspective')  # 'perspective' | 'isometric' | 'camera'
        self.render_mode = tk.StringVar(value='wireframe')  # 'wireframe' | 'gouraud' | 'phong' | 'texture'

        # Текущая модель многогранника
        self.model: Polyhedron = make_poly(self.poly_var.get())

        # Вектор обзора (направление ОТ камеры К объекту, по умолчанию смотрим вдоль +Z)
        self.view_vector = np.array([0.0, 0.0, 1.0])
        # self.cull_backfaces = tk.BooleanVar(value=False)

        # Камера
        self.camera = Camera(position=[0, 2, 5], target=[0, 0, 0], up=[0, 1, 0])
        self.drag = None

        # Освещение
        self.light = Light(position=[2, 2, 5], color=(1.0, 1.0, 1.0), intensity=1.0)
        self.material = Material(color=(0.8, 0.8, 0.8), ambient=0.2, diffuse=0.7, specular=0.3, shininess=32.0)

        # Текстуры
        self.textures = {
            'checkerboard': create_checkerboard_texture(),
            'gradient': create_gradient_texture(),
            'loaded': None
        }
        self.current_texture = 'checkerboard'

        # Создаем интерфейс
        self.create_ui()
        self.fit_camera()
        self.redraw()

    def create_ui(self):
        """Боковая прокручиваемая панель в стиле лабораторной № 8."""
        self.root.title('Лабораторная № 9 — Освещение и текстурирование')
        self.root.geometry('1260x780')
        self.root.minsize(850, 540)

        shell = ttk.Frame(self.root)
        shell.pack(fill='both', expand=True)

        # Левая панель с вертикальной прокруткой — как в лабораторной № 8.
        sidebar = ttk.Frame(shell, width=285)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        scroll_canvas = tk.Canvas(sidebar, width=269, highlightthickness=0, bg='#f4f6fa')
        scrollbar = ttk.Scrollbar(sidebar, orient='vertical', command=scroll_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        scroll_canvas.pack(side='left', fill='both', expand=True)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        panel = ttk.Frame(scroll_canvas, padding=9)
        window_id = scroll_canvas.create_window((0, 0), window=panel, anchor='nw')
        panel.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig(window_id, width=e.width))
        scroll_canvas.bind('<MouseWheel>', lambda e: scroll_canvas.yview_scroll(-int(e.delta / 120), 'units'))
        scroll_canvas.bind('<Button-4>', lambda e: scroll_canvas.yview_scroll(-1, 'units'))
        scroll_canvas.bind('<Button-5>', lambda e: scroll_canvas.yview_scroll(1, 'units'))

        # Большая область визуализации справа.
        self.canvas = tk.Canvas(shell, bg='#f7f9fc', highlightthickness=0)
        self.canvas.pack(side='right', fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.redraw())
        self.canvas.bind('<ButtonPress-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag_camera)
        self.canvas.bind('<MouseWheel>', lambda e: self.camera_zoom(1 if e.delta > 0 else -1))
        self.canvas.bind('<Button-4>', lambda e: self.camera_zoom(1))
        self.canvas.bind('<Button-5>', lambda e: self.camera_zoom(-1))

        def section(title):
            frame = ttk.LabelFrame(panel, text=title, padding=7)
            frame.pack(fill='x', pady=4)
            return frame

        def entry(parent, value, width=7):
            widget = ttk.Entry(parent, width=width)
            widget.insert(0, str(value))
            widget.pack(side='left', padx=2)
            return widget

        def row(parent):
            frame = ttk.Frame(parent)
            frame.pack(fill='x', pady=2)
            return frame

        def triple(parent, label, defaults):
            ttk.Label(parent, text=label).pack(anchor='w', pady=(3, 1))
            r = row(parent)
            return [entry(r, v) for v in defaults]

        # ЛАБ 6 и 7.1 — Выбор модели и OBJ
        # Модель и загрузка файлов.
        f = section('Модель / сцена')
        ttk.Label(f, text='Многогранник').pack(anchor='w')
        self.poly_box = ttk.Combobox(
            f, textvariable=self.poly_var, values=list(POLY_BUILDERS.keys()),
            state='readonly', width=27
        )
        self.poly_box.pack(fill='x', pady=3)
        self.poly_box.bind('<<ComboboxSelected>>', lambda e: self.rebuild_model())
        r = row(f)
        ttk.Button(r, text='Открыть OBJ', command=self.load_obj).pack(side='left', fill='x', expand=True)
        ttk.Button(r, text='Сохранить', command=self.save_obj).pack(side='left', fill='x', expand=True, padx=(5, 0))
        ttk.Button(f, text='Сбросить модель', command=self.rebuild_model).pack(fill='x', pady=2)

        # ЛАБ 6, 8 и 9 — Проекции и режимы отображения
        # Способы отображения и проекции.
        f = section('Режим отображения')
        for title, value in [
            ('Каркас', 'wireframe'), ('Гуро (Ламберт)', 'gouraud'),
            ('Фонг (туншейдинг)', 'phong'), ('Текстура', 'texture')
        ]:
            ttk.Radiobutton(f, text=title, variable=self.render_mode,
                            value=value, command=self.redraw).pack(anchor='w', pady=1)
        ttk.Label(f, text='Проекция:', font=('Arial', 9, 'bold')).pack(anchor='w', pady=(6, 1))
        self.rb_persp = ttk.Radiobutton(f, text='Перспективная', value='perspective',
                                       variable=self.proj_var, command=self.redraw)
        self.rb_iso = ttk.Radiobutton(f, text='Аксонометрическая', value='isometric',
                                     variable=self.proj_var, command=self.redraw)
        self.rb_camera = ttk.Radiobutton(f, text='Камера', value='camera',
                                        variable=self.proj_var, command=self.redraw)
        for control in (self.rb_persp, self.rb_iso, self.rb_camera):
            control.pack(anchor='w')
        # Сохраняем переменную render_combo для совместимости со старым кодом.
        # Выбор режима теперь осуществляется радиокнопками выше.
        self.render_combo = None

        # ЛАБ 9.1 — Управление освещением
        # Освещение.
        f = section('Освещение')
        self.light_x_entry, self.light_y_entry, self.light_z_entry = triple(
            f, 'Позиция источника света (X, Y, Z)', ('2', '2', '5')
        )
        ttk.Button(f, text='Применить положение света',
                   command=self.apply_light_position).pack(fill='x', pady=2)
        self.mat_r_entry, self.mat_g_entry, self.mat_b_entry = triple(
            f, 'Цвет объекта (R, G, B)', ('0.8', '0.8', '0.8')
        )
        ttk.Button(f, text='Применить цвет',
                   command=self.apply_material_color).pack(fill='x', pady=2)

        # ЛАБ 9.2 — Управление текстурами
        # Текстуры.
        f = section('Текстурирование')
        ttk.Label(f, text='Текстура').pack(anchor='w')
        self.texture_combo = ttk.Combobox(
            f, values=['checkerboard', 'gradient', 'loaded'], state='readonly', width=27
        )
        self.texture_combo.set(self.current_texture)
        self.texture_combo.pack(fill='x', pady=3)
        self.texture_combo.bind('<<ComboboxSelected>>', lambda e: self.change_texture())
        ttk.Button(f, text='Загрузить текстуру', command=self.load_texture).pack(fill='x', pady=2)

        # ЛАБ 8.3 — Управление камерой
        # Камера — компактные кнопки в духе лабораторной № 8.
        f = section('Камера')
        ttk.Label(f, text='Шаг вращения (градусы)').pack(anchor='w')
        r = row(f)
        ttk.Label(r, text='Азимут').pack(side='left')
        self.cam_azimuth_entry = entry(r, '10', 6)
        ttk.Label(r, text='Высота').pack(side='left', padx=(6, 0))
        self.cam_elevation_entry = entry(r, '10', 6)
        r = row(f)
        ttk.Button(r, text='◀ Влево', command=lambda: self.camera_orbit(-1, 0)).pack(
            side='left', fill='x', expand=True
        )
        ttk.Button(r, text='Вправо ▶', command=lambda: self.camera_orbit(1, 0)).pack(
            side='left', fill='x', expand=True
        )
        r = row(f)
        ttk.Button(r, text='▲ Вверх', command=lambda: self.camera_orbit(0, 1)).pack(
            side='left', fill='x', expand=True
        )
        ttk.Button(r, text='Вниз ▼', command=lambda: self.camera_orbit(0, -1)).pack(
            side='left', fill='x', expand=True
        )
        r = row(f)
        ttk.Label(r, text='Шаг приближения').pack(side='left')
        self.cam_zoom_entry = entry(r, '0.5', 6)
        r = row(f)
        ttk.Button(r, text='+ Ближе', command=lambda: self.camera_zoom(1)).pack(
            side='left', fill='x', expand=True
        )
        ttk.Button(r, text='− Дальше', command=lambda: self.camera_zoom(-1)).pack(
            side='left', fill='x', expand=True
        )
        ttk.Label(f, text='Позиция камеры (X, Y, Z)').pack(anchor='w', pady=(5, 0))
        r = row(f)
        self.cam_pos_x_entry, self.cam_pos_y_entry, self.cam_pos_z_entry = [
            entry(r, value) for value in ('0', '2', '5')
        ]
        ttk.Label(f, text='Цель камеры (X, Y, Z)').pack(anchor='w')
        r = row(f)
        self.cam_target_x_entry, self.cam_target_y_entry, self.cam_target_z_entry = [
            entry(r, value) for value in ('0', '0', '0')
        ]
        r = row(f)
        ttk.Button(r, text='Установить', command=self.camera_set_position).pack(
            side='left', fill='x', expand=True
        )
        ttk.Button(r, text='Сброс камеры', command=self.camera_reset).pack(
            side='left', fill='x', expand=True
        )
        # ЛАБ 8.3 — Автоматическое вращение камеры
        # Возможность автовращения из исходной девятой лабораторной сохранена.
        self.auto_rotate = tk.BooleanVar(value=False)
        self.animation_id = None
        r = row(f)
        ttk.Checkbutton(r, text='Автовращение', variable=self.auto_rotate,
                        command=self.toggle_auto_rotate).pack(side='left')
        ttk.Label(r, text='°/кадр').pack(side='left', padx=(5, 1))
        self.auto_rotate_speed_entry = entry(r, '2', 5)

        # ЛАБ 6 — Управление преобразованиями
        # Аффинные преобразования.
        f = section('Преобразования объекта')
        self.dx_entry, self.dy_entry, self.dz_entry = triple(
            f, 'Перенос (dx, dy, dz)', ('0', '0', '0')
        )
        ttk.Button(f, text='Переместить', command=self.apply_translate).pack(fill='x', pady=2)

        r = row(f)
        ttk.Label(r, text='Ось').pack(side='left')
        self.rot_axis_var = tk.StringVar(value='x')
        self.rot_axis = ttk.Combobox(r, textvariable=self.rot_axis_var,
                                     values=['x', 'y', 'z'], state='readonly', width=4)
        self.rot_axis.pack(side='left', padx=4)
        ttk.Label(r, text='Угол').pack(side='left')
        self.angle_entry = entry(r, '30', 7)
        ttk.Button(f, text='Повернуть объект', command=self.apply_rotate).pack(fill='x', pady=2)
        ttk.Button(f, text='Повернуть вокруг центра', command=self.apply_rotate_center).pack(fill='x', pady=2)

        self.sx_entry, self.sy_entry, self.sz_entry = triple(
            f, 'Масштаб (sx, sy, sz)', ('1', '1', '1')
        )
        ttk.Button(f, text='Масштабировать', command=self.apply_scale).pack(fill='x', pady=2)
        r = row(f)
        ttk.Label(r, text='Масштаб относительно центра').pack(side='left')
        self.s_uniform_entry = entry(r, '1', 6)
        ttk.Button(f, text='Применить масштаб к центру',
                   command=self.apply_scale_center).pack(fill='x', pady=2)

        ttk.Label(f, text='Поворот вокруг прямой (две точки)').pack(anchor='w', pady=(5, 0))
        self.p1x_entry, self.p1y_entry, self.p1z_entry = triple(
            f, 'Точка P1 (x, y, z)', ('0', '0', '0')
        )
        self.p2x_entry, self.p2y_entry, self.p2z_entry = triple(
            f, 'Точка P2 (x, y, z)', ('0', '1', '0')
        )
        r = row(f)
        ttk.Label(r, text='Угол').pack(side='left')
        self.angle_line_entry = entry(r, '30')
        ttk.Button(f, text='Вращать вокруг прямой',
                   command=self.apply_rotate_line).pack(fill='x', pady=2)

        r = row(f)
        ttk.Label(r, text='Отражение').pack(side='left')
        self.refl_plane_var = tk.StringVar(value='xy')
        self.refl_plane = ttk.Combobox(r, textvariable=self.refl_plane_var,
                                       values=['xy', 'yz', 'xz'], state='readonly', width=6)
        self.refl_plane.pack(side='left', padx=5)
        ttk.Button(f, text='Отразить', command=self.apply_reflect).pack(fill='x', pady=2)

        self.redraw()

    # ЛАБ 9.1 — Настройка света и цвета
    def apply_light_position(self):
        """Применяет новую позицию источника света."""
        lx = self._parse_float(self.light_x_entry, 2.0)
        ly = self._parse_float(self.light_y_entry, 2.0)
        lz = self._parse_float(self.light_z_entry, 5.0)
        self.light.position = np.array([lx, ly, lz])
        self.redraw()

    def apply_material_color(self):
        """Применяет новый цвет материала."""
        r = self._parse_float(self.mat_r_entry, 0.8)
        g = self._parse_float(self.mat_g_entry, 0.8)
        b = self._parse_float(self.mat_b_entry, 0.8)
        self.material.color = np.array([r, g, b])
        self.redraw()

    # ЛАБ 9.2 — Выбор и загрузка текстуры
    def change_texture(self):
        """Изменяет текущую текстуру."""
        self.current_texture = self.texture_combo.get()
        self.redraw()

    def load_texture(self):
        """Загружает текстуру из файла."""
        filename = filedialog.askopenfilename(
            title="Загрузить текстуру",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")]
        )
        if filename:
            texture = load_texture_from_file(filename)
            if texture is not None:
                self.textures['loaded'] = texture
                self.current_texture = 'loaded'
                self.texture_combo.set('loaded')
                self.redraw()

    def get_poly(self) -> Polyhedron:
        return self.model

    def rebuild_model(self):
        self.model = make_poly(self.poly_var.get())
        self.fit_camera()
        self.redraw()

    # ЛАБ 8.1 — Направление обзора
    def apply_view_vector(self):
        """Применяет новый вектор обзора из полей ввода."""
        vx = self._parse_float(self.view_x_entry, 0.0)
        vy = self._parse_float(self.view_y_entry, 0.0)
        vz = self._parse_float(self.view_z_entry, 1.0)
        self.view_vector = np.array([vx, vy, vz])
        self.redraw()

    def _parse_float(self, widget, default=0.0):
        try:
            return float(widget.get())
        except Exception:
            return default

    # ЛАБ 6 — Обработчики преобразований
    def apply_translate(self):
        dx = self._parse_float(self.dx_entry, 0.0)
        dy = self._parse_float(self.dy_entry, 0.0)
        dz = self._parse_float(self.dz_entry, 0.0)
        # UI семантика:
        #  +dx -> вправо (совпадает с мировой осью X)
        #  +dy -> вверх (экранная Y инвертирована относительно мировой, поэтому инвертируем знак)
        #  +dz -> ближе к камере (камера смотрит вдоль +Z; чтобы объект казался больше, двигаем его к камере: -Z)
        self.model.translate(dx, -dy, -dz)
        self.redraw()

    def apply_rotate(self):
        axis = (self.rot_axis_var.get() or 'x').lower()
        angle = self._parse_float(self.angle_entry, 0.0)
        # Поворот вокруг оси, проходящей через начало координат
        if axis == 'x':
            self.model.rotate_x(angle)
        elif axis == 'y':
            self.model.rotate_y(angle)
        else:
            self.model.rotate_z(angle)
        self.redraw()

    def apply_rotate_center(self):
        """Явное вращение вокруг прямой через центр модели, параллельной выбранной оси."""
        axis = (self.rot_axis_var.get() or 'x').lower()
        angle = self._parse_float(self.angle_entry, 0.0)
        self.model.rotate_around_axis_through_center(axis, angle)
        self.redraw()

    def apply_scale(self):
        sx = self._parse_float(self.sx_entry, 1.0)
        sy = self._parse_float(self.sy_entry, 1.0)
        sz = self._parse_float(self.sz_entry, 1.0)
        # Анизотропный масштаб вокруг начала координат
        self.model.scale(sx, sy, sz)
        self.redraw()

    def apply_scale_center(self):
        # Равномерный масштаб вокруг центра модели (одно число)
        s = self._parse_float(self.s_uniform_entry, 1.0)
        self.model.scale_about_center(s)
        self.redraw()

    def apply_reflect(self):
        plane = (self.refl_plane_var.get() or 'xy').lower()
        if plane not in ('xy', 'yz', 'xz'):
            plane = 'xy'
        self.model.reflect(plane)
        self.redraw()

    def apply_rotate_line(self):
        # Чтение точек p1, p2 и угла
        x1 = self._parse_float(self.p1x_entry, 0.0)
        y1 = self._parse_float(self.p1y_entry, 0.0)
        z1 = self._parse_float(self.p1z_entry, 0.0)
        x2 = self._parse_float(self.p2x_entry, 0.0)
        y2 = self._parse_float(self.p2y_entry, 1.0)
        z2 = self._parse_float(self.p2z_entry, 0.0)
        angle = self._parse_float(self.angle_line_entry, 0.0)
        p1 = (x1, y1, z1)
        p2 = (x2, y2, z2)
        # Проверка на нулевую ось
        if np.linalg.norm(np.asarray(p2, float) - np.asarray(p1, float)) < 1e-12:
            # Ничего не делаем, если ось нулевая
            return
        self.model.rotate_around_line(p1, p2, angle)
        self.redraw()

    # ЛАБ 8.3 — Обработчики камеры
    def camera_orbit(self, direction_horizontal, direction_vertical):
        """Вращает камеру вокруг объекта."""
        azimuth = self._parse_float(self.cam_azimuth_entry, 10.0)
        elevation = self._parse_float(self.cam_elevation_entry, 10.0)

        delta_theta = direction_horizontal * azimuth
        delta_phi = direction_vertical * elevation

        self.camera.orbit_rotate(delta_theta, delta_phi)
        self.update_camera_fields()
        self.redraw()

    def _bounds(self):
        pts = (self.model.V[:3] / self.model.V[3]).T
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        return (lo + hi) / 2, max(float(np.linalg.norm(hi - lo)), 0.01)

    def fit_camera(self):
        center, diameter = self._bounds()
        self.camera.reset(position=center + np.array([diameter * 1.05, diameter * .30,
                                                      diameter * .60]), target=center)
        self.update_camera_fields()

    def start_drag(self, event):
        self.drag = (event.x, event.y)

    def drag_camera(self, event):
        if self.drag is not None:
            dx, dy = event.x - self.drag[0], event.y - self.drag[1]
            self.drag = (event.x, event.y)
            self.camera.orbit_rotate(-dx * .45, dy * .45)
            self.update_camera_fields()
            self.redraw()

    def camera_zoom(self, direction):
        radius = self.camera.orbit_radius
        _, diameter = self._bounds()
        min_radius = max(0.5, diameter * .65)
        max_radius = diameter * 20.0
        new_radius = float(np.clip(radius - direction * radius * .12,
                                   min_radius, max_radius))
        vec = normalize(self.camera.position - self.camera.target)
        self.camera.orbit_radius = new_radius
        self.camera.position = self.camera.target + vec * new_radius
        self.update_camera_fields()
        self.redraw()

    def camera_set_position(self):
        """Устанавливает позицию камеры и цель из полей ввода."""
        pos_x = self._parse_float(self.cam_pos_x_entry, 0.0)
        pos_y = self._parse_float(self.cam_pos_y_entry, 2.0)
        pos_z = self._parse_float(self.cam_pos_z_entry, 5.0)

        target_x = self._parse_float(self.cam_target_x_entry, 0.0)
        target_y = self._parse_float(self.cam_target_y_entry, 0.0)
        target_z = self._parse_float(self.cam_target_z_entry, 0.0)

        self.camera.reset(
            position=[pos_x, pos_y, pos_z],
            target=[target_x, target_y, target_z]
        )
        self.redraw()

    def camera_reset(self):
        self.fit_camera()
        self.redraw()

    def update_camera_fields(self):
        """Обновляет поля ввода позиции камеры."""
        # Обновляем позицию
        self.cam_pos_x_entry.delete(0, tk.END)
        self.cam_pos_x_entry.insert(0, f'{self.camera.position[0]:.2f}')

        self.cam_pos_y_entry.delete(0, tk.END)
        self.cam_pos_y_entry.insert(0, f'{self.camera.position[1]:.2f}')

        self.cam_pos_z_entry.delete(0, tk.END)
        self.cam_pos_z_entry.insert(0, f'{self.camera.position[2]:.2f}')

        # Обновляем цель
        self.cam_target_x_entry.delete(0, tk.END)
        self.cam_target_x_entry.insert(0, f'{self.camera.target[0]:.2f}')

        self.cam_target_y_entry.delete(0, tk.END)
        self.cam_target_y_entry.insert(0, f'{self.camera.target[1]:.2f}')

        self.cam_target_z_entry.delete(0, tk.END)
        self.cam_target_z_entry.insert(0, f'{self.camera.target[2]:.2f}')

    def toggle_auto_rotate(self):
        """Включает/выключает автоматическое вращение камеры."""
        if self.auto_rotate.get():
            self.start_auto_rotate()
        else:
            self.stop_auto_rotate()

    def start_auto_rotate(self):
        """Запускает автоматическое вращение."""
        if self.animation_id is None:
            self.animate_camera()

    def stop_auto_rotate(self):
        """Останавливает автоматическое вращение."""
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def animate_camera(self):
        """Анимация вращения камеры."""
        if self.auto_rotate.get():
            speed = self._parse_float(self.auto_rotate_speed_entry, 2.0)
            self.camera.orbit_rotate(speed, 0)
            self.update_camera_fields()
            self.redraw()
            # Запланировать следующий кадр (примерно 30 FPS)
            self.animation_id = self.root.after(33, self.animate_camera)
        else:
            self.animation_id = None

    def redraw(self):
        self.canvas.delete('all')
        W = self.canvas.winfo_width()
        H = self.canvas.winfo_height()
        if W < 10 or H < 10:
            return

        P = self.get_poly()
        mode = self.proj_var.get()
        render_mode = self.render_mode.get()
        if render_mode == 'texture':
            ensure_texture_coordinates(P)

        # Обновляем aspect ratio камеры
        if W > 0 and H > 0:
            self.camera.aspect = W / H

        # Получаем проекцию и 3D координаты
        x, y, edges, visible_faces, transformed_poly, vertices_3d = project_points(
            P, mode, camera=self.camera
        )

        # Преобразуем в пиксели
        Xs = (x + 1.0) * W * 0.5
        Ys = (1.0 - y) * H * 0.5

        if render_mode == 'wireframe':
            # Для каркасного режима рисуем как раньше
            for a, b in edges:
                coords = [Xs[a], Ys[a], Xs[b], Ys[b]]
                if np.all(np.isfinite(coords)):
                    self.canvas.create_line(*map(float, coords), fill='#1f77b4')
        else:
            # ЛАБ 8.2 — Создание Z-буфера
            # Создаем z-буфер
            zbuffer = ZBuffer(W, H)
            zbuffer.clear()

            # ЛАБ 9.1.2 — Согласование света, обзора и глубины для Фонга
            if render_mode == 'phong':
                if mode == 'camera':
                    view_matrix = self.camera.get_view_matrix()
                    depth_sign = -1.0
                elif mode == 'perspective':
                    view_matrix = self.camera.get_view_matrix()
                    depth_sign = -1.0
                else:
                    view_matrix = Rx(35.264389682754654) @ Rz(45.0)
                    depth_sign = -1.0

                light_position = from_h(view_matrix @ to_h(self.light.position))
                phong_light = Light(light_position, self.light.color, self.light.intensity)
                visible_faces = []
                for face in transformed_poly.faces:
                    if len(face.indices) < 3 or face.normal is None:
                        continue
                    face_points = vertices_3d[:, face.indices]
                    if mode in ('camera', 'perspective'):
                        # Не проецируем грани, пересекающие плоскость камеры.
                        if np.any(depth_sign * face_points[2] <= 1e-8):
                            continue
                        view_dir = -np.mean(face_points, axis=1)
                    else:
                        view_dir = np.array([0.0, 0.0, 1.0])
                    if np.dot(face.normal, view_dir) > 0:
                        visible_faces.append(face)

            # Рендерим все грани через z-буфер
            for face in visible_faces:
                if len(face.indices) < 3:
                    continue

                # Подготавливаем данные для грани
                face_vertices_2d = [(float(Xs[i]), float(Ys[i])) for i in face.indices]
                if render_mode != 'phong':
                    # Глубина для текстуры и Гуро: меньшая положительная глубина ближе.
                    if mode == 'isometric':
                        depth_values = np.max(vertices_3d[2]) - vertices_3d[2] + 1.0
                    else:
                        depth_values = -vertices_3d[2]
                    face_vertices_3d = [np.array([vertices_3d[0, i], vertices_3d[1, i], depth_values[i]])
                                        for i in face.indices]
                else:
                    # Фонг Алёны получает исходные координаты камеры и свой depth_sign.
                    face_vertices_3d = [vertices_3d[:, i] for i in face.indices]

                # ЛАБ 9.1.1 — Отрисовка Гуро
                if render_mode == 'gouraud':
                    # Вычисляем цвета вершин
                    vertex_colors = []
                    for i, vertex_idx in enumerate(face.indices):
                        vertex_pos = vertices_3d[:, vertex_idx]
                        vertex_normal = face.vertex_normals[i] if face.vertex_normals else face.normal

                        if vertex_normal is None:
                            vertex_colors.append(self.material.color)
                            continue

                        light_dir = normalize(self.light.position - vertex_pos)
                        vertex_color = lambert_shading(vertex_normal, light_dir, self.material, self.light)
                        vertex_colors.append(vertex_color)

                    # Растеризуем треугольники
                    if len(face.indices) == 3:
                        rasterize_triangle_gouraud_zbuffer(zbuffer, face_vertices_2d, face_vertices_3d, vertex_colors)
                    elif len(face.indices) == 4:
                        # Разбиваем четырехугольник на два треугольника
                        tri1_2d = [face_vertices_2d[0], face_vertices_2d[1], face_vertices_2d[2]]
                        tri1_3d = [face_vertices_3d[0], face_vertices_3d[1], face_vertices_3d[2]]
                        tri1_colors = [vertex_colors[0], vertex_colors[1], vertex_colors[2]]
                        rasterize_triangle_gouraud_zbuffer(zbuffer, tri1_2d, tri1_3d, tri1_colors)

                        tri2_2d = [face_vertices_2d[0], face_vertices_2d[2], face_vertices_2d[3]]
                        tri2_3d = [face_vertices_3d[0], face_vertices_3d[2], face_vertices_3d[3]]
                        tri2_colors = [vertex_colors[0], vertex_colors[2], vertex_colors[3]]
                        rasterize_triangle_gouraud_zbuffer(zbuffer, tri2_2d, tri2_3d, tri2_colors)

                # ЛАБ 9.1.2 — Отрисовка Фонга с туншейдингом
                elif render_mode == 'phong':
                    vertex_normals = face.vertex_normals if face.vertex_normals else [face.normal] * len(face.indices)
                    rasterize_triangle_phong_zbuffer(
                        zbuffer, face_vertices_2d, face_vertices_3d,
                        vertex_normals, None, phong_light, self.material,
                        depth_sign=depth_sign,
                        perspective_correct=mode in ('camera', 'perspective')
                    )

                # ЛАБ 9.2 — Отрисовка текстуры
                elif render_mode == 'texture':
                    texture = self.textures.get(self.current_texture)
                    view_dir = np.array([0, 0, 1])  # Направление взгляда для освещения
                    vertex_normals = face.vertex_normals if face.vertex_normals else [face.normal] * len(face.indices)

                    # ЛАБ 9.2 — Заранее назначенные UV-координаты вершин грани
                    tex_coords = [
                        np.asarray(transformed_poly.tex_coords[idx], dtype=float)
                        for idx in face.tex_coords
                    ]

                    if len(face.indices) == 3:
                        rasterize_triangle_textured_zbuffer(zbuffer, face_vertices_2d, face_vertices_3d, tex_coords,
                                                            texture, vertex_normals, view_dir, self.light, self.material,
                                                            perspective=(mode != 'isometric'))
                    elif len(face.indices) == 4:
                        tri1_2d = [face_vertices_2d[0], face_vertices_2d[1], face_vertices_2d[2]]
                        tri1_3d = [face_vertices_3d[0], face_vertices_3d[1], face_vertices_3d[2]]
                        tri1_tex_coords = [tex_coords[0], tex_coords[1], tex_coords[2]]
                        tri1_normals = [vertex_normals[0], vertex_normals[1], vertex_normals[2]]
                        rasterize_triangle_textured_zbuffer(zbuffer, tri1_2d, tri1_3d, tri1_tex_coords, texture,
                                                            tri1_normals, view_dir, self.light, self.material,
                                                            perspective=(mode != 'isometric'))

                        tri2_2d = [face_vertices_2d[0], face_vertices_2d[2], face_vertices_2d[3]]
                        tri2_3d = [face_vertices_3d[0], face_vertices_3d[2], face_vertices_3d[3]]
                        tri2_tex_coords = [tex_coords[0], tex_coords[2], tex_coords[3]]
                        tri2_normals = [vertex_normals[0], vertex_normals[2], vertex_normals[3]]
                        rasterize_triangle_textured_zbuffer(zbuffer, tri2_2d, tri2_3d, tri2_tex_coords, texture,
                                                            tri2_normals, view_dir, self.light, self.material,
                                                            perspective=(mode != 'isometric'))

            # Отрисовываем z-буфер на canvas
            zbuffer.draw_to_canvas(self.canvas)

    # ЛАБ 7.1 — Обработчики загрузки и сохранения OBJ
    def load_obj(self):
        """Загрузка модели из OBJ файла"""
        filename = filedialog.askopenfilename(
            title="Открыть OBJ файл",
            filetypes=[("OBJ файлы", "*.obj"), ("Все файлы", "*.*")]
        )
        if not filename:
            return

        obj_model = OBJModel()
        if obj_model.load_from_file(filename):
            self.model = obj_model.polyhedron
            self.poly_var.set('(Загружено из OBJ)')
            self.fit_camera()
            self.redraw()
            messagebox.showinfo("Успех", f"Модель успешно загружена из {filename}")
        else:
            messagebox.showerror("Ошибка", f"Не удалось загрузить модель из {filename}")

    def save_obj(self):
        """Сохранение текущей модели в OBJ файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить OBJ файл",
            defaultextension=".obj",
            filetypes=[("OBJ файлы", "*.obj"), ("Все файлы", "*.*")]
        )
        if not filename:
            return

        obj_model = OBJModel(self.model)
        if obj_model.save_to_file(filename):
            messagebox.showinfo("Успех", f"Модель успешно сохранена в {filename}")
        else:
            messagebox.showerror("Ошибка", f"Не удалось сохранить модель в {filename}")


def main():
    """Запуск GUI приложения"""
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()