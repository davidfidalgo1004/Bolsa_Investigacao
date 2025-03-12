import sys
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView,
    QDialog, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QBrush, QColor, QGuiApplication

# Matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Seu modelo e função de cores
from ambiente import EnvironmentModel
from MapColor import EncontrarCor
from GraficoAnalise import GraphWindow


class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Incêndio – Abordagem Integrada")

        # Ocupa a tela disponível
        screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.setGeometry(geometry)

        # Ajuste o tamanho da grid aqui:
        self.world_width = 125
        self.world_height = 108
        self.forest_density = 0.5

        self.model = EnvironmentModel(self.world_width, self.world_height, density=self.forest_density)

        # Dados para o gráfico
        self.burned_area_evol = []
        self.forested_area_evol = []
        self.timesteps = []

        # Layout principal (grid)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # -------------------------
        # LINHA 0: Controles
        # -------------------------
        self.create_controls_row()

        # -------------------------
        # LINHA 1 (col 0): Log
        # -------------------------
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.main_layout.addWidget(self.log_text, 1, 0)

        # -------------------------
        # LINHA 1 e 2 (col 1): Grid
        # -------------------------
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.main_layout.addWidget(self.graphics_view, 1, 1, 2, 1)

        # Cria as células
        self.cell_size = 5
        self.cells = []
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

        # Mensagem inicial no log
        self.add_log("Interface pronta. Ajuste as configurações e clique em 'Iniciar Simulação'.")

        # -------------------------
        # PARÂMETROS GERAIS (ex.: temperatura e qualidade do ar)
        # -------------------------
        self.bottom_left_widget = QWidget()
        self.bottom_left_layout = QVBoxLayout(self.bottom_left_widget)
        self.bottom_left_layout.setSpacing(10)

        self.monitor_label = QLabel("Parâmetros: Temp: -- °C, Ar: --")
        self.bottom_left_layout.addWidget(self.monitor_label)

        self.monitors_widget = QWidget()
        monitors_layout = QFormLayout(self.monitors_widget)

        self.wind_dir_label = QLabel("Direção do Vento: --")
        self.wind_speed_label = QLabel("Velocidade do Vento: -- m/s")
        self.co_label = QLabel("Monóxido de Carbono (CO): --")
        self.co2_label = QLabel("Dióxido de Carbono (CO₂): --")
        self.pm25_label = QLabel("Partículas Finas (PM2.5): --")
        self.pm10_label = QLabel("Partículas Finas (PM10): --")
        self.O_label = QLabel("Oxigénio (O): --")
        monitors_layout.addRow("Vento (Direção):", self.wind_dir_label)
        monitors_layout.addRow("Vento (Velocidade):", self.wind_speed_label)
        monitors_layout.addRow("CO:", self.co_label)
        monitors_layout.addRow("CO₂:", self.co2_label)
        monitors_layout.addRow("PM2.5:", self.pm25_label)
        monitors_layout.addRow("PM10:", self.pm10_label)
        monitors_layout.addRow("O:", self.O_label)

        self.bottom_left_layout.addWidget(self.monitors_widget)
        self.main_layout.addWidget(self.bottom_left_widget, 2, 0)

    def create_controls_row(self):
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setSpacing(5)

        iter_label = QLabel("Iterações:")
        controls_layout.addWidget(iter_label)
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(10, 500)
        self.iter_slider.setValue(100)
        controls_layout.addWidget(self.iter_slider)

        density_label = QLabel("Densidade Florestal:")
        controls_layout.addWidget(density_label)
        self.density_slider = QSlider(Qt.Horizontal)
        self.density_slider.setRange(0, 100)
        self.density_slider.setValue(int(self.forest_density * 100))
        controls_layout.addWidget(self.density_slider)

        self.setup_button = QPushButton("Setup")
        self.setup_button.clicked.connect(self.setup_model)
        controls_layout.addWidget(self.setup_button)

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
    def setup_model(self):
        self.forest_density = self.density_slider.value() / 100.0
        self.add_log(f"Recriando o modelo com densidade florestal = {self.forest_density:.2f}")

        # Reseta os dados da evolução da simulação
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()
        wind_direction = random.randint(0, 360)
        wind_speed = random.randint(1, 15)
        self.model.wind_direction = wind_direction
        self.model.wind_speed = wind_speed

        # Recria o modelo (todos os parâmetros internos serão reinicializados)
        self.model = EnvironmentModel(self.world_width, self.world_height, density=self.forest_density)

        # Reseta as cores da grid e atualiza conforme o estado inicial dos patches
        for row in range(self.world_height):
            for col in range(self.world_width):
                self.cells[row][col].setBrush(QBrush(QColor("white")))
        self.update_grid()

        self.add_log("Modelo recriado e dados resetados com sucesso!")

    @Slot()
    def run_simulation(self):
        self.log_text.clear()
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()

        self.total_iterations = self.iter_slider.value()
        self.current_iteration = 0

        self.add_log("Iniciando simulação...")
        self.add_log(f"Executando {self.total_iterations} iterações.\n")

        # Cria um timer para executar cada iteração com um intervalo definido (ex.: 100 ms)
        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.simulation_step)
        self.timer.start()

    @Slot()
    def simulation_step(self):
        if self.current_iteration >= self.total_iterations:
            self.timer.stop()
            self.add_log("\nSimulação finalizada!")
            self.show_graph_window()
            return

        # Atualiza valores ambientais (ex.: vento) a cada iteração
        self.model.wind_direction = (self.model.wind_direction + random.uniform(-2, 2)) % 360
        self.model.wind_speed = max(self.model.wind_speed + random.uniform(-0.3, 0.3), 0)

        # Incendeia aleatoriamente com probabilidade de 10%
        if random.random() < 0.1:
            self.model.start_fire()

        # Executa um passo da simulação
        self.model.step()

        # Atualiza monitores e log
        air_agent = self.model.air_agent
        air_status = air_agent.get_air_status()
        self.monitor_label.setText(
            f"Parâmetros: Temp: {self.model.temperature:.1f} °C, Ar: {air_status}"
        )
        self.fire_status_label.setText(
            f"Incêndio: {'ATIVO' if self.model.temperature > 25 else 'Inativo'} (Temp: {self.model.temperature:.1f} °C)"
        )
        # Uso correto dos parâmetros de vento
        self.wind_dir_label.setText(f"{self.model.wind_direction:.1f}°")
        self.wind_speed_label.setText(f"{self.model.wind_speed:.1f} m/s")
        self.co_label.setText(f"{air_agent.co_level:.2f} ppm")
        self.co2_label.setText(f"{air_agent.co2_level:.2f} ppm")
        self.pm25_label.setText(f"{air_agent.pm2_5_level:.2f} µg/m³")
        self.pm10_label.setText(f"{air_agent.pm10_level:.2f} µg/m³")
        self.O_label.setText(f"{air_agent.o2_level:.2f} ppm")

        burned = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "burned")
        forested = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "forested")

        self.burned_area_evol.append(burned)
        self.forested_area_evol.append(forested)
        self.timesteps.append(self.current_iteration)

        self.add_log(f"Iteração {self.current_iteration} | Queimadas: {burned}, Florestadas: {forested}")

        self.update_grid()
        self.current_iteration += 1

    @Slot()
    def stop_fire(self):
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")

    def update_grid(self):
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor"):
                x, y = agent.pos
                color_value = agent.pcolor
                qt_color = EncontrarCor(color_value)
                self.cells[y][x].setBrush(QBrush(QColor(qt_color)))

    def show_graph_window(self):
        dialog = GraphWindow(
            burned_data=self.burned_area_evol,
            forested_data=self.forested_area_evol,
            timesteps=self.timesteps,
            parent=self
        )
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
