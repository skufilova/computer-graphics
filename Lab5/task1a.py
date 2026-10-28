import matplotlib.pyplot as plt
import numpy as np
import random
import re
import os
import glob


def load_system(path):
    """Читает описание L-системы из текстового файла."""
    params = {}
    rules = {}
    header_tokens = None

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            # Правило: "X -> F[+X]" или "X=F[+X]" или "X:F[+X]"
            if "->" in line or "→" in line:
                lhs, rhs = re.split(r"->|→", line, maxsplit=1)
                lhs = lhs.strip()
                rules[lhs] = rhs.strip()
                continue
            elif "=" in line and len(line.split("=")[0].strip()) == 1:
                lhs, rhs = line.split("=", 1)
                rules[lhs.strip()] = rhs.strip()
                continue
            elif ":" in line and len(line.split(":")[0].strip()) == 1:
                lhs, rhs = line.split(":", 1)
                rules[lhs.strip()] = rhs.strip()
                continue

            # Строка-заголовок в формате "<атом> <угол> <направление>"
            parts = line.split()
            if len(parts) in (3, 4) and "=" not in line and "->" not in line:
                try:
                    axiom, angle, start_dir = parts[0], float(parts[1]), float(parts[2])
                    if len(parts) == 4:
                        params["random_angle"] = parts[3]
                    header_tokens = (axiom, angle, start_dir)
                    continue
                except ValueError:
                    pass

            # Параметр key=value
            if "=" in line:
                key, val = line.split("=", 1)
                if len(key.strip()) > 1: # чтобы не спутать с правилом F=F
                    params[key.strip()] = val.strip()
                continue

    # Собираем систему
    system = {}
    if header_tokens is not None:
        system["axiom"] = header_tokens[0]
        system["angle"] = header_tokens[1]
        system["start_direction"] = header_tokens[2]

    if "axiom" in params: system["axiom"] = params["axiom"]
    if "angle" in params: system["angle"] = float(params["angle"])
    if "start_direction" in params: system["start_direction"] = float(params["start_direction"])

    system.setdefault("axiom", "X")
    system.setdefault("angle", 90.0)
    system.setdefault("start_direction", 0.0)

    system["name"] = params.get("name", os.path.basename(path).replace(".txt", ""))
    system["random_angle"] = float(params.get("random_angle", 0.0))
    system["seed"] = int(params["seed"]) if "seed" in params else None
    system["iterations"] = int(params.get("iterations", 5))
    system["rules"] = rules

    return system

# --- 1.а. Генерация L-системы ---
def generate_l_system(axiom, rules, iterations):
    current = axiom
    for _ in range(iterations):
        current = "".join(rules.get(ch, ch) for ch in current)
    return current

# --- 1.а. Перевод в точки ---
def instructions_to_points(system, iterations):
    rng = random.Random(system.get("seed"))
    instructions = generate_l_system(system["axiom"], system["rules"], iterations)
    
    x, y = 0.0, 0.0
    current_angle = np.radians(system["start_direction"])
    stack = []
    points = [(x, y)]

    for ch in instructions:
        if ch == "F":
            step = 1.0
            ang = current_angle
            
            if system.get("random_angle", 0) > 0:
                ang += np.radians(rng.uniform(-system["random_angle"], system["random_angle"]))
                
            x_new = x + step * np.sin(ang)
            y_new = y + step * np.cos(ang)
            points.append((x_new, y_new))
            x, y = x_new, y_new
        elif ch == "+":
            current_angle += np.radians(system["angle"])
        elif ch == "-":
            current_angle -= np.radians(system["angle"])
        elif ch == "@":
            r_ang = system.get("random_angle", 45)
            current_angle += np.radians(rng.uniform(-r_ang, r_ang))
        elif ch == "[":
            stack.append((x, y, current_angle))
        elif ch == "]":
            if stack:
                x, y, current_angle = stack.pop()
                points.append((x, y))

    return points

# --- 1.а. Отрисовка ---
def draw_points(points, title):
    if not points:
        return
    pts = np.asarray(points, dtype=float)
    mn = pts.min(axis=0)
    mx = pts.max(axis=0)
    pts = pts - mn
    span = mx - mn
    scale = max(span.max(), 1.0)
    pts = pts / scale
    plt.figure(figsize=(8, 8))
    plt.plot(pts[:, 0], pts[:, 1], color="green", linewidth=1)
    plt.axis("equal")
    plt.axis("off")
    plt.title(title)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join("l_systems", "*.txt")))
    
    if not files:
        print("Файлы .txt не найдены. Убедитесь, что они лежат в той же папке, что и скрипт.")
    else:
        for path in files:
            try:
                sys_info = load_system(path)
                print(f"Построение: {sys_info['name']} (итераций: {sys_info['iterations']})...")
                
                pts = instructions_to_points(sys_info, sys_info["iterations"])
                draw_points(pts, f"{sys_info['name']} (итераций: {sys_info['iterations']})")
                
            except Exception as e:
                print(f"Ошибка при чтении {path}: {e}")

        print("Все фракталы успешно построены!")