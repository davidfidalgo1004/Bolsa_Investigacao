# ProbVento.py

# Standard library imports
import math

def Ignicaoprob(p0, wind_velocidade, i, j, k, l, wind_angle_deg):
    """
    Retorna a probabilidade de ignição (p0 ajustada pelo cosseno da diferença de ângulos)
    de uma célula (i, j) para sua vizinha (k, l), dado que (k, l) está em chamas.
    
    Parâmetros:
      p0 (float): probabilidade base de ignição
      r  (float): intensidade do vento (0.0 = sem efeito, > 0 aumenta/diminui a prob)
      i, j (int): coordenadas da célula de referência
      k, l (int): coordenadas do vizinho
      wind_angle_deg (float): direção do vento em graus (0° = vento soprando para "direita")
      
    Retorna:
      (float): probabilidade ajustada de ignição
    """
    r = wind_velocidade * 0.0666667
    # Converte a direção do vento (0° = Norte) para o ângulo matemático (0° = Leste)
    math_wind_angle = math.radians(90 - wind_angle_deg)
    
    dx = k - i
    dy = l - j
    if dx == 0 and dy == 0:
        return 0.0
    
    alpha = math.atan2(dy, dx)
    delta = alpha - math_wind_angle
    cos_delta = math.cos(delta)
    w = cos_delta * r
    return w