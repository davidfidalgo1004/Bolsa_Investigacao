"""
CanvasGrid
----------

A visualization module for displaying a grid of agents using an HTML5 Canvas.

This module is part of the Mesa visualization framework.
"""

import json

class CanvasGrid:
    """
    Portrayal module that draws a grid of cells.

    Attributes:
        portrayal_method: A function that takes an agent and returns a portrayal
            dictionary (with keys like "Shape", "Color", "w", "h", etc.).
        grid_width: Number of cells along the horizontal direction.
        grid_height: Number of cells along the vertical direction.
        canvas_width: The total width (in pixels) of the canvas.
        canvas_height: The total height (in pixels) of the canvas.
    """
    def __init__(self, portrayal_method, grid_width, grid_height, canvas_width, canvas_height):
        self.portrayal_method = portrayal_method
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def render(self, model):
        """
        Render the current state of the model's grid.
        
        This method iterates over the model's grid (which is assumed to have a 
        method `coord_iter()` that retorna, para cada célula, uma tupla com a posição
        e uma lista de agentes nessa célula). Para cada célula, se houver algum agente,
        aplica o método de portrayal ao primeiro agente.
        
        Retorna:
            Um objeto JSON (string) representando o estado da grade.
        """
        grid_state = []
        # Itera sobre cada célula usando coord_iter()
        for cell in model.grid.coord_iter():
            cell_content = cell[2]  # conteúdo da célula (lista de agentes)
            portrayal = None
            if cell_content:
                portrayal = self.portrayal_method(cell_content[0])
            # Se não houver representação, envia dicionário vazio
            grid_state.append(portrayal if portrayal is not None else {})
        return json.dumps(grid_state)

    def render_json(self, model):
        """
        Alias para render(): retorna o estado do grid em formato JSON.
        """
        return self.render(model)
