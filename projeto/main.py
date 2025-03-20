import sys
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView,
    QDialog, QFormLayout, QLineEdit, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QBrush, QColor, QGuiApplication

from ambiente import EnvironmentModel
from MapColor import EncontrarCor
from GraficoAnalise import GraphWindow

class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Incêndio – Abordagem Integrada")

        screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.setGeometry(geometry)

        self.world_width = 125
        self.world_height = 108
        self.forest_density = 0.5

        # Cria o modelo com tipo de ambiente padrão "only_trees"
        self.model = EnvironmentModel(self.world_width, self.world_height,
                                      density=self.forest_density,
                                      env_type="only_trees")

        self.burned_area_evol = []
        self.forested_area_evol = []
        self.timesteps = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.create_controls_row()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.main_layout.addWidget(self.log_text, 1, 0)

        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.main_layout.addWidget(self.graphics_view, 1, 1, 2, 1)

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

        self.add_log("Interface pronta. Ajuste as configurações e clique em 'Setup'.")

        self.bottom_left_widget = QWidget()
        self.bottom_left_layout = QVBoxLayout(self.bottom_left_widget)
        self.bottom_left_layout.setSpacing(10)

        self.monitor_label = QLabel("Parâmetros: Temp: -- °C, Ar: --")
        self.bottom_left_layout.addWidget(self.monitor_label)

        self.monitors_widget = QWidget()
        monitors_layout = QFormLayout(self.monitors_widget)

        self.wind_dir_label = QLabel("Direção do Vento: --")
        self.wind_speed_label = QLabel("Velocidade do Vento: -- m/s")
        self.co_label = QLabel("CO: --")
        self.co2_label = QLabel("CO₂: --")
        self.pm25_label = QLabel("PM2.5: --")
        self.pm10_label = QLabel("PM10: --")
        self.O_label = QLabel("O: --")
        self.humidity_label = QLabel("Humidade: -- %")
        self.precip_label = QLabel("Precipitação: -- %")
        monitors_layout.addRow("Vento (Direção):", self.wind_dir_label)
        monitors_layout.addRow("Vento (Velocidade):", self.wind_speed_label)
        monitors_layout.addRow("CO:", self.co_label)
        monitors_layout.addRow("CO₂:", self.co2_label)
        monitors_layout.addRow("PM2.5:", self.pm25_label)
        monitors_layout.addRow("PM10:", self.pm10_label)
        monitors_layout.addRow("O:", self.O_label)
        monitors_layout.addRow("Humidade:", self.humidity_label)
        monitors_layout.addRow("Precipitação:", self.precip_label)

        self.bottom_left_layout.addWidget(self.monitors_widget)
        self.main_layout.addWidget(self.bottom_left_widget, 2, 0)

    def create_controls_row(self):
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(5)

        # Linha de controles superiores (rádio, setup, iniciar, etc.)
        row1 = QHBoxLayout()
        iter_label = QLabel("Iterações:")
        row1.addWidget(iter_label)

        # Slider de iterações
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(10, 500)
        self.iter_slider.setValue(100)
        row1.addWidget(self.iter_slider)

        self.env_type_group = QButtonGroup()
        self.radio_only_trees = QRadioButton("Somente Árvores")
        self.radio_road_trees = QRadioButton("Estrada + Árvores")
        self.radio_river_trees = QRadioButton("Rio + Árvores")
        self.radio_only_trees.setChecked(True)

        for btn in [self.radio_only_trees, self.radio_road_trees, self.radio_river_trees]:
            self.env_type_group.addButton(btn)
            row1.addWidget(btn)

        self.setup_button = QPushButton("Setup")
        self.setup_button.clicked.connect(self.setup_model)
        row1.addWidget(self.setup_button)

        self.run_button = QPushButton("Iniciar Simulação")
        self.run_button.clicked.connect(self.run_simulation)
        row1.addWidget(self.run_button)

        self.stop_fire_button = QPushButton("Apagar Fogo")
        self.stop_fire_button.clicked.connect(self.stop_fire)
        row1.addWidget(self.stop_fire_button)

        self.fire_status_label = QLabel("Incêndio: Inativo (Temp: -- °C)")
        row1.addWidget(self.fire_status_label)

        controls_layout.addLayout(row1)

        # Linha de sliders de clima (vento, densidade, etc.)
        row2 = QHBoxLayout()
        wind_speed_label = QLabel("Vento (m/s):")
        row2.addWidget(wind_speed_label)

        self.wind_speed_slider = QSlider(Qt.Horizontal)
        self.wind_speed_slider.setRange(1, 15)
        self.wind_speed_slider.setValue(4)
        row2.addWidget(self.wind_speed_slider)

        wind_direction_label = QLabel("Direção Vento (º):")
        row2.addWidget(wind_direction_label)

        self.wind_direction_slider = QSlider(Qt.Horizontal)
        self.wind_direction_slider.setRange(1, 15)
        self.wind_direction_slider.setValue(4)
        row2.addWidget(self.wind_direction_slider)

        density_label = QLabel("Densidade Florestal:")
        row2.addWidget(density_label)

        self.density_slider = QSlider(Qt.Horizontal)
        self.density_slider.setRange(0, 100)
        self.density_slider.setValue(int(self.forest_density * 100))
        row2.addWidget(self.density_slider)

        precip_label = QLabel("Precipitação (%):")
        row2.addWidget(precip_label)

        self.precip_slider = QSlider(Qt.Horizontal)
        self.precip_slider.setRange(0, 100)
        self.precip_slider.setValue(50)
        row2.addWidget(self.precip_slider)

        humid_label = QLabel("Humidade (%):")
        row2.addWidget(humid_label)

        self.humid_slider = QSlider(Qt.Horizontal)
        self.humid_slider.setRange(1, 100)
        self.humid_slider.setValue(15)
        row2.addWidget(self.humid_slider)

        controls_layout.addLayout(row2)
        self.main_layout.addWidget(controls_widget, 0, 0, 1, 2)

    def add_log(self, message: str):
        self.log_text.append(message)

    @Slot()
    def setup_model(self):
        """Reseta o modelo e as listas de dados, configurando o tipo de ambiente."""
        self.forest_density = self.density_slider.value() / 100.0

        if self.radio_road_trees.isChecked():
            chosen_env = "road_trees"
        elif self.radio_river_trees.isChecked():
            chosen_env = "river_trees"
        else:
            chosen_env = "only_trees"

        self.add_log(f"Recriando o modelo com densidade={self.forest_density:.2f}, "
                     f"env_type={chosen_env}, precipitação={self.precip_slider.value()}%")

        # Limpa históricos
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()

        # Configurações de vento e clima iniciais
        self.model.wind_direction = self.wind_direction_slider.value()
        self.model.wind_speed = self.wind_speed_slider.value()
        self.model.rain_level = self.precip_slider.value() / 100.0
        self.model.humidity = self.humid_slider.value()

        # Cria novo modelo
        self.model = EnvironmentModel(
            self.world_width,
            self.world_height,
            density=self.forest_density,
            env_type=chosen_env
        )
        # Atualiza com sliders
        self.model.wind_direction = self.wind_direction_slider.value()
        self.model.wind_speed = self.wind_speed_slider.value()
        self.model.humidity = self.humid_slider.value()
        self.model.rain_level = self.precip_slider.value() / 100.0

        # Limpa a interface
        for row in range(self.world_height):
            for col in range(self.world_width):
                self.cells[row][col].setBrush(QBrush(QColor("white")))

        self.update_grid()
        self.add_log("Modelo recriado e dados resetados com sucesso!")

    @Slot()
    def run_simulation(self):
        """Inicia a simulação usando o número de iterações escolhido no slider."""
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
        """Executa um passo da simulação (chamada pelo QTimer)."""
        if self.current_iteration >= self.total_iterations:
            self.timer.stop()
            self.add_log("\nSimulação finalizada!")
            self.show_graph_window()
            return

        # Pequena variação aleatória de direção/velocidade do vento
        self.model.wind_direction = (self.model.wind_direction + random.uniform(-2, 2)) % 360
        self.model.wind_speed = max(self.model.wind_speed + random.uniform(-0.3, 0.3), 0)

        # Precipitação ajustada em tempo real
        self.model.rain_level = self.precip_slider.value() / 100.0
        self.model.humidity = self.humid_slider.value()

        # Executa a simulação
        self.model.step()

        # Atualiza estado do ar
        air_agent = self.model.air_agent
        air_status = air_agent.get_air_status()
        self.monitor_label.setText(
            f"Parâmetros: Temp: {self.model.temperature:.1f} °C, Ar: {air_status}"
        )

        # Verifica se há incêndio ativo
        self.fire_status_label.setText(
            f"Incêndio: {'ATIVO' if self.model.temperature > 35 or air_status == 'Perigo' else 'Inativo'} "
            f"(Temp: {self.model.temperature:.1f} °C)"
        )
        self.wind_dir_label.setText(f"{self.model.wind_direction:.1f}°")
        self.wind_speed_label.setText(f"{self.model.wind_speed:.1f} m/s")
        self.co_label.setText(f"{air_agent.co_level:.2f} ppm")
        self.co2_label.setText(f"{air_agent.co2_level:.2f} ppm")
        self.pm25_label.setText(f"{air_agent.pm2_5_level:.2f} µg/m³")
        self.pm10_label.setText(f"{air_agent.pm10_level:.2f} µg/m³")
        self.O_label.setText(f"{air_agent.o2_level:.2f} ppm")
        self.humidity_label.setText(f"{self.model.humidity:.1f} %")
        self.precip_label.setText(f"{self.model.rain_level * 100:.1f} %")

        # Atualiza contadores
        burned = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "burned")
        forested = sum(1 for a in self.model.schedule if hasattr(a, "state") and a.state == "forested")

        self.burned_area_evol.append(burned)
        self.forested_area_evol.append(forested)
        self.timesteps.append(self.current_iteration)

        # Log a cada iteração
        self.add_log(f"Iteração {self.current_iteration} | Queimadas: {burned}, Florestadas: {forested}")

        # Inicia incêndio aleatório (10% de chance)
        if random.random() < 0.1:
            self.model.start_fire()

        self.update_grid()
        self.current_iteration += 1

    @Slot()
    def stop_fire(self):
        """Chamada para apagar o fogo manualmente."""
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")

    def update_grid(self):
        """Atualiza a cor de cada célula na interface."""
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor"):
                x, y = agent.pos
                color_value = agent.pcolor
                qt_color = EncontrarCor(color_value)
                self.cells[y][x].setBrush(QBrush(QColor(qt_color)))

    def show_graph_window(self):
        """Exibe janelas de gráficos ao final da simulação."""
        # Coletar alturas e altitudes das árvores
        tree_heights = [
            (agent.pos[0], agent.pos[1], agent.tree_height)
            for agent in self.model.schedule
            if hasattr(agent, "tree_height")
        ]
        tree_altitudes = [
            (agent.pos[0], agent.pos[1], agent.altitude)
            for agent in self.model.schedule
            if hasattr(agent, "altitude")
        ]

        # Gráfico de evolução
        self.burned_forest_dialog = GraphWindow(
            burned_data=self.burned_area_evol,
            forested_data=self.forested_area_evol,
            timesteps=self.timesteps,
            parent=self
        )
        self.burned_forest_dialog.setWindowTitle("Evolução de Árvores Queimadas vs Florestadas")
        self.burned_forest_dialog.show()

        # Mapa de altitude
        self.altitude_dialog = GraphWindow(
            tree_altitudes=tree_altitudes,
            parent=self
        )
        self.altitude_dialog.setWindowTitle("Mapa de Altitude das Árvores")
        self.altitude_dialog.show()

        # Mapa de altura
        self.height_dialog = GraphWindow(
            tree_heights=tree_heights,
            parent=self
        )
        self.height_dialog.setWindowTitle("Mapa de Altura das Árvores")
        self.height_dialog.show()

    def add_log(self, message: str):
        self.log_text.append(message)

def main():
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
