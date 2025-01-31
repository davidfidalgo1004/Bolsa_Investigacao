import pynetlogo

# Inicializar conexão com NetLogo
netlogo = pynetlogo.NetLogoLink(gui=False, netlogo_home=r'C:\Program Files\NetLogo 6.4.0')

# Carregar o modelo
netlogo.load_model(r'C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo')

# Configurar e rodar a simulação
netlogo.command('setup')

for i in range(100):
    netlogo.command('go')
    if i == 20:
        netlogo.command('start-fire')

# Obter o valor final da variável global 'burned-trees'
arvoresqueimadas = netlogo.report('burned-trees')
print(f'O valor final da variável burned-trees é: {arvoresqueimadas}')

