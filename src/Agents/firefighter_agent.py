# firefighter_agent.py

# Standard library imports
import math
import random

# Third-party imports
from mesa import Agent


class FirefighterAgent(Agent):
    def __init__(self, unique_id, model, pos, technique="water"):
        super().__init__(model)
        self.unique_id = unique_id
        self.model = model
        self.pos = pos
        self.starting_pos = pos  # Guarda posição inicial para retorno
        self.technique = technique  # "water" ou "alternative"
        self.pcolor = 205          # mantém cor base (azul-escuro)
        self.mode = "idle"         # idle | navigating | direct_attack | firebreak | evacuated | returning_home
        self.extinguish_capacity = 2  # Reduzido de 3 para 2 para apagar mais rápido
        self.extinguish_progress: dict = {}
        self.firebreak_width = 2   # Largura inicial da linha de corte
        self.firebreak_progress = {}  # Progresso da criação da linha de corte
        self.firebreak_target = None  # Posição alvo para criar firebreak
        self.firebreak_angle = None   # Ângulo da linha de corte
        self.firebreak_center = None  # Centro da linha de corte
        self.firebreak_length = 0     # Comprimento atual da linha de corte
        self.max_firebreak_length = 30  # Aumentado de 20 para 30 para criar linhas mais longas
        self.last_action = "init"     # Para debug
        self.danger_time = 0          # Tempo em condições perigosas
        self.min_danger_time = 5      # Tempo mínimo em condições perigosas antes de evacuar
        self.history = [pos] 

    def step(self):
        # Debug: Imprime o estado atual do bombeiro
        if self.technique == "alternative":
            print(f"Bombeiro Técnico {self.unique_id}: Modo={self.mode}, Pos={self.pos}, Última ação={self.last_action}")
        self.history.append(self.pos)
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
            # Se não há fogo, retorna ao ponto de partida
            if self.pos != self.starting_pos:
                self.mode = "returning_home"
                self._move_towards_home()
                self.last_action = "returning_home"
            else:
                self.mode = "idle"
                self.last_action = "idle"
            
            # Limpa alvos de firebreak
            self.firebreak_target = None
            self.firebreak_angle = None
            self.firebreak_center = None
            self.firebreak_length = 0
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
            # Tenta criar o firebreak neste ponto
            if self.set_firebreak(self.pos):
                self.firebreak_length += 1
                if self.technique == "alternative":
                    print(f"Bombeiro Técnico {self.unique_id} criou firebreak em {self.pos}, comprimento={self.firebreak_length}")
            else:
                if self.technique == "alternative":
                    print(f"Bombeiro Técnico {self.unique_id} não pôde criar firebreak em {self.pos} - local inadequado")
            
            # Calcula o próximo ponto (independentemente de ter criado firebreak ou não)
            current_offset = math.dist(self.pos, self.firebreak_center)
            next_point = self.calculate_next_firebreak_point(current_offset + 1)
            
            # Procura um ponto adequado saltando locais inadequados
            attempts = 0
            while next_point and attempts < 5:  # Máximo 5 tentativas para encontrar local adequado
                if self._is_suitable_for_firebreak(next_point):
                    break
                current_offset += 1
                next_point = self.calculate_next_firebreak_point(current_offset)
                attempts += 1
            
            if next_point and self.firebreak_length < self.max_firebreak_length and attempts < 5:
                self.firebreak_target = next_point
            else:
                # Se não há mais pontos adequados ou atingiu o comprimento máximo, procura novo alvo
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
        if not any(hasattr(p, "state") and p.state == "burning" for p in self.model.grid.get_cell_list_contents(new_pos)):
            self.model.grid.move_agent(self, new_pos)
            self.pos = new_pos

    def set_firebreak(self, pos):
        """Cria ou reforça um firebreak e regista a posição."""
        # Verifica se é um local adequado para firebreak
        if not self._is_suitable_for_firebreak(pos):
            return False
            
        # 1) Marca o patch como firebreak (se ainda não estiver)
        for patch in self.model.grid.get_cell_list_contents(pos):
            if getattr(patch, "state", None) != "firebreak":
                patch.state = "firebreak"
                patch.pcolor = 25  # laranja

        # 2) Regista a posição (sem duplicados)
        if not hasattr(self.model, "firebreak_history"):
            self.model.firebreak_history = []

        if pos not in self.model.firebreak_history:
            self.model.firebreak_history.append(pos)
        
        return True
    
    def _is_suitable_for_firebreak(self, pos):
        """Verifica se a posição é adequada para criar firebreak."""
        patches = self.model.grid.get_cell_list_contents(pos)
        for patch in patches:
            state = getattr(patch, "state", None)
            # Não criar firebreaks em:
            # - Zonas queimadas ("burned")
            # - Fogo ativo ("burning") 
            # - Rios ("river")
            # - Firebreaks já existentes ("firebreak")
            if state in ["burned", "burning", "river", "firebreak"]:
                return False
            
            # Locais ideais para firebreak:
            # - Zonas vazias ("empty") - melhor opção
            # - Estradas ("road") - também bom
            # - Florestas ("forested") - aceitável mas não ideal
            if state in ["empty", "road"]:
                return True
            elif state == "forested":
                # Para florestas, só aceita se não houver alternativa melhor nas proximidades
                return self._no_better_alternative_nearby(pos)
        
        return True  # Se não encontrou patch, assume que é adequado
    
    def _no_better_alternative_nearby(self, pos, radius=2):
        """Verifica se não há locais melhores nas proximidades."""
        neighborhood = self.model.grid.get_neighborhood(
            pos, moore=True, include_center=False, radius=radius
        )
        
        for nx, ny in neighborhood:
            if (0 <= nx < self.model.world_width and 
                0 <= ny < self.model.world_height):
                patches = self.model.grid.get_cell_list_contents((nx, ny))
                for patch in patches:
                    state = getattr(patch, "state", None)
                    # Se há locais vazios ou estradas próximas, prefere esses
                    if state in ["empty", "road"]:
                        return False
        
        return True  # Não há alternativas melhores próximas

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
        """
        Aproxima-se do foco mais próximo **pelo lado oposto ao vento** (up-wind).
        Se já estiver do lado ideal, vai directo; caso contrário contorna gradualmente.
        """
        fire = min(fires, key=lambda f: math.dist(self.pos, f.pos))
        fx, fy = fire.pos

        # vector do vento (para onde o vento sopra)
        rad = math.radians(self.model.wind_direction)
        wind_dx = round(math.sin(rad))
        wind_dy = -round(math.cos(rad))

        # ponto "rendez-vous" a algumas células up-wind
        SAFE_DIST = 3
        upwind_target = (
            max(0, min(self.model.world_width  - 1, fx - wind_dx * SAFE_DIST)),
            max(0, min(self.model.world_height - 1, fy - wind_dy * SAFE_DIST)),
        )

        # escolhe o ponto que me deixa mais perto do lado correcto
        if math.dist(self.pos, upwind_target) < math.dist(self.pos, (fx, fy)):
            tx, ty = upwind_target
        else:
            tx, ty = fx, fy

        # movimento de 1 célula evitando entrar em fogo
        x, y = self.pos
        dx = 1 if tx > x else -1 if tx < x else 0
        dy = 1 if ty > y else -1 if ty < y else 0
        new_pos = (x + dx, y + dy)

        # só avança se a célula destino não estiver a arder
        if not any(getattr(p, "state", None) == "burning"
                for p in self.model.grid.get_cell_list_contents(new_pos)):
            self.model.grid.move_agent(self, new_pos)
            self.pos = new_pos

    def _move_towards_home(self):
        """Move-se em direção ao ponto de partida."""
        x, y = self.pos
        hx, hy = self.starting_pos
        
        # Calcula direção para casa
        dx = 1 if hx > x else -1 if hx < x else 0
        dy = 1 if hy > y else -1 if hy < y else 0
        new_pos = (x + dx, y + dy)
        
        # Verifica se a nova posição está dentro dos limites e é segura
        if (0 <= new_pos[0] < self.model.world_width and 
            0 <= new_pos[1] < self.model.world_height):
            # Só move se não estiver em fogo
            if not any(getattr(p, "state", None) == "burning"
                    for p in self.model.grid.get_cell_list_contents(new_pos)):
                self.model.grid.move_agent(self, new_pos)
                self.pos = new_pos
