from PySide6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as mpatches

class GraphWindow(QDialog):
    def __init__(self, burned_data=None, forested_data=None, timesteps=None,
                 tree_heights=None, tree_altitudes=None, parent=None):
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
            self.axes.set_ylabel("Quantidade de Árvores")
            self.axes.grid(True)
            self.axes.plot(timesteps, burned_data, label='Queimadas', color='red')
            self.axes.plot(timesteps, forested_data, label='Florestadas', color='green')
            self.axes.legend(loc='best')
        elif tree_altitudes is not None:
            self.setWindowTitle("Mapa de Altitude das Árvores")
            x, y, altitudes = zip(*tree_altitudes)
            scatter = self.axes.scatter(x, y, c=altitudes, cmap='terrain', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altitude (unidades)")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")
            self.axes.set_title("Distribuição de Altitudes")
        elif tree_heights is not None:
            self.setWindowTitle("Mapa de Altura das Árvores")
            x, y, heights = zip(*tree_heights)
            scatter = self.axes.scatter(x, y, c=heights, cmap='Greens', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altura das Árvores (m)")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")
            self.axes.set_title("Distribuição de Alturas")

        self.canvas.draw()

class FragulhaArrowsWindow(QDialog):
    """
    Janela que desenha trajetórias detalhadas das fragulhas,
    utilizando linha contínua com marcadores em cada ponto.
    """
    def __init__(self, fragulha_history, world_width, world_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trajetórias Detalhadas das Fragulhas")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)
        # Desenha cada trajetória com linha contínua e marcador em cada ponto
        for frag_id, path in fragulha_history.items():
            if len(path) > 1:
                x_coords, y_coords = zip(*path)
                self.axes.plot(x_coords, y_coords, marker='o', linestyle='-', color='red', alpha=0.8)
                # Marca o início (verde) e o fim (vermelho)
                self.axes.plot(x_coords[0], y_coords[0], 'go')
                self.axes.plot(x_coords[-1], y_coords[-1], 'ro')
        self.axes.set_xlim(0, world_width)
        self.axes.set_ylim(0, world_height)
        # Inverte o eixo Y para que o gráfico corresponda ao grid da simulação
        self.axes.invert_yaxis()
        self.axes.set_xlabel("X")
        self.axes.set_ylabel("Y")
        self.axes.set_title("Trajetórias das Fragulhas")
        self.canvas.draw()

class FireStartWindow(QDialog):
    """
    Janela que mostra os pontos onde o incêndio foi iniciado.
    """
    def __init__(self, fire_start_positions, world_width, world_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pontos de Início do Incêndio")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)
        
        if fire_start_positions:
            x_coords, y_coords = zip(*fire_start_positions)
            self.axes.scatter(x_coords, y_coords, color='red', marker='x', s=100, label="Início do Incêndio")
            self.axes.legend(loc='best')
        
        self.axes.set_xlim(0, world_width)
        self.axes.set_ylim(0, world_height)
        self.axes.invert_yaxis()  # Para que o gráfico combine com o grid da simulação
        self.axes.set_xlabel("X")
        self.axes.set_ylabel("Y")
        self.axes.set_title("Pontos de Início do Incêndio")
        self.canvas.draw()
