import sys
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView,
    QDialog, QFormLayout, QLineEdit, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QBrush, QColor, QGuiApplication

# Matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Importa o modelo e funções auxiliares
from ambiente import EnvironmentModel
from MapColor import EncontrarCor
from GraficoAnalise import GraphWindow
from AlertIncendio import SensorAlertDialog

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

        # Cria as células da grid
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

        # Rótulo e slider de iterações
        iter_label = QLabel("Iterações:")
        controls_layout.addWidget(iter_label)
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(10, 500)
        self.iter_slider.setValue(100)
        controls_layout.addWidget(self.iter_slider)

        # Rótulo e slider de densidade florestal
        density_label = QLabel("Densidade Florestal:")
        controls_layout.addWidget(density_label)
        self.density_slider = QSlider(Qt.Horizontal)
        self.density_slider.setRange(0, 100)
        self.density_slider.setValue(int(self.forest_density * 100))
        controls_layout.addWidget(self.density_slider)

        # Rótulo e slider de percentual de eucaliptos
        eucalyptus_label = QLabel("Percentual de Eucaliptos:")
        controls_layout.addWidget(eucalyptus_label)
        self.eucalyptus_slider = QSlider(Qt.Horizontal)
        self.eucalyptus_slider.setRange(0, 100)
        self.eucalyptus_slider.setValue(50)  # Exemplo: inicia em 50%
        controls_layout.addWidget(self.eucalyptus_slider)

        # Radio buttons para o tipo de ambiente
        self.radio_road = QRadioButton("Estrada + Árvores")
        self.radio_river = QRadioButton("Rio + Árvores")
        self.radio_only = QRadioButton("Só Árvores")
        self.radio_only.setChecked(True)  # Define este como padrão

        # Agrupa os radio buttons
        self.env_group = QButtonGroup(self)
        self.env_group.addButton(self.radio_road)
        self.env_group.addButton(self.radio_river)
        self.env_group.addButton(self.radio_only)

        controls_layout.addWidget(self.radio_road)
        controls_layout.addWidget(self.radio_river)
        controls_layout.addWidget(self.radio_only)

        # Botão de Setup
        self.setup_button = QPushButton("Setup")
        self.setup_button.clicked.connect(self.setup_model)
        controls_layout.addWidget(self.setup_button)

        # Botão de Iniciar Simulação
        self.run_button = QPushButton("Iniciar Simulação")
        self.run_button.clicked.connect(self.run_simulation)
        controls_layout.addWidget(self.run_button)

        # Botão de Apagar Fogo
        self.stop_fire_button = QPushButton("Apagar Fogo")
        self.stop_fire_button.clicked.connect(self.stop_fire)
        controls_layout.addWidget(self.stop_fire_button)

        # Label para mostrar status do incêndio
        self.fire_status_label = QLabel("Incêndio: Inativo (Temp: -- °C)")
        controls_layout.addWidget(self.fire_status_label)

        # Botão para destacar células dentro de um raio (opcional, para testes)
        self.highlight_button = QPushButton("Destacar Células no Raio")
        self.highlight_button.clicked.connect(self.highlight_cells_in_radius)
        controls_layout.addWidget(self.highlight_button)

        self.main_layout.addWidget(controls_widget, 0, 0, 1, 2)


    @Slot()
    def setup_model(self):
        self.forest_density = self.density_slider.value() / 100.0
        eucalyptus_percentage = self.eucalyptus_slider.value() / 100.0

        if self.radio_road.isChecked():
            env_type = "road_trees"
        elif self.radio_river.isChecked():
            env_type = "river_trees"
        else:
            env_type = "only_trees"

        self.add_log(f"Recriando o modelo com modo: {env_type}")

        self.model = EnvironmentModel(
            self.world_width,
            self.world_height,
            density=self.forest_density,
            eucalyptus_percentage=eucalyptus_percentage,
            env_type=env_type
        )
        self.model.wind_direction = random.randint(0, 359)
        self.model.wind_speed = random.randint(1, 15)

        for row in range(self.world_height):
            for col in range(self.world_width):
                self.cells[row][col].setBrush(QBrush(QColor("white")))

        self.update_grid()
        self.add_log("Modelo recriado com sucesso!")


    def add_log(self, message: str):
        self.log_text.append(message)


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

        if random.random() < 0.1:
            self.model.start_fire()

        self.model.step()

        air_agent = self.model.air_agent
        air_status = air_agent.get_air_status()
        self.monitor_label.setText(
            f"Parâmetros: Temp: {self.model.temperature:.1f} °C, Ar: {air_status}"
        )
        self.fire_status_label.setText(
            f"Incêndio: {'ATIVO' if self.model.temperature > 25 else 'Inativo'} (Temp: {self.model.temperature:.1f} °C)"
        )

        burned = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "burned")
        forested = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "forested")
        self.burned_area_evol.append(burned)
        self.forested_area_evol.append(forested)
        self.timesteps.append(self.current_iteration)
        self.model.wind_direction = self.model.wind_direction + random.uniform(-0.2, 0.2)
        self.model.wind_speed = self.model.wind_speed + random.uniform(-0.2, 0.2)
        self.add_log(f"Iteração {self.current_iteration} | Queimadas: {burned}, Florestadas: {forested}")
        self.update_grid()
        self.current_iteration += 1

        if air_status == "Perigo":
            if not hasattr(self, "sensor_alert_dialog") or self.sensor_alert_dialog is None:
                self.sensor_alert_dialog = SensorAlertDialog(self)
                self.sensor_alert_dialog.show()
        else:
            if hasattr(self, "sensor_alert_dialog") and self.sensor_alert_dialog is not None:
                self.sensor_alert_dialog.close()
                self.sensor_alert_dialog = None
        self.wind_dir_label.setText(f"Direção: {self.model.wind_direction}°")
        self.wind_speed_label.setText(f"Velocidade: {self.model.wind_speed} m/s")
        self.co_label.setText(f"CO: {self.model.air_agent.co_level:.1f}")
        self.co2_label.setText(f"CO₂: {self.model.air_agent.co2_level:.1f}")
        self.pm25_label.setText(f"PM2.5: {self.model.air_agent.pm2_5_level:.1f}")
        self.pm10_label.setText(f"PM10: {self.model.air_agent.pm10_level:.1f}")
        self.O_label.setText(f"O₂: {self.model.air_agent.o2_level:.1f}")


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
