import matplotlib.pyplot as plt
import numpy as np
import random
from matplotlib.collections import LineCollection, PolyCollection
from task1a import load_system, generate_l_system


def draw_fractal_tree(system):
    rng = random.Random(system.get('seed'))
    instructions = generate_l_system(system['axiom'], system['rules'], system['iterations'])
    x, y = 0.0, 0.0
    angle = np.radians(system['start_direction'])
    turn = np.radians(system['angle'])
    random_angle = np.radians(system.get('random_angle', 0.0))
    stack, segments, tips = [], [], [] #стек для запоминания положения, seegments— список всех отрезков дерева, tips писок концов ветвей
    depth = 0

    for ch in instructions:
        if ch == 'F':
            a = angle + rng.uniform(-random_angle, random_angle)
            new_x, new_y = x + np.sin(a), y + np.cos(a)
            segments.append(((x, y), (new_x, new_y), depth))
            x, y = new_x, new_y
        elif ch == '+':
            angle += turn
        elif ch == '-':
            angle -= turn
        elif ch == '@':
            angle += rng.uniform(-random_angle, random_angle)
        elif ch == '[':
            stack.append((x, y, angle, depth))
            depth += 1
        elif ch == ']' and stack:
            x, y, angle, depth = stack.pop()
        elif ch in ('X', 'C'):
            tips.append((x, y, angle))

    if not segments:
        print('Дерево не построено')
        return

    deepest = max(d for _, _, d in segments) #самая глубокая ветка, чтобы сделать плавный градиент
    dark = np.array([0.40, 0.22, 0.08])  
    pale = np.array([0.55, 0.72, 0.48]) 
    lines, colors, widths = [], [], []
    for start, end, d in segments:
        t = d / max(deepest, 1)
        lines.append((start, end))
        colors.append(dark * (1 - t) + pale * t)
        widths.append(max(0.32, 7.0 * 0.66 ** d))

   
    twig_lines, leaf_shapes, leaf_colors = [], [], []
    palette = ['#789c76', '#8ead89', '#a5bca1', '#bdd0b8', '#9ab497']

    for px, py, direction in tips:
    #3 тонких стебелька: влево, прямо и вправо
        for side in (-1, 0, 1):
            a = direction + np.radians(side * rng.uniform(15, 42))
            length = rng.uniform(0.35, 0.65)
            start = np.array([px, py])
            unit = np.array([np.sin(a), np.cos(a)])
            end = start + length * unit
            twig_lines.append((start, end))

           ''' 
            for fraction in (0.40, 0.78):
                center = start + fraction * length * unit # точка, откуда растёт лист
                for leaf_side in (-1, 1):
                    ## Направление листа (отклоняется от стебелька на 32-58 градусов)
                    leaf_dir = a + leaf_side * np.radians(rng.uniform(32, 58))
                    axis = np.array([np.sin(leaf_dir), np.cos(leaf_dir)])
                    normal = np.array([-axis[1], axis[0]])
                    #  Размеры листа
                    leaf_length = rng.uniform(0.18, 0.29)
                    leaf_half_width = leaf_length * rng.uniform(0.19, 0.28)
                    tip = center + leaf_length * axis #кончик листа
                    mid = center + 0.55 * leaf_length * axis #середина листа
                    leaf_shapes.append([
                        center,
                        mid + leaf_half_width * normal,
                        tip,
                        mid - leaf_half_width * normal
                    ])
                    leaf_colors.append(rng.choice(palette))''''

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor('#fffbd5') ## Нежно-желтый фон
    ax.set_facecolor('#fffbd5')
    ax.add_collection(LineCollection(lines, colors=colors, linewidths=widths, capstyle='round'))
    if twig_lines:
        ax.add_collection(LineCollection(twig_lines, colors='#8da68a', linewidths=0.42, alpha=0.78))
    if leaf_shapes:
        ax.add_collection(PolyCollection(leaf_shapes, facecolors=leaf_colors, edgecolors='none', alpha=0.8, zorder=3))

    all_points = [p for a, b, _ in segments for p in (a, b)]
    for leaf in leaf_shapes:
        all_points.extend(leaf)
    coords = np.asarray(all_points)
    xmin, ymin = coords.min(axis=0)
    xmax, ymax = coords.max(axis=0)
    w, h = max(xmax - xmin, 1), max(ymax - ymin, 1)
    #отступы 7%, чтобы дерево не прилипало к краям
    ax.set_xlim(xmin - w * 0.07, xmax + w * 0.07)
    ax.set_ylim(ymin - h * 0.07, ymax + h * 0.07)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(system.get('name', 'Fractal Tree'), fontsize=16)
    plt.tight_layout()
    plt.show()



if __name__ == '__main__':
    try:
        system = load_system('tree.txt')
        draw_fractal_tree(system)
    except Exception as e:
        print(f'Ошибка: {e}')
