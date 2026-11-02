# Dicionário de Dados — Versão 0.3

**Projeto:** Preditor de degradação de rede com RTT normalizado  
**Gerado por:** `arvore_inicial.py` (Tarefa 3) e `ajuste_arvore.py` (Tarefa 4)  
**Base:** `data/processed/dataset_rotulado_B.csv` da Tarefa 2 (dicionário v0.2). Nenhuma coluna do v0.2 mudou.

---

## 1. Coluna relativa testada na Tarefa 4 (não adotada)

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `delta_z_robusto` | Float | `z_robusto` da medição menos o `z_robusto` da medição anterior do **mesmo fluxo** (só passado, dentro do Período B). Vazia na 1ª medição do fluxo e quando uma das duas é timeout. Nunca preenchida com 0. Calculada em memória por `arvore_comum.carregar_dataset`; não é gravada nos CSVs. |

Resultado: F1 macro na validação igual ao da árvore sem ela (1,0000, 12 folhas). **Não entra na árvore final.**

## 2. Arquivos novos

| Arquivo | Origem | Conteúdo |
| :--- | :--- | :--- |
| `config/config_arvore.json` | Tarefas 3 e 4 | `random_state` 42, grades de busca de cada tarefa e, em `final`, os parâmetros escolhidos na validação |
| `models/arvore_tarefa3.joblib` | T3 | Árvore (Gini, `max_depth` 5, `min_samples_leaf` 5) ajustada no treino |
| `models/arvore_tarefa4.joblib` | T4 | Árvore ajustada (Gini, `max_depth` 5, `min_samples_leaf` 2) |
| `reports/t3_grade_validacao.csv` | T3 | Grade de profundidade × folha mínima com F1 macro e recalls na validação |
| `reports/t3_regras.csv`, `t3_regras.txt` | T3 | Uma linha por folha: regra em português, classe, amostras, pureza |
| `reports/t3_erros_validacao.csv` | T3 | Erros da validação com métricas, classe real e prevista |
| `reports/t3_contraste.json` | T3 | Árvores de contraste (com RTT absoluto e país) — **não são o modelo** |
| `reports/t3_resumo.json` | T3 | Parâmetros, profundidade, folhas, matriz e métricas |
| `reports/t4_busca_validacao.csv` | T4 | 960 combinações avaliadas só na validação |
| `reports/t4_regras.csv`, `t4_regras.txt`, `t4_erros_validacao.csv`, `t4_resumo.json` | T4 | Regras, erros restantes e resumo da árvore ajustada |

O teste temporal **não** é aberto nas Tarefas 3 e 4 (`teste_usado: false` nos resumos).
