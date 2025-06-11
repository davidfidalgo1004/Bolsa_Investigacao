# 🚀 Guia de Início Rápido

## ⚡ Execução em 3 Passos

### 1. **Instalar Dependências**
```bash
pip install mesa PySide6 matplotlib numpy
```

### 2. **Executar o Simulador**
```bash
cd src
python main.py
```

### 3. **Configurar e Executar**
1. Ajuste os sliders conforme desejado
2. Clique em **"Setup"**
3. Clique em **"Iniciar Simulação"**

---

## 🎛️ Configurações Recomendadas

### 🌲 **Simulação Básica (Iniciantes)**
- **Densidade Florestal**: 70%
- **Bombeiros**: 4 (2 água + 2 técnicos)
- **Ambiente**: Apenas Árvores
- **Temperatura**: 25°C
- **Vento**: 5 m/s
- **Humidade**: 50%

### 🔥 **Cenário de Alto Risco**
- **Densidade Florestal**: 80%
- **Bombeiros**: 6 (3 água + 3 técnicos)
- **Ambiente**: Floresta com Rio
- **Temperatura**: 35°C
- **Vento**: 15 m/s
- **Humidade**: 20%

### 🌧️ **Condições Favoráveis**
- **Densidade Florestal**: 60%
- **Bombeiros**: 2 (1 água + 1 técnico)
- **Ambiente**: Floresta com Estrada
- **Temperatura**: 20°C
- **Vento**: 3 m/s
- **Humidade**: 80%
- **Precipitação**: 40%

---

## 📊 Como Interpretar os Resultados

### **Durante a Simulação**
- **Verde**: Floresta saudável 🌳
- **Vermelho**: Fogo ativo 🔥
- **Preto**: Área queimada ⚫
- **Azul**: Bombeiros 🚒
- **Amarelo**: Linhas de corte ⚡

### **Métricas Importantes**
- **Área Queimada**: Menor = melhor performance
- **Tempo de Extinção**: Mais rápido = estratégia eficaz
- **Qualidade do Ar**: Monitorar picos de poluição
- **Eficácia dos Bombeiros**: Observar estados (atacando/movendo)

---

## 🛠️ Resolução de Problemas Comuns

### **❌ Erro: "No module named 'mesa'"**
```bash
pip install mesa
```

### **❌ Interface não abre**
```bash
pip install --upgrade PySide6
```

### **❌ Gráficos não aparecem**
```bash
pip install matplotlib
```

### **❌ Simulação muito lenta**
- Reduza o tamanho do grid (world_width/height no código)
- Diminua o número de bombeiros
- Feche outras aplicações

---

## 🎯 Experimentos Sugeridos

### **Teste 1: Impacto do Vento**
1. Execute com vento 5 m/s
2. Execute com vento 15 m/s
3. Compare a propagação do fogo

### **Teste 2: Estratégias de Bombeiros**
1. Use apenas bombeiros de água
2. Use apenas bombeiros técnicos
3. Use uma combinação equilibrada

### **Teste 3: Densidade Florestal**
1. Teste com 40% de densidade
2. Teste with 80% de densidade
3. Observe a diferença na velocidade de propagação

---

## 📈 Próximos Passos

Após dominar o básico:

1. **📋 Leia a [Estrutura do Código](ESTRUTURA_CODIGO.md)** para entender a arquitetura
2. **🔧 Personalize parâmetros** no código fonte
3. **📊 Analise dados** exportados das simulações
4. **🧪 Crie cenários** personalizados

---

## 💡 Dicas Avançadas

- **Ctrl+C** para parar a simulação rapidamente
- Use **"Próximo Passo"** para análise detalhada frame-a-frame
- **"Ver Gráficos"** funciona melhor após completar a simulação
- Experimente diferentes posições de bombeiros editando o código

---

*✨ Está pronto para simular incêndios florestais! Boa sorte! ✨* 