# ambiente.py

from mesa import Model
from mesa.space import MultiGrid
import random
from agentes import AirAgent, PatchAgent
from firefighter_agent import FirefighterAgent   # <-- import do bombeiro


class EnvironmentModel(Model):
    def __init__(self, width, height, density=0.8, eucalyptus_percentage=0.5,
                 env_type="only_trees", num_firefighters=4, water_ratio=0.5):
        super().__init__()
        self.world_width = width
        self.world_height = height
        self.running = True
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = []
        

        # Contador para IDs únicos
        self.agent_id_counter = 0

        # Histórico das fagulhas
        self.fragulha_history = {}

        # ------------------------------------------------------------------
        # Cria patches (floresta / estrada / rio)
        # ------------------------------------------------------------------
        self.env_type = env_type
        road_y = height // 2
        river_y = height // 3

        for x in range(width):
            for y in range(height):
                patch = PatchAgent(self.agent_id_counter, self, (x, y))
                self.agent_id_counter += 1

                if self.env_type == "road_trees":
                    if abs(y - road_y) <= 1:
                        patch.state = "road"
                        patch.pcolor = 85
                        patch.altitude = 0
                    else:
                        self._make_forest_patch(patch, density, eucalyptus_percentage)

                elif self.env_type == "river_trees":
                    if abs(y - river_y) <= 1:
                        patch.state = "river"
                        patch.pcolor = 95
                        patch.altitude = 0
                    else:
                        self._make_forest_patch(patch, density, eucalyptus_percentage)

                else:  # only_trees
                    self._make_forest_patch(patch, density, eucalyptus_percentage)

                self.schedule.append(patch)
                self.grid.place_agent(patch, (x, y))

        # ------------------------------------------------------------------
        # Agente do ar + Bombeiros
        # ------------------------------------------------------------------
                # Agente do ar
        self.air_agent = AirAgent(self.agent_id_counter, self)
        self.agent_id_counter += 1
        self.schedule.append(self.air_agent)

        # Bombeiros inseridos dinamicamente conforme sliders:
        border_positions = []
        # coleta todas as posições na borda do grid (células seguras nas extremidades)
        for x in range(self.world_width):
            border_positions.append((x, 0))
            border_positions.append((x, self.world_height - 1))
        for y in range(1, self.world_height - 1):
            border_positions.append((0, y))
            border_positions.append((self.world_width - 1, y))
        random.shuffle(border_positions)
        selected_positions = border_positions[:num_firefighters]
        water_count = int(num_firefighters * water_ratio)
        for idx, (fx, fy) in enumerate(selected_positions):
            # Define técnica conforme proporção (jato de água ou alternativa)
            technique = "water" if idx < water_count else "alternative"
            firefighter = FirefighterAgent(self.agent_id_counter, self, (fx, fy), technique=technique)
            self.agent_id_counter += 1
            self.schedule.append(firefighter)
            self.grid.place_agent(firefighter, (fx, fy))

        # ------------------------------------------------------------------
        # Parâmetros ambientais
        # ------------------------------------------------------------------
        self.temperature = 25.0
        self.wind_direction = 0
        self.wind_speed = 2
        self.rain_level = 0
        self.humidity = 0
        self.itsrain_ = False

    def _make_forest_patch(self, patch, density, eucalyptus_percentage):
        if random.random() > density:
            patch.state = "empty"
            patch.pcolor = 0
            patch.tree_type = "NA"
            patch.factor_type_tree = 0
        else:
            patch.state = "forested"
            if random.random() < eucalyptus_percentage:
                patch.tree_type = "eucalyptus"
                patch.pcolor = 75
                patch.factor_type_tree = 0.8
            else:
                patch.tree_type = "pine"
                patch.pcolor = 55
                patch.factor_type_tree = 0.5

    def step(self):
        for agent in self.schedule[:]:
            agent.step()

        burning = sum(
            1 for a in self.schedule if getattr(a, "state", None) == "burning"
        )
        target_temp = 25.0 + burning * 0.5
        self.temperature += (target_temp - self.temperature) * 0.1

    def start_fire(self):
        forested = [
            a for a in self.schedule if getattr(a, "state", None) == "forested"
        ]
        if forested:
            chosen = random.choice(forested)
            chosen.state = "burning"
            chosen.pcolor = 15

    def stop_fire(self):
        for agent in self.schedule:
            if getattr(agent, "state", None) == "burning":
                agent.state = "burned"
                agent.pcolor = 5
