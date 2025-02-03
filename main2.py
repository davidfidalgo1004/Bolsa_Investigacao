import pynetlogo
import random
import mesa
import ipywidgets as widgets
from IPython.display import display
from mesa.visualization import Slider
# Data visualization tools.
import seaborn as sns

# Has multi-dimensional arrays and matrices. Has a large collection of
# mathematical functions to operate on these arrays.
import numpy as np

# Data manipulation and analysis.
import pandas as pd

import matplotlib.pyplot as plt  # Importar matplotlib

from mesa.visualization import (
    SolaraViz,
    make_plot_component,
    make_space_component,
)

# Inicializar conexão com NetLogo
netlogo = pynetlogo.NetLogoLink(gui=False, netlogo_home=r'C:\Program Files\NetLogo 6.4.0')
netlogo.load_model(r'C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo')


class GenericAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, model, agent_type):
        super().__init__(model)
        self.wealth = 1
        self.agent_type = agent_type
        if (agent_type == "Wind"):
            self.wind_speed = 10
            self.wind_direction = 15
            netlogo.command(f"set wind-speed {self.wind_speed}")
            netlogo.command(f"set wind-direction {self.wind_direction}")
        if (agent_type == "Air"):
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
            if(self.o2_level <= 20000 or self.co_level >= 10 or self.co2_level>=1000 or self.pm10_level>=100 or self.pm2_5_level >=100):
                return "Perigo"
    def DirectionWind(self):
        if (self.wind_direction <22.5 or self.wind_direction>=337.5):
            return "Incendio com vento em direção a Sul"
        if (self.wind_direction >=22.5 and self.wind_direction<67.5):
            return "Incendio com vento em direção a Sudoeste"
        if (self.wind_direction >=67.5 and self.wind_direction<112.5):
            return "Incendio com vento em direção a Oeste"
        if (self.wind_direction >=112.5 and self.wind_direction<157.5):
            return "Incendio com vento em direção a Noroeste"
        if (self.wind_direction >=157.5 and self.wind_direction<202.5):
            return "Incendio com vento em direção a Norte"
        if (self.wind_direction >=202.5 and self.wind_direction<247.5):
            return "Incendio com vento em direção a Nordeste"
        if (self.wind_direction >=247.5 and self.wind_direction<292.5):
            return "Incendio com vento em direção a Este"
        if (self.wind_direction >=292.5 and self.wind_direction<337.5):
            return "Incendio com vento em direção a Sudeste"



class AnimalsAgent(mesa.Agent):
    """Agente animal com um sensor de direção."""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.Sensor = None
        self.Detetation = 0

    def definition(self, Direction):
        """Define a direção do sensor do agente."""
        self.Sensor = Direction

    def Alerta(self):
        if netlogo.report('escaped-north')>50 and self.Sensor == "N":
            self.Detetation = 1
            return "Incendio"
        if netlogo.report('escaped-south')>50 and self.Sensor == "S":
            self.Detetation = 1
            return "Incendio"
        if netlogo.report('escaped-west')>50 and self.Sensor == "O":
            self.Detetation = 1
            return "Incendio"
        if netlogo.report('escaped-east')>50 and self.Sensor == "E":
            self.Detetation = 1
            return "Incendio"
        else:
            self.Detetation = 0
            return "Sem incendios"
        


class EnvironmentModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, seed=None):
        super().__init__(seed=seed)
        def create_animals_agents(model, directions): #criar os sensores
            agents = {}
            for direction in directions:
                agent = AnimalsAgent(model)
                agent.definition(direction)
                agents[direction] = agent
            return agents
        #self.schedule = mesa.time.BaseScheduler(self)
        #self.grid = mesa.space.MultiGrid(10, 10, torus=True)
        #self.num_agents = n
        #self.grid = mesa.space.MultiGrid(width, height, True)
        #para tornar mais eficaz e menos pesado
        self.AirAgent = GenericAgent(self, "Air")
        self.VentoAgent = GenericAgent(self, "Wind")
        
        directions = ["O", "E", "N", "S"]
        self.animals_agents = create_animals_agents(directions) #guarda os agentes de sensor de animais num dicionario
        self.oeste_agent = self.animals_agents[0]
        self.este_agent = self.animals_agents[1]
        self.norte_agent = self.animals_agents[2]
        self.sul_agent = self.animals_agents[3]

    def StartFire(self):
        netlogo.command('start-fire')

    def FinishFire(self):
        netlogo.command('stop-fire')

    def step(self):
        netlogo.command('go')
        if(self.AirAgent.AtualizacaoAir() == "Perigo" and (self.oeste_agent.Alerta() != "Sem incendio" or self.este_agent.Alerta() != "Sem incendio" or self.norte_agent.Alerta() != "Sem incendio" or self.sul_agent.Alerta() != "Sem incendio")):
            if (self.oeste_agent.Detetation == 1):
                print("Incendio a Oeste\n")
                print(self.VentoAgent.DirectionWind(),"\n")
                print("Vento com velocidade de ", self.VentoAgent.wind_speed, "m/s")


model= EnvironmentModel()

for i in range(200):
    if random.random < 0.3:
        model.StartFire()
    model.step()
    if random.random < 0.4:
        model.FinishFire()


