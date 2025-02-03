import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Gerando dados simulados
np.random.seed(42)
n_samples = 1000

data = {
    'velocidade_fuga': np.random.uniform(0, 50, n_samples),  # m/s
    'distancia_percorrida': np.random.uniform(0, 200, n_samples),  # metros
    'proximidade_agua': np.random.uniform(0, 1, n_samples),  # 0 = longe, 1 = perto
    'vocalizacao_aumento': np.random.randint(0, 2, n_samples),  # 0 = normal, 1 = aumento
}

df = pd.DataFrame(data)

# Definindo regra para indicar incêndio
# Se velocidade > 30, distância > 100, e aumento de vocalização, classifica como incêndio
limiar_fogo = (df['velocidade_fuga'] > 30) & (df['distancia_percorrida'] > 100) & (df['vocalizacao_aumento'] == 1)
df['incendio'] = limiar_fogo.astype(int)

# Separação em treino e teste
X = df.drop(columns=['incendio'])
y = df['incendio']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Treinando modelo de Random Forest
modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

# Predição e avaliação
y_pred = modelo.predict(X_test)
print("Acurácia:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Visualizando os dados
plt.figure(figsize=(10, 6))
plt.scatter(df['velocidade_fuga'], df['distancia_percorrida'], c=df['incendio'], cmap='coolwarm', alpha=0.6)
plt.xlabel("Velocidade de Fuga (m/s)")
plt.ylabel("Distância Percorrida (m)")
plt.title("Detecção de Incêndio Baseada no Comportamento Animal")
plt.colorbar(label='0 = Normal, 1 = Incêndio')
plt.show()
