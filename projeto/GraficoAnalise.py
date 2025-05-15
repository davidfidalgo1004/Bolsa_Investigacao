from PySide6.QtWidgets import QDialog, QVBoxLayout, QGraphicsScene, QGraphicsView
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt

class GraphWindow(QDialog):
    def __init__(self, burned_data=None, forested_data=None, timesteps=None,
                 tree_heights=None, tree_altitudes=None,
                 air_co_evol=None, air_co2_evol=None, air_pm25_evol=None,
                 air_pm10_evol=None, air_o2_evol=None,
                 temperatura_evol=None, humidade_evol=None, precipitacao_evol=None,
                 parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Aumenta o tamanho para acomodar legendas externas
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)

        # 1) Gráfico evolução de árvores queimadas vs florestadas
        if burned_data is not None and forested_data is not None and timesteps is not None:
            self.setWindowTitle("Evolução de Árvores Queimadas vs Florestadas")
            self.axes.set_xlabel("Iterações")
            self.axes.set_ylabel("Quantidade de Árvores")
            self.axes.grid(True)
            self.axes.plot(timesteps, burned_data, label='Queimadas', color='red')
            self.axes.plot(timesteps, forested_data, label='Florestadas', color='green')
            # Legenda fora do gráfico
            self.axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # 2) Gráfico de altitude
        elif tree_altitudes is not None:
            self.setWindowTitle("Mapa de Altitude das Árvores")
            x, y, altitudes = zip(*tree_altitudes)
            scatter = self.axes.scatter(x, y, c=altitudes, cmap='terrain', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altitude (unidades)")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")
            self.axes.set_title("Distribuição de Altitudes")

        # 3) Gráfico de altura das árvores
        elif tree_heights is not None:
            self.setWindowTitle("Mapa de Altura das Árvores")
            x, y, heights = zip(*tree_heights)
            scatter = self.axes.scatter(x, y, c=heights, cmap='Greens', marker='s')
            self.fig.colorbar(scatter, ax=self.axes, label="Altura das Árvores (m)")
            self.axes.set_xlabel("Posição X")
            self.axes.set_ylabel("Posição Y")
            self.axes.set_title("Distribuição de Alturas")

        # 4) Gráfico com evolução do ar (CO, CO2, PM2.5, PM10, O2)
        elif (air_co_evol is not None and air_co2_evol is not None and
              air_pm25_evol is not None and air_pm10_evol is not None and
              air_o2_evol is not None and timesteps is not None):
            self.setWindowTitle("Evolução dos Poluentes e Oxigênio no Ar")
            self.axes.set_xlabel("Iterações")
            self.axes.set_ylabel("Níveis de Poluentes / O₂")
            self.axes.grid(True)
            self.axes.plot(timesteps, air_co_evol, label='CO', color='brown')
            self.axes.plot(timesteps, air_co2_evol, label='CO₂', color='gray')
            self.axes.plot(timesteps, air_pm25_evol, label='PM2.5', color='magenta')
            self.axes.plot(timesteps, air_pm10_evol, label='PM10', color='blue')
            self.axes.plot(timesteps, air_o2_evol, label='O₂', color='green')
            # Legenda fora do gráfico
            self.axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # 5) Gráfico com temperatura, humidade e precipitação
        elif (temperatura_evol is not None and humidade_evol is not None and
              precipitacao_evol is not None and timesteps is not None):
            self.setWindowTitle("Evolução de Temperatura, Humidade e Precipitação")
            self.axes.set_xlabel("Iterações")
            self.axes.set_ylabel("Valores")
            self.axes.grid(True)
            self.axes.plot(timesteps, temperatura_evol, label='Temperatura (°C)', color='red')
            self.axes.plot(timesteps, humidade_evol, label='Humidade (%)', color='green')
            self.axes.plot(timesteps, [p * 100 for p in precipitacao_evol],
                           label='Precipitação (%)', color='blue')
            # Legenda fora do gráfico
            self.axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # Ajusta layout para acomodar legendas externas
        self.fig.subplots_adjust(right=0.75)
        self.canvas.draw()


class FragulhaArrowsWindow(QDialog):
    """
    Exibe as trajetórias de fagulhas num gráfico cartesiano (xOy) tradicional,
    mostrando apenas o ponto inicial (0,0) e o ponto final.
    """
    def __init__(self, fragulha_history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trajetórias Detalhadas das Fragulhas (xOy)")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)

        all_x = []
        all_y = []

        for frag_id, path in fragulha_history.items():
            if len(path) > 1:
                x_coords, y_coords = zip(*path)

                # Ponto inicial absoluto
                x0, y0 = x_coords[0], y_coords[0]

                # Translada e inverte Y para corrigir espelhamento
                x_shifted = [x - x0 for x in x_coords]
                y_shifted = [y0 - y for y in y_coords]

                # Apenas início e fim
                self.axes.plot(x_shifted[0],  y_shifted[0],  'go')  # início (0,0)
                self.axes.plot(x_shifted[-1], y_shifted[-1], 'ro')  # fim

                all_x.extend([x_shifted[0], x_shifted[-1]])
                all_y.extend([y_shifted[0], y_shifted[-1]])

        # Ajusta limites do gráfico
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            self.axes.set_xlim(min_x - 1, max_x + 1)
            self.axes.set_ylim(min_y - 1, max_y + 1)

        # Mantém escala igual no X e Y
        self.axes.set_aspect("equal", adjustable="box")

        self.axes.set_xlabel("X")
        self.axes.set_ylabel("Y")
        self.axes.set_title("Trajetórias das Fragulhas (início em (0,0) e fim)")

        self.canvas.draw()



class FireStartWindow(QDialog):
    """
    Mostra os pontos onde o incêndio começou.
    Agora com inversão do eixo X para alinhar com a grelha da simulação.
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
            self.axes.scatter(
                x_coords, y_coords, color='red', marker='x', s=100,
                label="Início do Incêndio"
            )
            self.axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # Limites originais
        self.axes.set_xlim(0, world_width)
        self.axes.set_ylim(0, world_height)

        # >>> Inverte apenas o eixo X <<<
        self.axes.invert_xaxis()
        self.axes.invert_yaxis()
        # Mantém Y tal como na simulação (0,0 no canto inferior-esquerdo)
        # self.axes.invert_yaxis()  # deixe comentado se Y já estiver correto

        self.axes.set_xlabel("X")
        self.axes.set_ylabel("Y")
        self.axes.set_title("Pontos de Início do Incêndio")

        self.fig.subplots_adjust(right=0.75)
        self.canvas.draw()


class FirebreakMapWindow(QDialog):
    def __init__(self, firebreak_positions, world_width, world_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mapa de Linhas de Corte")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = Figure(figsize=(8, 6), dpi=100)  # Increased figure size
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)

        # Configura o tamanho do gráfico
        self.axes.set_xlim(0, world_width)
        self.axes.set_ylim(0, world_height)

        # Desenha as linhas de corte
        if firebreak_positions:
            # Agrupa posições consecutivas para formar linhas
            lines = []
            current_line = []
            
            for pos in firebreak_positions:
                if not current_line:
                    current_line.append(pos)
                else:
                    last_pos = current_line[-1]
                    # Se a posição atual é adjacente à última, adiciona à linha atual
                    if abs(pos[0] - last_pos[0]) <= 1 and abs(pos[1] - last_pos[1]) <= 1:
                        current_line.append(pos)
                    else:
                        # Se não é adjacente, finaliza a linha atual e começa uma nova
                        if len(current_line) > 1:
                            lines.append(current_line)
                        current_line = [pos]
            
            # Adiciona a última linha se tiver mais de um ponto
            if len(current_line) > 1:
                lines.append(current_line)

            # Desenha as linhas com estilo melhorado
            for line in lines:
                x_coords, y_coords = zip(*line)
                # Linha principal mais grossa e laranja
                self.axes.plot(x_coords, y_coords, color='orange', linewidth=3, 
                             label='Linha de Corte' if line == lines[0] else "")
                # Adiciona pontos nos vértices
                self.axes.scatter(x_coords, y_coords, color='red', s=30, 
                                label='Pontos de Corte' if line == lines[0] else "")

        # Inverte os eixos para corresponder à visualização da simulação
        self.axes.invert_xaxis()
        self.axes.invert_yaxis()

        # Configurações do gráfico
        self.axes.set_xlabel("Posição X")
        self.axes.set_ylabel("Posição Y")
        self.axes.set_title("Mapa de Linhas de Corte de Fogo", pad=20, size=12)
        
        # Adiciona grade com estilo melhorado
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        # Adiciona legenda
        if firebreak_positions:
            self.axes.legend(loc='upper right', bbox_to_anchor=(1.15, 1))

        # Mantém a proporção dos eixos igual
        self.axes.set_aspect("equal", adjustable="box")

        # Ajusta o layout para evitar cortes
        self.fig.tight_layout()

        self.canvas.draw()