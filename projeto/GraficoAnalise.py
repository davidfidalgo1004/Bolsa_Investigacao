from PySide6.QtCore import QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QDialog, QVBoxLayout

class GraphWindow(QDialog):
    def __init__(self, burned_data=None, forested_data=None, timesteps=None, tree_heights=None, tree_altitudes=None, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)

        if burned_data is not None and forested_data is not None:
            self.setWindowTitle("Evolução de Árvores Queimadas vs Florestadas")
            self.axes.set_xlabel("Iterações")
            self.axes.set_ylabel("Quantidade")
            self.axes.grid(True)
            self.axes.plot(timesteps, burned_data, label='Queimadas', color='red')
            self.axes.plot(timesteps, forested_data, label='Florestadas', color='green')
            self.axes.legend()
        
        elif tree_altitudes is not None:
            self.setWindowTitle("Mapa de Altitude das Árvores")
            x, y, altitudes = zip(*tree_altitudes)
            scatter = self.axes.scatter(x, y, c=altitudes, cmap='terrain', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altitude")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")
        
        elif tree_heights is not None:
            self.setWindowTitle("Mapa de Altura das Árvores")
            x, y, heights = zip(*tree_heights)
            scatter = self.axes.scatter(x, y, c=heights, cmap='Greens', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altura das Árvores")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")

        self.canvas.draw()
