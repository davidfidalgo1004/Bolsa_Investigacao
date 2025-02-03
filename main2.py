import pynetlogo
import random
import mesa
import ipywidgets as widgets
from IPython.display import display
from mesa.visualization import Slider
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
        # Em vez de chamar super().__init__, atribuímos os atributos manualmente:
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

    
    def AtualizacaoAir(self):
        self.co_level = netlogo.report('co-level')
        self.co2_level = netlogo.report('co2-level')
        self.pm2_5_level = netlogo.report('pm2_5-level')
        self.pm10_level = netlogo.report('pm10-level')
        self.o2_level = netlogo.report('o2-level')
        if self.o2_level <= 20000 or self.co_level >= 10 or self.co2_level >= 1000 or self.pm10_level >= 100 or self.pm2_5_level >= 100:
            return "Perigo"
    
    def DirectionWind(self):
        if self.wind_direction < 22.5 or self.wind_direction >= 337.5:
            return "Incendio com vento em direção a Sul"
        if 22.5 <= self.wind_direction < 67.5:
            return "Incendio com vento em direção a Sudoeste"
        if 67.5 <= self.wind_direction < 112.5:
            return "Incendio com vento em direção a Oeste"
        if 112.5 <= self.wind_direction < 157.5:
            return "Incendio com vento em direção a Noroeste"
        if 157.5 <= self.wind_direction < 202.5:
            return "Incendio com vento em direção a Norte"
        if 202.5 <= self.wind_direction < 247.5:
            return "Incendio com vento em direção a Nordeste"
        if 247.5 <= self.wind_direction < 292.5:
            return "Incendio com vento em direção a Este"
        if 292.5 <= self.wind_direction < 337.5:
            return "Incendio com vento em direção a Sudeste"

class AnimalsAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.Sensor = None
        self.Detetation = 0


    def definition(self, Direction):
        self.Sensor = Direction

    def Alerta(self):
        if netlogo.report('escaped-north') > 50 and self.Sensor == "N":
            self.Detetation = 1
            return "Incendio"
        elif netlogo.report('escaped-south') > 50 and self.Sensor == "S":
            self.Detetation = 1
            return "Incendio"
        elif netlogo.report('escaped-west') > 50 and self.Sensor == "O":
            self.Detetation = 1
            return "Incendio"
        elif netlogo.report('escaped-east') > 50 and self.Sensor == "E":
            self.Detetation = 1
            return "Incendio"
        else:
            self.Detetation = 0
            return "Sem incendios"

class EnvironmentModel(mesa.Model):
    def __init__(self, n, width, height, seed=None):
        super().__init__(seed=seed)
        self.current_id = 0  # Contador para unique_id
        self.apagarfogoem5ticks = 0

        def create_animals_agents(model, directions):
            agents = []
            for direction in directions:
                agent = AnimalsAgent(unique_id=self.next_id(), model=model)  # Usar next_id para unique_id
                agent.definition(direction)
                agents.append(agent)
            return agents
        
        # Criar agentes com unique_id único
        self.AirAgent = GenericAgent(unique_id=self.next_id(), model=self, agent_type="Air")
        self.VentoAgent = GenericAgent(unique_id=self.next_id(), model=self, agent_type="Wind")
        
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

    def StartFire(self):
        netlogo.command('start-fire')


    def step(self):
        netlogo.command('go')
        self.AirAgent.AtualizacaoAir()
        self.oeste_agent.Alerta()
        self.este_agent.Alerta()
        self.norte_agent.Alerta()
        self.sul_agent.Alerta()

        if self.AirAgent.AtualizacaoAir() == "Perigo" and (
            self.oeste_agent.Detetation == 1 or
            self.este_agent.Detetation == 1 or
            self.norte_agent.Detetation == 1 or
            self.sul_agent.Detetation == 1
        ):
            if self.oeste_agent.Detetation == 1:
                print("Incendio a Oeste\n")
            if self.este_agent.Detetation == 1:
                print("Incendio a Este\n")
            if self.norte_agent.Detetation == 1:
                print("Incendio a Norte\n")
            if self.sul_agent.Detetation == 1:
                print("Incendio a Sul\n")
            print(self.VentoAgent.DirectionWind(), "\n")
            print("Vento com velocidade de ", self.VentoAgent.wind_speed, "m/s")
            self.apagarfogoem5ticks = self.apagarfogoem5ticks + 1
            if (self.apagarfogoem5ticks == 5):
                netlogo.command('stop-fire')
        else:
            self.apagarfogoem5ticks = 0

model = EnvironmentModel(5, 10, 10)
netlogo.command('setup')
for i in range(200):
    print("iteracao:", i, "\n")
    if random.random() < 0.3:
        model.StartFire()
    model.step()


netlogo.kill_workspace()