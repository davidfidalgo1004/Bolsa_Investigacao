import pynetlogo  # Importação correta
import os
from mesa import Agent, Model
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.time import SimultaneousActivation

# Caminho para o modelo NetLogo
script_dir = os.path.dirname(os.path.abspath(__file__))
netlogo_model_path = os.path.join(script_dir, 'Fire.nlogo')
netlogo_home = '/opt/netlogo'  # Ajuste conforme sua instalação do NetLogo

# Inicializar a conexão com NetLogo (sem o argumento netlogo_version)
netlogo = pynetlogo.NetLogoLink(gui=True, netlogo_home=netlogo_home)

# Carregar o modelo NetLogo
netlogo.load_model(netlogo_model_path)
netlogo.command('set density 60')  # Configurar densidade inicial
netlogo.command('setup')  # Inicializar NetLogo

# Definição dos estados das células
EMPTY, TREE, BURNING = 0, 1, 2

class FireCell(Agent):
    """Célula da floresta visualizada na interface Mesa."""

    def __init__(self, pos, model, state=EMPTY):
        super().__init__(pos, model)
        self.pos = pos
        self.state = state

    def step(self):
        """Os estados das células serão atualizados com base no NetLogo."""
        pass

class FireModel(Model):
    """Modelo de incêndio para integração com NetLogo e visualização na Mesa."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[FireCell((x, y), self, TREE) for y in range(height)] for x in range(width)]
        self.schedule = SimultaneousActivation(self)

        # Adicionar todas as células ao agendador
        for row in self.grid:
            for cell in row:
                self.schedule.add(cell)

    def step(self):
        """Atualiza o estado das células com dados do NetLogo."""
        netlogo.command('go')  # Executa um passo no NetLogo
        
        for agent in self.schedule.agents:
            x, y = agent.pos

            # Captura a cor da célula no NetLogo (representando estado)
            patch_color = netlogo.report(f"[pcolor] of patch {x - self.width//2} {y - self.height//2}")

            if patch_color == 55:  # Verde (árvore)
                agent.state = TREE
            elif patch_color == 15:  # Vermelho (fogo)
                agent.state = BURNING
            else:
                agent.state = EMPTY
        
        print(f"Passo atualizado na Mesa com dados do NetLogo")

def cell_portrayal(agent):
    """Define as cores para a visualização do estado das células."""
    if agent.state == EMPTY:
        color = "black"
    elif agent.state == TREE:
        color = "green"
    elif agent.state == BURNING:
        color = "red"

    return {"Shape": "rect", "Color": color, "Filled": True, "Layer": 0, "w": 1, "h": 1}

# Dimensões do modelo com base na simulação NetLogo
width, height = 20, 20

# Criar visualização usando a biblioteca Mesa
grid = CanvasGrid(cell_portrayal, width, height, 500, 500)
server = ModularServer(FireModel, [grid], "Visualização do Incêndio (Mesa)", {"width": width, "height": height})

if __name__ == "__main__":
    server.launch()
