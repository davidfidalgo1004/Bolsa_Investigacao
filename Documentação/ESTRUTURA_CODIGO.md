# 📋 Estrutura e Organização do Código

## 📂 Visão Geral da Estrutura

```
Bolsa_Investigacao/
├── 📁 src/                           # Código principal da aplicação
│   ├── 📄 main.py                   # Ponto de entrada - Interface gráfica principal
│   ├── 📁 Agents/                   # Agentes inteligentes do sistema
│   │   ├── 📄 agentes.py           # Agentes de ar e patches do terreno
│   │   └── 📄 firefighter_agent.py # Agentes bombeiros com diferentes técnicas
│   ├── 📁 Environment/              # Modelo do ambiente de simulação
│   │   └── 📄 ambiente.py          # Modelo principal do ambiente
│   ├── 📁 components/               # Componentes auxiliares da aplicação
│   │   ├── 📁 objects/             # Objetos e widgets personalizados
│   │   │   ├── 📄 GraficoAnalise.py # Janelas de gráficos e análises
│   │   │   └── 📄 bossula.py       # Widget de bússola para direção do vento
│   │   ├── 📁 settings/            # Configurações e utilitários
│   │   │   ├── 📄 AlertIncendio.py # Sistema de alertas
│   │   │   ├── 📄 ProbVento.py     # Cálculos de probabilidade do vento
│   │   │   └── 📄 MapColor.py      # Mapeamento de cores para visualização
│   │   └── 📁 assets/              # Recursos visuais (ícones, imagens)
│   ├── 📁 Tests/                   # Testes automatizados
│   └── 📁 Netlogo/                 # Comparação com NetLogo (referência)
├── 📁 Simulações/                   # Resultados de simulações organizados
│   ├── 📁 Bombeiros_Diretos/       # Simulações com estratégia direta
│   ├── 📁 Bombeiros_Indiretos/     # Simulações com estratégia indireta
│   ├── 📁 Bombeiros_Equilibrado/   # Simulações com estratégia equilibrada
│   └── 📁 [Condições Climáticas]/  # Simulações por tipo de clima
└── 📁 Documentação/                # Documentação do projeto
    ├── 📄 Post_Cientifico.pdf      # Artigo científico
    └── 📄 PlanoTrabalho.docx       # Plano de trabalho
```

## 🏗️ Arquitetura do Sistema

### 1. **Padrão Arquitetural: Model-View-Controller (MVC)**

- **Model**: `Environment/ambiente.py` - Lógica de negócio e estado da simulação
- **View**: `main.py` - Interface gráfica e visualização 
- **Controller**: `main.py` + `Agents/` - Controle de fluxo e agentes inteligentes

### 2. **Sistema Multi-Agente (Mesa Framework)**

O projeto utiliza o framework Mesa para implementar um sistema multi-agente onde diferentes entidades interagem:

#### **Agentes Principais:**

##### 🚒 **FirefighterAgent** (`Agents/firefighter_agent.py`)
- **Responsabilidade**: Combate ao fogo com diferentes técnicas
- **Técnicas**:
  - `"water"`: Bombeiros com água (ataque direto)
  - `"alternative"`: Bombeiros técnicos (estratégia preventiva)
- **Estados**: idle, navigating, direct_attack, firebreak, evacuated, returning_home
- **Comportamentos**:
  - Navegação inteligente em direção ao fogo
  - Criação de linhas de corte (firebreaks)
  - Evacuação em situações perigosas
  - Retorno à base quando não há fogo

##### 🌬️ **AirAgent** (`Agents/agentes.py`)
- **Responsabilidade**: Modelagem da qualidade do ar
- **Monitora**: CO, CO₂, PM2.5, PM10, O₂
- **Influencia**: Dispersão de fagulhas e propagação do fogo

##### 🌳 **PatchAgent** (`Agents/agentes.py`)
- **Responsabilidade**: Representação de cada célula do terreno
- **Estados**: empty, forested, burning, burned, road, river, firebreak
- **Tipos de Árvore**: eucalyptus, pine (com diferentes inflammabilidades)
- **Propriedades**: altitude, humidade, densidade

### 3. **Modelo de Ambiente** (`Environment/ambiente.py`)

#### **EnvironmentModel - Classe Principal**
```python
class EnvironmentModel:
    - Gerencia o grid espacial (MultiGrid)
    - Coordena todos os agentes
    - Controla parâmetros ambientais:
      * Temperatura
      * Direção e velocidade do vento  
      * Precipitação e humidade
    - Tipos de ambiente:
      * "only_trees": Apenas floresta
      * "road_trees": Floresta com estrada
      * "river_trees": Floresta with rio
```

## 🎮 Interface Gráfica (`main.py`)

### **SimulationApp - Classe Principal da UI**

#### **Componentes da Interface:**

1. **🎛️ Painel de Controles**
   - Sliders para configuração de parâmetros
   - Botões de controle (Setup, Iniciar, Parar)
   - Seleção de tipos de ambiente

2. **🗺️ Visualização da Simulação**
   - Grid visual com cores representando estados
   - Ícones para bombeiros e sirenes
   - Atualização em tempo real

3. **📊 Painel de Monitorização**
   - Status dos bombeiros
   - Parâmetros ambientais em tempo real
   - Bússola para direção do vento

4. **📈 Sistema de Gráficos**
   - Evolução de áreas queimadas
   - Qualidade do ar
   - Condições climáticas
   - Trajetórias de fagulhas

## 🔧 Componentes Auxiliares

### **📊 Análise de Dados** (`components/objects/GraficoAnalise.py`)
- **GraphWindow**: Gráficos de evolução temporal
- **FragulhaArrowsWindow**: Visualização de trajetórias
- **FireStartWindow**: Mapa de pontos de início de fogo
- **FirebreakMapWindow**: Mapa de linhas de corte

### **🧭 Widgets Personalizados** (`components/objects/bossula.py`)
- **CompassWidget**: Bússola visual para direção do vento

### **⚙️ Configurações** (`components/settings/`)
- **MapColor.py**: Sistema de cores para diferentes estados
- **ProbVento.py**: Cálculos probabilísticos do vento
- **AlertIncendio.py**: Sistema de alertas e notificações

## 🔄 Fluxo de Execução

### **1. Inicialização**
```
main.py → SimulationApp.__init__()
├── Criação da interface gráfica
├── Inicialização do EnvironmentModel
└── Configuração dos agentes iniciais
```

### **2. Setup da Simulação**
```
setup_model() 
├── Reconfigura parâmetros ambientais
├── Posiciona bombeiros conforme configuração
└── Prepara o ambiente para simulação
```

### **3. Loop Principal de Simulação**
```
simulation_step()
├── model.step() → Executa um passo de todos os agentes
├── update_grid() → Atualiza visualização
├── Coleta métricas para gráficos
└── Verifica condições de parada
```

### **4. Execução dos Agentes (por step)**
```
Para cada agente no scheduler:
├── PatchAgent: Propagação do fogo, evaporação
├── FirefighterAgent: Decisões estratégicas, movimento, combate
└── AirAgent: Atualização da qualidade do ar
```

## 🎯 Padrões de Design Utilizados

### **1. Observer Pattern**
- Interface gráfica observa mudanças no modelo
- Atualização automática da visualização

### **2. Strategy Pattern**
- Diferentes técnicas de combate aos bombeiros
- Múltiplos tipos de ambiente

### **3. State Pattern**
- Estados dos patches (forested → burning → burned)
- Estados dos bombeiros (idle → navigating → attacking)

### **4. Factory Pattern**
- Criação de agentes com diferentes configurações
- Geração de diferentes tipos de terreno

## 📊 Sistema de Dados

### **Métricas Coletadas:**
- **Fogo**: Área queimada, área florestal, pontos de início
- **Ar**: Níveis de poluentes (CO, CO₂, PM2.5, PM10, O₂)
- **Clima**: Temperatura, humidade, precipitação
- **Bombeiros**: Posições, estados, eficácia

### **Estruturas de Dados:**
```python
# Evolução temporal
self.burned_area_evol: List[int]
self.air_co_evol: List[float] 
self.temp_evol: List[float]

# Histórico espacial
self.fire_start_positions: List[Tuple[int, int]]
self.fragulha_history: Dict[pos, List[trajectory]]
```

## 🚀 Extensibilidade

O sistema foi projetado para ser facilmente extensível:

### **Novos Tipos de Agentes:**
1. Herdar de `mesa.Agent`
2. Implementar método `step()`
3. Adicionar ao scheduler em `EnvironmentModel`

### **Novas Estratégias de Combate:**
1. Estender `FirefighterAgent`
2. Adicionar nova técnica no parâmetro `technique`
3. Implementar lógica específica no método `step()`

### **Novos Tipos de Ambiente:**
1. Adicionar tipo em `env_type`
2. Implementar lógica em `_make_forest_patch()`
3. Atualizar interface para nova opção

## 🧪 Testes e Validação

### **Estrutura de Testes** (`src/Tests/`)
- Testes unitários para componentes individuais
- Validação de comportamentos dos agentes
- Verificação de integridade dos dados

### **Simulações de Referência** (`Simulações/`)
- Cenários pré-definidos para validação
- Comparação com resultados esperados
- Análise de performance em diferentes condições

---

*Esta documentação fornece uma visão completa da arquitetura e organização do simulador de incêndios florestais, facilitando a manutenção, extensão e compreensão do sistema.* 