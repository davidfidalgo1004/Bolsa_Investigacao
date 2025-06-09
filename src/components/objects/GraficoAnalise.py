# Third-party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGraphicsScene, QGraphicsView, 
    QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt


class BaseGraphWindow(QDialog):
    """Classe base para janelas de gráficos com funcionalidade de download."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_for_csv = None  # Will store data for CSV export
        
    def add_download_buttons(self, layout):
        """Adiciona botões de download CSV e PNG ao layout."""
        button_layout = QHBoxLayout()
        
        # Botão Download PNG
        self.btn_download_png = QPushButton("💾 Download PNG")
        self.btn_download_png.clicked.connect(self.download_png)
        button_layout.addWidget(self.btn_download_png)
        
        # Botão Download CSV
        self.btn_download_csv = QPushButton("📊 Download CSV")
        self.btn_download_csv.clicked.connect(self.download_csv)
        button_layout.addWidget(self.btn_download_csv)
        
        layout.addLayout(button_layout)
    
    def download_png(self):
        """Exporta o gráfico como PNG."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Gráfico", 
                f"{self.windowTitle()}.png", 
                "PNG Files (*.png)"
            )
            if file_path:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Sucesso", f"Gráfico guardado em:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao guardar PNG:\n{str(e)}")
    
    def download_csv(self):
        """Exporta os dados como CSV."""
        if self.data_for_csv is None:
            QMessageBox.warning(self, "Aviso", "Não há dados disponíveis para exportar.")
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Dados", 
                f"{self.windowTitle()}.csv", 
                "CSV Files (*.csv)"
            )
            if file_path:
                if isinstance(self.data_for_csv, dict):
                    df = pd.DataFrame(self.data_for_csv)
                else:
                    df = self.data_for_csv
                df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Sucesso", f"Dados guardados em:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao guardar CSV:\n{str(e)}")


def plot_trajectories(model):
    """Desenha as trajectórias percorridas por todos os bombeiros."""
    plt.figure(figsize=(6, 6))

    for ag in model.schedule:
        if hasattr(ag, "history"):
            xs, ys = zip(*ag.history)

            # bombeiros "alternative" em laranja; os de água em azul‑escuro
            cor = "orange" if getattr(ag, "technique", "water") == "alternative" else "navy"
            lbl = "Técnico" if cor == "orange" else "Apagadores"

            plt.plot(xs, ys, color=cor, linewidth=.9, marker="o", markersize=1.8, label=lbl)

    plt.gca().set_aspect("equal", "box")
    # evita legendas duplicadas
    handles, labels = plt.gca().get_legend_handles_labels()
    by_lbl = dict(zip(labels, handles))
    plt.legend(by_lbl.values(), by_lbl.keys(), loc="upper right")
    plt.title("Trajectórias dos Bombeiros")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.tight_layout()
    plt.show()


class GraphWindow(BaseGraphWindow):
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

        # Prepara dados para CSV baseado no tipo de gráfico
        if burned_data is not None and forested_data is not None and timesteps is not None:
            self.data_for_csv = {
                'Iteracao': timesteps,
                'Arvores_Queimadas': burned_data,
                'Arvores_Florestadas': forested_data
            }
        elif tree_altitudes is not None:
            x, y, altitudes = zip(*tree_altitudes)
            self.data_for_csv = {
                'Posicao_X': x,
                'Posicao_Y': y,
                'Altitude': altitudes
            }
        elif tree_heights is not None:
            x, y, heights = zip(*tree_heights)
            self.data_for_csv = {
                'Posicao_X': x,
                'Posicao_Y': y,
                'Altura_Arvores': heights
            }
        elif (air_co_evol is not None and air_co2_evol is not None):
            self.data_for_csv = {
                'Iteracao': timesteps,
                'CO': air_co_evol,
                'CO2': air_co2_evol,
                'PM2_5': air_pm25_evol,
                'PM10': air_pm10_evol,
                'O2': air_o2_evol
            }
        elif (temperatura_evol is not None and humidade_evol is not None):
            self.data_for_csv = {
                'Iteracao': timesteps,
                'Temperatura_C': temperatura_evol,
                'Humidade_Percent': humidade_evol,
                'Precipitacao_Percent': [p * 100 for p in precipitacao_evol]
            }

        # Ajusta layout para acomodar legendas externas
        self.fig.subplots_adjust(right=0.75)
        self.canvas.draw()
        
        # Adiciona botões de download
        self.add_download_buttons(layout)


class FragulhaArrowsWindow(BaseGraphWindow):
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

        # Prepara dados para CSV
        csv_data = []
        for frag_id, path in fragulha_history.items():
            if len(path) > 1:
                x_coords, y_coords = zip(*path)
                x0, y0 = x_coords[0], y_coords[0]
                x_shifted = [x - x0 for x in x_coords]
                y_shifted = [y0 - y for y in y_coords]
                
                csv_data.append({
                    'Fragulha_ID': frag_id,
                    'X_Inicio': x_shifted[0],
                    'Y_Inicio': y_shifted[0],
                    'X_Fim': x_shifted[-1],
                    'Y_Fim': y_shifted[-1],
                    'Distancia': ((x_shifted[-1] - x_shifted[0])**2 + (y_shifted[-1] - y_shifted[0])**2)**0.5
                })
        
        if csv_data:
            self.data_for_csv = pd.DataFrame(csv_data)

        self.canvas.draw()
        
        # Adiciona botões de download
        self.add_download_buttons(layout)



class FireStartWindow(BaseGraphWindow):
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

        # Prepara dados para CSV
        if fire_start_positions:
            x_coords, y_coords = zip(*fire_start_positions)
            self.data_for_csv = {
                'Posicao_X': x_coords,
                'Posicao_Y': y_coords,
                'Tipo': ['Inicio_Incendio'] * len(x_coords)
            }

        self.fig.subplots_adjust(right=0.75)
        self.canvas.draw()
        
        # Adiciona botões de download
        self.add_download_buttons(layout)


class FirebreakMapWindow(BaseGraphWindow):
    """Exibe todas as linhas de corte desenhadas durante a simulação.

    A versão anterior agrupava posições apenas na ordem em que eram registadas –
    se os pontos chegavam desordenados, muitas linhas ficavam com tamanho 1 e
    eram descartadas.  Agora usamos uma busca em largura (BFS) para encontrar
    *todos* os componentes conectados (vizinhança de Moore) garantindo que cada
    segmento aparece, mesmo os de um único patch."""

    def __init__(self, firebreak_positions, world_width, world_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mapa de Linhas de Corte")
        layout = QVBoxLayout(); self.setLayout(layout)
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.fig); layout.addWidget(self.canvas)
        ax = self.fig.add_subplot(111)
        ax.invert_yaxis()
        ax.set_xlim(0, world_width); ax.set_ylim(0, world_height)

        if firebreak_positions:
            # ---------- agrupa posições conectadas ----------
            pos_set = set(firebreak_positions)
            visited = set(); lines = []
            for pos in pos_set:
                if pos in visited:
                    continue
                queue = [pos]; visited.add(pos); comp = []
                while queue:
                    x, y = queue.pop()
                    comp.append((x, y))
                    # vizinhança de Moore (8‑ligação)
                    for nx in range(x - 1, x + 2):
                        for ny in range(y - 1, y + 2):
                            if (nx, ny) in pos_set and (nx, ny) not in visited:
                                visited.add((nx, ny)); queue.append((nx, ny))
                lines.append(comp)

            # ---------- desenha cada componente ----------
            for idx, line in enumerate(lines):
                xs, ys = zip(*line)
                ax.plot(xs, ys, color="orange", linewidth=3,
                        label="Linha de Corte" if idx == 0 else "")
                ax.scatter(xs, ys, color="red", s=30,
                           label="Pontos de Corte" if idx == 0 else "")

            ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1))

        ax.set_xlabel("Posição X"); ax.set_ylabel("Posição Y")
        ax.set_title("Mapa de Linhas de Corte de Fogo", pad=20, size=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_aspect("equal", adjustable="box")

        # Prepara dados para CSV
        if firebreak_positions:
            csv_data = []
            for idx, line in enumerate(lines):
                for pos_idx, (x, y) in enumerate(line):
                    csv_data.append({
                        'Linha_ID': idx + 1,
                        'Posicao_X': x,
                        'Posicao_Y': y,
                        'Posicao_na_Linha': pos_idx + 1,
                        'Tamanho_da_Linha': len(line)
                    })
            if csv_data:
                self.data_for_csv = pd.DataFrame(csv_data)

        self.fig.tight_layout(); self.canvas.draw()
        
        # Adiciona botões de download
        self.add_download_buttons(layout)
