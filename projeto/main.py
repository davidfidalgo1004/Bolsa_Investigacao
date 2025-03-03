import random
import altair as alt
import solara
import pandas as pd
from mesa import Model
from mesa.visualization.solara_viz import SolaraViz
from ambiente import EnvironmentModel
from pynetlogo import NetLogoLink

# Inicializando NetLogo
netlogo = NetLogoLink()
netlogo.load_model("simulacao_fogo.nlogo")  # Certifique-se de que o caminho do modelo está correto

# Criando um modelo reativo com NetLogo
model_instance = solara.reactive(EnvironmentModel(n=10, width=10, height=10, netlogo=netlogo))

# Criando Gráficos com Altair baseado nas cores do NetLogo
@solara.component
def AltairChart(model: Model, key: str, label: str, color: str):
    df = model.datacollector.get_model_vars_dataframe().reset_index()
    if df.empty:
        df = pd.DataFrame({"index": [], key: []})
    chart = (
        alt.Chart(df)
        .mark_line(color=color)
        .encode(
            x=alt.X("index:Q", title="Iteração"),
            y=alt.Y(f"{key}:Q", title=label),
        )
        .properties(width=400, height=200)
    )
    return solara.Altair(chart)

# Criando a Interface Interativa com SolaraViz
@solara.component
def SimulationPage(model: Model):
    solara.Markdown("## Simulação de Incêndio e Qualidade do Ar")
    AltairChart(model, key="temperature", label="Temperatura", color="orange")
    AltairChart(model, key="fires_detected", label="Incêndios Detectados", color="red")

# Criando a interface SolaraViz
page = SolaraViz(
    EnvironmentModel,
    model_params={"n": 10, "width": 10, "height": 10, "netlogo": netlogo},
    name="Simulação de Incêndio e Qualidade do Ar",
    components=[SimulationPage],
)

# Para rodar, use: solara run <nome_do_arquivo>.py
