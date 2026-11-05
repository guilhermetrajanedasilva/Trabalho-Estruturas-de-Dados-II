import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score, balanced_accuracy_score
from sklearn.tree import DecisionTreeClassifier, _tree

CLASSES = ["OK", "RISCO", "FALHA"]
# Tarefa 3: colunas que a árvore oficial pode usar (todas relativas ao baseline do fluxo)
COLUNAS_OFICIAIS = ["z_robusto", "aumento_pct", "jitter_relativo", "perda_pct",
                    "timeout_atual", "n5_timeout", "n5_aumento80", "n5_risco"]
# Tarefa 4: coluna relativa nova (tendência do z_robusto), calculada só com o passado do fluxo
COLUNA_NOVA = "delta_z_robusto"
# Nunca entram na árvore oficial
PROIBIDAS = ["fluxo_id", "timestamp", "rtt_ms", "jitter_ms", "split", "classe", "regra_disparada",
             "criterio_risco_atual", "probe_pais", "anchor_pais", "probe_cidade", "anchor_cidade",
             "dst_addr", "par_id", "rota_id"]


def pastas(base: Path) -> dict:
    p = {"base": base, "config": base / "config", "processed": base / "data" / "processed",
         "interim": base / "data" / "interim", "reports": base / "reports", "models": base / "models"}
    for k in ("reports", "models"):
        p[k].mkdir(parents=True, exist_ok=True)
    return p


def carregar_dataset(p: dict) -> pd.DataFrame:
    """Dataset rotulado do Período B (Tarefa 2), ordenado por fluxo e tempo, com a coluna nova de tendência."""
    caminho = p["processed"] / "dataset_rotulado_B.csv"
    if not caminho.exists():
        sys.exit(f"Dataset da Tarefa 2 não encontrado: {caminho}\nRode antes: baseline_rotulagem.py")
    d = pd.read_csv(caminho, dtype={"fluxo_id": str}, parse_dates=["timestamp"])
    d = d.sort_values(["fluxo_id", "timestamp"]).reset_index(drop=True)
    # tendência do z_robusto: diferença para a medição anterior do MESMO fluxo (só passado, dentro do Período B).
    # Vazia na 1ª medição do fluxo e quando uma das duas é timeout (z ausente). Nunca preenchida com 0.
    d[COLUNA_NOVA] = d.groupby("fluxo_id")["z_robusto"].diff()
    return d


def auditoria_rotas(p: dict) -> pd.DataFrame:
    """País/cidade por fluxo. SÓ para a árvore de contraste e para auditoria — nunca para a árvore oficial."""
    return pd.read_csv(p["interim"] / "auditoria_fluxos.csv", dtype={"fluxo_id": str})


def blocos(d: pd.DataFrame, usar_teste: bool = False) -> tuple:
    """Treino e validação. O teste só é devolvido se for pedido explicitamente (Tarefa 5)."""
    tr = d[d["split"] == "treino"]
    va = d[d["split"] == "validacao"]
    te = d[d["split"] == "teste"] if usar_teste else None
    return tr, va, te


def nova_arvore(cfg: dict) -> DecisionTreeClassifier:
    return DecisionTreeClassifier(
        criterion=cfg.get("criterion", "gini"),
        max_depth=cfg.get("max_depth"),
        min_samples_leaf=cfg.get("min_samples_leaf", 1),
        ccp_alpha=cfg.get("ccp_alpha", 0.0),
        class_weight=cfg.get("class_weight"),
        random_state=cfg.get("random_state", 42),
    )  # NaN é aceito nativamente (timeout deixa z_robusto/aumento_pct vazios; não é preenchido com 0)


def avaliar(y_real, y_prev) -> dict:
    cm = confusion_matrix(y_real, y_prev, labels=CLASSES)
    prec, rec, f1, sup = precision_recall_fscore_support(y_real, y_prev, labels=CLASSES, zero_division=0)
    return {
        "matriz": cm.tolist(),
        "precisao": dict(zip(CLASSES, prec.round(4))), "recall": dict(zip(CLASSES, rec.round(4))),
        "f1": dict(zip(CLASSES, f1.round(4))), "suporte": dict(zip(CLASSES, sup.astype(int).tolist())),
        "f1_macro": round(float(np.mean(f1)), 4),
        "acuracia": round(float(accuracy_score(y_real, y_prev)), 4),
        "acuracia_balanceada": round(float(balanced_accuracy_score(y_real, y_prev)), 4),
    }


def matriz_md(m: dict) -> str:
    cm = m["matriz"]
    linhas = ["| Real \\ Previsto | OK | RISCO | FALHA | Total real |", "|---|---:|---:|---:|---:|"]
    for i, c in enumerate(CLASSES):
        linhas.append(f"| **{c}** | {cm[i][0]:,} | {cm[i][1]:,} | {cm[i][2]:,} | {sum(cm[i]):,} |".replace(",", "."))
    tot = [sum(cm[i][j] for i in range(3)) for j in range(3)]
    linhas.append(f"| **Total previsto** | {tot[0]:,} | {tot[1]:,} | {tot[2]:,} | {sum(tot):,} |".replace(",", "."))
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# Regras da árvore em português (copiadas da árvore, não inventadas)
# --------------------------------------------------------------------------- #
def _fmt(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def regras_folhas(arvore: DecisionTreeClassifier, colunas: list) -> pd.DataFrame:
    """Uma linha por folha: condições do caminho (limiares repetidos da mesma coluna fundidos), classe, amostras e pureza."""
    t = arvore.tree_
    classes = list(arvore.classes_)
    saida = []

    def descer(no, limites):
        if t.feature[no] == _tree.TREE_UNDEFINED:
            valores = t.value[no][0]
            valores = valores / valores.sum()
            k = int(np.argmax(valores))
            conds = []
            for nome in colunas:
                if nome in limites:
                    baixo, alto = limites[nome]
                    if baixo > -np.inf and alto < np.inf:
                        conds.append(f"{_fmt(baixo)} < {nome} <= {_fmt(alto)}")
                    elif alto < np.inf:
                        conds.append(f"{nome} <= {_fmt(alto)}")
                    else:
                        conds.append(f"{nome} > {_fmt(baixo)}")
            saida.append({"condicoes": conds, "classe": classes[k], "amostras": int(t.n_node_samples[no]),
                          "pureza": round(float(valores[k]), 4)})
            return
        nome, lim = colunas[t.feature[no]], t.threshold[no]
        baixo, alto = limites.get(nome, (-np.inf, np.inf))
        descer(t.children_left[no], {**limites, nome: (baixo, min(alto, lim))})
        descer(t.children_right[no], {**limites, nome: (max(baixo, lim), alto)})

    descer(0, {})
    df = pd.DataFrame(saida)
    df["regra"] = df.apply(lambda r: ("SE " + " E ".join(r["condicoes"]) if r["condicoes"] else "SEMPRE")
                           + f" ENTÃO {r['classe']}", axis=1)
    return df


def resumo_arvore(arvore, colunas) -> dict:
    t = arvore.tree_
    raiz = {"coluna": colunas[t.feature[0]], "limiar": round(float(t.threshold[0]), 4)} if t.feature[0] >= 0 else None
    # primeiras divisões (nível 1)
    nivel1 = []
    for filho in (t.children_left[0], t.children_right[0]):
        if t.feature[filho] != _tree.TREE_UNDEFINED:
            nivel1.append({"coluna": colunas[t.feature[filho]], "limiar": round(float(t.threshold[filho]), 4)})
    imp = pd.Series(arvore.feature_importances_, index=colunas).sort_values(ascending=False)
    return {"profundidade_obtida": int(arvore.get_depth()), "folhas": int(arvore.get_n_leaves()),
            "raiz": raiz, "divisoes_nivel_1": nivel1,
            "importancias": {k: round(float(v), 4) for k, v in imp.items() if v > 0}}


def gravar_json(caminho: Path, conteudo):
    caminho.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
