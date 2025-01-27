import pynetlogo
import os

# Defina o caminho do NetLogo
netlogo_home = '/opt/netlogo'
netlogo_version = '6.4.0'
netlogo_path = f'{netlogo_home}/lib/app/netlogo-{netlogo_version}.jar'

# Definir variável de ambiente
os.environ['CLASSPATH'] = f'{netlogo_path}:/opt/netlogo/lib/app/*'

# Inicializar NetLogo
netlogo = pynetlogo.NetLogoLink(gui=False, netlogo_home=netlogo_home)
print("NetLogo iniciado com sucesso!")

