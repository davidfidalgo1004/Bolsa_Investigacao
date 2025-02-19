import mesa

class GenericAgent(mesa.Agent):
    """Agente genérico, que pode ser 'Air' ou 'Wind', sem chamar super().__init__."""
    def __init__(self, unique_id, model, agent_type):
        # Em versões mais novas do Mesa, não chamamos super().__init__ com esses argumentos,
        # pois a assinatura mudou. Então, atribuimos manualmente:
        self.unique_id = unique_id
        self.model = model
        self.agent_type = agent_type
        self.wealth = 1

        if agent_type == "Wind":
            self.wind_speed = 10
            self.wind_direction = 15
            self.netlogo.command(f"set wind-speed {self.wind_speed}")
            self.netlogo.command(f"set wind-direction {self.wind_direction}")

        elif agent_type == "Air":
            self.co_level = self.netlogo.report('co-level')
            self.co2_level = self.netlogo.report('co2-level')
            self.pm2_5_level = self.netlogo.report('pm2_5-level')
            self.pm10_level = self.netlogo.report('pm10-level')
            self.o2_level = self.netlogo.report('o2-level')


    def atualizacao_air(self):
        """Atualiza as variáveis de ar no NetLogo e retorna 'Perigo' ou 'Seguro'."""
        self.co_level = self.netlogo.report('co-level')
        self.co2_level = self.netlogo.report('co2-level')
        self.pm2_5_level = self.netlogo.report('pm2_5-level')
        self.pm10_level = self.netlogo.report('pm10-level')
        self.o2_level = self.netlogo.report('o2-level')

        if (self.o2_level <= 20000 or self.co_level >= 10 or 
            self.co2_level >= 1000 or self.pm10_level >= 100 or 
            self.pm2_5_level >= 100):
            return "Perigo"
        return "Seguro"

    def direction_wind(self):
        """Retorna uma string descrevendo a direção do vento."""
        if self.wind_direction < 22.5 or self.wind_direction >= 337.5:
            return "Incêndio com vento em direção a Sul"
        elif 22.5 <= self.wind_direction < 67.5:
            return "Incêndio com vento em direção a Sudoeste"
        elif 67.5 <= self.wind_direction < 112.5:
            return "Incêndio com vento em direção a Oeste"
        elif 112.5 <= self.wind_direction < 157.5:
            return "Incêndio com vento em direção a Noroeste"
        elif 157.5 <= self.wind_direction < 202.5:
            return "Incêndio com vento em direção a Norte"
        elif 202.5 <= self.wind_direction < 247.5:
            return "Incêndio com vento em direção a Nordeste"
        elif 247.5 <= self.wind_direction < 292.5:
            return "Incêndio com vento em direção a Este"
        elif 292.5 <= self.wind_direction < 337.5:
            return "Incêndio com vento em direção a Sudeste"


class AnimalsAgent(mesa.Agent):
    """Agente que representa animais com sensores direcionais."""
    def __init__(self, unique_id, model, netlogo):
        # Atribuição direta, sem chamar super().__init__.
        self.netlogo=netlogo
        self.unique_id = unique_id
        self.model = model
        self.sensor = None
        self.detection = 0

    def set_sensor(self, direction):
        """Define a direção do sensor (N, S, O, E)."""
        self.sensor = direction

    def alerta(self):
        """Verifica se há 'escaped' acima de 50 para a direção que o agente monitora."""
        if self.netlogo.report('escaped-north') > 50 and self.sensor == "N":
            self.detection = 1
            return "Incêndio"
        elif self.netlogo.report('escaped-south') > 50 and self.sensor == "S":
            self.detection = 1
            return "Incêndio"
        elif self.netlogo.report('escaped-west') > 50 and self.sensor == "O":
            self.detection = 1
            return "Incêndio"
        elif self.netlogo.report('escaped-east') > 50 and self.sensor == "E":
            self.detection = 1
            return "Incêndio"
        else:
            self.detection = 0
            return "Sem incêndios"