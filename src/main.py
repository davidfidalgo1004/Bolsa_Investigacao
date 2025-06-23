# Standard library imports
import sys
import random
import subprocess, os, webbrowser, time, json
from pathlib import Path
import requests
from components.settings.geradorAPIs import generate_token

# Third-party imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView,
    QFormLayout, QRadioButton, QButtonGroup, QToolTip, QFileDialog
)
from PySide6.QtCore import Qt, Slot, QTimer, QEvent
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QPixmap, QCursor

# Local imports
from components.objects.bossula import CompassWidget
from Environment.ambiente import EnvironmentModel
from Agents.firefighter_agent import FirefighterAgent
from components.settings.MapColor import EncontrarCor
from components.objects.GraficoAnalise import (
    GraphWindow, FragulhaArrowsWindow, FireStartWindow, 
    FirebreakMapWindow, plot_trajectories
)

# ------------- Wildfire API Config -------------
BASE_URL = os.getenv("WILDFIRE_API_BASE_URL", "http://ken01.utad.pt:8080")
AUDIENCE = os.getenv("WILDFIRE_API_AUDIENCE", "ken01.utad.pt:8080")
TOKEN = os.getenv("WILDFIRE_API_TOKEN") or generate_token(AUDIENCE)

# --- Timeout para pedidos à Wildfire API ---
# Pode ser definido via variável de ambiente WILDFIRE_API_TIMEOUT (segundos).
API_TIMEOUT = int(os.getenv("WILDFIRE_API_TIMEOUT", "300"))  # default 300 s (5 min)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Mostra o token no arranque para depuração (remova em produção se necessário)
print(f"[DEBUG] JWT token usado: {TOKEN}")

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
        self.setWindowTitle("Simulador de Incêndio Multi-Agente")

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
        
        # Controle de pausa
        self.is_paused = False
        self.timer = None

        self.fire_start_positions = []

        # Valor de risco recebido via API (0-1); usado para probabilidades de ignição
        self.api_risk_value = None

        # Flag para permitir apenas uma ignição automática até voltar a ser reactivada
        self.fireigni = True

        self.has_setup = False

        # Caminho escolhido para GeoJSON (default area.geojson)
        self.selected_geojson_path = Path("area.geojson")

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

        # Carrega ícone da sirene (100% da célula) ou fallback azul-escuro
        try:
            self.siren_icon = QPixmap("components/assets/patch/siren.jpg").scaled(
                self.cell_size,
                self.cell_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            print(f"✅ Siren icon loaded: {not self.siren_icon.isNull()}, size: {self.siren_icon.width()}x{self.siren_icon.height()}")
        except Exception as e:
            print(f"❌ Failed to load siren icon: {e}")
            self.siren_icon = QPixmap(self.cell_size, self.cell_size)
            self.siren_icon.fill(QColor("#00008B"))
        self.siren_items = []

        try:
            self.tech_icon = QPixmap("components/assets/patch/bombeirotec.jpg").scaled(
                self.cell_size,
                self.cell_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            print(f"✅ Tech icon loaded: {not self.tech_icon.isNull()}, size: {self.tech_icon.width()}x{self.tech_icon.height()}")
        except Exception as e:
            print(f"❌ Failed to load tech icon: {e}")
            self.tech_icon = QPixmap(self.cell_size, self.cell_size)
            self.tech_icon.fill(QColor("#00008B"))
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

        # ---------- Ignicao por Clique ----------
        # Permite ao utilizador iniciar o fogo clicando na célula desejada
        self.graphics_view.setMouseTracking(True)
        self.graphics_view.mousePressEvent = self.handle_view_click

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

        # Guarda para alternar visibilidade
        self.env_type_widgets = [
            self.radio_only_trees,
            self.radio_road_trees,
            self.radio_river_trees,
        ]

        # ---------------- Modo de operação ----------------
        self.mode_group = QButtonGroup()
        self.radio_sim_mode = QRadioButton("Modo Simulado")
        self.radio_real_mode = QRadioButton("Modo Real (API)")
        self.radio_sim_mode.setChecked(True)
        for btn in [self.radio_sim_mode, self.radio_real_mode]:
            self.mode_group.addButton(btn)
            row1.addWidget(btn)

        self.setup_button = QPushButton("Setup")
        self.setup_button.clicked.connect(self.setup_model)
        row1.addWidget(self.setup_button)

        self.run_button = QPushButton("Iniciar Simulação")
        self.run_button.clicked.connect(self.run_simulation)
        row1.addWidget(self.run_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_simulation)
        self.pause_button.setEnabled(False)  # Desabilitado inicialmente
        row1.addWidget(self.pause_button)

        self.step_button = QPushButton("Próximo Passo")
        self.step_button.clicked.connect(self.single_step)
        row1.addWidget(self.step_button)

        # Botão para encerrar e visualizar resultados
        self.end_button = QPushButton("Encerrar Simulação")
        self.end_button.clicked.connect(self.stop_and_show_results)
        self.end_button.setEnabled(False)
        row1.addWidget(self.end_button)

        self.fire_status_label = QLabel("Incêndio: Inativo (Temp: -- °C)")
        # Label ocultada para simplificar a interface
        self.fire_status_label.hide()

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

        # Guarda widgets climáticos para poder ocultar em modo API
        self.climate_widgets = [
            wind_speed_label, self.wind_speed_slider,
            wind_direction_label, self.wind_direction_slider,
            density_label, self.density_slider,
            precip_label, self.precip_slider,
            humid_label, self.humid_slider,
            temp_label, self.temp_slider,
        ]

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

        # Linha 4: Integração com GeoJSON / API de risco
        row4 = QHBoxLayout()
        self.choose_loc_button = QPushButton("Escolher Local (Mapa)")
        self.choose_loc_button.clicked.connect(self.choose_location)
        row4.addWidget(self.choose_loc_button)

        self.calc_risk_button = QPushButton("Ver Locais Disponíveis")
        self.calc_risk_button.clicked.connect(self.select_existing_location)
        row4.addWidget(self.calc_risk_button)

        controls_layout.addLayout(row4)

        # Actualiza visibilidade conforme modo inicial
        self.radio_sim_mode.toggled.connect(self.update_controls_visibility)
        self.update_controls_visibility()

    # Utilitário interno para remover emojis (intervalo Unicode 1F300-1FAFF)
    @staticmethod
    def _strip_emojis(text: str) -> str:
        return text.translate({code: None for code in range(0x1F300, 0x1FB00)})

    def add_log(self, message: str):
        self.log_text.append(self._strip_emojis(message))

    def update_firefighter_status_label(self):
        """Atualiza a label com o status atual dos bombeiros."""
        firefighters = [a for a in self.model.schedule if isinstance(a, FirefighterAgent)]
        
        # Contagem por modo específico
        em_ataque = sum(1 for f in firefighters if f.mode == "direct_attack")
        navegando = sum(1 for f in firefighters if f.mode == "navigating")
        criando_firebreak = sum(1 for f in firefighters if f.mode == "firebreak")
        retornando_casa = sum(1 for f in firefighters if f.mode == "returning_home")
        ociosos = sum(1 for f in firefighters if f.mode == "idle")
        evacuados = sum(1 for f in firefighters if f.mode == "evacuated")
        
        # Contagem por técnica
        bombeiros_agua = sum(1 for f in firefighters if f.technique == "water")
        bombeiros_tecnico = sum(1 for f in firefighters if f.technique == "alternative")
        
        # Atualiza rótulo de status dos bombeiros
        status_text = f"Bombeiros (Water {bombeiros_agua} | Tech {bombeiros_tecnico}) – "
        
        if em_ataque > 0:
            status_text += f"Ataque: {em_ataque}, "
        if criando_firebreak > 0:
            status_text += f"Firebreak: {criando_firebreak}, "
        if navegando > 0:
            status_text += f"Movendo: {navegando}, "
        if retornando_casa > 0:
            status_text += f"Regressando: {retornando_casa}, "
        if ociosos > 0:
            status_text += f"Ociosos: {ociosos}, "
        if evacuados > 0:
            status_text += f"Evacuados: {evacuados}, "
        
        # Remove vírgula final
        status_text = status_text.rstrip(", ")
        
        self.ff_status_label.setText(status_text)


    @Slot()
    def setup_model(self):
        self.fireigni=True
        # Se houver dados da simulação anterior, mostra gráficos antes de reiniciar
        if (self.burned_area_evol or self.forested_area_evol or self.timesteps or
            self.model.fragulha_history or self.fire_start_positions or
            self.air_co_evol or self.temp_evol):
            self.add_log("Exibindo gráficos da simulação anterior...")
            self.show_graph_window()
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

        # Atualiza label dos bombeiros na inicialização
        self.update_firefighter_status_label()

        # Iteração e controles
        self.current_iteration = 0
        self.total_iterations = 0
        
        # Reset dos controles de simulação
        if self.timer and self.timer.isActive():
            self.timer.stop()
        self.is_paused = False
        self.run_button.setText("Iniciar Simulação")
        self.run_button.setEnabled(True)
        self.pause_button.setText("Pausar")
        self.pause_button.setEnabled(False)


    @Slot()
    def run_simulation(self):
        if self.is_paused:
            # Retomar simulação pausada
            self.is_paused = False
            self.run_button.setText("Executando...")
            self.run_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.pause_button.setText("Pausar")
            self.add_log("Simulação retomada!")
            if self.timer:
                self.timer.start()
            return
            
        self.setup_button.setEnabled(False)
        self.log_text.clear()
        self.add_log("Iniciando simulação...")
        self.run_button.setText("Executando...")
        self.run_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("Pausar")

        if self.current_iteration > 0:
            self.total_iterations += self.iter_slider.value()
        else:
            self.total_iterations = self.iter_slider.value()

        if not self.timer:
            self.timer = QTimer()
            self.timer.setInterval(250)
            self.timer.timeout.connect(self.simulation_step)
        self.timer.start()


    @Slot()
    def simulation_step(self):
        if self.current_iteration >= self.total_iterations:
            if self.timer:
                self.timer.stop()
            self.add_log("\nSimulação finalizada!")
            self.setup_button.setEnabled(True)
            self.run_button.setText("Iniciar Simulação")
            self.run_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.pause_button.setText("Pausar")
            self.is_paused = False
            return
        if self.current_iteration % 20 == 0:
            if random.random() < self.model.rain_level:
                self.model.itsrain_ = True
            else:
                self.model.itsrain_ = False
            # A ignição automática via probabilidade foi desativada.
            # O utilizador pode agora iniciar o fogo clicando directamente na célula
            # desejada. Ver método `handle_view_click`.
        
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
        # Atualiza label dos bombeiros
        self.update_firefighter_status_label()

        self.update_grid()
        self.current_iteration += 1

    @Slot()
    def pause_simulation(self):
        """Pausa ou retoma a simulação."""
        if not self.is_paused:
            # Pausar simulação
            self.is_paused = True
            if self.timer:
                self.timer.stop()
            self.run_button.setText("Retomar Simulação")
            self.run_button.setEnabled(True)
            self.pause_button.setText("Pausado")
            self.pause_button.setEnabled(False)
            self.add_log("⏸️ Simulação pausada! Use 'Retomar Simulação' ou 'Próximo Passo'")

    @Slot()
    def single_step(self):
        """Executa um único passo da simulação."""
        if self.current_iteration >= self.total_iterations:
            self.add_log("Simulação já finalizada! Use 'Setup' para reiniciar.")
            return
            
        # Se a simulação estiver executando, pause primeiro
        if self.timer and self.timer.isActive():
            self.pause_simulation()
            
        self.add_log(f"🔄 Executando passo único: {self.current_iteration + 1}")
        self.simulation_step()

    @Slot()
    def stop_fire(self):
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")


    
    def update_grid(self):
        # Remove ícones antigos
        for item in getattr(self, "siren_items", []):
            self.graphics_scene.removeItem(item)
        self.siren_items = []

        icon_offset = 0  # sem margem, ícone ocupa toda a célula
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor"):
                x, y = agent.pos
                # Pinta a célula conforme pcolor
                qt_color = QColor(EncontrarCor(agent.pcolor))
                # Se for firebreak, pode forçar uma cor específica
                if getattr(agent, "state", None) == "firebreak":
                    qt_color = QColor("#8B4513")  # marrom, por exemplo
                elif getattr(agent, "state", None) == "house":
                    qt_color = QColor("#C0C0C0")  # cinza casas
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

        # ---------------- GeoJSON / API Risco ----------------
    
    def _start_streamlit(self):
        """Inicia o servidor Streamlit se ainda não estiver em execução."""
        if getattr(self, "_geojson_process", None) and self._geojson_process.poll() is None:
            return  # Já está em execução

        self.add_log("🗺️ Iniciando interface de seleção de local (Streamlit)...")
        try:
            # Caminho absoluto para o novo ficheiro Streamlit
            script_path = Path(__file__).resolve().parent / "components" / "objects" / "geojson_interface.py"
            self._geojson_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(script_path),
                "--server.port", "8501", "--server.headless", "true"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Dá tempo para o servidor lançar
            time.sleep(2)
        except FileNotFoundError:
            self.add_log("⚠️ Streamlit não encontrado. Instale com 'pip install streamlit'.")
            self._geojson_process = None

    @Slot()
    def choose_location(self):
        """Abre a interface Streamlit para escolha de área."""
        self._start_streamlit()
        if getattr(self, "_geojson_process", None):
            webbrowser.open("http://localhost:8501", new=2)
            self.add_log("⚙️ Interface aberta no navegador. Desenhe o polígono e use 'Export' para guardar 'area.geojson'.")

    @Slot()
    def select_existing_location(self):
        """Abre um diálogo para escolher um ficheiro .geojson em components/assets/locals.
        O ficheiro selecionado é copiado para area.geojson e processado."""

        start_dir = Path(__file__).resolve().parent / "components" / "assets" / "locals"
        if not start_dir.exists():
            self.add_log("⚠️ Pasta de locais não encontrada.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher Local",
            str(start_dir),
            "GeoJSON (*.geojson)"
        )
        if not file_path:
            return  # cancelado

        try:
            # Guarde o caminho selecionado
            self.selected_geojson_path = Path(file_path)
            self.add_log(f"📂 Local '{self.selected_geojson_path.name}' selecionado.")
            # Processa diretamente sem copiar
            self.load_area_and_risk(self.selected_geojson_path)
        except Exception as e:
            self.add_log(f"❌ Erro ao processar o local: {e}")

    def load_area_and_risk(self, file_path: Path | None = None):
        """Carrega o GeoJSON indicado (ou 'area.geojson' por omissão) e calcula o risco via API."""
        area_path = file_path or self.selected_geojson_path
        if not area_path.exists():
            self.add_log("⚠️ Ficheiro 'area.geojson' não encontrado. Exporte primeiro na interface de mapa.")
            return
        try:
            geojson = json.loads(area_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.add_log(f"⚠️ Erro ao ler 'area.geojson': {e}")
            return

        self.add_log("🔎 A calcular risco da área selecionada…")
        result = self._calculate_risk_api(geojson)
        if result is not None:
            self.add_log(f"✅ Resultado do risco: {result}")

            # Analisa latitude do GeoJSON
            self._analyze_geojson_latitude(geojson)

            # Aplica valores climáticos apenas se estiver em Modo Real (API)
            if self.radio_real_mode.isChecked():
                self._apply_api_values(result)

            # Se ainda não houver modelo criado em modo Real, cria-o agora
            if not self.has_setup:
                self._initialize_model_from_current_settings()

            # Desenha estradas (se houver)
            try:
                self._draw_roads_from_geojson(geojson)
            except Exception as e:
                self.add_log(f"⚠️ Não foi possível desenhar estradas do ficheiro: {e}")

            # Se não houver LineStrings, tenta buscar estradas ao OpenStreetMap
            try:
                self._fetch_and_draw_osm_roads(geojson)
                self._fetch_and_draw_osm_buildings(geojson)
            except Exception as e:
                self.add_log(f"⚠️ Overpass falhou: {e}")

    def _calculate_risk_api(self, geojson, **params):
        """Wrapper para chamar o endpoint /calculate-risk/."""
        try:
            # --- DEBUG: mostra tamanho do payload e alguns cabeçalhos ---
            if params.get("debug"):
                self.add_log(
                    f"➡️ POST {BASE_URL}/calculate-risk/ (payload {len(json.dumps(geojson))} bytes)"
                )
                self.add_log(f" Token: {TOKEN}")

            # Também imprime na consola sempre que é feita a requisição
            print(f"[DEBUG] Enviando requisição com token: {TOKEN}")

            resp = requests.post(
                f"{BASE_URL}/calculate-risk/",
                headers=HEADERS,
                params={k: v for k, v in params.items() if k != "debug"},
                json=geojson,
                timeout=(10, API_TIMEOUT)  # 10 s ligação, API_TIMEOUT leitura
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as err:
            self.add_log(f"❌ Erro API {err.response.status_code}: {err.response.text}")
        except Exception as exc:
            self.add_log(f"❌ Erro ao contactar API: {exc}")
        return None

    def _apply_api_values(self, result):
        """Aplica os valores devolvidos pela API à configuração actual.

        O objecto `result` é um FeatureCollection. Para cada feature do tipo
        *Polygon* recolhemos as propriedades pertinentes. Se houver várias
        features, calculamos a média simples; caso exista apenas uma, usamos
        directamente."""

        # --- Extracção dos valores das propriedades ---
        keys_of_interest = [
            "temperature", "humidity", "precipitation",
            "wind_speed", "wind_direction"
        ]

        agg = {k: [] for k in keys_of_interest}

        features = result.get("features", []) if isinstance(result, dict) else []
        for feat in features:
            props = feat.get("properties", {})
            for k in keys_of_interest:
                if k in props and props[k] is not None:
                    agg[k].append(props[k])

        # Se não encontrámos nada, avisa e sai
        if not any(agg.values()):
            self.add_log("⚠️ A resposta não contém valores climáticos utilizáveis.")
            return

        def _mean(values):
            return sum(values) / len(values) if values else None

        averaged = {k: _mean(v) for k, v in agg.items()}

        # --- Sincroniza sliders ---
        def _set_slider(slider, value, minimum=None, maximum=None):
            if value is None:
                return
            if minimum is None:
                minimum = slider.minimum()
            if maximum is None:
                maximum = slider.maximum()
            value = max(min(value, maximum), minimum)
            slider.setValue(int(round(value)))

        # Temperatura (°C)
        _set_slider(self.temp_slider, averaged.get("temperature"))

        # Humidade (%)
        _set_slider(self.humid_slider, averaged.get("humidity"))

        # Precipitação (%) – algumas APIs devolvem 0-1; converte para 0-100
        precip_val = averaged.get("precipitation")
        if precip_val is not None and precip_val <= 1:
            precip_val *= 100
        _set_slider(self.precip_slider, precip_val)

        # Velocidade do vento (m/s)
        _set_slider(self.wind_speed_slider, averaged.get("wind_speed"))

        # Direcção do vento (graus 0-359)
        wind_dir = averaged.get("wind_direction")
        if wind_dir is not None:
            wind_dir = wind_dir % 360
        _set_slider(self.wind_direction_slider, wind_dir, 0, 359)

        # --- Propaga imediatamente se já houver modelo configurado ---
        if self.has_setup:
            self.model.wind_direction = self.wind_direction_slider.value()
            self.model.wind_speed = self.wind_speed_slider.value()
            self.model.rain_level = self.precip_slider.value() / 100.0
            self.model.humidity = self.humid_slider.value()
            self.model.temperature = self.temp_slider.value()

            self.add_log("🔄 Parâmetros do modelo actualizados com dados reais da API.")

        # Determina o nível de risco mais elevado para colorir a grelha
        def _risk_color(level: str):
            mapping = {
                "Very Low": "#9aff9a",      # verde claro
                "Low": "#ccff66",          # amarelo-esverdeado
                "Moderate": "#ffff66",     # amarelo
                "High": "#ffb347",         # laranja
                "Very High": "#ff704d",     # laranja-avermelhado
                "Extreme": "#ff3333",      # vermelho
            }
            return mapping.get(level, None)

        highest_feat = None
        highest_val = -1
        for feat in features:
            props = feat.get("properties", {})
            val = props.get("risk_value")
            if val is not None and val > highest_val:
                highest_val = val
                highest_feat = feat

        if highest_feat is not None:
            risk_level = highest_feat["properties"].get("risk_level")
            color_hex = _risk_color(risk_level)
            if color_hex:
                # Aplica cor de fundo a toda a grelha
                for row in range(self.world_height):
                    for col in range(self.world_width):
                        self.cells[row][col].setBrush(QBrush(QColor(color_hex)))

                self.add_log(f"🎨 Grelha colorida segundo nível de risco '{risk_level}'.")

        # Guarda o valor de risco global para lógica de ignição
        self.api_risk_value = highest_val if highest_val >= 0 else None

    # ------------------------------------------------------------------
    # GeoJSON → Estradas na grelha
    # ------------------------------------------------------------------
    def _draw_roads_from_geojson(self, geojson):
        """Percorre o GeoJSON atrás de geometrias LineString / MultiLineString
        (usadas normalmente para estradas) e pinta as respectivas células
        como 'road'.

        Requer que o modelo já tenha sido configurado (Setup executado)."""

        if not self.has_setup:
            self.add_log("⚠️ Execute o 'Setup' antes de aplicar estradas do GeoJSON.")
            return

        from Agents.agentes import PatchAgent  # import tardio para evitar ciclos

        # 1) Extrai todas as coordenadas para calcular bounding box
        def _collect_coords(geom):
            gtype = geom.get("type")
            if gtype == "LineString":
                return geom.get("coordinates", [])
            elif gtype == "MultiLineString":
                coords = []
                for line in geom.get("coordinates", []):
                    coords.extend(line)
                return coords
            elif gtype == "Polygon":
                return geom.get("coordinates", [])[0]  # limite exterior
            elif gtype == "MultiPolygon":
                coords = []
                for poly in geom.get("coordinates", []):
                    coords.extend(poly[0])
                return coords
            return []

        all_coords = []
        for feat in geojson.get("features", []):
            geom = feat.get("geometry", {})
            all_coords.extend(_collect_coords(geom))

        if not all_coords:
            self.add_log("⚠️ GeoJSON sem coordenadas utilizáveis.")
            return

        lons, lats = zip(*all_coords)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        lon_span = max_lon - min_lon or 1e-9  # evita div/0
        lat_span = max_lat - min_lat or 1e-9

        def _to_grid(lon, lat):
            gx = int(round((lon - min_lon) / lon_span * (self.world_width - 1)))
            gy = int(round((max_lat - lat) / lat_span * (self.world_height - 1)))
            gx = max(0, min(self.world_width - 1, gx))
            gy = max(0, min(self.world_height - 1, gy))
            return gx, gy

        ROAD_RADIUS = 1  # torna a estrada mais larga

        def _set_patch_road(x, y):
            for dx in range(-ROAD_RADIUS, ROAD_RADIUS + 1):
                for dy in range(-ROAD_RADIUS, ROAD_RADIUS + 1):
                    gx, gy = x + dx, y + dy
                    if 0 <= gx < self.world_width and 0 <= gy < self.world_height:
                        for agent in self.model.grid.get_cell_list_contents((gx, gy)):
                            if isinstance(agent, PatchAgent) and agent.state != "road":
                                agent.state = "road"
                                agent.pcolor = 85
                                break

        # 2) Varre features LineString / MultiLineString
        for feat in geojson.get("features", []):
            geom = feat.get("geometry", {})
            gtype = geom.get("type")
            if gtype not in ("LineString", "MultiLineString"):
                continue

            lines = geom.get("coordinates", [])
            if gtype == "LineString":
                lines = [lines]

            for line in lines:
                prev = None
                for lon, lat in line:
                    gx, gy = _to_grid(lon, lat)
                    _set_patch_road(gx, gy)

                    # Conecta com célula anterior para evitar falhas
                    if prev is not None:
                        px, py = prev
                        dx = gx - px
                        dy = gy - py
                        steps = max(abs(dx), abs(dy))
                        if steps:
                            for i in range(1, steps):
                                ix = px + round(dx * i / steps)
                                iy = py + round(dy * i / steps)
                                _set_patch_road(ix, iy)
                    prev = (gx, gy)

        # 3) Atualiza visualização
        self.update_grid()
        self.add_log("🛣️ Estradas do GeoJSON desenhadas na grelha.")

    # ------------------------------------------------------------------
    # Overpass API — estradas
    # ------------------------------------------------------------------
    def _fetch_and_draw_osm_roads(self, polygon_geojson):
        """Consulta a Overpass API para obter 'ways' com tag highway dentro do
        bounding box do polígono e desenha-as na grelha."""

        # Extrai bounding box
        coords = []
        for feat in polygon_geojson.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Polygon":
                coords.extend(geom.get("coordinates", [[]])[0])
        if not coords:
            return  # sem polígono

        lons, lats = zip(*coords)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        overpass_query = f"""
        [out:json][timeout:25];
        (
          way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out geom;
        """

        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query.encode("utf-8"),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        road_features = []
        for el in data.get("elements", []):
            if el.get("type") == "way" and "geometry" in el:
                coords_ll = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
                if len(coords_ll) >= 2:
                    road_features.append(
                        {
                            "type": "Feature",
                            "properties": {"highway": el.get("tags", {}).get("highway", "")},
                            "geometry": {"type": "LineString", "coordinates": coords_ll},
                        }
                    )

        if not road_features:
            self.add_log("ℹ️ Nenhuma estrada encontrada na área (OSM).")
            return

        roads_geojson = {"type": "FeatureCollection", "features": road_features}
        self._draw_roads_from_geojson(roads_geojson)

    # ------------------------------------------------------------------
    # Overpass API — edifícios
    # ------------------------------------------------------------------
    def _fetch_and_draw_osm_buildings(self, polygon_geojson):
        """Obtém edifícios (ways/relações com tag building) dentro da área
        e colore as células como 'house'."""

        if not self.has_setup:
            return  # ignora se o modelo ainda não existe

        coords = []
        for feat in polygon_geojson.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Polygon":
                coords.extend(geom.get("coordinates", [[]])[0])
        if not coords:
            return

        lons, lats = zip(*coords)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        overpass_query = f"""
        [out:json][timeout:25];
        (
          way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
          relation["building"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out geom;
        """

        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query.encode("utf-8"),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("elements"):
            self.add_log("ℹ️ Nenhum edifício encontrado (OSM).")
            return

        from Agents.agentes import PatchAgent

        # Conversão lon/lat → grid
        lon_span = max_lon - min_lon or 1e-9
        lat_span = max_lat - min_lat or 1e-9

        def _to_grid(lon, lat):
            gx = int(round((lon - min_lon) / lon_span * (self.world_width - 1)))
            gy = int(round((max_lat - lat) / lat_span * (self.world_height - 1)))
            return gx, gy

        HOUSE_RADIUS = 1

        def _set_house(x, y):
            for dx in range(-HOUSE_RADIUS, HOUSE_RADIUS + 1):
                for dy in range(-HOUSE_RADIUS, HOUSE_RADIUS + 1):
                    gx, gy = x + dx, y + dy
                    if 0 <= gx < self.world_width and 0 <= gy < self.world_height:
                        for agent in self.model.grid.get_cell_list_contents((gx, gy)):
                            if isinstance(agent, PatchAgent) and agent.state != "house":
                                agent.state = "house"
                                agent.pcolor = 25
                                break

        for el in data.get("elements", []):
            geom = el.get("geometry")
            if not geom:
                continue
            for idx, point in enumerate(geom):
                gp = _to_grid(point["lon"], point["lat"])
                _set_house(*gp)
                if idx > 0:
                    prev = geom[idx - 1]
                    px, py = _to_grid(prev["lon"], prev["lat"])
                    gx, gy = gp
                    dx = gx - px
                    dy = gy - py
                    steps = max(abs(dx), abs(dy))
                    if steps:
                        for i in range(1, steps):
                            ix = px + round(dx * i / steps)
                            iy = py + round(dy * i / steps)
                            _set_house(ix, iy)

        self.update_grid()
        self.add_log("🏠 Edifícios do OSM pintados na grelha.")

    # Override para terminar o processo Streamlit ao fechar a aplicação
    def closeEvent(self, event):
        if getattr(self, "_geojson_process", None) and self._geojson_process.poll() is None:
            self._geojson_process.terminate()
        super().closeEvent(event)

    # --------------------- Visibilidade ---------------------
    def update_controls_visibility(self):
        """Mostra/esconde controlos conforme o modo (Simulado vs Real)."""
        api_mode = self.radio_real_mode.isChecked()
        self.setup_button.setVisible(not api_mode)
        self.choose_loc_button.setVisible(api_mode)
        self.calc_risk_button.setVisible(api_mode)

        # Esconde sliders climáticos em modo API
        for w in getattr(self, 'climate_widgets', []):
            w.setVisible(not api_mode)

        # Esconde opções de ambiente (árvores/estrada/rio) em modo API
        for w in getattr(self, 'env_type_widgets', []):
            w.setVisible(not api_mode)

    # -------------------- Modelo a partir dos sliders --------------------
    def _initialize_model_from_current_settings(self):
        """Cria o EnvironmentModel com os valores atuais dos sliders (usado no modo Real)."""
        self.add_log("🔧 A criar modelo com parâmetros da API…")

        self.forest_density = self.density_slider.value() / 100.0
        if self.radio_road_trees.isChecked():
            chosen_env = "road_trees"
        elif self.radio_river_trees.isChecked():
            chosen_env = "river_trees"
        else:
            chosen_env = "only_trees"

        # Cria o modelo
        self.model = EnvironmentModel(
            self.world_width,
            self.world_height,
            density=self.forest_density,
            env_type=chosen_env,
            num_firefighters=self.ff_count_slider.value(),
            water_ratio=self.ff_ratio_slider.value() / 100.0,
        )

        # Propaga sliders (já podem ter sido alterados pela API)
        self.model.wind_direction = self.wind_direction_slider.value()
        self.model.wind_speed = self.wind_speed_slider.value()
        self.model.rain_level = self.precip_slider.value() / 100.0
        self.model.humidity = self.humid_slider.value()
        self.model.temperature = self.temp_slider.value()

        # Limpa e pinta grelha inicial
        for row in range(self.world_height):
            for col in range(self.world_width):
                self.cells[row][col].setBrush(QBrush(QColor("white")))

        self.update_grid()

        self.has_setup = True
        self.run_button.setEnabled(True)
        self.end_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.add_log("✅ Modelo pronto! Use 'Iniciar Simulação'.")

    # -------------------- Encerrar Simulação --------------------
    def stop_and_show_results(self):
        """Pára a simulação e exibe os gráficos finais."""
        if self.timer and self.timer.isActive():
            self.timer.stop()
        self.is_paused = False
        self.run_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.end_button.setEnabled(False)

        self.add_log("🛑 Simulação encerrada!")
        self.show_graph_window()

    # ------------------- Latitude analysis -------------------
    def _analyze_geojson_latitude(self, geojson):
        """Extrai latitudes das coordenadas e regista estatísticas no log."""
        lats = []
        for feat in geojson.get("features", []):
            geom = feat.get("geometry", {})
            coords = []
            if geom.get("type") == "Polygon":
                coords = geom.get("coordinates", [[]])[0]
            elif geom.get("type") == "LineString":
                coords = geom.get("coordinates", [])
            elif geom.get("type") == "MultiPolygon":
                for poly in geom.get("coordinates", []):
                    coords.extend(poly[0])
            elif geom.get("type") == "MultiLineString":
                for line in geom.get("coordinates", []):
                    coords.extend(line)
            lats.extend([lat for _, lat in coords])

        if lats:
            min_lat = min(lats)
            max_lat = max(lats)
            mean_lat = sum(lats) / len(lats)
            self.add_log(
                f"📍 Latitude mínima: {min_lat:.4f}, máxima: {max_lat:.4f}, média: {mean_lat:.4f}")

    def handle_view_click(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.graphics_view.mapToScene(event.pos())
            x = int(pos.x() / self.cell_size)
            y = int(pos.y() / self.cell_size)
            if 0 <= x < self.world_width and 0 <= y < self.world_height:
                if self.model.start_fire_at(x, y):
                    self.fire_start_positions.append((x, y))
                    self.add_log(f"🔥 Fogo iniciado em ({x}, {y}) via clique")
                    self.update_grid()


def main():
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
