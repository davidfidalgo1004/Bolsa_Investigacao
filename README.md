# 🔥🌲 Simulador Integrado de Incêndios Florestais

Este projeto é um simulador detalhado de incêndios florestais, utilizando agentes inteligentes que modelam comportamentos de bombeiros, dispersão de fagulhas e interação ambiental, com interface gráfica intuitiva e geração de gráficos analíticos.
A ser desenvolvido pela INESCTEC.

## 📌 Características

* Simulação detalhada com diferentes tipos de ambiente (apenas árvores, árvores com estrada, árvores com rio)
* Bombeiros inteligentes com técnicas de combate variadas (direto, indireto, criação de linhas de corte)
* Modelagem precisa da influência ambiental (vento, precipitação, humidade, temperatura)
* Interface gráfica interativa com visualização dinâmica
* Análise gráfica de evolução do incêndio, qualidade do ar e condições ambientais

## 🛠️ Tecnologias

* Python
* Mesa Framework (Agentes)
* PySide6 (Interface Gráfica)
* Matplotlib (Análise de Dados)

## 🚀 Instalação

1. Clona o repositório:

```bash
git clone <url-do-teu-repositorio>
cd <diretorio-do-projeto>
```

2. Instala as dependências:

```bash
pip install -r requirements.txt
```

Se o ficheiro `requirements.txt` não existir, instala manualmente:

```bash
pip install mesa PySide6 matplotlib numpy
```

## ▶️ Como Executar

1. Inicializa a aplicação:

```bash
python main.py
```

2. Na interface gráfica:

   * Configura os parâmetros desejados (iteração, densidade florestal, condições climáticas).
   * Pressiona **Setup** para configurar o ambiente inicial.
   * Pressiona **Iniciar Simulação** para executar a simulação.

3. Observa o comportamento em tempo real e analisa os resultados após a execução.

## 📈 Análise de Resultados

Após a simulação, serão automaticamente apresentados gráficos:

* Evolução das áreas queimadas e florestadas.
* Qualidade do ar (níveis de CO, CO₂, PM2.5, PM10 e O₂).
* Condições climáticas (temperatura, humidade, precipitação).
* Mapas de altitude e altura das árvores.
* Trajetórias detalhadas das fagulhas.
* Pontos de início do incêndio e linhas de corte criadas pelos bombeiros.


## 📄 Licença

Este projeto está licenciado sob a licença MIT. Consulta [LICENSE](LICENSE) para mais informações.

---

✨ Desenvolvido por \David Fidalgo ✨
