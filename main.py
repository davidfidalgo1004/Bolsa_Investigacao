import mesa
import numpy as np
import matplotlib.pyplot as plt

# Resource Classes
class Agente(mesa.Agent):
    def __init__(self, unique_id, model, pos, max_sugar):
        super().__init__(unique_id, model)
        self.pos = pos
        self.amount = max_sugar
        self.max_sugar = max_sugar

class Agente2(mesa.Agent):
    def __init__(self):
        print("Agente 2")

class Agente3(mesa.Agent):
    def __init__(self):
        print("Agente 3")

# Trader Class
class Modelo(mesa.Model):
    def __init__(self, width=50, height=50):
        #Inicialização da tela do modelo
        self.width=width
        self.height=height

        #Inicilização da mesa grid class
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)

        sugar_distribution = np.genfromtxt("map.txt") 
        sugar_distribution = np.flip(sugar_distribution, 1)
        plt.imshow(sugar_distribution, origin="lower")
        plt.show()
        

modelo = Modelo()