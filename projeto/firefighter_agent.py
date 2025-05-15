# firefighter_agent.py

from mesa import Agent
import math
import random


class FirefighterAgent(Agent):
    def __init__(self, unique_id, model, pos, technique="water"):
        super().__init__(model)
        self.unique_id = unique_id
        self.model = model
        self.pos = pos
        self.technique = technique  # "water" ou "alternative"
        self.pcolor = 205          # mantém cor base (azul-escuro)
        self.mode = "idle"         # idle | navigating | direct_attack | firebreak | evacuated
        self.extinguish_capacity = 3
        self.extinguish_progress: dict = {}
        self.firebreak_width = 2   # Largura inicial da linha de corte
        self.firebreak_progress = {}  # Progresso da criação da linha de corte
        self.firebreak_target = None  # Posição alvo para criar firebreak
        self.firebreak_angle = None   # Ângulo da linha de corte
        self.firebreak_center = None  # Centro da linha de corte
        self.firebreak_length = 0     # Comprimento atual da linha de corte
        self.max_firebreak_length = 20  # Comprimento máximo da linha de corte
        self.last_action = "init"     # Para debug
        self.danger_time = 0          # Tempo em condições perigosas
        self.min_danger_time = 5      # Tempo mínimo em condições perigosas antes de evacuar

    def step(self):
        # Debug: Imprime o estado atual do bombeiro
        if self.technique == "alternative":
            print(f"Bombeiro Técnico {self.unique_id}: Modo={self.mode}, Pos={self.pos}, Última ação={self.last_action}")

        # 1) Se estiver sobre fogo, "morre" (remove-se do grid e do scheduler)
        patches = self.model.grid.get_cell_list_contents(self.pos)
        for patch in patches:
            if getattr(patch, "state", None) == "burning":
                try:
                    self.model.schedule.remove(self)
                except ValueError:
                    pass
                try:
                    self.model.grid.remove_agent(self)
                except ValueError:
                    pass
                return

        # 3) Combate normal
        active_fires = [
            a for a in self.model.schedule
            if getattr(a, "state", None) == "burning"
        ]
        if not active_fires:
            self.mode = "idle"
            self.firebreak_target = None
            self.firebreak_angle = None
            self.firebreak_center = None
            self.firebreak_length = 0
            self.last_action = "idle"
            return

        # Bombeiros com água focam em apagar o fogo diretamente
        if self.technique == "water":
            if self._try_extinguish_neighbors():
                self.mode = "direct_attack"
                self.last_action = "direct_attack"
                return
            self.mode = "navigating"
            self._move_towards_priority_fire(active_fires)
            self.last_action = "moving_to_fire"
            return

        # Bombeiros técnicos focam em criar linhas de corte
        if self.technique == "alternative":
            # Se não tem alvo de firebreak ou completou a linha atual
            if self.firebreak_target is None or self.firebreak_length >= self.max_firebreak_length:
                if self.should_create_firebreak(active_fires):
                    self.plan_firebreak(active_fires)
                    self.last_action = "planning_firebreak"
                else:
                    self.mode = "navigating"
                    self._move_towards_priority_fire(active_fires)
                    self.last_action = "moving_to_fire"
                return

            # Se está criando firebreak
            if self.mode == "firebreak":
                self.work_on_firebreak()
                self.last_action = "creating_firebreak"
                return

    def should_create_firebreak(self, fires):
        if not fires:
            return False

        # Bombeiros técnicos são mais agressivos em criar firebreaks
        # Calcula a área total do fogo
        fire_area = len(fires)
        
        # Calcula a velocidade do vento e sua influência
        wind_speed = self.model.wind_speed
        
        # Bombeiros técnicos sempre criam firebreaks
        should_create = True if self.technique == "alternative" else (wind_speed > 2 or fire_area > 3)
        if self.technique == "alternative" and should_create:
            print(f"Bombeiro Técnico {self.unique_id} decidiu criar firebreak: vento={wind_speed}, área={fire_area}")
        return should_create

    def plan_firebreak(self, fires):
        """Planeja uma nova linha de corte"""
        target_fire = min(fires, key=lambda f: math.dist(self.pos, f.pos))
        fire_x, fire_y = target_fire.pos
        x, y = self.pos

        # Calcula a direção do vento em radianos
        wind_rad = math.radians(self.model.wind_direction)
        
        # Calcula o ângulo entre o bombeiro e o fogo
        dx = fire_x - x
        dy = fire_y - y
        angle_to_fire = math.atan2(dy, dx)

        # Ajusta a direção da linha de corte considerando o vento
        wind_speed = self.model.wind_speed
        if wind_speed > 2:  # Valor mais baixo para considerar o vento
            # Linha perpendicular ao vento
            self.firebreak_angle = wind_rad + math.pi/2
        else:
            # Linha entre o bombeiro e o fogo
            self.firebreak_angle = angle_to_fire

        # Define o centro da linha de corte
        self.firebreak_center = ((x + fire_x) / 2, (y + fire_y) / 2)
        
        # Define o primeiro alvo da linha de corte
        self.firebreak_length = 0
        self.firebreak_target = self.calculate_next_firebreak_point(0)
        self.mode = "firebreak"
        
        if self.technique == "alternative":
            print(f"Bombeiro Técnico {self.unique_id} planejou firebreak: ângulo={self.firebreak_angle}, alvo={self.firebreak_target}")

    def calculate_next_firebreak_point(self, offset):
        """Calcula o próximo ponto da linha de corte"""
        if self.firebreak_center is None or self.firebreak_angle is None:
            return None

        center_x, center_y = self.firebreak_center
        # Calcula o ponto na linha principal
        px = center_x + offset * math.cos(self.firebreak_angle)
        py = center_y + offset * math.sin(self.firebreak_angle)
        
        # Arredonda para coordenadas do grid
        grid_x = round(px)
        grid_y = round(py)
        
        # Verifica se está dentro dos limites do grid
        if (0 <= grid_x < self.model.world_width and 
            0 <= grid_y < self.model.world_height):
            return (grid_x, grid_y)
        return None

    def work_on_firebreak(self):
        """Trabalha na criação da linha de corte"""
        if self.firebreak_target is None:
            return

        # Se chegou ao alvo atual
        if self.pos == self.firebreak_target:
            # Cria o firebreak neste ponto
            self.set_firebreak(self.pos)
            self.firebreak_length += 1
            
            if self.technique == "alternative":
                print(f"Bombeiro Técnico {self.unique_id} criou firebreak em {self.pos}, comprimento={self.firebreak_length}")
            
            # Calcula o próximo ponto
            current_offset = math.dist(self.pos, self.firebreak_center)
            next_point = self.calculate_next_firebreak_point(current_offset + 1)
            
            if next_point and self.firebreak_length < self.max_firebreak_length:
                self.firebreak_target = next_point
            else:
                # Se não há mais pontos ou atingiu o comprimento máximo, procura novo alvo
                self.firebreak_target = None
                self.firebreak_angle = None
                self.firebreak_center = None
                self.firebreak_length = 0
                return

        # Move em direção ao alvo
        x, y = self.pos
        tx, ty = self.firebreak_target
        dx = 1 if tx > x else -1 if tx < x else 0
        dy = 1 if ty > y else -1 if ty < y else 0
        new_pos = (x + dx, y + dy)
        
        # Verifica se a nova posição é segura
        if not any(p.state == "burning" for p in self.model.grid.get_cell_list_contents(new_pos)):
            self.model.grid.move_agent(self, new_pos)
            self.pos = new_pos

    def set_firebreak(self, pos):
        """Cria um firebreak em uma posição específica"""
        for patch in self.model.grid.get_cell_list_contents(pos):
            if hasattr(patch, "state") and patch.state == "forested":
                patch.state = "firebreak"
                patch.pcolor = 25  # cor laranja para firebreak
                # Adiciona a posição ao histórico de firebreaks
                if not hasattr(self.model, 'firebreak_history'):
                    self.model.firebreak_history = []
                self.model.firebreak_history.append(pos)
                # Reduz a chance de falha para 2%
                if random.random() < 0.02:
                    patch.state = "forested"  # Volta ao estado original

    def _try_extinguish_neighbors(self) -> bool:
        """Tenta apagar fogo nas células adjacentes (raio 1)."""
        extinguished = False
        neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=True, radius=1
        )

        for nx, ny in neighborhood:
            for patch in self.model.grid.get_cell_list_contents((nx, ny)):
                if getattr(patch, "state", None) == "burning":
                    key = (nx, ny)
                    self.extinguish_progress[key] = (
                        self.extinguish_progress.get(key, 0) + 1
                    )

                    if self.extinguish_progress[key] >= self.extinguish_capacity:
                        patch.state = "burned"
                        patch.pcolor = 5
                        patch.burn_time = None
                        self.extinguish_progress.pop(key, None)
                        extinguished = True
        return extinguished

    def _move_towards_priority_fire(self, fires):
        """Desloca-se um passo na direção do incêndio mais próximo."""
        target_pos = min(fires, key=lambda f: math.dist(self.pos, f.pos)).pos

        x, y = self.pos
        tx, ty = target_pos
        dx = 1 if tx > x else -1 if tx < x else 0
        dy = 1 if ty > y else -1 if ty < y else 0
        new_pos = (x + dx, y + dy)

        self.model.grid.move_agent(self, new_pos)
        self.pos = new_pos
