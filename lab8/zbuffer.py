"""Программный Z-буфер: глубина каждого пикселя и закраска треугольников.

Алгоритм не зависит от Tkinter: принимает массив RGB, массив глубин и
треугольник в экранных координатах. Меньшая положительная глубина ближе.
"""
import numpy as np


def clear_buffers(width, height, background=(247, 249, 252)):
    rgb = np.empty((height, width, 3), dtype=np.uint8)
    rgb[:] = background
    depth = np.full((height, width), np.inf, dtype=np.float32)
    return rgb, depth


def raster_triangle(screen, depths, color, rgb, zbuf, ztest=True):
    """Векторизованная растеризация треугольника с обратной глубиной 1/z."""
    height, width = zbuf.shape
    p = np.asarray(screen, dtype=float)
    z = np.asarray(depths, dtype=float)
    if np.any(z <= 0.02) or not np.all(np.isfinite(p)):
        return
    x0 = max(0, int(np.floor(p[:, 0].min())))
    x1 = min(width - 1, int(np.ceil(p[:, 0].max())))
    y0 = max(0, int(np.floor(p[:, 1].min())))
    y1 = min(height - 1, int(np.ceil(p[:, 1].max())))
    if x0 > x1 or y0 > y1:
        return
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-8:
        return
    yy, xx = np.mgrid[y0:y1+1, x0:x1+1]
    xx = xx + .5
    yy = yy + .5
    u = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
    v = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
    w = 1 - u - v
    inside = (u >= -1e-7) & (v >= -1e-7) & (w >= -1e-7)
    with np.errstate(divide='ignore', invalid='ignore'):
        depth = 1 / (u/z[0] + v/z[1] + w/z[2])
    regionz = zbuf[y0:y1+1, x0:x1+1]
    regioncolor = rgb[y0:y1+1, x0:x1+1]
    if ztest:
        mask = inside & (depth < regionz) & np.isfinite(depth)
        regionz[mask] = depth[mask]
    else:
        mask = inside
    regioncolor[mask] = color

