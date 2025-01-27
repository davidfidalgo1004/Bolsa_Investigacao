import matplotlib.pyplot as plt
import pandas as pd
from mesa import Model, Agent
from mesa.time import RandomActivation
from pynetlogo import NetLogoLink

class FireAgent(Agent):
    """Agente que detecta e responde a incêndios."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.detected_fire = False

    def step(self):
        # Obter dados do NetLogo
        burned_trees = self.model.netlogo.report("burned-trees")
        if burned_trees > 0:
            self.detected_fire = True
            print(f"Agente {self.unique_id} detectou incêndio!")

class FireDetectionModel(Model):
    def __init__(self):
        # Definir caminho do modelo NetLogo
        netlogo_home = "/home/david-fidalgo/Transferências/NetLogo-6.4.0-64"  # Atualize para o seu caminho
        self.netlogo = NetLogoLink(gui=False, netlogo_home=netlogo_home)
        self.netlogo.load_model('simulacao.nlogo')  # Caminho para o seu arquivo .nlogo

        self.schedule = RandomActivation(self)

        # Criar agentes de monitoramento
        for i in range(5):
            agent = FireAgent(i, self)
            self.schedule.add(agent)

    def step(self):
        # Configurar parâmetros no NetLogo
        self.netlogo.command("setup")  # Chama o procedimento de setup no NetLogo
        self.netlogo.command("repeat 5 [ go ]")  # Executa 5 ciclos de simulação no NetLogo

        # Executar agentes no modelo de Mesa
        self.schedule.step()

    def run_model(self, steps=10):
        for _ in range(steps):
            self.step()

# Rodar a simulação
model = FireDetectionModel()
model.run_model(steps=10)

# Analisar dados do NetLogo
burned_trees = model.netlogo.report("burned-trees")
print(f"Total de árvores queimadas: {burned_trees}")
