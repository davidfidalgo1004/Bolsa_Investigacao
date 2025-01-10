from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt

class Sensor(Agent):
    """Agente sensor que detecta incêndios."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.detecting_fire = False

    def step(self):
        # Verifica as células vizinhas para detectar incêndio
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
        self.detecting_fire = any(isinstance(agent, Fire) for agent in neighbors)

class Fire(Agent):
    """Agente que representa um incêndio."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        # Espalha o incêndio com base em uma probabilidade
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
        for neighbor in neighbors:
            if self.random.random() < 0.2:  # 20% de chance de espalhar
                if not any(isinstance(agent, Fire) for agent in self.model.grid.get_cell_list_contents(neighbor)):
                    new_fire = Fire(self.model.next_id(), self.model)
                    self.model.grid.place_agent(new_fire, neighbor)
                    self.model.schedule.add(new_fire)

class FireModel(Model):
    """Modelo de detecção de incêndios."""
    def __init__(self, width, height, num_sensors):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)

        # Adiciona sensores
        for i in range(num_sensors):
            sensor = Sensor(self.next_id(), self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(sensor, (x, y))
            self.schedule.add(sensor)

        # Adiciona incêndio inicial
        fire = Fire(self.next_id(), self)
        self.grid.place_agent(fire, (width // 2, height // 2))
        self.schedule.add(fire)

        # Coletor de dados
        self.datacollector = DataCollector(
            model_reporters={"Sensores Detectando Fogo": self.count_sensors_detecting_fire}
        )

    def count_sensors_detecting_fire(self):
        """Conta os sensores que detectam incêndio."""
        return sum([agent.detecting_fire for agent in self.schedule.agents if isinstance(agent, Sensor)])

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

# Configurar e executar o modelo
model = FireModel(20, 20, 50)

for i in range(20):
    model.step()

# Resultados
results = model.datacollector.get_model_vars_dataframe()

# Visualizar os resultados
results.plot(title="Sensores Detectando Incêndio")
plt.xlabel("Passos de Simulação")
plt.ylabel("Número de Sensores Detectando Fogo")
plt.show()
