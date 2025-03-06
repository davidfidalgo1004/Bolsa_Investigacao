import sys
import random
import pynetlogo
import matplotlib
matplotlib.use('Qt5Agg')
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QBrush, QColor
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from ambiente import EnvironmentModel
from MapColor import EncontrarCor

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Incêndio")

        # ------------------ INICIALIZAÇÃO DO NETLOGO ------------------
        self.netlogo = pynetlogo.NetLogoLink(
            gui=False,
            netlogo_home=r"C:\Program Files\NetLogo 6.4.0"
        )
        self.netlogo.load_model(r"C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo")
        
        # Obter os limites do mundo do NetLogo
        self.min_pxcor = int(self.netlogo.report("min-pxcor"))
        self.min_pycor = int(self.netlogo.report("min-pycor"))
        self.max_pxcor = int(self.netlogo.report("max-pxcor"))
        self.max_pycor = int(self.netlogo.report("max-pycor"))

        self.tamhorizontal = self.max_pxcor - self.min_pxcor + 1
        self.tamvertical = self.max_pycor - self.min_pycor + 1
        # Configurando um mundo de 52x52 patches
        self.world_width = self.tamhorizontal
        self.world_height = self.tamvertical
        self.model = EnvironmentModel(5, self.world_width, self.world_height, netlogo=self.netlogo)
        self.netlogo.command("setup")

        # ------------------ VARIÁVEIS PARA O GRÁFICO ------------------
        self.burned_area_evol = []
        self.forested_area_evol = []
        self.timesteps = []
        self.last_detected_count = 0

        # ------------------ LAYOUT PRINCIPAL ------------------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Aqui usamos um grid com 2 colunas
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 1) Linha de controles (ocupando duas colunas)
        self.create_controls_row()

        # 2) Log de saída na coluna esquerda (linha 1)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.main_layout.addWidget(self.log_text, 1, 0)

        # 3) Gráfico (Matplotlib) na coluna esquerda (linha 2)
        self.canvas = MplCanvas(self, width=5, height=3, dpi=100)
        self.canvas.axes.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.canvas.axes.set_xlabel("Iterações")
        self.canvas.axes.set_ylabel("Quantidade")
        self.main_layout.addWidget(self.canvas, 2, 0)

        # 4) Mapa do NetLogo com QGraphicsScene – agora na coluna direita, ocupando as linhas 1 e 2
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.main_layout.addWidget(self.graphics_view, 1, 1, 2, 1)

        # Cria os itens da grade (grid) como retângulos (QGraphicsRectItem)
        self.cell_size = 5  # Tamanho de cada célula; ajuste conforme necessário
        self.cells = []
        self.netlogo.command("setup")
        for row in range(self.world_height):
            row_items = []
            for col in range(self.world_width):
                rect = self.graphics_scene.addRect(
                    col * self.cell_size, row * self.cell_size,
                    self.cell_size, self.cell_size
                )
                rect.setBrush(QBrush(QColor("white")))
                row_items.append(rect)
            self.cells.append(row_items)

        self.add_log("Interface pronta. Ajuste as iterações e clique em 'Iniciar Simulação'.")

    def create_controls_row(self):
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setSpacing(5)

        iter_label = QLabel("Iterações:")
        controls_layout.addWidget(iter_label)

        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(10, 500)
        self.iter_slider.setValue(200)
        controls_layout.addWidget(self.iter_slider)

        self.run_button = QPushButton("Iniciar Simulação")
        self.run_button.clicked.connect(self.run_simulation)
        controls_layout.addWidget(self.run_button)

        self.stop_fire_button = QPushButton("Apagar Fogo")
        self.stop_fire_button.clicked.connect(self.stop_fire)
        controls_layout.addWidget(self.stop_fire_button)

        self.fire_status_label = QLabel("Incêndio: Inativo (Temp: -- °C)")
        controls_layout.addWidget(self.fire_status_label)

        # A linha de controles ocupa as duas colunas (linha 0, col 0, com span de 2)
        self.main_layout.addWidget(controls_widget, 0, 0, 1, 2)

    def add_log(self, message: str):
        self.log_text.append(message)

    @Slot()
    def run_simulation(self):
        # Limpa os dados e o log
        self.log_text.clear()
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()

        self.model.fires_created = 0
        self.model.fires_detected = 0
        self.model.detect_countdown = 0
        self.last_detected_count = 0

        iterations = self.iter_slider.value()

        self.add_log("Preparando simulação...")
        self.add_log(f"Executando {iterations} iterações.\n")

        # Loop principal da simulação
        for i in range(iterations):
            # Cria fogo com chance de 10%
            if random.random() < 0.1:
                self.model.start_fire()

            # Avança um passo no modelo
            self.model.step()

            # Verifica sensores de incêndio
            if self.model.check_fire_sensors():
                self.add_log("[ALERTA] 🚨 Múltiplos sensores ativados! POSSÍVEL INCÊNDIO DETECTADO!")
                self.fire_status_label.setText(f"🔥 ALERTA DE INCÊNDIO! (Temp: {self.model.temperature:.1f} °C)")
            else:
                if self.model.is_fire_active():
                    self.fire_status_label.setText(f"Incêndio: ATIVO (Temp: {self.model.temperature:.1f} °C)")
                else:
                    self.fire_status_label.setText(f"Incêndio: Inativo (Temp: {self.model.temperature:.1f} °C)")

            if self.model.fires_detected > self.last_detected_count:
                self.last_detected_count = self.model.fires_detected
                self.add_log(f"[TICK {i}] Incêndio DETECTADO! Temperatura = {self.model.temperature:.1f} °C")

            # Coleta dados do NetLogo
            burned_trees = self.netlogo.report("burned-trees")
            forested_trees = self.netlogo.report("count patches with [pcolor = green]")

            self.burned_area_evol.append(burned_trees)
            self.forested_area_evol.append(forested_trees)
            self.timesteps.append(i)

            self.add_log(f"Iteração {i} | Queimadas: {burned_trees}, Florestadas: {forested_trees}")

            # Atualiza o mapa usando uma única chamada para obter a matriz de cores
            self.update_netlogo_grid(i)

            # Processa eventos para atualizar a interface
            QApplication.processEvents()

        self.add_log("\nSimulação finalizada!")
        self.add_log(f"Número de incêndios criados: {self.model.fires_created}")
        self.add_log(f"Número de incêndios detectados: {self.model.fires_detected}")
        self.update_plot()

    @Slot()
    def stop_fire(self):
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")

    def update_plot(self):
        self.canvas.axes.clear()
        self.canvas.axes.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.canvas.axes.set_xlabel("Iterações")
        self.canvas.axes.set_ylabel("Quantidade")
        self.canvas.axes.grid(True)

        if self.timesteps:
            self.canvas.axes.plot(self.timesteps, self.burned_area_evol, label='Árvores Queimadas', color='red')
            self.canvas.axes.plot(self.timesteps, self.forested_area_evol, label='Árvores Florestadas', color='green')
            self.canvas.axes.legend()

        self.canvas.draw()

    def update_netlogo_grid(self, i):
        """
        Atualiza a cor de cada célula do QGraphicsScene utilizando uma única chamada
        ao NetLogo para obter uma matriz com os valores pcolor de todos os patches.
        """
        cmd = (
            f"map [[y] -> "
            f"  map [[x] -> [pcolor] of patch (x + {self.min_pxcor}) (y + {self.min_pycor})] "
            f"       n-values {self.world_width} [[x] -> x] "
            f"] n-values {self.world_height} [[y] -> y]"
        )
        patch_colors = self.netlogo.report(cmd)
        if (i % 5) ==0:
            # Atualiza cada célula com a cor correspondente baseada nos intervalos
            for row in range(self.world_height):
                for col in range(self.world_width):
                    pcolor_value = patch_colors[row][col]
                    try:
                        pcolor_value = round(pcolor_value, 1)
                    except Exception:
                        pass
                    qt_color = EncontrarCor(pcolor_value)
                    self.cells[row][col].setBrush(QBrush(QColor(qt_color)))

def main():
    aplicacao = QApplication(sys.argv)
    janela = SimulationApp()
    janela.show()
    sys.exit(aplicacao.exec())

if __name__ == "__main__":
    main()
