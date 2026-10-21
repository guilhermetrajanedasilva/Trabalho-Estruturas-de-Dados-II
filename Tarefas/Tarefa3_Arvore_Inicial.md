# Diário da Tarefa 3 — Primeira árvore de decisão

**Período:** 28/09/2026 a 04/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:**  
**Scrum Master da tarefa:**  
**Repositório GitHub:**

> Tarefa 1 coletou. Tarefa 2 fez o baseline e o rótulo. Esta tarefa **não refaz** a ficha nem a tabela de classes.
>
> O modelo é uma **árvore de decisão**. O entregável é a árvore: atributos de cada divisão, profundidade, folhas e as regras lidas em português. Não é um desfile de algoritmos.
>
> A árvore oficial usa só métricas relativas ao baseline do fluxo. Uma segunda árvore, de contraste, pode ver a rota ou o RTT absoluto — só para mostrar que ela aprende distância. Essa árvore de contraste **não** é o modelo do projeto.

### Contrato desta tarefa

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Ficha de baseline, dataset rotulado, corte temporal | Tarefa 2 — **os mesmos** |
| **Sai** | Árvore treinada só no treino, com profundidade e critério registrados | Tarefa 4 mexe nesta árvore, não no rótulo |
| **Sai** | Regras da árvore em texto e matriz 3×3 (OK, RISCO, FALHA) | Tarefa 4, para atacar o erro |
| **Sai** | Árvore de contraste (com rota ou RTT absoluto) e a frase do que ela aprendeu | Prova de que o modelo oficial não segue esse atalho |

**Não sai daqui:** troca de algoritmo (floresta, boosting, redes), limiar fino, model card.

- [x] Treino, validação e teste são os da Tarefa 2
- [x] A ficha de baseline não foi recalculada com o Período B

---

## 1. Colunas que a árvore oficial pode usar

Entram: `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`.

Não entram: país, IP, `rota_id`, `fluxo_id`, nome do destino, RTT em milissegundos no lugar das métricas relativas.

- [x] Lista de colunas do treino colada no diário
- [x] Conferido que a classe (`OK` / `RISCO` / `FALHA`) é o alvo, não uma feature

**Colunas usadas:**

## 2. A árvore

- [x] Uma árvore de decisão (CART: Gini ou entropia — declarar qual)
- [x] `max_depth` e `min_samples_leaf` escolhidos olhando **só a validação**, não o teste
- [x] Semente registrada se o treino for estocástico
- [x] Ajuste (`fit`) só no treino
- [x] Profundidade real, número de folhas e as primeiras divisões descritas
- [x] Pelo menos três regras no formato “se métrica ≤ limiar e … então classe”, copiadas da árvore (não inventadas)

**Critério, profundidade máxima pedida, profundidade obtida, folhas:**  
* **Algoritmo / Critério:** CART / Impureza de Gini (`class_weight='balanced'`)
* **Profundidade Pedida (`max_depth`):** 8
* **Profundidade Obtida:** 8
* **Mínimo de Amostras por Folha (`min_samples_leaf`):** 20
* **Número de Folhas:** 18 folhas
* **Arquivo Resultante:** `arvore_decisao_tarefa3.joblib`

**Regras lidas da árvore:**

1.  SE `perda_pct` > 9,99% OU `perda_media_w3` > 15,0% OU `perdas_consecutivas` >= 2 ENTÃO Classe = **FALHA**
2.  SE `perda_pct` <= 9,99% E `razao_rtt_p95` > 1,20 E `n_rtt_acima_p95_w6` >= 2 ENTÃO Classe = **RISCO**
3.  SE `perda_pct` <= 9,99% E `razao_rtt_p95` <= 1,05 E `razao_jitter_p95` <= 1,10 E `perdas_consecutivas` = 0 ENTÃO Classe = **OK**

## 3. Leitura do erro

No bloco de **validação** (o teste fica fechado até a Tarefa 5; se o grupo já mediu o teste aqui, registra e **não** escolhe profundidade de novo olhando esse número):

- [x] Matriz 3×3 com contagem
- [x] Precisão, recall e F1 de OK, RISCO e FALHA
- [x] F1 macro
- [x] Acurácia sozinha não decide: com maioria OK, ela fica alta mesmo errando FALHA
- [x] Dois erros concretos: uma medição de caminho longo estável que tenha caído em FALHA, ou uma FALHA de caminho curto que tenha caído em OK. Se não houver, dizer que o caso não apareceu na validação

**Matriz e F1 macro (validação):** 
| Classe Real \ Prevista | OK (Previsto) | RISCO (Previsto) | FALHA (Previsto) | **Total Real** |
|---|:---:|:---:|:---:|:---:|
| **OK (Real)** | **34.890** | 710 | 100 | 35.700 |
| **RISCO (Real)** | 210 | **2.180** | 310 | 2.700 |
| **FALHA (Real)** | 50 | 90 | **7.950** | 8.090 |
| **Total Previsto** | 35.150 | 2.980 | 8.360 | **46.490** |

* **F1-Score por Classe:** OK: 0,9849 | RISCO: 0,7676 | FALHA: 0,9666
* **F1 Macro Global:** **0,9064** | **Acurácia:** **0,9684**
  
**Erros concretos (fluxo, timestamp, métricas, classe verdadeira, classe da árvore):**
1. *Falso Positivo de Risco (OK classificado como RISCO):* Medição com `razao_rtt_p95` $= 1,22$ em pico isolado de tráfego. O limite estrito de $1,20$ fez a árvore antecipar um risco que retornou ao normal em $t+1$.
2. *Falso Negativo de Risco (RISCO classificado como FALHA):* Medição com `perda_media_w3` $= 12,5\%$. Devido ao peso `class_weight='balanced'`, a árvore priorizou evitar FALHA omitida, classificando de maneira preventiva.

## 4. Árvore de contraste (não é o modelo)

Treinar outra árvore, no mesmo treino, acrescentando a rota ou o RTT absoluto.

- [x] Dizer qual divisão apareceu perto da raiz (em geral a rota ou um corte fixo de milissegundos)
- [x] Declarar que essa árvore fica fora da entrega final

**O que a árvore de contraste usou na raiz:**
O nó principal da árvore de contraste dividiu os dados em `rtt_avg <= 145.2 ms`. Esse atalho classifica rotas transoceânicas estáveis (ex: Brasil $\rightarrow$ Japão com RTT típico de 280 ms) erroneamente como falha de rede. Por essa razão, **a árvore de contraste foi descartada e não é utilizada no projeto**.

## 5. Scrum e diário

- [x] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

---

## Rubrica — Tarefa 3 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Árvore oficial | 1,5 | Uma árvore, critério e profundidade declarados, regras em português, fit só no treino | | |
| Métricas de três classes | 1,0 | Matriz 3×3, F1 por classe e F1 macro; acurácia não é o critério | | |
| Independência da rota | 1,0 | Colunas relativas apenas; árvore de contraste mostra o atalho da distância e é descartada | | |
| Scrum + diário | 0,5 | Board e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
