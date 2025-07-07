import tkinter as tk
from tkinter import Scrollbar, Canvas

class TreeVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minimax Tree Visualizer")
        self.geometry("1200x700")

        self.frame = tk.Frame(self)
        self.frame.pack(fill="both", expand=True)

        # Scrollbars
        self.hbar = Scrollbar(self.frame, orient="horizontal")
        self.hbar.pack(side="bottom", fill="x")
        self.vbar = Scrollbar(self.frame, orient="vertical")
        self.vbar.pack(side="right", fill="y")

        self.canvas = Canvas(self.frame, bg="white", scrollregion=(0, 0, 3000, 3000),
                             xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(fill="both", expand=True)

        self.hbar.config(command=self.canvas.xview)
        self.vbar.config(command=self.canvas.yview)

        self.bind("<MouseWheel>", self.zoom)
        self.scale = 1.0

        self.nodes = {}

    def draw_tree(self, root):
        self.canvas.delete("all")
        self._draw_node(root, 1500, 50, x_spacing=300)

    def count_leaves(self, node):
        if not node.children:
            return 1
        return sum(self.count_leaves(child) for child in node.children)

    def _draw_node(self, node, x, y, x_spacing):
        # Determine node label
        if node.is_chance and node.is_max is None:  # chance wrapper node
            label = f"CHANCE WRAPPER\nS:{node.score}"
        elif node.is_chance:    # chance node
            label = f"CHANCE\nS:{node.score}"
        elif node.probability is not None:
            label = f"{'MAX' if node.is_max else 'MIN'}\nS:{node.score}\nP={node.probability}"
        else:
            label = f"{'MAX' if node.is_max else 'MIN'}\nS:{node.score}"

        # Determine node color
        if node.best:
            node_color = "orange"
        elif node.is_chance and node.probability is not None:
            node_color = "yellow"  # inner chance node
        elif node.is_chance:
            node_color = "violet"  # wrapper node
        else:
            node_color = "lightgreen" if node.is_max else "lightblue"

        # Draw the node
        node_id = self.canvas.create_oval(x - 50, y - 50, x + 50, y + 50, fill=node_color)
        text_id = self.canvas.create_text(x, y, text=label)
        self.nodes[node] = (node_id, text_id)

        if not node.children:
            return

        total_leaves = sum(self.count_leaves(child) for child in node.children)
        spacing_unit = x_spacing

        left = x - total_leaves * spacing_unit / 2
        for child in node.children:
            child_leaves = self.count_leaves(child)
            child_x = left + child_leaves * spacing_unit / 2
            line_color = "red" if child.best else "grey"
            self.canvas.create_line(x, y + 30, child_x, y + 100 - 30, fill=line_color, width=2 if child.best else 1)
            self._draw_node(child, child_x, y + 100, x_spacing)
            left += child_leaves * spacing_unit



    def zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor
        self.canvas.scale("all", 0, 0, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
