import sys
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView,
    QFormLayout, QRadioButton, QButtonGroup, QToolTip)
from PySide6.QtCore import Qt, Slot, QTimer, QEvent
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QPixmap, QCursor
from bossula import CompassWidget

from ambiente import EnvironmentModel
from firefighter_agent import FirefighterAgent
from MapColor import EncontrarCor
from GraficoAnalise import GraphWindow, FragulhaArrowsWindow, FireStartWindow, FirebreakMapWindow, plot_response_heatmap, plot_trajectories

class HoverValueSlider(QSlider):
    """
    QSlider que exibe, em tempo-real, o valor na posição do cursor.
    """
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)       # recebe eventos de movimento mesmo sem botão
        self.installEventFilter(self)     # intercepta eventos para mostrar tooltip

    # ---------- evento genérico ----------
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.Enter):
            # actualiza o texto da tooltip e mostra onde está o cursor
            QToolTip.showText(QCursor.pos(), str(self.value()), self)
        return super().eventFilter(obj, event)

    # opcional: garante que a tooltip desaparece ao sair
    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)


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

        # Cria o modelo inicial
        self.model = EnvironmentModel(
            self.world_width,
            self.world_height,
            density=self.forest_density,
            env_type="only_trees"
        )

        # Dados para gráficos de incêndio
        self.burned_area_evol = []
        self.forested_area_evol = []
        self.timesteps = []
        self.siren_items = []
        # Dados para o gráfico do ar
        self.air_co_evol = []
        self.air_co2_evol = []
        self.air_pm25_evol = []
        self.air_pm10_evol = []
        self.air_o2_evol = []

        # Dados para o gráfico de clima
        self.temp_evol = []
        self.humid_evol = []
        self.precip_evol = []

        self.current_iteration = 0
        self.total_iterations = 0

        self.fire_start_positions = []

        self.has_setup = False

        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.create_controls_row()

        # Área de log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.main_layout.addWidget(self.log_text, 1, 0)

        # Área para exibir a simulação (grid)
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.main_layout.addWidget(self.graphics_view, 1, 1, 2, 1)

        self.cell_size = 5

        # Carrega ícone da sirene (80% da célula) ou fallback azul-escuro
        try:
            self.siren_icon = QPixmap("siren.jpg").scaled(
                int(self.cell_size * 0.8),
                int(self.cell_size * 0.8),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        except Exception:
            self.siren_icon = QPixmap(self.cell_size, self.cell_size)
            self.siren_icon.fill(QColor("#00008B"))
        self.siren_items = []

        try:
            self.tech_icon = QPixmap("bombeirotec.jpg").scaled(
                int(self.cell_size * 0.8),
                int(self.cell_size * 0.8),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        except Exception:
            # fallback para caso não encontre o arquivo
            self.siren_icon = QPixmap(self.cell_size, self.cell_size)
            self.siren_icon.fill(QColor("#00008B"))
         # Painel inferior (cria o widget e o layout antes de usar)
        self.bottom_left_widget = QWidget()
        self.bottom_left_layout = QVBoxLayout(self.bottom_left_widget)
        self.bottom_left_layout.setSpacing(10)
        # status dos bombeiros
        self.ff_status_label = QLabel("Bombeiros – Ataque: 0, Movendo: 0, Ociosos: 4")
        self.bottom_left_layout.addWidget(self.ff_status_label)
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
        self.temp_display_label = QLabel("-- °C")

        monitors_layout.addRow("Vento (Direção):", self.wind_dir_label)
        monitors_layout.addRow("Vento (Velocidade):", self.wind_speed_label)
        monitors_layout.addRow("CO:", self.co_label)
        monitors_layout.addRow("CO₂:", self.co2_label)
        monitors_layout.addRow("PM2.5:", self.pm25_label)
        monitors_layout.addRow("PM10:", self.pm10_label)
        monitors_layout.addRow("O:", self.O_label)
        monitors_layout.addRow("Humidade:", self.humidity_label)
        monitors_layout.addRow("Precipitação:", self.precip_label)
        monitors_layout.addRow("Temperatura:", self.temp_display_label)

        self.bottom_left_layout.addWidget(self.monitors_widget)

        self.compass = CompassWidget()
        self.compass.setMinimumSize(150, 150)

        bottom_h_layout = QHBoxLayout()
        bottom_h_layout.addWidget(self.bottom_left_widget)
        bottom_h_layout.addWidget(self.compass)
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_h_layout)
        self.main_layout.addWidget(bottom_container, 2, 0)


    def create_controls_row(self):
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(5)

        # Linha 1
        row1 = QHBoxLayout()
        iter_label = QLabel("Iterações:")
        row1.addWidget(iter_label)

        self.iter_slider = HoverValueSlider(Qt.Horizontal)
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

        # Linha 2: Sliders climáticos
        row2 = QHBoxLayout()
        wind_speed_label = QLabel("Vento (m/s):")
        row2.addWidget(wind_speed_label)

        self.wind_speed_slider = HoverValueSlider(Qt.Horizontal)
        self.wind_speed_slider.setRange(1, 15)
        self.wind_speed_slider.setValue(4)
        row2.addWidget(self.wind_speed_slider)

        wind_direction_label = QLabel("Direção Vento (º):")
        row2.addWidget(wind_direction_label)

        self.wind_direction_slider = HoverValueSlider(Qt.Horizontal)
        self.wind_direction_slider.setRange(0, 359)
        self.wind_direction_slider.setValue(4)
        row2.addWidget(self.wind_direction_slider)

        density_label = QLabel("Densidade Florestal:")
        row2.addWidget(density_label)

        self.density_slider = HoverValueSlider(Qt.Horizontal)
        self.density_slider.setRange(0, 100)
        self.density_slider.setValue(int(self.forest_density * 100))
        row2.addWidget(self.density_slider)

        precip_label = QLabel("Precipitação (%):")
        row2.addWidget(precip_label)

        self.precip_slider = HoverValueSlider(Qt.Horizontal)
        self.precip_slider.setRange(0, 100)
        self.precip_slider.setValue(50)
        row2.addWidget(self.precip_slider)

        humid_label = QLabel("Humidade (%):")
        row2.addWidget(humid_label)

        self.humid_slider = HoverValueSlider(Qt.Horizontal)
        self.humid_slider.setRange(1, 100)
        self.humid_slider.setValue(15)
        row2.addWidget(self.humid_slider)

        temp_label = QLabel("Temperatura (°C):")
        row2.addWidget(temp_label)

        self.temp_slider = HoverValueSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 30)
        self.temp_slider.setValue(25)
        row2.addWidget(self.temp_slider)

        controls_layout.addLayout(row2)
        self.main_layout.addWidget(controls_widget, 0, 0, 1, 2)

        row3 = QHBoxLayout()
        # Slider para número total de bombeiros
        ff_count_label = QLabel("Número de Bombeiros:")
        row3.addWidget(ff_count_label)
        self.ff_count_slider = HoverValueSlider(Qt.Horizontal)
        self.ff_count_slider.setRange(4, 120)
        self.ff_count_slider.setValue(4)  # valor inicial padrão
        row3.addWidget(self.ff_count_slider)
        # Slider para proporção de jatos de água
        ff_ratio_label = QLabel("Tecnicistas | Apagadores (%)")
        row3.addWidget(ff_ratio_label)
        self.ff_ratio_slider = HoverValueSlider(Qt.Horizontal)
        self.ff_ratio_slider.setRange(0, 100)
        self.ff_ratio_slider.setValue(50)  # valor inicial 50%
        row3.addWidget(self.ff_ratio_slider)

        # Adiciona a nova linha de controles ao layout principal de controles
        controls_layout.addLayout(row3)


    def add_log(self, message: str):
        self.log_text.append(message)


    @Slot()
    def setup_model(self):
        self.fireigni=True
        # Se houver dados da simulação anterior, mostra gráficos antes de reiniciar
        if (self.burned_area_evol or self.forested_area_evol or self.timesteps or
            self.model.fragulha_history or self.fire_start_positions or
            self.air_co_evol or self.temp_evol):
            self.add_log("Exibindo gráficos da simulação anterior...")
            self.show_graph_window()
            plot_response_heatmap(self.model, self.world_width, self.world_height)
            plot_trajectories(self.model)

        self.add_log("Recriando o modelo com novas configurações...")

        self.forest_density = self.density_slider.value() / 100.0
        if self.radio_road_trees.isChecked():
            chosen_env = "road_trees"
        elif self.radio_river_trees.isChecked():
            chosen_env = "river_trees"
        else:
            chosen_env = "only_trees"

        # Limpa dados
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()
        self.fire_start_positions.clear()
        self.air_co_evol.clear()
        self.air_co2_evol.clear()
        self.air_pm25_evol.clear()
        self.air_pm10_evol.clear()
        self.air_o2_evol.clear()
        self.temp_evol.clear()
        self.humid_evol.clear()
        self.precip_evol.clear()

        # Reinicia modelo
        self.model = EnvironmentModel(
            self.world_width,
            self.world_height,
            density=self.forest_density,
            env_type=chosen_env,
            num_firefighters=self.ff_count_slider.value(),
            water_ratio=self.ff_ratio_slider.value() / 100.0
        )

        self.model.wind_direction = self.wind_direction_slider.value()
        self.model.wind_speed = self.wind_speed_slider.value()
        self.model.rain_level = self.precip_slider.value() / 100.0
        basehumidity = self.humid_slider.value()
        self.model.temperature = self.temp_slider.value()

        if chosen_env == "river_trees":
             self.model.humidity = basehumidity * 1.5
        else:
            self.model.humidity = basehumidity
        for row in range(self.world_height):
            for col in range(self.world_width):
                self.cells[row][col].setBrush(QBrush(QColor("white")))

        self.update_grid()

        air_agent = self.model.air_agent
        air_status = air_agent.get_air_status()
        self.monitor_label.setText(
            f"Parâmetros: Temp: {self.model.temperature:.1f} °C, Ar: {air_status}"
        )
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
        self.temp_display_label.setText(f"{self.model.temperature:.1f} °C")

        self.has_setup = True
        self.run_button.setText("Iniciar Simulação")

        # Iteração
        self.current_iteration = 0
        self.total_iterations = 0


    @Slot()
    def run_simulation(self):
        self.setup_button.setEnabled(False)
        self.log_text.clear()
        self.add_log("Iniciando/continuando simulação...")
        self.run_button.setText("Continuar Simulação")

        if self.current_iteration > 0:
            self.total_iterations += self.iter_slider.value()
        else:
            self.total_iterations = self.iter_slider.value()

        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.simulation_step)
        self.timer.start()


    @Slot()
    def simulation_step(self):
        if self.current_iteration >= self.total_iterations:
            self.timer.stop()
            self.add_log("\nSimulação finalizada!")
            self.setup_button.setEnabled(True)
            return
        if self.current_iteration % 20 == 0:
            if random.random() < self.model.rain_level:
                self.model.itsrain_ = True
            else:
                self.model.itsrain_ = False
        # Atualiza parâmetros a cada iteração
        self.model.current_iteration = self.current_iteration
        self.model.wind_direction = (self.model.wind_direction + random.uniform(-1, 1)) % 360
        self.model.wind_speed = max(self.model.wind_speed + random.uniform(-0.3, 0.3), 0)
        self.model.rain_level = self.precip_slider.value() / 100.0
        self.model.humidity = self.humid_slider.value()
        self.model.temperature = self.temp_slider.value()

        self.model.step()

        air_agent = self.model.air_agent
        air_status = air_agent.get_air_status()
        self.monitor_label.setText(
            f"Parâmetros: Temp: {self.model.temperature:.1f} °C, Ar: {air_status}"
        )
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
        self.temp_display_label.setText(f"{self.model.temperature:.1f} °C")

        self.compass.setAngle(self.model.wind_direction)

        # Dados de incêndio
        burned = sum(1 for a in self.model.schedule if getattr(a, "state", None) == "burned")
        forested = sum(1 for a in self.model.schedule if getattr(a, "state", None) == "forested")
        self.burned_area_evol.append(burned)
        self.forested_area_evol.append(forested)
        self.timesteps.append(self.current_iteration)

        # Dados de ar
        self.air_co_evol.append(air_agent.co_level)
        self.air_co2_evol.append(air_agent.co2_level)
        self.air_pm25_evol.append(air_agent.pm2_5_level)
        self.air_pm10_evol.append(air_agent.pm10_level)
        self.air_o2_evol.append(air_agent.o2_level)

        # Dados de clima
        self.temp_evol.append(self.model.temperature)
        self.humid_evol.append(self.model.humidity)
        self.precip_evol.append(self.model.rain_level)

        self.add_log(
            f"Iteração {self.current_iteration} | Queimadas: {burned}, Florestadas: {forested}"
        )
        # Chance de iniciar incêndio aleatório
        if (self.model.temperature < 30 or air_status != "Perigo"):
            if random.random() < 0.05 and self.fireigni==True:
                self.fireigni=False
                forested_patches = [
                    a for a in self.model.schedule
                    if getattr(a, "state", None) == "forested"
                ]
                if forested_patches:
                    chosen = random.choice(forested_patches)
                    chosen.state = "burning"
                    chosen.pcolor = 15
                    self.fire_start_positions.append(chosen.pos)
        
        # Contagem de estados dos bombeiros
        firefighters = [a for a in self.model.schedule if isinstance(a, FirefighterAgent)]
        ativos = sum(1 for f in firefighters if f.mode != "evacuated")
        em_ataque = sum(1 for f in firefighters if f.mode == "direct_attack")
        evacuados = sum(1 for f in firefighters if f.mode == "evacuated")
        # Atualiza rótulo de status dos bombeiros
        self.ff_status_label.setText(
            f"Bombeiros – Ativos: {ativos}, Em ataque: {em_ataque}, Evacuados: {evacuados}"
        )

        self.update_grid()
        self.current_iteration += 1


    @Slot()
    def stop_fire(self):
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")


    
    def update_grid(self):
        # Remove ícones antigos
        for item in getattr(self, "siren_items", []):
            self.graphics_scene.removeItem(item)
        self.siren_items = []

        icon_offset = int(self.cell_size * 0.1)  # margem para canto
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor"):
                x, y = agent.pos
                # Pinta a célula conforme pcolor
                qt_color = QColor(EncontrarCor(agent.pcolor))
                # Se for firebreak, pode forçar uma cor específica
                if getattr(agent, "state", None) == "firebreak":
                    qt_color = QColor("#8B4513")  # marrom, por exemplo
                self.cells[y][x].setBrush(QBrush(qt_color))

                # Sobrepõe ícone se for bombeiro
                if isinstance(agent, FirefighterAgent):
                    # Escolhe ícone conforme técnica do bombeiro
                    if getattr(agent, "technique", "water") == "alternative":
                        pixmap = self.tech_icon
                    else:
                        pixmap = self.siren_icon

                    pixmap_item = self.graphics_scene.addPixmap(pixmap)
                    pixmap_item.setPos(
                        x * self.cell_size + icon_offset,
                        y * self.cell_size + icon_offset
                    )
                    self.siren_items.append(pixmap_item)

    def show_graph_window(self):
        # Se não houver dados, sai
        if not (self.burned_area_evol or self.forested_area_evol or self.timesteps or
                self.model.fragulha_history or self.fire_start_positions or
                self.air_co_evol or self.temp_evol):
            self.add_log("Sem dados para exibir gráficos.")
            return

        # Dados opcionais para gráficos
        tree_heights = [
            (agent.pos[0], agent.pos[1], agent.tree_height)
            for agent in self.model.schedule if hasattr(agent, "tree_height")
        ]
        tree_altitudes = [
            (agent.pos[0], agent.pos[1], agent.altitude)
            for agent in self.model.schedule if hasattr(agent, "altitude")
        ]

        # 1) Evolução do incêndio
        if self.burned_area_evol or self.forested_area_evol or self.timesteps:
            burn_dialog = GraphWindow(
                burned_data=self.burned_area_evol,
                forested_data=self.forested_area_evol,
                timesteps=self.timesteps,
                parent=self
            )
            burn_dialog.setWindowTitle("Evolução de Árvores Queimadas vs Florestadas")
            burn_dialog.show()

        # 2) Gráfico do ar
        if self.air_co_evol:
            air_dialog = GraphWindow(
                air_co_evol=self.air_co_evol,
                air_co2_evol=self.air_co2_evol,
                air_pm25_evol=self.air_pm25_evol,
                air_pm10_evol=self.air_pm10_evol,
                air_o2_evol=self.air_o2_evol,
                timesteps=self.timesteps,
                parent=self
            )
            air_dialog.setWindowTitle("Evolução dos Poluentes e Oxigênio no Ar")
            air_dialog.show()

        # 3) Gráfico de clima (temp, hum, precip)
        if self.temp_evol:
            climate_dialog = GraphWindow(
                temperatura_evol=self.temp_evol,
                humidade_evol=self.humid_evol,
                precipitacao_evol=self.precip_evol,
                timesteps=self.timesteps,
                parent=self
            )
            climate_dialog.setWindowTitle("Evolução de Temperatura, Humidade e Precipitação")
            climate_dialog.show()

        # 4) Gráfico de altitude
        if tree_altitudes:
            altitude_dialog = GraphWindow(
                tree_altitudes=tree_altitudes,
                parent=self
            )
            altitude_dialog.setWindowTitle("Mapa de Altitude das Árvores")
            altitude_dialog.show()

        # 5) Gráfico de altura
        if tree_heights:
            height_dialog = GraphWindow(
                tree_heights=tree_heights,
                parent=self
            )
            height_dialog.setWindowTitle("Mapa de Altura das Árvores")
            height_dialog.show()

        # 6) Trajetórias das fragulhas
        if self.model.fragulha_history:
            frag_dialog = FragulhaArrowsWindow(
                self.model.fragulha_history,
                parent=self
            )
            frag_dialog.setWindowTitle("Trajetórias Detalhadas das Fragulhas")
            frag_dialog.show()

        # 7) Pontos de início do incêndio
        if self.fire_start_positions:
            fire_dialog = FireStartWindow(
                self.fire_start_positions,
                self.world_width,
                self.world_height,
                parent=self
            )
            fire_dialog.setWindowTitle("Pontos de Início do Incêndio")
            fire_dialog.show()

        # 8) Mapa de linhas de corte
        if hasattr(self.model, 'firebreak_history') and self.model.firebreak_history:
            firebreak_dialog = FirebreakMapWindow(
                self.model.firebreak_history,
                self.world_width,
                self.world_height,
                parent=self
            )
            firebreak_dialog.setWindowTitle("Mapa de Linhas de Corte")
            firebreak_dialog.show()


def main():
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
