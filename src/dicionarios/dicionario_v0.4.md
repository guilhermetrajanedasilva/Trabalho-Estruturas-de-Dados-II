# Dicionário de Dados — Versão 0.4

**Projeto:** Preditor de degradação de rede com RTT normalizado  
**Gerado por:** `arvore_final.py` (Tarefa 5)  
**Base:** dicionários v0.2 e v0.3. Nenhuma coluna de dados mudou.

---

## 1. Colunas usadas pela árvore final (8, todas relativas ao baseline do fluxo)

`z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`. Alvo: `classe` (OK, RISCO, FALHA).

Importância na árvore final: `z_robusto` 0,72; `n5_risco` 0,14; `jitter_relativo` 0,12; `perda_pct` 0,01; `n5_timeout` 0,001. As outras três colunas não são usadas por nenhuma divisão.

**Proibidas** (conferido por `assert` em `arvore_final.py`): `fluxo_id`, `timestamp`, `rtt_ms`, `jitter_ms`, `split`, `regra_disparada`, `criterio_risco_atual`, país, cidade, IP, `par_id`, `rota_id`. `delta_z_robusto` não é usada.

## 2. Parâmetros finais (`config/config_arvore.json`, chave `final`)

`DecisionTreeClassifier(criterion='gini', max_depth=5, min_samples_leaf=2, ccp_alpha=0.0, class_weight=None, random_state=42)`; 12 folhas, profundidade 5. Ajustada só no treino (10.067 linhas).

## 3. Arquivos novos

| Arquivo | Conteúdo |
| :--- | :--- |
| `models/arvore_final.joblib` | Árvore final |
| `reports/arvore_final.png` | Figura da árvore (o vetor `value` de cada nó segue a ordem [FALHA, OK, RISCO]) |
| `reports/t5_regras.txt` | 12 regras em português |
| `reports/t5_teste_unico.json` | **Trava do teste**: resultado, data/hora UTC da medição e `repetido` (se foi rodado com `--repetir`) |
| `reports/t5_erros_teste.csv` | Os 2 erros do teste |
| `reports/t5_fluxos_nao_vistos.csv` | Leave-one-flow-out: métricas por fluxo separado (`f1_macro_classes_presentes` considera só as classes que existem no fluxo) |
| `reports/t5_fluxos_nao_vistos_erros.csv` | Erros do leave-one-flow-out |

## 4. Resultado no teste (6.034 linhas, medido uma vez)

F1 macro 0,9995; recall de FALHA 1,0000; recall de RISCO 0,9976; 2 erros (RISCO previsto como OK). Ver `Tarefa5_Arvore_Final.md`, incluindo as declarações e limitações.
