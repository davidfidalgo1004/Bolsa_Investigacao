import mesa

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

class AirLevelsAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, model):
        super().__init__(model)
        self.wealth = 1

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def give_money(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        # Ensure agent is not giving money to itself
        cellmates.pop(cellmates.index(self))
        if len(cellmates) > 0:
            other_agent = self.random.choice(cellmates)
            other_agent.wealth += 1
            self.wealth -= 1

class EnvironmentAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, model):
        super().__init__(model)
        self.wealth = 1

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def give_money(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        # Ensure agent is not giving money to itself
        cellmates.pop(cellmates.index(self))
        if len(cellmates) > 0:
            other_agent = self.random.choice(cellmates)
            other_agent.wealth += 1
            self.wealth -= 1

class WindAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, model):
        super().__init__(model)
        self.wealth = 1

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def give_money(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        # Ensure agent is not giving money to itself
        cellmates.pop(cellmates.index(self))
        if len(cellmates) > 0:
            other_agent = self.random.choice(cellmates)
            other_agent.wealth += 1
            self.wealth -= 1

class AnimalsAgent(mesa.Agent):
    """Agente animal com um sensor de direção."""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.Sensor = None

    def definition(self, Direction):
        """Define a direção do sensor do agente."""
        self.Sensor = Direction


class EnvironmentModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, n, width, height, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        self.grid = mesa.space.MultiGrid(width, height, True)

        # Create agents
        self.AirAgent = AirLevelsAgent.create_agents(model=self, n=1)
        self.VentoAgent = WindAgent.create_agents(model=self, n=1)
        self.AnimaisAgentOeste = AnimalsAgent(self)
        self.AnimaisAgentOeste.definition("O")
        self.AnimaisAgentEste = AnimalsAgent(self)
        self.AnimaisAgentEste.definition("E")
        self.AnimaisAgentNorte = AnimalsAgent(self)
        self.AnimaisAgentNorte.definition("N")
        self.AnimaisAgentSul = AnimalsAgent(self)
        self.AnimaisAgentSul.definition("S")

    def step(self):
        self.agents.shuffle_do("move")
        self.agents.do("give_money")



model = EnvironmentModel(100, 10, 10)

for i in range(200):
    model.step()

