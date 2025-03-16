from mesa import Model
from mesa.space import MultiGrid
import random
from agentes import AirAgent, PatchAgent

class EnvironmentModel(Model):
    def __init__(self, width, height, density=0.8, eucalyptus_percentage=0.5, env_type="only_trees"):
        """
        Parâmetros:
          - width, height: dimensões da grid
          - density: fração de patches que terão árvore (0 a 1)
          - eucalyptus_percentage: fração das árvores que serão eucaliptos
          - env_type: "road_trees", "river_trees" ou "only_trees"
        """
        super().__init__()
        self.running = True
        self.world_width = width
        self.world_height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = []
        
        self.env_type = env_type
        # Vamos criar a estrada ou rio sempre no meio (você pode personalizar):
        road_y = height // 2
        river_y = height // 3

        agent_id = 0
        for x in range(width):
            for y in range(height):
                patch = PatchAgent(agent_id, self, (x, y))
                
                # ---------------------------
                # 1) Estrada + Árvores
                # ---------------------------
                if self.env_type == "road_trees":
                    if abs(y - road_y) <= 1:
                        patch.state = "road"
                        patch.pcolor = 85  # cor estrada
                    else:
                        self._make_forest_patch(patch, density, eucalyptus_percentage)

                # ---------------------------
                # 2) Rio + Árvores
                # ---------------------------
                elif self.env_type == "river_trees":
                    if abs(y - river_y) <= 1:
                        patch.state = "river"
                        patch.pcolor = 95  # cor rio
                    else:
                        self._make_forest_patch(patch, density, eucalyptus_percentage)

                # ---------------------------
                # 3) Só Árvores
                # ---------------------------
                else:  # "only_trees"
                    self._make_forest_patch(patch, density, eucalyptus_percentage)
                
                self.schedule.append(patch)
                self.grid.place_agent(patch, (x, y))
                agent_id += 1

        # Adiciona agente de ar
        self.air_agent = AirAgent(agent_id, self)
        self.schedule.append(self.air_agent)

        # Parâmetros de clima
        self.temperature = 25.0
        self.wind_direction = 0
        self.wind_speed = 2
        self.rain_level = 0  # Precipitação: 0 sem chuva, 1 chuva intensa

    def _make_forest_patch(self, patch, density, eucalyptus_percentage):
        """Define se o patch será vazio ou terá árvore (e qual tipo)."""
        if random.random() > density:
            patch.state = "empty"
            patch.pcolor = 0
        else:
            patch.state = "forested"
            if random.random() < eucalyptus_percentage:
                patch.tree_type = "eucalyptus"
                patch.pcolor = 75  # eucalipto
            else:
                patch.tree_type = "pine"
                patch.pcolor = 55  # pinheiro

    def step(self):
        for agent in self.schedule:
            agent.step()

        burning = sum(1 for agent in self.schedule if getattr(agent, "state", None) == "burning")
        target_temp = 25.0 + burning * 0.5
        decay = 0.1
        self.temperature += (target_temp - self.temperature) * decay
        

    def start_fire(self):
        forested_patches = [a for a in self.schedule if getattr(a, "state", None) == "forested"]
        if forested_patches:
            chosen = random.choice(forested_patches)
            chosen.state = "burning"
            chosen.pcolor = 15  # vermelho

    def stop_fire(self):
        for agent in self.schedule:
            if getattr(agent, "state", None) == "burning":
                agent.state = "burned"
                agent.pcolor = 5  # cinza
