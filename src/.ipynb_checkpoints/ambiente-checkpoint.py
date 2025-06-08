import mesa
from agentes import GenericAgent, AnimalsAgent

class EnvironmentModel(mesa.Model):
    def __init__(self, n, width, height, netlogo, seed=None):
        super().__init__(seed=seed)
        self.current_id = 0  
        self.apagar_fogo_em_5_ticks = 0

        # Contadores de incêndios
        self.fires_created = 0
        self.fires_detected = 0
        
        # Flag para controlar a detecção de incêndio
        self.fire_detected_this_tick = False

        def create_animals_agents(model, directions):
            agents = []
            for direction in directions:
                agent = AnimalsAgent(unique_id=self.next_id(), model=model, netlogo)
                agent.set_sensor(direction)
                agents.append(agent)
            return agents

        # Cria agentes
        self.air_agent = GenericAgent(unique_id=self.next_id(), model=self, agent_type="Air", netlogo)
        self.wind_agent = GenericAgent(unique_id=self.next_id(), model=self, agent_type="Wind", netlogo)

        directions = ["O", "E", "N", "S"]
        self.animals_agents = create_animals_agents(self, directions)
        self.oeste_agent = self.animals_agents[0]
        self.este_agent = self.animals_agents[1]
        self.norte_agent = self.animals_agents[2]
        self.sul_agent = self.animals_agents[3]

    def next_id(self):
        self.current_id += 1
        return self.current_id

    def start_fire(self):
        """Chama o procedimento NetLogo para iniciar um incêndio e contabiliza."""
        self.netlogo.command('start-fire')
        self.fires_created += 1

    def stop_fire(self):
        """Chama o procedimento NetLogo para apagar o incêndio atual."""
        self.netlogo.command('stop-fire')

    def step(self):
        """
        Executa um tick do modelo:
          - Manda NetLogo avançar um tick ('go')
          - Atualiza ar
          - Verifica detecção
        """
        self.netlogo.command('go')
        air_status = self.air_agent.atualizacao_air()
        
        self.oeste_agent.alerta()
        self.este_agent.alerta()
        self.norte_agent.alerta()
        self.sul_agent.alerta()

        # Verifica se qualquer um dos animais detectou incêndio
        any_detected = (
            self.oeste_agent.detection == 1 or
            self.este_agent.detection == 1 or
            self.norte_agent.detection == 1 or
            self.sul_agent.detection == 1
        )

        if air_status == "Perigo" and any_detected:
            # Se não contamos ainda neste tick, incrementa o contador de incêndios detectados
            if not self.fire_detected_this_tick:
                self.fires_detected += 1
                self.fire_detected_this_tick = True

            # Impressão de logs
            detections = []
            if self.oeste_agent.detection == 1:
                detections.append("Incêndio a Oeste")
            if self.este_agent.detection == 1:
                detections.append("Incêndio a Este")
            if self.norte_agent.detection == 1:
                detections.append("Incêndio a Norte")
            if self.sul_agent.detection == 1:
                detections.append("Incêndio a Sul")

            # Exibe as direções detectadas
            for d in detections:
                print(d)
            print(self.wind_agent.direction_wind())
            print("Vento com velocidade de", self.wind_agent.wind_speed, "m/s\n")

            self.apagar_fogo_em_5_ticks += 1
            if self.apagar_fogo_em_5_ticks == 5:
                self.stop_fire()

        else:
            self.apagar_fogo_em_5_ticks = 0
            # Se não há detecção neste tick, resetamos a flag
            self.fire_detected_this_tick = False