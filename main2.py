import numpy as np

# Gerar uma matriz 50x50 com valores inteiros entre 0 e 4
sugar_map_example = np.random.randint(0, 5, size=(50, 50))

# Salvar o exemplo em um arquivo de texto
file_path = "sugar-map-example.txt"
np.savetxt(file_path, sugar_map_example, fmt="%d", delimiter=" ")

file_path
