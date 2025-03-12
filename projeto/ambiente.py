# ambiente.py
from mesa import Model
from mesa.space import MultiGrid
from agentes import AirAgent, PatchAgent
import random

class EnvironmentModel(Model):
    def __init__(self, width, height, density=0.8):
        """
        width, height: dimensões da grid
        density: fração de patches que estarão 'forested'
        """
        self.running = True
        self.world_width = width
        self.world_height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = []

        # Criação dos patches com base na densidade
        agent_id = 0
        for x in range(width):
            for y in range(height):
                patch = PatchAgent(agent_id, self, (x, y))
                if random.random() > density:
                    patch.state = "empty"
                    patch.pcolor = 0
                self.schedule.append(patch)
                self.grid.place_agent(patch, (x, y))
                agent_id += 1

        # Cria o agente de ar
        self.air_agent = AirAgent(agent_id, self)
        self.schedule.append(self.air_agent)

        # Parâmetro ambiental global
        self.temperature = 25.0
        
        # Inicializa parâmetros de vento com valores default
        self.wind_direction = 0   # Ex: 0 graus
        self.wind_speed = 2       # Ex: 2 m/s

    def step(self):
        for agent in self.schedule:
            agent.step()
        burning = sum(1 for agent in self.schedule if hasattr(agent, "state") and agent.state == "burning")
        self.temperature = 25.0 + burning * 0.5

    def start_fire(self):
        forested = [agent for agent in self.schedule if hasattr(agent, "state") and agent.state == "forested"]
        if forested:
            chosen = random.choice(forested)
            chosen.state = "burning"
            chosen.pcolor = 25

    def stop_fire(self):
        for agent in self.schedule:
            if hasattr(agent, "state") and agent.state == "burning":
                agent.state = "burned"
                agent.pcolor = 5
