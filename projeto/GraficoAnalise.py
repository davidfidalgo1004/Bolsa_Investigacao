from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView,
    QDialog, QFormLayout, QLineEdit
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class GraphWindow(QDialog):
    def __init__(self, burned_data, forested_data, timesteps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gráfico de Evolução da Simulação")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)

        layout.addWidget(self.canvas)

        self.axes.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.axes.set_xlabel("Iterações")
        self.axes.set_ylabel("Quantidade")
        self.axes.grid(True)

        if timesteps:
            self.axes.plot(timesteps, burned_data, label='Queimadas', color='red')
            self.axes.plot(timesteps, forested_data, label='Florestadas', color='green')
            self.axes.legend()

        self.canvas.draw()