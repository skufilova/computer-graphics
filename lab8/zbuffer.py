"""Программный Z-буфер: глубина каждого пикселя и закраска треугольников.

Алгоритм не зависит от Tkinter: принимает массив RGB, массив глубин и
треугольник в экранных координатах. Меньшая положительная глубина ближе.
"""
import numpy as np


def clear_buffers(width, height, background=(247, 249, 252)):
    # Создаём массив для хранения RGB-цветов всех пикселей
    rgb = np.empty((height, width, 3), dtype=np.uint8)

    # Заполняем все пиксели цветом фона
    rgb[:] = background

    # Создаём Z-буфер, заполняя глубины бесконечностью
    depth = np.full((height, width), np.inf, dtype=np.float32)

    # Возвращаем массив цветов и массив глубин
    return rgb, depth


def raster_triangle(screen, depths, color, rgb, zbuf, ztest=True):
    """Закраска треугольника с проверкой глубины пикселей."""

    # Получаем размеры изображения из Z-буфера
    height, width = zbuf.shape

    # Получаем экранные координаты и глубины трёх вершин
    p = np.asarray(screen, dtype=float)
    z = np.asarray(depths, dtype=float)

    # Пропускаем треугольник с некорректными данными
    if np.any(z <= 0.02) or not np.all(np.isfinite(p)):
        return

    # Определяем прямоугольную область вокруг треугольника
    x0 = max(0, int(np.floor(p[:, 0].min())))
    x1 = min(width - 1, int(np.ceil(p[:, 0].max())))
    y0 = max(0, int(np.floor(p[:, 1].min())))
    y1 = min(height - 1, int(np.ceil(p[:, 1].max())))

    # Проверяем, попадает ли область в экран
    if x0 > x1 or y0 > y1:
        return

    # Получаем координаты вершин A, B, C
    a, b, c = p

    # Вычисляем знаменатель для барицентрических координат
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])

    # Пропускаем вырожденный треугольник
    if abs(den) < 1e-8:
        return

    # Создаём координаты всех пикселей внутри прямоугольной области
    yy, xx = np.mgrid[y0:y1+1, x0:x1+1]

    # Переходим к центрам пикселей
    xx = xx + .5
    yy = yy + .5

    # Вычисляем барицентрические коэффициенты для каждого пикселя
    u = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
    v = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
    w = 1 - u - v

    # Определяем пиксели, находящиеся внутри треугольника
    inside = (u >= -1e-7) & (v >= -1e-7) & (w >= -1e-7)

    # Вычисляем глубину каждого пикселя через обратную глубину 1/z
    with np.errstate(divide='ignore', invalid='ignore'):
        depth = 1 / (u/z[0] + v/z[1] + w/z[2])

    # Получаем соответствующие участки буферов глубины и цвета
    regionz = zbuf[y0:y1+1, x0:x1+1]
    regioncolor = rgb[y0:y1+1, x0:x1+1]

    # Если Z-буфер включён, выбираем только ближайшие пиксели
    if ztest:
        mask = inside & (depth < regionz) & np.isfinite(depth)

        # Сохраняем новые глубины ближайших поверхностей
        regionz[mask] = depth[mask]
    else:
        # Без Z-буфера закрашиваем все пиксели внутри треугольника
        mask = inside

    # Записываем цвет треугольника в выбранные пиксели
    regioncolor[mask] = color

