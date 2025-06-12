# 🔥🌲 Simulador Integrado de Incêndios Florestais

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Mesa](https://img.shields.io/badge/Mesa-Multi--Agent-green.svg)
![PySide6](https://img.shields.io/badge/PySide6-GUI-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**🎯 Simulador avançado de incêndios florestais com agentes inteligentes e análise em tempo real**

[📚 Documentação](#-documentação) • [🚀 Instalação](#-instalação) • [▶️ Como Usar](#-como-usar) • [📊 Funcionalidades](#-funcionalidades)

</div>

---

## 🌟 Sobre o Projeto

Este simulador de incêndios florestais utiliza **inteligência artificial multi-agente** para modelar comportamentos realistas de propagação do fogo, estratégias de combate de bombeiros, e impactos ambientais. Desenvolvido como parte de investigação científica, oferece uma plataforma completa para análise e estudo de dinâmicas de incêndios florestais.

### ✨ Destaques

- 🤖 **Agentes Inteligentes**: Bombeiros com diferentes técnicas e estratégias
- 🌍 **Modelagem Ambiental**: Condições climáticas, vento, humidade, precipitação
- 📈 **Análise em Tempo Real**: Gráficos dinâmicos de evolução do incêndio
- 🎮 **Interface Intuitiva**: Controles visuais e monitorização detalhada
- 🔬 **Base Científica**: Algoritmos baseados em investigação académica

---

## 🚀 Instalação

### 📋 Pré-requisitos

- **Python 3.8+** instalado no sistema
- **pip** (gestor de pacotes Python)
- **Git** (para clonar o repositório)

### 🔧 Passo a Passo

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd Bolsa_Investigacao
   ```

2. **Instale as dependências**
   
   **Opção A: Instalação automática (recomendado)**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Opção B: Instalação manual**
   ```bash
   pip install mesa PySide6 matplotlib numpy scipy
   ```

3. **Verifique a instalação**
   ```bash
   python src/main.py --version
   ```

### 🐳 Instalação com Docker (Opcional)

```bash
# Construir a imagem
docker build -t simulador-incendios .

# Executar o container
docker run -p 5000:5000 simulador-incendios
```

---

## ▶️ Como Usar

### 🎯 Execução Básica

1. **Inicie a aplicação**
   ```bash
   cd src
   python main.py
   ```

2. **Configure os parâmetros**
   - 🌡️ **Condições Climáticas**: Temperatura, vento, humidade
   - 🌳 **Densidade Florestal**: Percentagem de cobertura vegetal
   - 🚒 **Bombeiros**: Número e tipo de agentes
   - 🏞️ **Ambiente**: Floresta, estrada, rio

3. **Execute a simulação**
   - Clique em **"Setup"** para preparar o ambiente
   - Clique em **"Iniciar Simulação"** para começar
   - Use **"Pausar"** e **"Parar"** para controlar a execução

### 🎛️ Controlos Principais

| Controlo | Função |
|----------|--------|
| **Setup** | Configura o ambiente com os parâmetros atuais |
| **Iniciar Simulação** | Começa a simulação automática |
| **⏸️ Pausar** | Pausa a simulação em execução |
| **Próximo Passo** | Executa um step manual (passo-a-passo) |
| **Iniciar Fogo** | Acende um foco de incêndio aleatório |
| **Parar Fogo** | Extingue todos os focos ativos |
| **Ver Gráficos** | Abre janelas de análise detalhada |

### 📊 Interpretação dos Resultados

#### 🎨 Cores da Simulação
- 🟫 **Castanho**: Terreno vazio
- 🟢 **Verde**: Floresta intacta
- 🔴 **Vermelho**: Fogo ativo
- ⚫ **Preto**: Área queimada
- 🔵 **Azul**: Bombeiros
- 🟡 **Amarelo**: Sirenes/Alertas

#### 📈 Gráficos Disponíveis
- **Evolução do Incêndio**: Área queimada vs. tempo
- **Qualidade do Ar**: Níveis de CO, CO₂, PM2.5, PM10, O₂
- **Condições Climáticas**: Temperatura, humidade, precipitação
- **Trajetórias**: Movimento de fagulhas e bombeiros
- **Mapas Estratégicos**: Pontos de início e linhas de corte

---

## 📊 Funcionalidades

### 🤖 Sistema Multi-Agente

#### 🚒 Bombeiros Inteligentes
- **Bombeiros de Água**: Ataque direto aos focos
- **Bombeiros Técnicos**: Estratégias preventivas e linhas de corte
- **Comportamentos**: Navegação, combate, evacuação, retorno à base

#### 🌬️ Agente Ambiental
- Monitorização da qualidade do ar
- Simulação de dispersão de poluentes
- Influência na propagação do fogo

#### 🌳 Patches Inteligentes
- Diferentes tipos de vegetação (eucalipto, pinheiro)
- Propagação realista do fogo
- Interação com condições ambientais

### 🌍 Modelagem Ambiental

| Parâmetro | Influência | Configurável |
|-----------|------------|--------------|
| **Temperatura** | Velocidade de propagação | ✅ |
| **Vento** | Direção e intensidade do fogo | ✅ |
| **Humidade** | Resistência à ignição | ✅ |
| **Precipitação** | Extinção natural | ✅ |
| **Densidade Florestal** | Combustível disponível | ✅ |
| **Tipo de Árvore** | Inflammabilidade | ✅ |

### 📈 Sistema de Análise

- **Tempo Real**: Monitorização durante a simulação
- **Histórico**: Dados completos para análise posterior
- **Exportação**: Gráficos e dados em formatos padrão
- **Comparação**: Múltiplos cenários e estratégias

---

## 📚 Documentação

### 📖 Documentação Técnica

- **[📋 Estrutura do Código](Documentação/ESTRUTURA_CODIGO.md)**: Arquitetura detalhada do sistema
- **[⏸️ Funcionalidade de Pausa](Documentação/FUNCIONALIDADE_PAUSA.md)**: Controles avançados de simulação
- **[🔬 Post Científico](Documentação/Post_Cientifico.pdf)**: Post de demonstração
- **[🔬 Artigo Científico](Documentação/Artigo_Cientifico.pdf)**: Demonstração teórica
- **[📋 Plano de Trabalho](Documentação/PlanoTrabalho.pdf)**: Metodologia e objetivos
- **[📋 Relatório](Documentação/Relatorio.pdf)**: Documentação

### 🎓 Exemplos de Uso

#### Simulação Básica
```python
# Configuração simples
python src/main.py
# Configure: Densidade=0.7, Bombeiros=4, Ambiente="only_trees"
```

#### Cenário Complexo
```python
# Ambiente com rio, condições adversas
# Configure: Rio, Vento=15 m/s, Temperatura=35°C, Humidade=20%
```

#### Análise Comparativa
```bash
# Execute múltiplas simulações alterando apenas um parâmetro
# Compare resultados usando os gráficos gerados
```

---

## 🔧 Configuração Avançada

### ⚙️ Parâmetros Detalhados

```python
# Configurações no código (main.py)
WORLD_WIDTH = 125          # Largura do grid
WORLD_HEIGHT = 108         # Altura do grid
DEFAULT_DENSITY = 0.5      # Densidade florestal padrão
NUM_FIREFIGHTERS = 4       # Número de bombeiros
CELL_SIZE = 5             # Tamanho visual das células
```

### 🎯 Personalização de Agentes

```python
# Bombeiros personalizados (firefighter_agent.py)
extinguish_capacity = 2    # Capacidade de extinção
urgency_threshold = 4      # Distância crítica para mudança de estratégia
max_firebreak_length = 15  # Comprimento máximo das linhas de corte
```

---

## 🧪 Cenários de Teste

### 📁 Simulações Pré-configuradas

O projeto inclui cenários pré-definidos na pasta `Simulações/`:

- **🎯 Estratégias de Combate**
  - `Bombeiros_Diretos/`: Apenas ataques diretos
  - `Bombeiros_Indiretos/`: Estratégias preventivas
  - `Bombeiros_Equilibrado/`: Combinação de técnicas

- **🌤️ Condições Climáticas**
  - `Quente_Seco/`: Condições de alto risco
  - `Ameno_Chuvoso/`: Condições favoráveis
  - `Rio_MuitoVentoso/`: Vento extremo com barreira natural

### 🔬 Validação Científica

- Comparação com simulações NetLogo (pasta `src/Netlogo/`)
- Validação de comportamentos dos agentes
- Análise estatística de resultados

---

## 🤝 Contribuição

### 🐛 Reportar Problemas

1. Verifique os [issues existentes](../../issues)
2. Crie um novo issue com:
   - Descrição do problema
   - Passos para reproduzir
   - Versão do Python e sistema operativo
   - Logs de erro (se aplicável)

### 💡 Sugerir Melhorias

1. Fork do repositório
2. Crie uma branch para a funcionalidade
3. Implemente as alterações
4. Adicione testes (se aplicável)
5. Submeta um Pull Request

### 📧 Contacto

- **Investigador Principal**: David Fidalgo
- **Instituição**: INESCTEC
- **Email**: [david.fidalgo1010@hotmail.com]

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**. Consulte o ficheiro [LICENSE](LICENSE) para mais detalhes.

```
MIT License

Copyright (c) 2025 David Fidalgo - INESCTEC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## 🎉 Agradecimentos

- **INESCTEC** - Apoio institucional
- **Mesa Framework** - Base para sistema multi-agente
- **PySide6/Qt** - Interface gráfica robusta
- **Matplotlib** - Visualização de dados científicos
- **Comunidade Python** - Bibliotecas e ferramentas

---

<div align="center">

**⭐ Se este projeto foi útil, deixe uma estrela! ⭐**

</div>
