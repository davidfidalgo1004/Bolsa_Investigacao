import pynetlogo
import numpy as np

# Inicia a conexão com o NetLogo (sem interface gráfica)
netlogo = pynetlogo.NetLogoLink(gui=False)

# Carrega o modelo desejado (substitua o caminho/modelo conforme necessário)
netlogo.load_model(r"C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo")
netlogo.command("setup")
netlogo.command("start-fire")
for i in range(100):
    netlogo.command("go")
# Obtém os limites do mundo e converte para inteiros
min_pxcor = int(netlogo.report("min-pxcor"))
max_pxcor = int(netlogo.report("max-pxcor"))
min_pycor = int(netlogo.report("min-pycor"))
max_pycor = int(netlogo.report("max-pycor"))

# Calcula o número de colunas e linhas
cols = max_pxcor - min_pxcor + 1
rows = max_pycor - min_pycor + 1

# Cria um comando NetLogo para retornar uma matriz com as cores dos patches
# A expressão gera uma lista de 'rows' linhas, onde cada linha é uma lista de 'cols' pcolors.
cmd = (
    f"map [[y] -> "
    f"  map [[x] -> [pcolor] of patch (x + {min_pxcor}) (y + {min_pycor})] "
    f"       n-values {cols} [[x] -> x] "
    f"] n-values {rows} [[y] -> y]"
)

# Executa o comando e armazena o resultado
patch_colors = netlogo.report(cmd)

# Converte para uma matriz NumPy (opcional, se preferir trabalhar com arrays)
matrix = np.array(patch_colors)

# Exibe a matriz com as cores dos patches
print(matrix)
