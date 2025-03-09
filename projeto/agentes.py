import random
from mesa import Agent

class PatchAgent(Agent):
    def __init__(self, unique_id, model, pos):
        # Inicializa manualmente os atributos necessários
        self.unique_id = unique_id
        self.model = model
        self.pos = pos  # Posição na grid
        self.state = "forested"  # Possíveis estados: "forested", "burning", "burned"
        self.pcolor = 55  # Valor inicial que mapeia para "verde"

    def step(self):
        if self.state == "forested":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=False)
            if any(neighbor.state == "burning" for neighbor in neighbors):
                if random.random() < 0.3:
                    self.state = "burning"
                    self.pcolor = 25  # Valor para fogo (laranja)
        elif self.state == "burning":
            self.state = "burned"
            self.pcolor = 5  # Valor para queimado (cinzento)

class AirAgent(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.co_level = 0.0
        self.co2_level = 400.0
        self.pm2_5_level = 0.0
        self.pm10_level = 0.0
        self.o2_level = 21000.0

    def step(self):
        burning = sum(1 for agent in self.model.schedule if hasattr(agent, "state") and agent.state == "burning")
        self.co_level = burning * 2.0
        self.co2_level = 400.0 + burning * 5.0
        self.pm2_5_level = burning * 1.0
        self.pm10_level = burning * 1.0
        self.o2_level = max(21000.0 - burning * 10.0, 15000.0)

    def get_air_status(self):
        if (self.o2_level <= 20000 or self.co_level >= 10 or 
            self.co2_level >= 1000 or self.pm10_level >= 100 or 
            self.pm2_5_level >= 100):
            return "Perigo"
        return "Seguro"
