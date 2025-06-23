import pynetlogo
import random
import mesa
import ipywidgets as widgets
from IPython.display import display, clear_output
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mesa.visualization import SolaraViz, make_plot_component, make_space_component

# Inicializar conexão com NetLogo
netlogo = pynetlogo.NetLogoLink(gui=False, netlogo_home=r'C:\Program Files\NetLogo 6.4.0')
netlogo.load_model(r'C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo')

class GenericAgent(mesa.Agent):
    def __init__(self, unique_id, model, agent_type):
        # Atribuição manual dos atributos
        self.unique_id = unique_id
        self.model = model
        self.wealth = 1
        self.agent_type = agent_type
        
        if agent_type == "Wind":
            self.wind_speed = 10
            self.wind_direction = 15
            netlogo.command(f"set wind-speed {self.wind_speed}")
            netlogo.command(f"set wind-direction {self.wind_direction}")
        elif agent_type == "Air":
            self.co_level = netlogo.report('co-level')
            self.co2_level = netlogo.report('co2-level')
            self.pm2_5_level = netlogo.report('pm2_5-level')
            self.pm10_level = netlogo.report('pm10-level')
            self.o2_level = netlogo.report('o2-level')

    def atualizacao_air(self):
        """Atualiza os níveis dos gases e retorna 'Perigo' se algum limite for ultrapassado."""
        self.co_level = netlogo.report('co-level')
        self.co2_level = netlogo.report('co2-level')
        self.pm2_5_level = netlogo.report('pm2_5-level')
        self.pm10_level = netlogo.report('pm10-level')
        self.o2_level = netlogo.report('o2-level')
        if (self.o2_level <= 20000 or self.co_level >= 10 or 
            self.co2_level >= 1000 or self.pm10_level >= 100 or 
            self.pm2_5_level >= 100):
            return "Perigo"
        return "Seguro"

    def direction_wind(self):
        """Retorna a direção do vento formatada conforme o ângulo."""
        if self.wind_direction < 22.5 or self.wind_direction >= 337.5:
            return "Incêndio com vento em direção a Sul"
        elif 22.5 <= self.wind_direction < 67.5:
            return "Incêndio com vento em direção a Sudoeste"
        elif 67.5 <= self.wind_direction < 112.5:
            return "Incêndio com vento em direção a Oeste"
        elif 112.5 <= self.wind_direction < 157.5:
            return "Incêndio com vento em direção a Noroeste"
        elif 157.5 <= self.wind_direction < 202.5:
            return "Incêndio com vento em direção a Norte"
        elif 202.5 <= self.wind_direction < 247.5:
            return "Incêndio com vento em direção a Nordeste"
        elif 247.5 <= self.wind_direction < 292.5:
            return "Incêndio com vento em direção a Este"
        elif 292.5 <= self.wind_direction < 337.5:
            return "Incêndio com vento em direção a Sudeste"

class AnimalsAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.sensor = None
        self.detection = 0

    def set_sensor(self, direction):
        self.sensor = direction

    def alerta(self):
        """Verifica os níveis de fuga (escaped) e atualiza a detecção."""
        if netlogo.report('escaped-north') > 50 and self.sensor == "N":
            self.detection = 1
            return "Incêndio"
        elif netlogo.report('escaped-south') > 50 and self.sensor == "S":
            self.detection = 1
            return "Incêndio"
        elif netlogo.report('escaped-west') > 50 and self.sensor == "O":
            self.detection = 1
            return "Incêndio"
        elif netlogo.report('escaped-east') > 50 and self.sensor == "E":
            self.detection = 1
            return "Incêndio"
        else:
            self.detection = 0
            return "Sem incêndios"

class EnvironmentModel(mesa.Model):
    def __init__(self, n, width, height, seed=None):
        super().__init__(seed=seed)
        self.current_id = 0  # Contador para unique_id
        self.apagar_fogo_em_5_ticks = 0

        def create_animals_agents(model, directions):
            agents = []
            for direction in directions:
                agent = AnimalsAgent(unique_id=self.next_id(), model=model)
                agent.set_sensor(direction)
                agents.append(agent)
            return agents

        # Criar agentes com unique_id único
        self.air_agent = GenericAgent(unique_id=self.next_id(), model=self, agent_type="Air")
        self.wind_agent = GenericAgent(unique_id=self.next_id(), model=self, agent_type="Wind")

        directions = ["O", "E", "N", "S"]
        self.animals_agents = create_animals_agents(self, directions)
        self.oeste_agent = self.animals_agents[0]
        self.este_agent = self.animals_agents[1]
        self.norte_agent = self.animals_agents[2]
        self.sul_agent = self.animals_agents[3]

    def next_id(self):
        """Retorna um unique_id único."""
        self.current_id += 1
        return self.current_id

    def start_fire(self):
        netlogo.command('start-fire')

    def step(self):
        """Executa um passo da simulação."""
        netlogo.command('go')
        air_status = self.air_agent.atualizacao_air()
        
        # Atualiza o alerta de cada agente animal
        self.oeste_agent.alerta()
        self.este_agent.alerta()
        self.norte_agent.alerta()
        self.sul_agent.alerta()

        if air_status == "Perigo" and (
            self.oeste_agent.detection == 1 or
            self.este_agent.detection == 1 or
            self.norte_agent.detection == 1 or
            self.sul_agent.detection == 1
        ):
            if self.oeste_agent.detection == 1:
                print("Incêndio a Oeste\n")
            if self.este_agent.detection == 1:
                print("Incêndio a Este\n")
            if self.norte_agent.detection == 1:
                print("Incêndio a Norte\n")
            if self.sul_agent.detection == 1:
                print("Incêndio a Sul\n")
            print(self.wind_agent.direction_wind(), "\n")
            print("Vento com velocidade de", self.wind_agent.wind_speed, "m/s")
            self.apagar_fogo_em_5_ticks += 1
            if self.apagar_fogo_em_5_ticks == 5:
                netlogo.command('stop-fire')
        else:
            self.apagar_fogo_em_5_ticks = 0

# Criação do modelo
model = EnvironmentModel(5, 10, 10)

# Configuração inicial do NetLogo
netlogo.command('setup')

# --- Início do código da interface com ipywidgets ---
iterations_slider = widgets.IntSlider(
    value=200, 
    min=10, 
    max=500, 
    step=10,
    description='Iterações:',
    continuous_update=False
)

run_button = widgets.Button(
    description='Iniciar Simulação', 
    button_style='success',
    tooltip='Clique para iniciar a simulação'
)

output_area = widgets.Output()

def run_simulation(b):
    with output_area:
        clear_output()  # Limpa a saída anterior
        print("Preparando simulação...")
        # Reinicia o NetLogo, se necessário
        netlogo.command('setup')
        iterations = iterations_slider.value
        for i in range(iterations):
            print("Iteração:", i)
            # Com probabilidade de 30% inicia um incêndio
            if random.random() < 0.3:
                model.start_fire()
            model.step()
        print("Simulação finalizada!")
        # Se desejar encerrar a conexão, descomente a linha abaixo
        # netlogo.kill_workspace()

run_button.on_click(run_simulation)

display(widgets.VBox([iterations_slider, run_button, output_area]))
