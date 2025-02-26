import tkinter as tk
from PIL import Image, ImageTk
import pynetlogo
import numpy as np
import matplotlib.pyplot as plt

# Função que mapeia os valores de pcolor para cores RGB
def netlogo_color(num):
    mapping = {
        0:   (0, 0, 0),         # Black (área queimada)
        5:   (128, 128, 128),   # Gray (brasas)
        9:   (255, 255, 255),   # White
        15:  (255, 0, 0),       # Red (fogo, se for esse o caso)
        25:  (255, 165, 0),     # Orange
        35:  (139, 69, 19),     # Brown
        45:  (255, 255, 0),     # Yellow
        55:  (34, 139, 34),     # Green (árvores intactas)
        65:  (50, 205, 50),     # Lime green
        75:  (64, 224, 208),    # Turquoise
        85:  (0, 255, 255),     # Cyan
        95:  (135, 206, 235),   # Sky Blue
        105: (0, 0, 255),       # Blue
        115: (138, 43, 226),    # Violet
        125: (255, 0, 255),     # Magenta
        135: (255, 192, 203)    # Pink
    }
    rounded = int(round(num / 5.0) * 5)
    return mapping.get(rounded, (int(255 * (num / 140.0)),) * 3)

# Inicializa o NetLogo sem GUI
netlogo = pynetlogo.NetLogoLink(
    gui=False,
    netlogo_home=r"C:\Program Files\NetLogo 6.4.0"
)

# Carrega o modelo e realiza o setup
netlogo.load_model(r"C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo")
netlogo.command("setup")

# Obtemos os limites do mundo
min_px = int(netlogo.report("min-pxcor"))
max_px = int(netlogo.report("max-pxcor"))
min_py = int(netlogo.report("min-pycor"))
max_py = int(netlogo.report("max-pycor"))
grid_width = max_px - min_px + 1
grid_height = max_py - min_py + 1

# Criação da interface Tkinter
root = tk.Tk()
root.title("Visualização NetLogo - Simulação de Fogo")

frame_imagens = tk.Frame(root)
frame_imagens.pack(pady=10)

labels = [tk.Label(frame_imagens) for _ in range(3)]
for lbl in labels:
    lbl.pack(side=tk.LEFT, padx=5)

btn = tk.Button(root, text="Capturar Estados", command=lambda: capturar_e_exibir(root))
btn.pack(pady=10)

# Função que captura os estados e gera as imagens
def capturar_e_exibir(root):
    momentos = []
    for i in range(3):  # Três momentos distintos
        for j in range(10):
            netlogo.command("go")  # Avança a simulação

        # Obtém os valores de pcolor dos patches
        patches_data = netlogo.report("[pcolor] of patches")
        patches_matrix = np.array(patches_data).reshape(grid_height, grid_width)

        # Verifica se há focos de fogo
        count_fires = netlogo.report("count fires")
        if count_fires > 0:
            fire_positions = netlogo.report("[list xcor ycor] of fires")
        else:
            fire_positions = []  # Se não houver fires, a lista fica vazia

        filename = f"estado_{i}.png"
        gerar_imagem_mapa(patches_matrix, fire_positions, filename)
        momentos.append(filename)

        if i == 1:
            netlogo.command("start-fire")
    
    # Atualiza as imagens na interface Tkinter
    for i, filename in enumerate(momentos):
        img = Image.open(filename)
        img = img.resize((200, 200))
        img = ImageTk.PhotoImage(img)
        labels[i].config(image=img)
        labels[i].image = img

    root.update_idletasks()

# Função que gera a imagem usando Matplotlib
def gerar_imagem_mapa(matrix, fire_positions, filename):
    # Cria uma matriz RGB baseada nos valores de pcolor dos patches
    img_rgb = np.zeros((matrix.shape[0], matrix.shape[1], 3), dtype=np.uint8)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            pcolor_val = float(matrix[i, j])
            img_rgb[i, j] = netlogo_color(pcolor_val)
    
    # Sobrepõe os focos de fogo em vermelho, se houver algum
    if fire_positions is not None and np.size(fire_positions) > 0:
        # Caso fire_positions seja um array, convertê-lo para lista para iterar
        for pos in fire_positions.tolist():
            try:
                x, y = pos
                col = int(round(x - min_px))
                row = int(round(max_py - y))
                if 0 <= row < img_rgb.shape[0] and 0 <= col < img_rgb.shape[1]:
                    img_rgb[row, col] = (255, 0, 0)  # Vermelho para focos de fogo
            except Exception as e:
                print("Erro ao processar posição do fogo:", pos, e)
    
    # Gera e salva a imagem sem eixos
    plt.figure(figsize=(5, 5))
    plt.imshow(img_rgb)
    plt.axis("off")
    plt.savefig(filename, bbox_inches='tight', pad_inches=0)
    plt.close()

root.mainloop()
