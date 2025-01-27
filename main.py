# Importando as bibliotecas necessárias
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularVisualization

# Definição do Agente
class FireAgent(Agent):
    """ Um agente que pode estar em um estado de fogo ou não """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.fighting_fire = False  # Se o agente está combatendo o fogo

    def step(self):
        """ O agente alterna entre combater o fogo ou não """
        if self.fighting_fire:
            self.fighting_fire = False  # Desliga o combate ao fogo
        else:
            self.fighting_fire = True  # Liga o combate ao fogo

# Definição do Modelo
class FireModel(Model):
    """ Modelo de incêndio simples com uma grade e agentes """
    def __init__(self, width=10, height=10, num_agents=5):
        self.num_agents = num_agents
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        # Criando os agentes
        for i in range(self.num_agents):
            a = FireAgent(i, self)
            self.schedule.add(a)

            # Colocando os agentes aleatoriamente na grid
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        # Inicializando o DataCollector para coletar dados dos agentes
        self.datacollector = DataCollector(
            agent_reporters={"FightingFire": "fighting_fire"}
        )

    def step(self):
        """ Avança o modelo em um passo """
        self.datacollector.collect(self)
        self.schedule.step()

# Função para representar os agentes na interface
def agent_portrayal(agent):
    if agent.fighting_fire:
        portrayal = {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": "true",
            "Color": "red",  # Cor quando combatendo fogo
            "Layer": 0
        }
    else:
        portrayal = {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": "true",
            "Color": "green",  # Cor quando não combatendo fogo
            "Layer": 0
        }
    return portrayal

# Configuração da interface gráfica
grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)  # Tamanho da grid

# Criando o servidor da interface com a nova classe 'ModularVisualization'
model_params = {
    "width": 10,  # Largura da grid
    "height": 10,  # Altura da grid
    "num_agents": 5  # Número de agentes
}

# Configurando o servidor de visualização
visualization = ModularVisualization(
    FireModel, 
    [grid], 
    model_params=model_params
)
visualization.port = 8521  # Definindo a porta para o servidor
visualization.launch()  # Lançando o servidor
