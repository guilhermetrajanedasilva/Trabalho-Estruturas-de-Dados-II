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
# 2. ENGENHARIA DE FEATURES (MÉTRICA RELATIVA DA TAREFA 4)
# ==============================================================================
# Se a nova métrica 'delta_z_robusto' não existir no dataset, ela é calculada
# como a variação temporal do z_robusto agrupada por fluxo (se disponível)
if "delta_z_robusto" not in df.columns:
    if "z_robusto" in df.columns:
        if "id_fluxo" in df.columns:
            df["delta_z_robusto"] = df.groupby("id_fluxo")["z_robusto"].diff().fillna(0)
        else:
            df["delta_z_robusto"] = df["z_robusto"].diff().fillna(0)
        print("Métrica relativa 'delta_z_robusto' criada com sucesso.")

# ==============================================================================
# 3. ISOLAMENTO DAS FEATURES NUMÉRICAS E ALVO
# ==============================================================================
coluna_alvo = "alvo" if "alvo" in df.columns else df.columns[-1]
y = df[coluna_alvo]

X_bruto = df.drop(columns=[coluna_alvo])

# Metadados e colunas de rota/identificação a excluir obrigatoriamente
EXCLUIR_NOME = ["id_fluxo", "anchor_id", "probe_id", "timestamp", "split", "classe_atual", "rota_id", "pais", "ip"]
X_filtrado = X_bruto.drop(columns=[c for c in EXCLUIR_NOME if c in X_bruto.columns])

# Selecionar apenas atributos numéricos (relativos)
X = X_filtrado.select_dtypes(include=["number"]).fillna(-1)

# Divisão temporal por split
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
# 4. TREINAMENTO DA ÁRVORE DE DECISÃO AJUSTADA (TAREFA 4)
# ==============================================================================
print("\nA treinar a Árvore de Decisão ajustada (max_depth=6, min_samples_leaf=50, ccp_alpha=0.001)...")
modelo_t4 = DecisionTreeClassifier(
    criterion="gini",
    max_depth=6,
    min_samples_leaf=50,
    ccp_alpha=0.001,
    class_weight="balanced",
    random_state=42
)

# O ajuste é feito EXCLUSIVAMENTE no conjunto de treino
modelo_t4.fit(X_treino, y_treino)

# ==============================================================================
# 5. AVALIAÇÃO NO CONJUNTO DE VALIDAÇÃO
# ==============================================================================
previsoes_val = modelo_t4.predict(X_val)

print("\n" + "="*50)
print("RELATÓRIO DE CLASSIFICAÇÃO — TAREFA 4 (VALIDAÇÃO)")
print("="*50)
print(classification_report(y_val, previsoes_val, digits=4))

print("\nMATRIZ DE CONFUSÃO (VALIDAÇÃO):")
labels = sorted(y_val.unique())
matriz = confusion_matrix(y_val, previsoes_val, labels=labels)
df_matriz = pd.DataFrame(matriz, index=[f"Real: {l}" for l in labels], columns=[f"Prev: {l}" for l in labels])
print(df_matriz)

# ==============================================================================
# 6. SALVAMENTO DO FICHEIRO .JOBLIB
# ==============================================================================
caminho_saida = "arvore_decisao_tarefa4.joblib"
joblib.dump(modelo_t4, caminho_saida)

print(f"\nSucesso! O ficheiro oficial da Tarefa 4 '{caminho_saida}' foi gerado.")
