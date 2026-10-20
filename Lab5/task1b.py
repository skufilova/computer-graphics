import matplotlib.pyplot as plt
import numpy as np
import random

from task1a import load_system, generate_l_system

def draw_fractal_tree(system):
    rng = random.Random(system.get("seed", 42))

    # функция из 1.а
    instructions = generate_l_system(
        system["axiom"],
        system["rules"],
        system["iterations"]
    )

    x, y = 0.0, 0.0
    angle = np.radians(system["start_direction"])
    stack = []
    segments = []

    step = 1.0
    max_depth = max(system["iterations"], 1)
    base_width = 8.0
    random_angle = system.get("random_angle", 8.0)
    depth = 0

    for ch in instructions:
        if ch == "F":
            actual_angle = angle + np.radians(rng.uniform(-random_angle, random_angle))
            # Рост ВВЕРХ: sin для X, cos для Y
            x_new = x + step * np.sin(actual_angle)
            y_new = y + step * np.cos(actual_angle)

            t = min(depth / max_depth, 1.0)
            branch_width = base_width * (0.65 ** depth)

            segments.append({
                "x1": x, "y1": y, "x2": x_new, "y2": y_new,
                "depth": depth, "width": branch_width, "color_t": t
            })
            x, y = x_new, y_new

        elif ch == "+":
            angle += np.radians(system["angle"])
        elif ch == "-":
            angle -= np.radians(system["angle"])
        elif ch == "@":
            angle += np.radians(rng.uniform(-random_angle, random_angle))
        elif ch == "[":
            stack.append((x, y, angle, depth))
            depth += 1
        elif ch == "]":
            if stack:
                x, y, angle, depth = stack.pop()

    if not segments:
        print("Дерево не построено.")
        return

    # Границы и масштабирование
    xs = [s["x1"] for s in segments] + [s["x2"] for s in segments]
    ys = [s["y1"] for s in segments] + [s["y2"] for s in segments]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)

    # Цвета
    brown = np.array([0.40, 0.20, 0.08])
    green = np.array([0.10, 0.55, 0.12])

    fig, ax = plt.subplots(figsize=(8, 9))

    for s in segments:
        height = (s["y1"] - min_y) / span_y
        height = np.clip(height, 0.0, 1.0)
        depth_factor = min(s["depth"] / max_depth, 1.0)
        
        # Сужение ствола к верхушке
        height_factor = 1.0 - 0.55 * height
        width = max(0.5, s["width"] * height_factor)

        # Градиент цвета
        color_t = max(depth_factor, height * 0.45)
        color_t = np.clip(color_t, 0.0, 1.0)
        color = brown * (1 - color_t) + green * color_t

        ax.plot([s["x1"], s["x2"]], [s["y1"], s["y2"]], 
                color=color, linewidth=width, solid_capstyle="round")

    margin_x = span_x * 0.10
    margin_y = span_y * 0.06
    ax.set_xlim(min_x - margin_x, max_x + margin_x)
    ax.set_ylim(min_y - margin_y, max_y + margin_y)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(system.get("name", "Fractal Tree"), fontsize=16)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        system = load_system("tree.txt") 
        print("Построение фрактального дерева...")
        draw_fractal_tree(system)
        print("Построение завершено!")
    except Exception as e:
        print(f"Ошибка: {e}")