from mesa import Model
from mesa.space import MultiGrid
from agentes import AirAgent, PatchAgent
import random

class EnvironmentModel(Model):
    def __init__(self, width, height):
        self.running = True
        self.world_width = width
        self.world_height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = []  # Nosso scheduler simples: lista de agentes

        # Cria agentes patch para cada célula da grid
        agent_id = 0
        for x in range(width):
            for y in range(height):
                patch = PatchAgent(agent_id, self, (x, y))
                self.schedule.append(patch)
                self.grid.place_agent(patch, (x, y))
                agent_id += 1

        # Cria o agente de ar (para monitorar os níveis ambientais)
        self.air_agent = AirAgent(agent_id, self)
        self.schedule.append(self.air_agent)

        # Parâmetro ambiental global, por exemplo, a temperatura
        self.temperature = 25.0

    def step(self):
        # Atualiza todos os agentes sequencialmente
        for agent in self.schedule:
            agent.step()

        # Atualiza parâmetros globais com base nos patches queimados
        burning = sum(1 for agent in self.schedule if hasattr(agent, "state") and agent.state == "burning")
        self.temperature = 25.0 + burning * 0.5

    def start_fire(self):
        # Seleciona um patch florestado aleatório para iniciar o fogo
        forested = [agent for agent in self.schedule if hasattr(agent, "state") and agent.state == "forested"]
        if forested:
            chosen = random.choice(forested)
            chosen.state = "burning"
            chosen.pcolor = 25

    def stop_fire(self):
        # Apaga o fogo transformando os patches em queimados
        for agent in self.schedule:
            if hasattr(agent, "state") and agent.state == "burning":
                agent.state = "burned"
                agent.pcolor = 5
