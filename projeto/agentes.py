import math
import random
from mesa import Agent
from ProbVento import Ignicaoprob

class PatchAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.tree_type = "NA"
        self.unique_id = unique_id
        self.model = model
        self.pos = pos
        self.state = "forested"
        self.pcolor = 55  # Cor verde para patch florestado
        self.factor_type_tree = 0
        # Define a altitude para o patch (valor entre 0 e 100)
        self.altitude = self.calculate_altitude(pos[0], pos[1])

        # Para patches florestados, define a altura da árvore (entre 5 e 15)
        if self.state == "forested":
            self.tree_height = random.uniform(5, 15)
        else:
            self.tree_height = 0

        self.burn_time = None

    def calculate_altitude(self, x, y):
        """
        Calcula a altitude de forma mais realista, sem depender de rios ou estradas fixos.
        """
        # Criar variação suave da altitude usando senos/cossenos e ruído
        altitude_variation = (
            math.sin(x / self.model.world_width * math.pi)
            + math.cos(y / self.model.world_height * math.pi)
        ) * 20
        noise = random.uniform(-5, 5)
        altitude = max(0, altitude_variation + noise)
        return altitude

    def startfirepatch(self, patch):
        """Inicia fogo em um patch específico."""
        patch.state = "burning"
        patch.pcolor = 15
        patch.burn_time = None

    def step(self):
        """Lógica principal de queima de cada patch se estiver em combustão."""
        if self.state == "burning":
            if self.burn_time is None:
                if self.tree_type == "eucalyptus":
                    self.burn_time = random.randint(2, 4)
                else:
                    self.burn_time = random.randint(4, 6)
                self.pcolor = 15  # Indica que está a queimar

            # O raio de propagação depende da velocidade do vento
            raio = 1 + round(self.model.wind_speed / 10)
            cx, cy = self.pos

            min_x = max(0, cx - raio)
            max_x = min(self.model.world_width - 1, cx + raio)
            min_y = max(0, cy - raio)
            max_y = min(self.model.world_height - 1, cy + raio)

            alfaaltitude = 0.05
            alfahumidade = 0.3
            alfaprecip = 0.4
            alfavento = 0.1
            alfaaltura = 0.05

            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    distancia = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    if distancia <= raio:
                        # Probabilidade base decai com a distância
                        base_prob = 1 if distancia <= 0 else (1 / distancia)

                        # Ajustes ambientais
                        if self.altitude <= 0:
                            altitude_factor = alfaaltitude
                        else:
                            altitude_factor = (1 / self.altitude) * alfaaltitude

                        precip_factor = (1 - self.model.rain_level) * alfaprecip
                        height_factor = self.tree_height * alfaaltura
                        humidity_factor = (1 / self.model.humidity) * alfahumidade

                        wind_factor = Ignicaoprob(
                            1,
                            self.model.wind_speed,
                            cx,
                            cy,
                            x,
                            y,
                            self.model.wind_direction,
                        ) * alfavento

                        combined_factor = (
                            altitude_factor
                            + precip_factor
                            + height_factor
                            + humidity_factor
                            + wind_factor
                        )
                        final_prob = base_prob * combined_factor * self.factor_type_tree

                        patches = self.model.grid.get_cell_list_contents((x, y))
                        for patch in patches:
                            if getattr(patch, "state", None) == "forested" or getattr(patch, "state", None) == "dangered":
                                # Aleatoriedade extra
                                numrandom = random.choice([random.random() for _ in range(3)])
                                if numrandom < final_prob:
                                    patch.state = "burning"
                                    patch.pcolor = 15
                                    patch.burn_time = None
                                else:
                                    patch.state = "dangered"
                                    patch.pcolor = 45
                                    

            # Tempo de queima diminui a cada step
            self.burn_time -= 1
            if self.burn_time <= 0:
                self.state = "burned"
                self.pcolor = 5  # Cor para patch queimado (cinza)

class AirAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.unique_id = unique_id
        self.co_level = 0.1         # Monóxido de Carbono (CO)
        self.co2_level = 400.0      # Dióxido de Carbono (CO₂)
        self.pm2_5_level = 25.0     # Partículas PM2.5
        self.pm10_level = 10.0      # Partículas PM10
        self.o2_level = 21000.0     # Oxigênio (O₂)

    def step(self):
        """A cada passo, ajusta a qualidade do ar conforme a quantidade de fogo."""
        burning = sum(1 for agent in self.model.schedule if getattr(agent, "state", None) == "burning")

        # Alvos de poluentes conforme o número de burning
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
        """Retorna 'Perigo' se a qualidade do ar estiver ruim; caso contrário, 'Seguro'."""
        if (
            self.o2_level <= 20000
            or self.co_level >= 10
            or self.co2_level >= 1000
            or self.pm10_level >= 100
            or self.pm2_5_level >= 100
        ):
            return "Perigo"
        return "Seguro"
