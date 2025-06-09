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
        # Capacidade de extinção ajustada por técnica
        if technique == "water":
            self.extinguish_capacity = 2  # Bombeiros de água: mais eficazes
        else:
            self.extinguish_capacity = 3  # Bombeiros técnicos: menos eficazes mas capazes
        self.extinguish_progress: dict = {}
        self.firebreak_width = 2   # Largura inicial da linha de corte
        self.firebreak_progress = {}  # Progresso da criação da linha de corte
        self.firebreak_target = None  # Posição alvo para criar firebreak
        self.firebreak_angle = None   # Ângulo da linha de corte
        self.firebreak_center = None  # Centro da linha de corte
        self.firebreak_length = 0     # Comprimento atual da linha de corte
        self.max_firebreak_length = 15  # Reduzido de 30 para 15 para linhas mais curtas e diretas
        self.last_action = "init"     # Para debug
        self.danger_time = 0          # Tempo em condições perigosas
        self.min_danger_time = 5      # Tempo mínimo em condições perigosas antes de evacuar
        self.history = [pos] 
        # Novos atributos para comportamento mais agressivo
        self.urgency_threshold = 4    # Distância crítica para mudar de estratégia (aumentada)
        self.consecutive_firebreak_time = 0  # Tempo criando firebreak consecutivamente
        self.max_consecutive_firebreak = 8   # Máximo de turnos consecutivos fazendo firebreak
        self.last_fire_positions = []  # Histórico de posições do fogo para detectar expansão
        self.strategy_cooldown = 0     # Cooldown para mudança de estratégia

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
            self.consecutive_firebreak_time = 0
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

        # COMPORTAMENTO PREVENTIVO DOS BOMBEIROS TÉCNICOS
        if self.technique == "alternative":
            # Debug: Verifica quantos focos há
            print(f"Bombeiro Técnico {self.unique_id}: {len(active_fires)} focos ativos detectados")
            
            # **PRIORIDADE ABSOLUTA: Se está criando firebreak, CONTINUA até terminar**
            if self.mode == "firebreak" and self.firebreak_target is not None:
                self.consecutive_firebreak_time += 1
                
                # SÓ para se:
                # 1. Completou a linha inteira (atingiu comprimento máximo)
                # 2. Ficou preso muito tempo (mais de 20 turnos consecutivos)
                # 3. Não consegue encontrar próximo ponto válido
                if (self.firebreak_length >= self.max_firebreak_length or
                    self.consecutive_firebreak_time >= 20):
                    print(f"Bombeiro Técnico {self.unique_id} COMPLETOU firebreak! Comprimento: {self.firebreak_length}")
                    self._reset_firebreak()
                    return
                
                # CONTINUA criando a linha sem interrupções
                self.work_on_firebreak()
                self.last_action = "creating_firebreak"
                return
            
            # Atualiza cooldown de estratégia
            if self.strategy_cooldown > 0:
                self.strategy_cooldown -= 1
                
            # Análise de expansão do fogo para decisão estratégica
            current_fire_positions = {f.pos for f in active_fires}
            fire_expansion_detected = self._detect_fire_expansion(current_fire_positions)
            
            # ESTRATÉGIA PREVENTIVA - CRIA NOVA LINHA apenas se não está ocupado
            if self.firebreak_target is None:
                # SEMPRE cria firebreaks se há pelo menos 1 foco
                if len(active_fires) > 0:
                    print(f"Bombeiro Técnico {self.unique_id} vai criar NOVA firebreak preventiva!")
                    self._create_preventive_firebreak(active_fires, fire_expansion_detected)
                    self.last_action = "planning_preventive_firebreak"
                else:
                    # Se não há fogo, fica ocioso
                    self.mode = "idle"
                    self.last_action = "no_fire_idle"
                    print(f"Bombeiro Técnico {self.unique_id} sem focos para prevenir")
                return

    def _detect_fire_expansion(self, current_positions):
        """Detecta se o fogo está se expandindo rapidamente."""
        if len(self.last_fire_positions) < 3:  # Precisa de histórico
            self.last_fire_positions.append(current_positions.copy())
            return False
            
        # Mantém apenas as últimas 3 posições
        if len(self.last_fire_positions) > 3:
            self.last_fire_positions.pop(0)
        
        # Calcula taxa de expansão
        prev_count = len(self.last_fire_positions[-1])
        current_count = len(current_positions)
        expansion_rate = current_count - prev_count
        
        self.last_fire_positions.append(current_positions.copy())
        
        # Considera expansão rápida se ganhou 2+ focos ou há muitos focos em área estratégica
        rapid_expansion = (expansion_rate >= 2 or 
                          len([pos for pos in current_positions if math.dist(self.pos, pos) <= 8]) >= 3)
        
        if rapid_expansion and self.technique == "alternative":
            print(f"Bombeiro Técnico {self.unique_id} detectou expansão rápida do fogo! Taxa: +{expansion_rate}")
            
        return rapid_expansion

    def _reset_firebreak(self):
        """Reseta o estado do firebreak atual."""
        self.firebreak_target = None
        self.firebreak_angle = None
        self.firebreak_center = None
        self.firebreak_length = 0
        self.consecutive_firebreak_time = 0
        self.max_firebreak_length = 15  # Volta ao valor padrão

    def should_create_preventive_firebreak(self, fires):
        """Determina se deve criar firebreak preventivo (sem perseguir o fogo)."""
        if not fires:
            return False

        # Bombeiros técnicos sempre trabalham preventivamente
        fire_area = len(fires)
        wind_speed = self.model.wind_speed
        
        # Calcula distância ao fogo mais próximo (mas não é fator limitante)
        closest_distance = min(math.dist(self.pos, f.pos) for f in fires)
        
        # Critérios preventivos:
        # 1. Sempre cria se há fogo ativo (preventivo)
        # 2. Considera vento para direcionamento
        # 3. Não depende da proximidade - trabalha à distância
        should_create = (self.technique == "alternative" and fire_area >= 1)
        
        if self.technique == "alternative" and should_create:
            print(f"Bombeiro Técnico {self.unique_id} avalia firebreak preventivo: vento={wind_speed:.1f}, focos={fire_area}, distância_segura={closest_distance:.1f}")
        return should_create

    def _create_preventive_firebreak(self, fires, rapid_expansion):
        """Cria firebreak preventivo estratégico, perpendicular à direção do fogo."""
        x, y = self.pos

        # Calcula centro de massa do fogo para estratégia de contenção
        fire_center_x = sum(f.pos[0] for f in fires) / len(fires)
        fire_center_y = sum(f.pos[1] for f in fires) / len(fires)
        
        # NOVA ESTRATÉGIA: Detecta direção dominante do fogo e cria linha perpendicular
        
        # 1. Calcula vetor do fogo ao bombeiro (direção de avanço esperada)
        fire_to_firefighter_x = x - fire_center_x
        fire_to_firefighter_y = y - fire_center_y
        fire_distance = math.sqrt(fire_to_firefighter_x**2 + fire_to_firefighter_y**2)
        
        # 2. Considera também a direção do vento para prever avanço do fogo
        wind_rad = math.radians(self.model.wind_direction)
        wind_dx = math.sin(wind_rad)
        wind_dy = -math.cos(wind_rad)
        
        if fire_distance > 0:
            # Normaliza vetor fogo-bombeiro
            fire_to_firefighter_x /= fire_distance
            fire_to_firefighter_y /= fire_distance
            
            # Combina direção do fogo com efeito do vento (60% fogo, 40% vento)
            combined_dx = 0.6 * fire_to_firefighter_x + 0.4 * wind_dx
            combined_dy = 0.6 * fire_to_firefighter_y + 0.4 * wind_dy
            
            # Normaliza direção combinada
            combined_length = math.sqrt(combined_dx**2 + combined_dy**2)
            if combined_length > 0:
                combined_dx /= combined_length
                combined_dy /= combined_length
        else:
            # Se bombeiro está no centro do fogo, usa só o vento
            combined_dx = wind_dx
            combined_dy = wind_dy
        
        # 3. Calcula ângulo da direção do avanço do fogo
        fire_advance_angle = math.atan2(combined_dy, combined_dx)

        # 4. LINHA PERPENDICULAR: Adiciona 90 graus (π/2) para ficar perpendicular
        self.firebreak_angle = fire_advance_angle + math.pi/2
        
        # 5. Favorece linhas cardeais (vertical/horizontal) quando possível
        angle_degrees = math.degrees(self.firebreak_angle) % 360
        
        # Se estiver próximo de vertical (90° ou 270°), força vertical
        if 80 <= angle_degrees <= 100 or 260 <= angle_degrees <= 280:
            self.firebreak_angle = math.pi/2  # 90° - linha vertical
            line_type = "VERTICAL"
        # Se estiver próximo de horizontal (0°, 180° ou 360°), força horizontal
        elif angle_degrees <= 10 or angle_degrees >= 350 or 170 <= angle_degrees <= 190:
            self.firebreak_angle = 0  # 0° - linha horizontal
            line_type = "HORIZONTAL"
        else:
            line_type = f"DIAGONAL {angle_degrees:.0f}°"
        
        # 6. Posiciona a linha próxima ao bombeiro mas afastada do fogo
        distance_to_fire = math.dist((x, y), (fire_center_x, fire_center_y))
        
        if distance_to_fire < 10:
            # Se próximo, cria linha entre bombeiro e fogo (mais próxima do bombeiro)
            center_x = x + (fire_center_x - x) * 0.2  # 20% do caminho para o fogo (mais longe)
            center_y = y + (fire_center_y - y) * 0.2
        else:
            # Se longe, cria linha na frente do bombeiro na direção oposta ao fogo
            center_x = x - combined_dx * 3  # 3 células na direção oposta ao avanço
            center_y = y - combined_dy * 3

        # Garante que o centro está dentro dos limites
        center_x = max(2, min(self.model.world_width - 3, center_x))
        center_y = max(2, min(self.model.world_height - 3, center_y))
        
        self.firebreak_center = (center_x, center_y)
        
        # Comprimento baseado na situação
        if rapid_expansion:
            self.max_firebreak_length = 15  # Linha mais longa para expansão rápida
        else:
            self.max_firebreak_length = 12  # Linha padrão mais longa
        
        self.firebreak_length = 0
        self.firebreak_target = self.calculate_next_firebreak_point(0)
        
        # Verifica se o primeiro alvo é válido
        if self.firebreak_target is None:
            # Se não conseguiu calcular alvo, cria linha vertical simples
            self.firebreak_center = (x + 1, y)
            self.firebreak_angle = math.pi/2  # Linha vertical
            self.firebreak_target = self.calculate_next_firebreak_point(0)
            line_type = "VERTICAL (fallback)"
        
        self.mode = "firebreak"
        self.consecutive_firebreak_time = 0
        
        if self.technique == "alternative":
            print(f"Bombeiro Técnico {self.unique_id} criou firebreak {line_type}: centro={self.firebreak_center}, alvo={self.firebreak_target}, distância_fogo={distance_to_fire:.1f}, ângulo={math.degrees(self.firebreak_angle):.0f}°")

    def _move_to_strategic_position(self, fires):
        """Move para posição estratégica longe do fogo, mas apenas se necessário."""
        if not fires:
            return
            
        x, y = self.pos
        
        # Calcula centro do fogo
        fire_center_x = sum(f.pos[0] for f in fires) / len(fires)
        fire_center_y = sum(f.pos[1] for f in fires) / len(fires)
        
        # Calcula distância ao centro do fogo
        distance_to_fire = math.dist((x, y), (fire_center_x, fire_center_y))
        
        # Só se move se estiver MUITO próximo do fogo (distância < 6)
        if distance_to_fire >= 6:
            if self.technique == "alternative":
                print(f"Bombeiro Técnico {self.unique_id} mantém posição estratégica (distância segura: {distance_to_fire:.1f})")
            return
        
        # Se está muito próximo, afasta-se
        # Calcula direção oposta ao fogo
        dx = x - fire_center_x
        dy = y - fire_center_y
        
        # Normaliza
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        
        # Move uma célula para longe do fogo
        move_dx = 1 if dx > 0 else -1 if dx < 0 else 0
        move_dy = 1 if dy > 0 else -1 if dy < 0 else 0
        new_pos = (x + move_dx, y + move_dy)
        
        # Verifica se a nova posição é segura (não em fogo)
        if (0 <= new_pos[0] < self.model.world_width and 
            0 <= new_pos[1] < self.model.world_height):
            if not any(getattr(p, "state", None) == "burning"
                    for p in self.model.grid.get_cell_list_contents(new_pos)):
                self.model.grid.move_agent(self, new_pos)
                self.pos = new_pos
                
                if self.technique == "alternative":
                    print(f"Bombeiro Técnico {self.unique_id} afastou-se do fogo para distância segura")

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
                    print(f"Bombeiro Técnico {self.unique_id} não pôde criar firebreak em {self.pos} - local inadequado, CONTINUA para próximo ponto")
            
            # **SEMPRE calcula o próximo ponto** (independentemente de ter criado firebreak ou não)
            current_offset = math.dist(self.pos, self.firebreak_center)
            next_point = self.calculate_next_firebreak_point(current_offset + 1)
            
            # **BUSCA MAIS AMPLAMENTE** - procura até 10 pontos à frente se necessário
            attempts = 0
            while next_point and attempts < 10:  # Aumentado de 5 para 10 tentativas
                if self._is_suitable_for_firebreak(next_point):
                    break
                current_offset += 1
                next_point = self.calculate_next_firebreak_point(current_offset)
                attempts += 1
            
            # **SÓ PARA se realmente não há mais pontos OU atingiu comprimento máximo**
            if next_point and self.firebreak_length < self.max_firebreak_length and attempts < 10:
                self.firebreak_target = next_point
                if self.technique == "alternative":
                    print(f"Bombeiro Técnico {self.unique_id} continua firebreak para {next_point}, tentativas={attempts}")
            else:
                # **TENTA CRIAR LINHA EM DIREÇÃO ALTERNATIVA** antes de desistir
                if self.firebreak_length < 5:  # Se ainda é uma linha muito curta
                    # Tenta uma linha perpendicular à atual
                    alt_angle = self.firebreak_angle + math.pi/2
                    self.firebreak_angle = alt_angle
                    alt_point = self.calculate_next_firebreak_point(1)
                    if alt_point and self._is_suitable_for_firebreak(alt_point):
                        self.firebreak_target = alt_point
                        if self.technique == "alternative":
                            print(f"Bombeiro Técnico {self.unique_id} mudou direção da linha para {alt_point}")
                        return
                
                # Se realmente não consegue continuar, completa a linha
                if self.technique == "alternative":
                    print(f"Bombeiro Técnico {self.unique_id} FINALIZOU firebreak com {self.firebreak_length} segmentos")
                self.firebreak_target = None
                self.firebreak_angle = None
                self.firebreak_center = None
                self.firebreak_length = 0
                return

        # **MOVIMENTO MELHORADO** - Move em direção ao alvo com verificação de segurança
        x, y = self.pos
        tx, ty = self.firebreak_target
        dx = 1 if tx > x else -1 if tx < x else 0
        dy = 1 if ty > y else -1 if ty < y else 0
        new_pos = (x + dx, y + dy)
        
        # Verifica se a nova posição é segura e está dentro dos limites
        if (0 <= new_pos[0] < self.model.world_width and 
            0 <= new_pos[1] < self.model.world_height):
            if not any(hasattr(p, "state") and p.state == "burning" for p in self.model.grid.get_cell_list_contents(new_pos)):
                self.model.grid.move_agent(self, new_pos)
                self.pos = new_pos
                if self.technique == "alternative":
                    print(f"Bombeiro Técnico {self.unique_id} moveu para {new_pos} em direção ao alvo {self.firebreak_target}")
            else:
                # Se o caminho está em fogo, tenta um caminho alternativo
                alternative_moves = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
                for alt_pos in alternative_moves:
                    if (0 <= alt_pos[0] < self.model.world_width and 
                        0 <= alt_pos[1] < self.model.world_height):
                        if not any(hasattr(p, "state") and p.state == "burning" for p in self.model.grid.get_cell_list_contents(alt_pos)):
                            self.model.grid.move_agent(self, alt_pos)
                            self.pos = alt_pos
                            if self.technique == "alternative":
                                print(f"Bombeiro Técnico {self.unique_id} usou caminho alternativo para {alt_pos}")
                            break

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
        """Verifica se a posição é adequada para criar firebreak - VERSÃO MAIS PERMISSIVA."""
        # Verifica se está dentro dos limites
        if not (0 <= pos[0] < self.model.world_width and 
                0 <= pos[1] < self.model.world_height):
            return False
            
        patches = self.model.grid.get_cell_list_contents(pos)
        for patch in patches:
            state = getattr(patch, "state", None)
            # APENAS NÃO criar firebreaks em:
            # - Fogo ativo ("burning") 
            # - Rios ("river")
            # - Firebreaks já existentes ("firebreak")
            if state in ["burning", "river", "firebreak"]:
                return False
            
            # **AGORA ACEITA TODOS OS OUTROS TIPOS**:
            # - Florestas ("forested") - ÓTIMO
            # - Zonas vazias ("empty") - BOM  
            # - Estradas ("road") - BOM
            # - Zonas queimadas ("burned") - ACEITA (pode ajudar como barrier adicional)
            if state in ["forested", "empty", "road", "burned"]:
                return True
        
        return True  # Se não encontrou patch específico, assume que é adequado
    
    def _has_forest_nearby(self, pos, radius=3):
        """Verifica se há florestas próximas (para priorizar zonas verdes)."""
        neighborhood = self.model.grid.get_neighborhood(
            pos, moore=True, include_center=False, radius=radius
        )
        
        for nx, ny in neighborhood:
            if (0 <= nx < self.model.world_width and 
                0 <= ny < self.model.world_height):
                patches = self.model.grid.get_cell_list_contents((nx, ny))
                for patch in patches:
                    state = getattr(patch, "state", None)
                    # Se há florestas próximas, prefere criar firebreak nelas
                    if state == "forested":
                        return True
        
        return False  # Não há florestas próximas

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
        APENAS para bombeiros de água - bombeiros técnicos não usam este método.
        Aproxima-se do foco mais próximo **pelo lado oposto ao vento** (up-wind).
        """
        # Bombeiros técnicos não perseguem o fogo - usam _move_to_strategic_position
        if self.technique == "alternative":
            self._move_to_strategic_position(fires)
            return
            
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
