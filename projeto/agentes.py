import math
import random
from mesa import Agent
from ProbVento import Ignicaoprob

class PatchAgent(Agent):
    def __init__(self, unique_id, model, pos):
        self.unique_id = unique_id
        self.model = model
        self.pos = pos
        self.state = "forested"
        self.pcolor = 55  # Cor verde para patch florestado
        # Define a altitude para o patch (valor entre 0 e 100)
        # consideramos tudo com altitude 0 -> Rio
        self.altitude = random.uniform(1, 100)
        # Para patches florestados, define a altura da árvore (entre 5 e 15)
        if self.state == "forested":
            self.tree_height = random.uniform(5, 15)
        else:
            self.tree_height = 0
        self.burn_time = None

    def startfirepatch(self, patch):
        patch.state = "burning"
        patch.pcolor = 15
        patch.burn_time = None
    
    def step(self):
        if self.state == "burning":
            if self.burn_time is None:
                self.burn_time = random.randint(5, 8)
                self.pcolor = 15  # Indica que está queimando

            raio = 2
            cx, cy = self.pos

            min_x = max(0, cx - raio)
            max_x = min(self.model.world_width - 1, cx + raio)
            min_y = max(0, cy - raio)
            max_y = min(self.model.world_height - 1, cy + raio)

            alfadistancia=0.2
            alfaaltitude=0.05
            alfahumidade=0.3
            alfaprecipitação=0.4
            alfadirecaovelocidadevento=0.1
            alfaalturaarvore = 0.05

            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    distancia = math.sqrt((x - cx)**2 + (y - cy)**2)
                    if distancia <= raio and distancia>0:
                        # Probabilidade base decai linearmente com a distância
                        base_prob = (1/distancia)

                        # Fatores ambientais:
                        # 1) Altitude: quanto maior a altitude, maior o fator (mais seco)
                        altitude_factor = (1/self.altitude) * alfaaltitude
                        
                        # 2) Precipitação: quanto maior a chuva, menor a chance de queimar
                        precip_factor = (1 - self.model.rain_level) * alfaprecipitação

                        # 3) Altura da árvore
                        height_factor = self.tree_height * alfaalturaarvore

                        # 4) Humidade

                        humidity_factor = (1/self.model.humidity) *alfahumidade

                        # 5) Vento
                        wind_factor = Ignicaoprob(1, self.model.wind_speed,cx,cy,x,y,self.model.wind_direction) * alfadirecaovelocidadevento
                        # Somatorio  dos fatores
                        combined_factor = wind_factor + altitude_factor + precip_factor + height_factor + humidity_factor

                        #a base probabilistica tem a haver que quanto mais longe, menos probabilidade há para um determinado patch arder
                        final_prob = base_prob * combined_factor

                        patches = self.model.grid.get_cell_list_contents((x, y))
                        for patch in patches:
                            if getattr(patch, "state", None) == "forested":
                                if random.random() < final_prob:
                                    patch.state = "burning"
                                    patch.pcolor = 15
                                    patch.burn_time = None

            self.burn_time -= 1
            if self.burn_time <= 0:
                self.state = "burned"
                self.pcolor = 5  # Cor para patch queimado (cinza)

class AirAgent(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.co_level = 0.1         # Monóxido de Carbono (CO)
        self.co2_level = 400.0      # Dióxido de Carbono (CO₂)
        self.pm2_5_level = 25.0     # Partículas PM2.5
        self.pm10_level = 10.0      # Partículas PM10
        self.o2_level = 21000.0     # Oxigênio (O₂)

    def step(self):
        burning = sum(1 for agent in self.model.schedule if hasattr(agent, "state") and agent.state == "burning")
        
        target_co = 0.1 + burning * 2.0
        target_co2 = 400.0 + burning * 5.0
        target_pm2_5 = 25.0 + burning * 1.0
        target_pm10 = 10.0 + burning * 1.0
        target_o2 = max(21000.0 - burning * 10.0, 15000.0)
        
        decay = 0.1
        
        self.co_level += (target_co - self.co_level) * decay
        self.co2_level += (target_co2 - self.co2_level) * decay
        self.pm2_5_level += (target_pm2_5 - self.pm2_5_level) * decay
        self.pm10_level += (target_pm10 - self.pm10_level) * decay
        self.o2_level += (target_o2 - self.o2_level) * decay

    def get_air_status(self):
        if (self.o2_level <= 20000 or self.co_level >= 10 or 
            self.co2_level >= 1000 or self.pm10_level >= 100 or 
            self.pm2_5_level >= 100):
            return "Perigo"
        return "Seguro"
