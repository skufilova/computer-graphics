import tkinter as tk
from PIL import Image, ImageDraw, ImageTk


class Task2Window:
    def __init__(self, root: tk.Tk, parent):
        self.root = root
        self.parent = parent
        self.root.configure(bg=parent.back_ground)
        self.root.geometry("600x400+500+20")
        self.root.title("Task 2")

        self.canvas_bresenham = tk.Canvas(self.root, bg="white")
        self.canvas_bresenham.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.canvas_wu = tk.Canvas(self.root, bg="white")
        self.canvas_wu.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        label_bresenham = tk.Label(
            self.root, text="Алгоритм Брезенхема", bg=parent.back_ground, fg="white"
        )
        label_bresenham.grid(row=0, column=0, padx=10)
        label_wu = tk.Label(self.root, text="Алгоритм Ву", bg=parent.back_ground, fg="white")
        label_wu.grid(row=0, column=1, padx=10)

        self.reset_button = tk.Button(self.root, text="Reset", command=self.reset_canvas, bg="#555", fg="white")
        self.reset_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.root.bind("<Configure>", self.on_resize)

        self.image_bresenham = None
        self.image_wu = None

        self.current_point_bresenham = None
        self.current_point_wu = None

        self.lines_bresenham = []
        self.lines_wu = []

        self.canvas_bresenham.bind("<Button-1>", self.on_click_bresenham)
        self.canvas_wu.bind("<Button-1>", self.on_click_wu)

        self.draw_segments()

    def draw_segments(self):
        width = self.canvas_bresenham.winfo_width()
        height = self.canvas_bresenham.winfo_height()

        self.image_bresenham = Image.new("RGB", (width, height), "white")
        self.image_wu = Image.new("RGBA", (width, height), "white")

        for line in self.lines_bresenham:
            self.draw_bresenham(self.image_bresenham, *line)
        for line in self.lines_wu:
            self.draw_wu(self.image_wu, *line)

        self.update_canvas()

    def draw_bresenham(self, image, x1, y1, x2, y2):
        draw = ImageDraw.Draw(image)
        points = self.bresenham(int(x1), int(y1), int(x2), int(y2))
        for x, y in points:
            draw.point((x, y), fill="black")

    def draw_wu(self, image, x1, y1, x2, y2):
        draw = ImageDraw.Draw(image)
        points = self.wu(int(x1), int(y1), int(x2), int(y2))
        for x, y, brightness in points:
            color = f"#{int(brightness * 255):02x}{int(brightness * 255):02x}{int(brightness * 255):02x}"
            draw.point((x, y), fill=(0, 0, 0, int(brightness * 255)))

    

    def plot_line_low(self, x0, y0, x1, y1):
       
        points = []

        dx = x1 - x0
        dy = y1 - y0

        yi = 1
        if dy < 0:
            yi = -1
            dy = -dy

        D = 2 * dy - dx
        y = y0

        for x in range(x0, x1 + 1):
            points.append((x, y))
            if D > 0:
                y += yi
                D += 2 * (dy - dx)
            else:
                D += 2 * dy

        return points

    def plot_line_high(self, x0, y0, x1, y1):
   
        points = []

        dx = x1 - x0
        dy = y1 - y0

        xi = 1
        if dx < 0:
            xi = -1
            dx = -dx

        D = 2 * dx - dy
        x = x0

        for y in range(y0, y1 + 1):
            points.append((x, y))
            if D > 0:
                x += xi
                D += 2 * (dx - dy)
            else:
                D += 2 * dx

        return points

    def bresenham(self, x1, y1, x2, y2):
        points = []

        if abs(y2 - y1) < abs(x2 - x1):
            if x1 > x2:
                points = self.plot_line_low(x2, y2, x1, y1)
                points.reverse()
            else:
                points = self.plot_line_low(x1, y1, x2, y2)
        else:
            if y1 > y2:
                points = self.plot_line_high(x2, y2, x1, y1)
                points.reverse()
            else:
                points = self.plot_line_high(x1, y1, x2, y2)

        return points

    # ---------- Ву ----------

    def wu(self, x1, y1, x2, y2):
        points = []
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0:
            step = 1 if y1 < y2 else -1
            for y in range(y1, y2 + step, step):
                brightness = 1.0
                points.append((x1, y, brightness))
            return points

        gradient = dy / dx if dx != 0 else 0
        if abs(dx) > abs(dy):
            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
            y = y1
            for x in range(x1, x2 + 1):
                brightness = min(max(1 - (y - int(y)), 0), 1)
                points.append((x, int(y), brightness))
                points.append((x, int(y) + 1, 1 - brightness))
                y += gradient
        else:
            if y1 > y2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
            x = x1
            for y in range(y1, y2 + 1):
                brightness = min(max(1 - (x - int(x)), 0), 1)
                points.append((int(x), y, brightness))
                points.append((int(x) + 1, y, 1 - brightness))
                x += 1 / gradient if gradient != 0 else 0

        return points

    # ---------- Служебное ----------

    def on_resize(self, event):
        self.draw_segments()

    def update_canvas(self):
        if self.image_bresenham:
            self.tk_image_bresenham = ImageTk.PhotoImage(self.image_bresenham)
            self.canvas_bresenham.create_image(
                0, 0, anchor="nw", image=self.tk_image_bresenham
            )
            self.canvas_bresenham.image = self.tk_image_bresenham
        if self.image_wu:
            self.tk_image_wu = ImageTk.PhotoImage(self.image_wu)
            self.canvas_wu.create_image(0, 0, anchor="nw", image=self.tk_image_wu)
            self.canvas_wu.image = self.tk_image_wu

    def on_click_bresenham(self, event):
        if self.current_point_bresenham is None:
            self.current_point_bresenham = (event.x, event.y)
        else:
            x1, y1 = self.current_point_bresenham
            x2, y2 = event.x, event.y
            self.draw_bresenham(self.image_bresenham, x1, y1, x2, y2)
            self.lines_bresenham.append((x1, y1, x2, y2))
            self.current_point_bresenham = (x2, y2)
            self.update_canvas()

    def on_click_wu(self, event):
        if self.current_point_wu is None:
            self.current_point_wu = (event.x, event.y)
        else:
            x1, y1 = self.current_point_wu
            x2, y2 = event.x, event.y
            self.draw_wu(self.image_wu, x1, y1, x2, y2)
            self.lines_wu.append((x1, y1, x2, y2))
            self.current_point_wu = (x2, y2)
            self.update_canvas()

    def reset_canvas(self):
        self.lines_bresenham.clear()
        self.lines_wu.clear()
        self.current_point_bresenham = None
        self.current_point_wu = None
        self.draw_segments()