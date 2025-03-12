import random  # Para operações probabilísticas
from mesa import Agent  # Importa a classe base Agent da Mesa

import math
import random
from mesa import Agent

class PatchAgent(Agent):
    def __init__(self, unique_id, model, pos):
        self.unique_id = unique_id
        self.model = model
        self.pos = pos
        self.state = "forested"
        self.pcolor = 55  # Cor verde para florestado
        # Define a altitude para todos os patches
        self.altitude = random.uniform(0, 100)
        # Para patches florestados, define a altura da árvore
        if self.state == "forested":
            self.tree_height = random.uniform(5, 15)
        else:
            self.tree_height = 0
        self.burn_time = None

    def step(self):
        if self.state == "forested":
            # Aqui você pode deixar a ignição "passiva" – ou seja, ser incendiado pelos vizinhos.
            pass

        elif self.state == "burning":
            # Inicializa o tempo de queima se ainda não estiver definido
            if self.burn_time is None:
                self.burn_time = random.randint(5, 8)
                self.pcolor = 25  # vermelho para indicar que está queimando

            # Propaga o fogo para vizinhos na vizinhança (raio 2)
            neighbors = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False, radius=2
            )
            for neighbor in neighbors:
                if hasattr(neighbor, "state") and neighbor.state == "forested":
                    # Obter parâmetros ambientais do modelo (ou usar defaults)
                    wind_direction = getattr(self.model, "wind_direction", 0)
                    wind_speed = getattr(self.model, "wind_speed", 2)
                    rain_level = getattr(self.model, "rain_level", 0)

                    # Calcular ângulo do patch atual para o vizinho
                    dx = neighbor.pos[0] - self.pos[0]
                    dy = neighbor.pos[1] - self.pos[1]
                    angle_to_neighbor = (math.degrees(math.atan2(dy, dx)) + 360) % 360
                    # Calcula a menor diferença angular
                    angle_diff = abs((wind_direction - angle_to_neighbor + 180) % 360 - 180)
                    is_wind_favored = angle_diff <= 60

                    # Obter alturas e altitudes (usar valores padrão se não definidos)
                    source_height = getattr(self, "tree_height", 10)
                    neighbor_height = getattr(neighbor, "tree_height", 10)
                    source_altitude = getattr(self, "altitude", 50)
                    neighbor_altitude = getattr(neighbor, "altitude", 50)

                    # Multiplicador baseado na diferença de altura
                    tree_multiplier = max(0.1, 1 + (source_height - neighbor_height) / 10)
                    # Multiplicador baseado na diferença de altitude
                    alt_multiplier = max(0.1, 1 + (source_altitude - neighbor_altitude) / 100)

                    # Calcular probabilidade base
                    if is_wind_favored:
                        # Função semelhante a calc-wind-probability do NetLogo
                        base_prob = min(0.3 + wind_speed * 0.05, 0.8) * tree_multiplier * 2.0
                    else:
                        base_prob = 0.3 * tree_multiplier * 2.0

                    effective_prob = base_prob * alt_multiplier * (1 - rain_level)

                    if random.random() < effective_prob:
                        # Incendeia o vizinho
                        neighbor.state = "burning"
                        neighbor.pcolor = 25
                        neighbor.burn_time = None

            # Atualiza o tempo de queima e, se terminar, muda para "burned"
            self.burn_time -= 1
            if self.burn_time <= 0:
                self.state = "burned"
                self.pcolor = 5  # cor para queimado (cinza)

        # Se o patch estiver "burned" ou em outro estado, não realiza ação


class AirAgent(Agent):
    def __init__(self, unique_id, model):
        # Inicializa os atributos do agente de ar
        self.unique_id = unique_id  # Identificador único
        self.model = model          # Referência ao modelo
        # Define os níveis iniciais dos poluentes e oxigênio
        self.co_level = 0.1         # Nível de monóxido de carbono (CO)
        self.co2_level = 400.0      # Nível de dióxido de carbono (CO₂), valor base
        self.pm2_5_level = 25.0      # Nível de partículas PM2.5
        self.pm10_level = 10.0       # Nível de partículas PM10
        self.o2_level = 21000.0     # Nível de oxigênio (O₂)

    def step(self):
        # Conta quantos patches estão em estado "burning" na simulação
        burning = sum(1 for agent in self.model.schedule if hasattr(agent, "state") and agent.state == "burning")
        # Atualiza os níveis dos poluentes proporcionalmente ao número de patches em chamas
        self.co_level = 0.1 + burning * 2.0
        self.co2_level = 400.0 + burning * 5.0
        self.pm2_5_level = 25 + burning * 1.0
        self.pm10_level = 10 + burning * 1.0
        # O nível de oxigênio diminui com o aumento do fogo, mas não pode ser inferior a 15000
        self.o2_level = max(21000.0 - burning * 10.0, 15000.0)

    def get_air_status(self):
        # Verifica se algum dos parâmetros ultrapassa os limites de segurança
        if (self.o2_level <= 20000 or self.co_level >= 10 or 
            self.co2_level >= 1000 or self.pm10_level >= 100 or 
            self.pm2_5_level >= 100):
            return "Perigo"  # Condições de ar perigosas
        return "Seguro"  # Caso contrário, as condições são seguras
