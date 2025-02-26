import mesa
from agentes import GenericAgent, AnimalsAgent

class EnvironmentModel(mesa.Model):
    def __init__(self, n, width, height, netlogo, seed=None):
        super().__init__(seed=seed)
        self.netlogo = netlogo
        self.current_id = 0

        # Contadores de incêndios
        self.fires_created = 0  
        self.fires_detected = 0

        # Temperatura lida do NetLogo
        self.temperature = 0

        # Contagem regressiva para apagar fogo 10 ticks após DETECÇÃO
        self.detect_countdown = 0

        # Flag para evitar múltiplas detecções do mesmo incêndio em um mesmo tick
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
        """Retorna True se ainda há patches com fogo ativo (pcolor = orange)."""
        count_burning = self.netlogo.report("count patches with [pcolor = orange]")
        return (count_burning > 0)

    def start_fire(self):
        """Inicia fogo no NetLogo e incrementa o contador de incêndios criados."""
        self.netlogo.command("start-fire")
        self.fires_created += 1

    def stop_fire(self):
        """Apaga fogo no NetLogo."""
        self.netlogo.command("stop-fire")

    # ----------------------------------------------------
    # Verifica se pelo menos 2 sensores estão ativados.
    # ----------------------------------------------------
    def check_fire_sensors(self):
        """
        Verifica quantos sensores estão ativados:
        - Sensor de ar em 'Perigo'
        - Sensores de animais (se ao menos 1 = 1 ponto)
        - Temperatura muito alta (> 50°C)
        Retorna True se >= 2 sensores estiverem ativos.
        """
        active_sensors = 0

        # Sensor de qualidade do ar
        air_status = self.air_agent.atualizacao_air()
        if air_status == "Perigo":
            active_sensors += 1

        # Sensores de animais (somatório das detecções)
        animal_detections = sum([
            self.oeste_agent.detection,
            self.este_agent.detection,
            self.norte_agent.detection,
            self.sul_agent.detection
        ])
        if animal_detections > 0:
            active_sensors += 1

        # Sensor de temperatura
        if self.temperature > 50:
            active_sensors += 1

        return (active_sensors >= 2)

    def step(self):
        """
        Executa um tick do modelo:
         1) Chama 'go' no NetLogo
         2) Atualiza leituras de ar e temperatura
         3) Verifica sensores de animais
         4) Se >= 2 sensores ativos, incrementa contagem de incêndios
         5) Faz countdown e apaga fogo automaticamente quando detect_countdown chega a 0
        """
        # 1) Avança no NetLogo
        self.netlogo.command("go")

        # 2) Atualiza leituras
        self.air_agent.atualizacao_air()
        self.update_temperature()

        # 3) Verifica detecção (animais)
        self.oeste_agent.alerta()
        self.este_agent.alerta()
        self.norte_agent.alerta()
        self.sul_agent.alerta()

        # 4) Checa se >=2 sensores estão ativos
        multiple_sensors_active = self.check_fire_sensors()
        if multiple_sensors_active and not self.fire_detected_this_tick:
            # Se houve detecção neste tick, mas ainda não contabilizamos
            self.fires_detected += 1
            self.fire_detected_this_tick = True
            self.detect_countdown = 10  # inicia contagem de 10 ticks
        elif not multiple_sensors_active:
            # Se não há mais 2 sensores ativos, liberamos para futura detecção
            self.fire_detected_this_tick = False

        # 5) Countdown para apagar fogo
        if self.detect_countdown > 0:
            self.detect_countdown -= 1
            # Se chegou em zero e o fogo ainda está ativo, apaga
            if self.detect_countdown == 0 and self.is_fire_active():
                self.stop_fire()
