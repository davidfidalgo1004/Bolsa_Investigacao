import sys  # Necessário para a execução da aplicação Qt
import random  # Para operações probabilísticas
import pynetlogo  # Para integrar com o NetLogo
import matplotlib  # Biblioteca para gráficos
# Define o backend do Matplotlib para funcionar com Qt5
matplotlib.use('Qt5Agg')
# Importa componentes da biblioteca PySide6 para construir a interface gráfica
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QTextEdit, QGraphicsScene, QGraphicsView
)
from PySide6.QtCore import Qt, Slot  # Para controle de eventos e sinais
from PySide6.QtGui import QBrush, QColor  # Para manipulação de cores e pincéis gráficos
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# Importa o modelo de ambiente criado e uma função para mapear cores
from ambiente import EnvironmentModel
from MapColor import EncontrarCor

# Classe para integrar um canvas do Matplotlib na interface Qt
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        # Cria uma figura do Matplotlib com as dimensões e dpi especificados
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # Adiciona um único eixo à figura
        self.axes = self.fig.add_subplot(111)
        # Inicializa o canvas com a figura criada
        super().__init__(self.fig)

# Classe principal da aplicação de simulação, que herda de QMainWindow
class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Define o título da janela
        self.setWindowTitle("Simulador de Incêndio")

        # ------------------ INICIALIZAÇÃO DO NETLOGO ------------------
        # Cria uma ligação com o NetLogo sem interface gráfica
        self.netlogo = pynetlogo.NetLogoLink(
            gui=False,
            netlogo_home=r"C:\Program Files\NetLogo 6.4.0"
        )
        # Carrega o modelo NetLogo para simulação de incêndios
        self.netlogo.load_model(r"C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo")
        
        # Obtém os limites do mundo NetLogo para definir o tamanho da grid
        self.min_pxcor = int(self.netlogo.report("min-pxcor"))
        self.min_pycor = int(self.netlogo.report("min-pycor"))
        self.max_pxcor = int(self.netlogo.report("max-pxcor"))
        self.max_pycor = int(self.netlogo.report("max-pycor"))

        # Calcula a largura e altura do mundo com base nos limites obtidos
        self.tamhorizontal = self.max_pxcor - self.min_pxcor + 1
        self.tamvertical = self.max_pycor - self.min_pycor + 1
        # Define as dimensões do mundo para a simulação (neste exemplo, utiliza os valores do NetLogo)
        self.world_width = self.tamhorizontal
        self.world_height = self.tamvertical
        # Instancia o modelo de ambiente; observe que é passado o NetLogo para integração
        self.model = EnvironmentModel(5, self.world_width, self.world_height, netlogo=self.netlogo)
        # Executa o comando "setup" no NetLogo para inicializar a simulação
        self.netlogo.command("setup")

        # ------------------ VARIÁVEIS PARA O GRÁFICO ------------------
        # Inicializa listas para armazenar a evolução dos dados durante a simulação
        self.burned_area_evol = []      # Evolução das áreas queimadas
        self.forested_area_evol = []    # Evolução das áreas florestadas
        self.timesteps = []             # Armazena as iterações
        self.last_detected_count = 0    # Para controle do número de incêndios detectados

        # ------------------ LAYOUT PRINCIPAL ------------------
        # Cria o widget central da janela e define o layout em grid
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 1) Cria a linha de controles (botões, slider e labels) que ocupa duas colunas
        self.create_controls_row()

        # 2) Cria o widget de log (para exibir mensagens) e o posiciona na coluna esquerda
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.main_layout.addWidget(self.log_text, 1, 0)

        # 3) Cria o canvas do Matplotlib para o gráfico e o posiciona na coluna esquerda
        self.canvas = MplCanvas(self, width=5, height=3, dpi=100)
        self.canvas.axes.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.canvas.axes.set_xlabel("Iterações")
        self.canvas.axes.set_ylabel("Quantidade")
        self.main_layout.addWidget(self.canvas, 2, 0)

        # 4) Cria a área gráfica (QGraphicsScene e QGraphicsView) para exibir o mapa do NetLogo
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.main_layout.addWidget(self.graphics_view, 1, 1, 2, 1)

        # Cria os itens do mapa (células) como retângulos na cena gráfica
        self.cell_size = 5  # Define o tamanho de cada célula (pode ser ajustado conforme necessário)
        self.cells = []     # Lista que armazenará os retângulos representando os patches
        self.netlogo.command("setup")  # Reinicia o NetLogo para garantir a configuração inicial
        # Cria uma grade de retângulos com base nas dimensões do mundo
        for row in range(self.world_height):
            row_items = []
            for col in range(self.world_width):
                # Adiciona um retângulo à cena, posicionado de acordo com a célula
                rect = self.graphics_scene.addRect(
                    col * self.cell_size, row * self.cell_size,
                    self.cell_size, self.cell_size
                )
                # Inicialmente, pinta a célula de branco
                rect.setBrush(QBrush(QColor("white")))
                row_items.append(rect)
            self.cells.append(row_items)

        # Exibe uma mensagem inicial no log para informar que a interface está pronta
        self.add_log("Interface pronta. Ajuste as iterações e clique em 'Iniciar Simulação'.")

    def create_controls_row(self):
        # Cria o widget que conterá os controles (slider, botões e labels)
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setSpacing(5)

        # Label para indicar o número de iterações
        iter_label = QLabel("Iterações:")
        controls_layout.addWidget(iter_label)

        # Slider para selecionar o número de iterações (entre 10 e 500, valor inicial 200)
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(10, 500)
        self.iter_slider.setValue(200)
        controls_layout.addWidget(self.iter_slider)

        # Botão para iniciar a simulação, conectado ao método run_simulation
        self.run_button = QPushButton("Iniciar Simulação")
        self.run_button.clicked.connect(self.run_simulation)
        controls_layout.addWidget(self.run_button)

        # Botão para apagar o fogo, conectado ao método stop_fire
        self.stop_fire_button = QPushButton("Apagar Fogo")
        self.stop_fire_button.clicked.connect(self.stop_fire)
        controls_layout.addWidget(self.stop_fire_button)

        # Label para exibir o status do incêndio e a temperatura atual
        self.fire_status_label = QLabel("Incêndio: Inativo (Temp: -- °C)")
        controls_layout.addWidget(self.fire_status_label)

        # Adiciona o widget de controles ao layout principal, ocupando duas colunas
        self.main_layout.addWidget(controls_widget, 0, 0, 1, 2)

    def add_log(self, message: str):
        # Método para adicionar mensagens ao log da interface
        self.log_text.append(message)

    @Slot()
    def run_simulation(self):
        # Limpa os dados e o log antes de iniciar uma nova simulação
        self.log_text.clear()
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()

        # Reinicia contadores e variáveis do modelo de simulação
        self.model.fires_created = 0
        self.model.fires_detected = 0
        self.model.detect_countdown = 0
        self.last_detected_count = 0

        # Obtém o número de iterações definido pelo usuário via slider
        iterations = self.iter_slider.value()

        self.add_log("Preparando simulação...")
        self.add_log(f"Executando {iterations} iterações.\n")

        # Loop principal que executa cada iteração da simulação
        for i in range(iterations):
            # Em cada iteração, com 10% de chance, inicia um incêndio
            if random.random() < 0.1:
                self.model.start_fire()

            # Avança a simulação um passo, atualizando todos os agentes
            self.model.step()

            # Verifica os sensores de incêndio para atualizar a interface com alertas
            if self.model.check_fire_sensors():
                self.add_log("[ALERTA] 🚨 Múltiplos sensores ativados! POSSÍVEL INCÊNDIO DETECTADO!")
                self.fire_status_label.setText(f"🔥 ALERTA DE INCÊNDIO! (Temp: {self.model.temperature:.1f} °C)")
            else:
                # Verifica se há incêndio ativo para atualizar o status
                if self.model.is_fire_active():
                    self.fire_status_label.setText(f"Incêndio: ATIVO (Temp: {self.model.temperature:.1f} °C)")
                else:
                    self.fire_status_label.setText(f"Incêndio: Inativo (Temp: {self.model.temperature:.1f} °C)")

            # Se o número de incêndios detectados aumentar, registra no log
            if self.model.fires_detected > self.last_detected_count:
                self.last_detected_count = self.model.fires_detected
                self.add_log(f"[TICK {i}] Incêndio DETECTADO! Temperatura = {self.model.temperature:.1f} °C")

            # Coleta dados do NetLogo: número de árvores queimadas e florestadas
            burned_trees = self.netlogo.report("burned-trees")
            forested_trees = self.netlogo.report("count patches with [pcolor = green]")

            # Armazena os dados para posterior plotagem
            self.burned_area_evol.append(burned_trees)
            self.forested_area_evol.append(forested_trees)
            self.timesteps.append(i)

            self.add_log(f"Iteração {i} | Queimadas: {burned_trees}, Florestadas: {forested_trees}")

            # Atualiza o mapa visual do NetLogo
            self.update_netlogo_grid(i)

            # Processa eventos pendentes para manter a interface responsiva
            QApplication.processEvents()

        # Ao final da simulação, exibe um resumo no log e atualiza o gráfico
        self.add_log("\nSimulação finalizada!")
        self.add_log(f"Número de incêndios criados: {self.model.fires_created}")
        self.add_log(f"Número de incêndios detectados: {self.model.fires_detected}")
        self.update_plot()

    @Slot()
    def stop_fire(self):
        # Chama o método do modelo para apagar os incêndios e atualiza o log
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")

    def update_plot(self):
        # Atualiza o gráfico com a evolução dos dados coletados durante a simulação
        self.canvas.axes.clear()
        self.canvas.axes.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.canvas.axes.set_xlabel("Iterações")
        self.canvas.axes.set_ylabel("Quantidade")
        self.canvas.axes.grid(True)

        if self.timesteps:
            # Plota a evolução das árvores queimadas e florestadas em cores diferentes
            self.canvas.axes.plot(self.timesteps, self.burned_area_evol, label='Árvores Queimadas', color='red')
            self.canvas.axes.plot(self.timesteps, self.forested_area_evol, label='Árvores Florestadas', color='green')
            self.canvas.axes.legend()

        # Redesenha o canvas com o novo gráfico
        self.canvas.draw()

    def update_netlogo_grid(self, i):
        """
        Atualiza a cor de cada célula do QGraphicsScene utilizando uma única chamada
        ao NetLogo para obter uma matriz com os valores pcolor de todos os patches.
        """
        # Constrói o comando em linguagem NetLogo para obter uma matriz dos valores pcolor
        cmd = (
            f"map [[y] -> "
            f"  map [[x] -> [pcolor] of patch (x + {self.min_pxcor}) (y + {self.min_pycor})] "
            f"       n-values {self.world_width} [[x] -> x] "
            f"] n-values {self.world_height} [[y] -> y]"
        )
        # Executa o comando no NetLogo e recebe a matriz de cores
        patch_colors = self.netlogo.report(cmd)
        # Atualiza o grid a cada 5 iterações para otimizar desempenho
        if (i % 5) == 0:
            for row in range(self.world_height):
                for col in range(self.world_width):
                    pcolor_value = patch_colors[row][col]
                    try:
                        # Tenta arredondar o valor para facilitar a interpretação
                        pcolor_value = round(pcolor_value, 1)
                    except Exception:
                        pass
                    # Converte o valor numérico para uma cor através da função EncontrarCor
                    qt_color = EncontrarCor(pcolor_value)
                    # Atualiza a cor do retângulo correspondente na cena gráfica
                    self.cells[row][col].setBrush(QBrush(QColor(qt_color)))

def main():
    # Função principal que inicia a aplicação Qt
    aplicacao = QApplication(sys.argv)
    janela = SimulationApp()
    janela.show()
    sys.exit(aplicacao.exec())

# Garante que o script seja executado diretamente
if __name__ == "__main__":
    main()
