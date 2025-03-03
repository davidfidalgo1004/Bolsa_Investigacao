import mesa
print(f"Mesa version: {mesa.__version__}")
import solara
from matplotlib.figure import Figure

from mesa.visualization.utils import update_counter
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
# Import the local MoneyModel.py
