import mesa
from agentes import GenericAgent, AnimalsAgent

class EnvironmentModel(mesa.Model):
    def __init__(self, n, width, height, netlogo, seed=None):
        super().__init__(seed=seed)
        self.netlogo = netlogo
        self.current_id = 0

        # Contadores de incêndios
        self.fires_created = 0     # se ainda quiser contar quantas vezes o start_fire() foi chamado
        self.fires_detected = 0

        # Temperatura lida do NetLogo
        self.temperature = 0

        # Countdown para apagar fogo 10 ticks após DETECÇÃO
        self.detect_countdown = 0

        # Flags para evitar múltiplas detecções do mesmo incêndio num mesmo tick
        self.fire_detected_this_tick = False

        # Criação de agentes
        self.air_agent = GenericAgent(
            unique_id=self.next_id(),
            model=self,
            agent_type="Air",
            netlogo=self.netlogo
        )
        self.wind_agent = GenericAgent(
            unique_id=self.next_id(),
            model=self,
            agent_type="Wind",
            netlogo=self.netlogo
        )
        directions = ["O", "E", "N", "S"]
        self.animals_agents = self.create_animals_agents(directions)
        self.oeste_agent = self.animals_agents[0]
        self.este_agent = self.animals_agents[1]
        self.norte_agent = self.animals_agents[2]
        self.sul_agent = self.animals_agents[3]

    def create_animals_agents(self, directions):
        agents = []
        for direction in directions:
            agent = AnimalsAgent(
                unique_id=self.next_id(),
                model=self,
                netlogo=self.netlogo
            )
            agent.set_sensor(direction)
            agents.append(agent)
        return agents

    def next_id(self):
        self.current_id += 1
        return self.current_id

    def update_temperature(self):
        """Lê a temperatura do NetLogo (ajuste se tiver reporter custom)."""
        self.temperature = self.netlogo.report("ambient-temperature")

    def is_fire_active(self):
        """Verifica se ainda há fogo no NetLogo. Ajuste a cor ou variável se necessário."""
        count_burning = self.netlogo.report("count patches with [pcolor = orange]")
        return (count_burning > 0)

    def start_fire(self):
        """Caso queira criar fogo aleatoriamente em main.py, mas não exibiremos logs sobre isso."""
        self.netlogo.command("start-fire")
        self.fires_created += 1

    def stop_fire(self):
        self.netlogo.command("stop-fire")

    def step(self):
        """
        Executa um tick do modelo:
          - Chama 'go' no NetLogo
          - Atualiza ar, temperatura
          - Verifica se animais detectam fogo
          - Se detectado neste tick, inicia contagem de 10 ticks
          - A cada tick decrementa detect_countdown e, ao zerar, apaga fogo se ainda houver
        """
        self.netlogo.command("go")

        # 1) Atualiza leituras
        air_status = self.air_agent.atualizacao_air()
        self.update_temperature()

        # 2) Verifica detecção (animais)
        self.oeste_agent.alerta()
        self.este_agent.alerta()
        self.norte_agent.alerta()
        self.sul_agent.alerta()

        any_detected = (
            self.oeste_agent.detection == 1
            or self.este_agent.detection == 1
            or self.norte_agent.detection == 1
            or self.sul_agent.detection == 1
        )

        # Se houve detecção neste tick, mas ainda não contabilizamos
        if any_detected and not self.fire_detected_this_tick:
            self.fires_detected += 1
            self.fire_detected_this_tick = True
            # Inicia contagem de 10 ticks a partir deste momento
            self.detect_countdown = 10

        # Se não há detecção, libera para detectar de novo
        elif not any_detected:
            self.fire_detected_this_tick = False

        # 3) Controla countdown
        if self.detect_countdown > 0:
            self.detect_countdown -= 1
            # Se chegou a zero, apaga fogo se ainda estiver ativo
            if self.detect_countdown == 0 and self.is_fire_active():
                self.stop_fire()
