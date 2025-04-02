"""
ModularVisualization
--------------------

Este módulo implementa um servidor modular para a visualização de modelos Mesa,
usando o framework Tornado para criar uma interface web interativa.

O servidor permite que os elementos de visualização (por exemplo, CanvasGrid,
gráficos, etc.) sejam integrados e atualizados conforme o modelo evolui.
"""

import os
import json
import threading
import webbrowser
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode

# Handler para a página principal (index.html)
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        # Renderiza o template principal; o template espera a variável "title"
        self.render("index.html", title=self.application.settings.get("title", "Mesa Model"))

# Handler para servir os dados do modelo em JSON
class DataHandler(tornado.web.RequestHandler):
    def get(self):
        # O método model_reporter() deve estar disponível na aplicação
        model_state = self.application.model_reporter() if hasattr(self.application, "model_reporter") else {}
        self.write(json_encode(model_state))

# O servidor modular que integra o modelo e os elementos de visualização
class ModularServer:
    """
    ModularServer integra o modelo Mesa com a interface de visualização web.

    Args:
        model_cls: A classe do modelo que será executado.
        visualization_elements: Uma lista de módulos de visualização (ex.: CanvasGrid).
        name: Título da simulação.
        model_params: Dicionário de parâmetros para a inicialização do modelo.
    """
    def __init__(self, model_cls, visualization_elements, name, model_params):
        self.model_cls = model_cls
        self.visualization_elements = visualization_elements
        self.name = name
        self.model_params = model_params

        # Porta padrão para o servidor
        self.port = 8521

        # Variáveis auxiliares
        self.model = None
        self._build_app()

    def _build_app(self):
        """
        Prepara as variáveis de template e configura os handlers do Tornado.
        """
        # Determina os caminhos dos templates e arquivos estáticos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, "templates")
        static_path = os.path.join(base_dir, "static")

        settings = {
            "template_path": template_path,
            "static_path": static_path,
            "title": self.name,
            # Outras configurações do Tornado podem ser adicionadas aqui
        }

        # Define os handlers para as rotas
        handlers = [
            (r"/", IndexHandler),
            (r"/data", DataHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings["static_path"]})
        ]

        # Cria a aplicação Tornado e associa o model_reporter, se disponível
        self.app = tornado.web.Application(handlers, **settings)
        # Atribui um método para obter os dados do modelo a cada tick.
        # Aqui, por simplicidade, usamos um lambda que retorna um dicionário vazio.
        # Em uma implementação real, isso deveria coletar dados dos módulos de visualização.
        self.app.model_reporter = lambda: {}

    def launch(self):
        """
        Inicializa o modelo, lança o servidor Tornado em uma thread separada e
        abre o navegador para exibir a interface.
        
        O loop principal chama repetidamente o método step() do modelo.
        """
        # Inicializa o modelo com os parâmetros fornecidos
        self.model = self.model_cls(**self.model_params)

        def run_app():
            self.app.listen(self.port)
            print("Server running on port %s" % self.port)
            tornado.ioloop.IOLoop.current().start()

        # Inicia o servidor em uma thread separada
        server_thread = threading.Thread(target=run_app)
        server_thread.daemon = True
        server_thread.start()

        # Abre automaticamente o navegador com a URL do servidor
        webbrowser.open("http://127.0.0.1:%s" % self.port)

        try:
            # Loop principal: a cada iteração, o modelo avança um step
            while True:
                self.model.step()
        except KeyboardInterrupt:
            print("Interrompido pelo usuário. Encerrando o servidor.")
            tornado.ioloop.IOLoop.current().stop()
