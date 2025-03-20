# agent.py
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
    r= wind_velocidade*0.0666667
    # Converter ângulo do vento para radianos
    wind_angle_rad = math.radians(wind_angle_deg)
    
    # Vetor direção do (i,j) para o (k,l)
    dx = k - i
    dy = l - j
    
    # Se dx=dy=0, não há direção definida (mesma célula)
    if dx == 0 and dy == 0:
        return 0.0
    
    # Ângulo da direção (k,l) em relação a (i,j)
    alpha = math.atan2(dy, dx)  # Retorna ângulo em radianos entre -pi e pi
    
    # Diferença de ângulos
    delta = alpha - wind_angle_rad
    cos_delta = math.cos(delta) 
    w =cos_delta * r 
    return w

