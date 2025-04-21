import math
import random
from mesa import Agent
from ProbVento import Ignicaoprob

class FragulhaAgent(Agent):
    def __init__(self, unique_id, model, origin_pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.model = model
        
        # Posição inicial e trajetória
        self.origin_pos = origin_pos
        self.pos = origin_pos
        self.path = [origin_pos]  # Guarda histórico de posições

        self.pcolor = 105
        self.new_pos = self.compute_target_position()

    def compute_target_position(self):
        """Calcula a nova posição da fagulha baseada no vento."""
        ox, oy = self.origin_pos
        angle = math.radians(self.model.wind_direction)
        dist = random.uniform(2, 6) * max(self.model.wind_speed, 1)
        dx = int(round(math.sin(angle) * dist))
        dy = int(round(-math.cos(angle) * dist))
        nx = min(max(ox + dx, 0), self.model.world_width - 1)
        ny = min(max(oy + dy, 0), self.model.world_height - 1)
        return (nx, ny)

    def step(self):
        # Move-se para a new_pos
        x, y = self.new_pos
        self.pos = (x, y)
        self.path.append((x, y))  # Registra no histórico

        # Probabilidade de incendiar o patch se ele estiver florestado
        alfahumidade = 0.35
        alfaprecip = 0.35
        alfafragulhaqueda = 0.3
        ignition_chance = (
            alfafragulhaqueda
            + (1 - self.model.rain_level) * alfaprecip
            + (1 / self.model.humidity) * alfahumidade
        )

        # Verifica o patch onde caiu
        patches = self.model.grid.get_cell_list_contents((x, y))
        for patch in patches:
            # Se for floresta, há probabilidade de incendiar
            if getattr(patch, "state", None) == "forested":
                if random.random() < ignition_chance:
                    patch.state = "burning"
                    patch.pcolor = 15
                    patch.burn_time = None
                # senão, não incendeia
                break  # Basta afetar um PatchAgent na célula

        # Salva o trajeto final da fagulha no dicionário do modelo
        self.model.fragulha_history[self.unique_id] = self.path

        # Remove a fagulha do scheduler e da grelha
        if self in self.model.schedule:
            try:
                self.model.schedule.remove(self)
            except ValueError:
                pass
        try:
            self.model.grid.remove_agent(self)
        except ValueError:
            pass


class PatchAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.model = model
        self.pos = pos

        self.state = "forested"
        self.pcolor = 55  # Verde
        self.tree_type = "NA"
        self.factor_type_tree = 0
        self.burn_time = None

        # Define altitude
        self.altitude = self.calculate_altitude(pos[0], pos[1])
        self.dangered_time = 0

        # Altura da árvore (se florestado)
        if self.state == "forested":
            self.tree_height = random.uniform(5, 15)
        else:
            self.tree_height = 0

    def calculate_altitude(self, x, y):
        """
        Calcula a altitude de forma procedural.
        """
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
        if self.state == "dangered":
            self.dangered_time += 1
            if self.dangered_time >= 10:
                self.state = "forested"
                self.pcolor = 55
                self.dangered_time = 0
            return

        if self.state == "burning":
            if self.burn_time is None:
                # Define tempo de queima baseado no tipo
                if self.tree_type == "eucalyptus":
                    self.burn_time = random.randint(2, 4)
                else:
                    self.burn_time = random.randint(4, 6)
                self.pcolor = 15

            raio = 1 + round(self.model.wind_speed / 10)
            cx, cy = self.pos

            min_x = max(0, cx - raio)
            max_x = min(self.model.world_width - 1, cx + raio)
            min_y = max(0, cy - raio)
            max_y = min(self.model.world_height - 1, cy + raio)

            alfaaltitude = 0.025
            alfahumidade = 0.3
            alfaprecip = 0.3
            alfavento = 0.05
            alfaaltura = 0.025
            alfatemperature = 0.3

            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    distancia = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    if distancia <= raio:
                        base_prob = 1 if distancia <= 0 else (1 / distancia)

                        # Ajustes ambientais
                        if self.altitude <= 0:
                            altitude_factor = alfaaltitude
                        else:
                            altitude_factor = (1 / self.altitude) * alfaaltitude

                        if self.model.itsrain_:
                            precip_factor = 0
                        else:
                            
                            precip_factor = random.random() * alfaprecip
                    
                        height_factor = self.tree_height * alfaaltura
                        humidity_factor = (1 / self.model.humidity) * alfahumidade

                        # Import do ProbVento:
                        
                        wind_factor = Ignicaoprob(
                            1, 
                            self.model.wind_speed, 
                            cx, 
                            cy, 
                            x, 
                            y, 
                            self.model.wind_direction
                        ) * alfavento

                        temperatura_factor = self.model.temperature * alfatemperature

                        combined_factor = (
                            altitude_factor
                            + precip_factor
                            + height_factor
                            + humidity_factor
                            + wind_factor
                            + temperatura_factor
                        )
                        final_prob = base_prob * combined_factor * self.factor_type_tree

                        patches = self.model.grid.get_cell_list_contents((x, y))
                        for patch in patches:
                            if getattr(patch, "state", None) in ("forested", "dangered"):
                                if random.random() < final_prob:
                                    patch.state = "burning"
                                    patch.pcolor = 15
                                    patch.burn_time = None
                                else:
                                    patch.state = "dangered"
                                    patch.pcolor = 45

            # Chance de gerar nova fagulha
            if random.random() < 0.20:
                from agentes import FragulhaAgent
                new_f = FragulhaAgent(
                    self.model.agent_id_counter,
                    self.model,
                    self.pos
                )
                self.model.agent_id_counter += 1
                self.model.schedule.append(new_f)
                self.model.grid.place_agent(new_f, self.pos)

            # Reduz burn_time
            self.burn_time -= 1
            if self.burn_time <= 0:
                self.state = "burned"
                self.pcolor = 5  # cinza

class AirAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.unique_id = unique_id
        self.co_level = 0.1
        self.co2_level = 400.0
        self.pm2_5_level = 25.0
        self.pm10_level = 10.0
        self.o2_level = 21000.0

    def step(self):
        """A cada passo, ajusta a qualidade do ar conforme a quantidade de fogo."""
        burning = sum(
            1 for agent in self.model.schedule
            if getattr(agent, "state", None) == "burning"
        )

        # Ajuste simples de poluentes
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
