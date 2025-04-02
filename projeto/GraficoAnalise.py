from PySide6.QtCore import QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QDialog, QVBoxLayout
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
            # Gráfico de evolução (queimadas vs florestadas)
            self.setWindowTitle("Evolução de Árvores Queimadas vs Florestadas")
            self.axes.set_xlabel("Iterações")
            self.axes.set_ylabel("Quantidade de Árvores")
            self.axes.grid(True)
            self.axes.plot(timesteps, burned_data, label='Queimadas', color='red')
            self.axes.plot(timesteps, forested_data, label='Florestadas', color='green')
            self.axes.legend(loc='best')
        
        elif tree_altitudes is not None:
            # Mapa de Altitude
            self.setWindowTitle("Mapa de Altitude das Árvores")
            x, y, altitudes = zip(*tree_altitudes)
            scatter = self.axes.scatter(x, y, c=altitudes, cmap='terrain', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altitude (unidades)")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")
            self.axes.set_title("Distribuição de Altitudes")
        
        elif tree_heights is not None:
            # Mapa de Altura
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
    Janela que desenha setas indicando o caminho (path) de cada fragulha,
    com legendas para entender o que cada símbolo representa.
    """
    def __init__(self, fragulha_history, world_width, world_height, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Mapa de Fragulhas (Setas)")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)

        # Exemplo de patches para exibir na legenda
        arrow_patch = mpatches.FancyArrowPatch((0,0),(1,0), color="red", alpha=0.8)
        arrow_patch.set_label("Trajeto da fragulha")
        self.axes.add_patch(arrow_patch)
        self.axes.plot([], [], 'go', label="Início")
        self.axes.plot([], [], 'ro', label="Fim")

        # Remove o patch de "demonstração" (pois desenharemos o real)
        arrow_patch.remove()

        # Para cada fragulha, desenhar a sequência de setas
        for frag_id, path in fragulha_history.items():
            if len(path) > 1:
                for i in range(len(path) - 1):
                    x0, y0 = path[i]
                    x1, y1 = path[i+1]
                    dx = x1 - x0
                    dy = y1 - y0
                    self.axes.arrow(
                        x0, y0, dx, dy,
                        head_width=0.3,
                        length_includes_head=True,
                        color="red",
                        alpha=0.8
                    )
                # Marca início (verde) e fim (vermelho)
                self.axes.plot(path[0][0], path[0][1], 'go')
                self.axes.plot(path[-1][0], path[-1][1], 'ro')

        self.axes.set_xlim(0, world_width)
        self.axes.set_ylim(0, world_height)
        self.axes.set_xlabel("X")
        self.axes.set_ylabel("Y")
        self.axes.set_title("Trajetos das Fragulhas")

        self.axes.legend(loc='best')
        self.canvas.draw()
