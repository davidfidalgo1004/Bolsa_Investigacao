import sys, random
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
        self.setWindowTitle("Simulador de Incêndio – Abordagem Integrada")

        # Configura o modelo com grid de 52x52
        self.world_width = 52
        self.world_height = 52
        self.model = EnvironmentModel(self.world_width, self.world_height)

        # Variáveis para gráfico
        self.burned_area_evol = []
        self.forested_area_evol = []
        self.timesteps = []
        self.last_detected_count = 0

        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.create_controls_row()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.main_layout.addWidget(self.log_text, 1, 0)

        self.canvas = MplCanvas(self, width=5, height=3, dpi=100)
        self.canvas.axes.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.canvas.axes.set_xlabel("Iterações")
        self.canvas.axes.set_ylabel("Quantidade")
        self.main_layout.addWidget(self.canvas, 2, 0)

        # Cena gráfica para exibir a grid
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.main_layout.addWidget(self.graphics_view, 1, 1, 2, 1)

        self.cell_size = 5
        self.cells = []
        # Inicializa os retângulos com base no tamanho da grid
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
        self.monitor_label = QLabel("Parâmetros: Temp: -- °C, Ar: --")
        self.main_layout.addWidget(self.monitor_label, 3, 0, 1, 2)

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

        self.main_layout.addWidget(controls_widget, 0, 0, 1, 2)

    def add_log(self, message: str):
        self.log_text.append(message)

    @Slot()
    def run_simulation(self):
        self.log_text.clear()
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()
        iterations = self.iter_slider.value()

        self.add_log("Preparando simulação...")
        self.add_log(f"Executando {iterations} iterações.\n")

        for i in range(iterations):
            # Com chance de iniciar fogo
            if random.random() < 0.1:
                self.model.start_fire()

            self.model.step()

            # Atualiza o monitor com os parâmetros do agente de ar
            air_status = self.model.air_agent.get_air_status()
            self.monitor_label.setText(
                f"Parâmetros: Temp: {self.model.temperature:.1f} °C, Ar: {air_status}"
            )

            # Atualiza o log (note que usamos self.model.schedule diretamente)
            burned = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "burned")
            forested = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "forested")
            self.burned_area_evol.append(burned)
            self.forested_area_evol.append(forested)
            self.timesteps.append(i)
            self.add_log(f"Iteração {i} | Queimadas: {burned}, Florestadas: {forested}")

            self.update_grid()

            QApplication.processEvents()

        self.add_log("\nSimulação finalizada!")
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
            self.canvas.axes.plot(self.timesteps, self.burned_area_evol, label='Queimadas', color='red')
            self.canvas.axes.plot(self.timesteps, self.forested_area_evol, label='Florestadas', color='green')
            self.canvas.axes.legend()
        self.canvas.draw()

    def update_grid(self):
        # Atualiza as cores dos retângulos com base no valor de pcolor dos agentes patch
        for agent in self.model.schedule:
            if hasattr(agent, "state"):
                x, y = agent.pos
                pcolor_value = agent.pcolor
                qt_color = EncontrarCor(pcolor_value)
                self.cells[y][x].setBrush(QBrush(QColor(qt_color)))

def main():
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
