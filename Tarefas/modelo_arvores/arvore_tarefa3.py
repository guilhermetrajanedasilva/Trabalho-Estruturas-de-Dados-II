import os
import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, confusion_matrix

# ==============================================================================
# 1. LOCALIZAÇÃO E CARREGAMENTO DO DATASET
# ==============================================================================
caminho_csv = "data/raw/dados_finais_resumo_amostra.csv"

if not os.path.exists(caminho_csv) and os.path.exists(f"../{caminho_csv}"):
    caminho_csv = f"../{caminho_csv}"

if not os.path.exists(caminho_csv):
    raise FileNotFoundError(f"Ficheiro não localizado em: {caminho_csv}")

print(f"A carregar dataset real em: '{caminho_csv}'...")
df = pd.read_csv(caminho_csv)

# ==============================================================================
# 2. ISOLAMENTO DAS FEATURES NUMÉRICAS E ALVO
# ==============================================================================
# Identificar a coluna alvo
coluna_alvo = "alvo" if "alvo" in df.columns else df.columns[-1]
y = df[coluna_alvo]

# Remover a coluna alvo do DataFrame de atributos
X_bruto = df.drop(columns=[coluna_alvo])

# Metadados/colunas conhecidas a excluir
EXCLUIR_NOME = ["id_fluxo", "anchor_id", "probe_id", "timestamp", "split", "classe_atual"]
X_filtrado = X_bruto.drop(columns=[c for c in EXCLUIR_NOME if c in X_bruto.columns])

# FILTRO FUNDAMENTAL: Selecionar APENAS colunas numéricas (float/int), descartando nomes de cidades/texto
X = X_filtrado.select_dtypes(include=["number"]).fillna(-1)

# Divisão por split se existir, senão usa todo o conjunto
if "split" in df.columns:
    mask_treino = df["split"] == "treino"
    mask_val = df["split"] == "validação"
    X_treino, y_treino = X[mask_treino], y[mask_treino]
    X_val, y_val = X[mask_val], y[mask_val]
else:
    X_treino, y_treino = X, y
    X_val, y_val = X, y

print(f"Amostras para treino: {len(X_treino)} | Features numéricas utilizadas: {X_treino.shape[1]}")
print(f"Colunas utilizadas: {list(X_treino.columns)}")

# ==============================================================================
# 3. TREINAMENTO DA ÁRVORE DE DECISÃO (CART)
# ==============================================================================
print("A treinar a Árvore de Decisão oficial (max_depth=8, min_samples_leaf=20)...")
modelo = DecisionTreeClassifier(
    criterion="gini",
    max_depth=8,
    min_samples_leaf=20,
    class_weight="balanced",
    random_state=42
)

modelo.fit(X_treino, y_treino)

# ==============================================================================
# 4. AVALIAÇÃO NO CONJUNTO DE VALIDAÇÃO
# ==============================================================================
previsoes_val = modelo.predict(X_val)

print("\n" + "="*50)
print("RELATÓRIO DE CLASSIFICAÇÃO")
print("="*50)
print(classification_report(y_val, previsoes_val, digits=4))

# ==============================================================================
# 5. SALVAMENTO DO FICHEIRO .JOBLIB
# ==============================================================================
caminho_saida = "arvore_decisao_tarefa3.joblib"
joblib.dump(modelo, caminho_saida)

print(f"\nSucesso! O ficheiro oficial '{caminho_saida}' foi gerado a partir dos dados reais.")
