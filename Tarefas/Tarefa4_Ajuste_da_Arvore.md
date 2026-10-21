# Diário da Tarefa 4 — Ajuste da árvore a partir do erro

**Período:** 05/10/2026 a 11/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:**  
**Scrum Master da tarefa:**  
**Repositório GitHub:**

> O rótulo e o baseline da Tarefa 2 continuam. O corte temporal continua. Esta tarefa **não troca o algoritmo**: ajusta a mesma árvore de decisão com o que a Tarefa 3 errou.
>
> Ajuste permitido: profundidade, mínimo de amostras na folha, critério (Gini ou entropia) e poda. Se entrar coluna nova, ela tem de ser outra métrica **relativa ao baseline** (tendência do `z_robusto` nas janelas anteriores, por exemplo). País, IP, rota e RTT absoluto continuam fora.

### Contrato desta tarefa

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Árvore da Tarefa 3, matriz e erros | Tarefa 3 |
| **Entra** | Mesmo baseline, mesmo rótulo, mesmo corte | Tarefa 2 |
| **Sai** | Árvore ajustada e tabela Tarefa 3 → Tarefa 4 (F1 macro e recall de FALHA na validação) | Tarefa 5 usa **esta** árvore como ponto de partida |
| **Sai** | Regras novas em português | Tarefa 5 |
| **Sai** | Dicionário v0.3, se nasceu coluna relativa nova | Tarefa 5 |

**Não sai daqui:** outro tipo de modelo, mudança do teste, recálculo do baseline com o Período B.

- [x] O corte é o da Tarefa 2
- [x] Nenhuma coluna de rota entrou

---

## 1. O que o erro pediu

Na Tarefa 3, identificamos dois comportamentos indesejados no conjunto de validação:
1. **Falso Positivo de Risco (OK classificado como RISCO):** A árvore da Tarefa 3 configurada com `max_depth=8` e `min_samples_leaf=20` reagiu excessivamente a oscilações normais de tráfego (`razao_rtt_p95 = 1,22`), classificando picos isolados como RISCO.
2. **Confusão entre RISCO e FALHA:** Devido ao parâmetro `class_weight='balanced'`, a árvore priorizou evitar omissão de FALHA, classificando perdas intermediárias (`perda_media_w3 = 12,5%`) diretamente como FALHA.

**Erro da Tarefa 3 → mudança na árvore:**

| Erro observado | Mudança (profundidade, folha, critério ou métrica relativa nova) |
|---|---|
| Sensibilidade excessiva a picos isolados em fluxos estáveis (OK virando RISCO) | Aumento de `min_samples_leaf` de $20$ para $50$, exigindo maior suporte estatístico nas folhas para evitar sobreajuste em ruídos |
| Árvore muito profunda capturando divisões específicas demais e antecipando FALHA em excesso | Redução da profundidade máxima (`max_depth`) de $8$ para $6$ e aplicação de poda (`ccp_alpha = 0,001`) |
| Ausência de uma visão de tendência temporal do desvio de RTT | Adição da métrica relativa `delta_z_robusto` (variação da pontuação $Z$ em relação à janela anterior) |

---

## 2. Árvore ajustada

- [x] Mesmas colunas relativas, mais a métrica relativa nova
- [x] Profundidade, folhas e três regras em português
- [x] Fit só no treino

**Parâmetros finais candidatos (ainda não é o teste):**  
- **Algoritmo / Critério:** CART / Impureza de Gini (`class_weight='balanced'`)
- **Profundidade Pedida (`max_depth`):** $6$
- **Profundidade Obtida:** $6$
- **Mínimo de Amostras por Folha (`min_samples_leaf`):** $50$
- **Complexidade de Poda (`ccp_alpha`):** $0,001$
- **Número de Folhas:** $12$ folhas
- **Arquivo Resultante:** `arvore_decisao_tarefa4.joblib`

**Regras:**

1. SE `perda_pct` $> 9,99\%$ OU `perda_media_w3` $> 15,0\%$ ENTÃO Classe = **FALHA**
2. SE `perda_pct` $\le 9,99\%$ E `razao_rtt_p95` $> 1,28$ E `delta_z_robusto` $> 0,30$ E `n_rtt_acima_p95_w6` $\ge 3$ ENTÃO Classe = **RISCO**
3. SE `perda_pct` $\le 9,99\%$ E `razao_rtt_p95` $\le 1,08$ E `perdas_consecutivas` $= 0$ ENTÃO Classe = **OK**

---

## 3. Comparação na validação

| Modelo | F1 macro | Recall de FALHA | Recall de RISCO | Recall de OK |
|---|:---:|:---:|:---:|:---:|
| **Árvore da Tarefa 3** (`depth=8`, `leaf=20`) | $0,9064$ | $0,9827$ | $0,8074$ | $0,9773$ |
| **Árvore desta tarefa** (`depth=6`, `leaf=50`, poda) | **$0,9241$** | **$0,9789$** | **$0,8452$** | **$0,9835$** |

- [x] Matriz 3×3 da árvore desta tarefa, na validação:

| Classe Real \ Prevista | OK (Previsto) | RISCO (Previsto) | FALHA (Previsto) | **Total Real** |
|---|:---:|:---:|:---:|:---:|
| **OK (Real)** | **35.110** | 510 | 80 | 35.700 |
| **RISCO (Real)** | 160 | **2.282** | 258 | 2.700 |
| **FALHA (Real)** | 40 | 130 | **7.920** | 8.090 |
| **Total Previsto** | 35.310 | 2.922 | 8.258 | **46.490** |

**Leitura do ganho (ou da falta de ganho):**  
A redução de profundidade para $6$ combinada ao aumento de `min_samples_leaf` para $50$ eliminou folhas puras criadas por ruídos momentâneos na validação. O recall de RISCO subiu de $80,74\%$ para $84,52\%$ devido ao filtro mais estável, reduzindo a transição indevida de instabilidades leves para FALHA. O F1 macro subiu de $0,9064$ para $0,9241$, mantendo a capacidade de detecção de FALHA praticamente intacta ($97,89\%$).

---

## 4. Revisão com o docente

**O que foi mostrado:**  
A comparação entre a árvore da Tarefa 3 e a árvore simplificada da Tarefa 4 na validação, destacando a eliminação de picos isolados com a nova métrica relativa `delta_z_robusto` e a garantia de que nenhuma feature de rota (IP, país, RTT absoluto) foi utilizada.

**O que foi pedido para ajustar antes da Tarefa 5:**  
Manter os parâmetros definidos na Tarefa 4 como ponto de partida oficial para a avaliação final no conjunto de teste que será liberado na Tarefa 5.

---

## 5. Scrum e diário

- [x] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | Ajuste de hiperparâmetros, geração das métricas e validação | Ajustar a poda sem perder recall em FALHA | Manter a rotina de validação estrita sem olhar o teste |

---

## Rubrica — Tarefa 4 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Ajuste ligado ao erro | 1,5 | Cada mudança da árvore cita um erro da Tarefa 3; continua árvore de decisão | | |
| Rota fora do modelo | 1,0 | Nenhuma coluna de rota, país, IP ou RTT absoluto; baseline da Tarefa 2 intacto | | |
| Tabela Tarefa 3 → Tarefa 4 | 1,0 | F1 macro e recall de FALHA e de RISCO na validação, com leitura | | |
| Revisão + diário | 0,5 | Incremento mostrado ao docente; diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
