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

**Colunas usadas (8, todas relativas ao baseline do fluxo):** `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`. O alvo é `classe`. Conferido no script (`arvore_inicial.py`) que nenhuma coluna proibida (`fluxo_id`, país, IP, `rota_id`, `rtt_ms`, `jitter_ms`, `timestamp`) entra na árvore oficial.

## 2. A árvore

- [x] Uma árvore de decisão (CART: Gini ou entropia — declarar qual)
- [x] `max_depth` e `min_samples_leaf` escolhidos olhando **só a validação**, não o teste
- [x] Semente registrada se o treino for estocástico
- [x] Ajuste (`fit`) só no treino
- [x] Profundidade real, número de folhas e as primeiras divisões descritas
- [x] Pelo menos três regras no formato “se métrica ≤ limiar e … então classe”, copiadas da árvore (não inventadas)

**Critério, profundidade máxima pedida, profundidade obtida, folhas:**
* **Algoritmo / Critério:** CART / impureza de Gini, sem peso de classes
* **Como foram escolhidos:** `max_depth` e `min_samples_leaf` saíram de uma grade (profundidade 2, 3, 4, 5, 6, 8, 10 × folha mínima 5, 20, 50, 100) avaliada **só na validação**, pelo F1 macro; em caso de empate, a árvore mais simples. O teste não foi carregado nesta tarefa. Grade completa em `reports/t3_grade_validacao.csv`.
* **Profundidade pedida (`max_depth`):** 5 (profundidades 5, 6, 8 e 10 empataram com F1 macro 0,9991; ficou a menor)
* **Profundidade obtida:** 5
* **Mínimo de amostras por folha (`min_samples_leaf`):** 5
* **Número de folhas:** 14
* **Semente (`random_state`):** 42
* **Ajuste (`fit`):** só no treino (10.067 linhas; validação com 4.029)
* **Primeiras divisões:** a raiz divide por `z_robusto` ≤ 2,10; à esquerda (RTT perto do normal) a próxima divisão é `jitter_relativo` ≤ 3,00; à direita (`z_robusto` > 2,10) é `z_robusto` ≤ 3,50
* **Importância das colunas:** `z_robusto` 0,73; `n5_risco` 0,14; `jitter_relativo` 0,12; `perda_pct` 0,01; `aumento_pct` e `n5_timeout` perto de 0
* **Arquivo resultante:** `models/arvore_tarefa3.joblib`; regras em `reports/t3_regras.txt`

**Regras lidas da árvore** (as 6 folhas com mais amostras; as 14 estão em `reports/t3_regras.csv`):

1. SE z_robusto <= 2,01 E jitter_relativo <= 3,00 E perda_pct <= 16,67 E n5_timeout <= 0,50 ENTÃO OK  *(folha com 7310 amostras)*
2. SE z_robusto > 3,50 ENTÃO FALHA  *(folha com 1239 amostras)*
3. SE 2,10 < z_robusto <= 3,50 E perda_pct <= 16,67 E n5_risco > 1,50 ENTÃO RISCO  *(folha com 631 amostras)*
4. SE z_robusto <= 2,10 E jitter_relativo > 3,00 E n5_risco > 1,50 ENTÃO RISCO  *(folha com 430 amostras)*
5. SE z_robusto <= 2,10 E aumento_pct <= 2,05 E jitter_relativo > 3,00 E n5_risco <= 1,50 ENTÃO OK  *(folha com 237 amostras)*
6. SE 2,10 < z_robusto <= 3,50 E n5_risco <= 1,50 ENTÃO OK  *(folha com 114 amostras)*

Os limiares 2,10 e 3,50 de `z_robusto` e 3,00 de `jitter_relativo` coincidem com os da tabela de rotulagem da Tarefa 2 (2, 3,5 e 3). Isso era esperado: ver a declaração na seção 3.

## 3. Leitura do erro

No bloco de **validação** (o teste fica fechado até a Tarefa 5; se o grupo já mediu o teste aqui, registra e **não** escolhe profundidade de novo olhando esse número):

- [x] Matriz 3×3 com contagem
- [x] Precisão, recall e F1 de OK, RISCO e FALHA
- [x] F1 macro
- [x] Acurácia sozinha não decide: com maioria OK, ela fica alta mesmo errando FALHA
- [x] Dois erros concretos: uma medição de caminho longo estável que tenha caído em FALHA, ou uma FALHA de caminho curto que tenha caído em OK. Se não houver, dizer que o caso não apareceu na validação

**Matriz e F1 macro (validação, 4.029 linhas):**

| Real \ Previsto | OK | RISCO | FALHA | Total real |
|---|---:|---:|---:|---:|
| **OK** | 3.056 | 0 | 0 | 3.056 |
| **RISCO** | 0 | 553 | 0 | 553 |
| **FALHA** | 2 | 0 | 418 | 420 |
| **Total previsto** | 3.058 | 553 | 418 | 4.029 |

| | OK | RISCO | FALHA |
|---|---:|---:|---:|
| Precisão | 0,9993 | 1,0000 | 1,0000 |
| Recall | 1,0000 | 1,0000 | 0,9952 |
| F1 | 0,9997 | 1,0000 | 0,9976 |

* **F1 macro:** **0,9991** | **Acurácia:** 0,9995 | **Acurácia balanceada:** 0,9984
* A acurácia sozinha não decide: com 76% de OK, uma árvore que ignorasse FALHA ainda teria acurácia alta. O que se olha é o recall de FALHA (0,9952) e o F1 macro.

**Erros concretos (fluxo, timestamp, métricas, classe verdadeira, classe da árvore):** a árvore errou só 2 das 4.029 linhas (`reports/t3_erros_validacao.csv`):
1. *FALHA prevista como OK:* fluxo `7656|103.153.238.101` (Satigny → Sydney), 16/09/2026 21:34:41 UTC. RTT = 295,3 ms, `z_robusto` = −15,8, `perda_pct` = 0, `n5_timeout` = 3. Classe verdadeira FALHA (linha 2 da tabela: 3 timeouts nas últimas 5 medições). A árvore disse OK.
2. *FALHA prevista como OK:* mesmo fluxo, 16/09/2026 21:38:47 UTC. RTT = 294,2 ms, `z_robusto` = −19,6, `perda_pct` = 0, `n5_timeout` = 3. Mesmo erro.

Causa: só 8 linhas do treino têm `n5_timeout` ≥ 3, e com `min_samples_leaf` = 5 a árvore não isola esse caso e o agrupa com outras linhas de `n5_timeout` > 0, que são OK. É uma FALHA por persistência de timeout, não por RTT, e o RTT da própria medição estava normal.

Os dois tipos de erro pedidos não apareceram: **nenhuma** medição OK de caminho longo estável caiu em FALHA ou RISCO (0 alarmes falsos em caminho longo), e **nenhuma** FALHA do fluxo curto (Minsk → Klagenfurt) caiu em OK.

**Declaração:** o F1 macro perto de 1 não prova que a árvore "entende" a rede. O rótulo da Tarefa 2 foi construído com **as mesmas métricas** que a árvore recebe (`z_robusto`, `perda_pct`, `n5_*`, `jitter_relativo`), então a árvore está reaprendendo a política de rotulagem, não um incidente confirmado em roteador. O valor do experimento é mostrar que a política é aprendível só com colunas relativas, sem rota e sem RTT absoluto.

## 4. Árvore de contraste (não é o modelo)

Treinar outra árvore, no mesmo treino, acrescentando a rota ou o RTT absoluto.

- [x] Dizer qual divisão apareceu perto da raiz (em geral a rota ou um corte fixo de milissegundos)
- [x] Declarar que essa árvore fica fora da entrega final

**O que a árvore de contraste usou na raiz:** foram treinadas duas árvores de contraste no mesmo treino e com os mesmos parâmetros da árvore oficial (`models` não salvos; resultados em `reports/t3_contraste.json`). País de origem e de destino entraram como colunas 0/1.

1. **Colunas oficiais + `rtt_ms` + país:** a raiz continuou sendo `z_robusto` ≤ 2,10, F1 macro 0,9991 (igual à oficial), e `rtt_ms` e país ficaram com importância zero. Quando as métricas relativas estão disponíveis, a árvore não precisa da distância. O atalho não apareceu aqui.
2. **Somente `rtt_ms` + país (sem métricas relativas):** a raiz é `destino_AU` (país de destino = Austrália) e a coluna mais importante é `rtt_ms` (importância 0.82). O F1 macro cai para **0,8889** e o recall de RISCO para 0,6438. Ela classifica pelo fluxo, não pelo desvio: na validação, `7258|202.87.175.244` (Richterswil → Perth) saiu com 0 OK, 280 RISCO e 224 FALHA, enquanto Feira de Santana → Dubai e Osasco → Feldkirch saíram 100% OK (503 e 503 linhas), qualquer que fosse o que acontecia no enlace. Ela aprendeu "esta rota costuma ser assim" e não "este fluxo se afastou do próprio normal".

Essa árvore fica **fora da entrega final**. O modelo do projeto é a árvore oficial, só com métricas relativas.

## 5. Scrum e diário

- [x] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| **Vitor Julião Diogo dos Santos (Scrum Master)** | Facilitei a organização das tarefas no board, conduzi as reuniões de alinhamento para a escolha dos hiperparâmetros e revisei o cumprimento de todos os requisitos do contrato da tarefa. | Garantir que nenhum membro da equipe utilizasse o conjunto de teste para a tomada de decisão da profundidade da árvore, mantendo o teste completamente fechado. | Vou manter o rigor na blindagem dos dados de teste para as próximas sprints e focar em dinâmicas mais ágeis para a revisão dos resultados de validação. |
| **Mariana Moreira Barbosa** | Desenvolvi o script principal (`arvore_inicial.py`), implementando a árvore com critério Gini e executei a grade de hiperparâmetros (profundidades 2, 3, 4, 5, 6, 8, 10 × folhas 5, 20, 50, 100) no bloco de validação. | Tive um certo grau de dificuldade técnica para extrair e formatar as regras das divisões de nós da árvore para o formato de texto estruturado (SE... ENTÃO) exigido no relatório. | Pretendo ajustar o hiperparâmetro `min_samples_leaf` ou investigar pesos de classe na próxima tarefa para tentar isolar corretamente os casos raros de `n5_timeout` elevado. |
| **Guilherme Trajane da Silva** | Treinei a árvore de contraste no mesmo conjunto de dados, incorporando as features absolutas (`rtt_ms` e país) para comprovar a dependência de roteamento. | Garantir que o tratamento das variáveis categóricas de país (Origem/Destino) não afetasse o pipeline da árvore principal, que usa apenas variáveis relativas. | Manter a metodologia de comparação por contraste para comprovar que o nosso modelo não cria atalhos baseados na distância física, mas ajustando a forma como aplicamos o encoding. |
| **Leandro do Nascimento Lemes** | Elaborei a matriz de confusão 3×3, calculei as métricas (como o F1 macro de 0,9991) e conduzi a análise de falsos negativos rastreando as 2 linhas incorretas do fluxo Satigny → Sydney. | Foi complexo debugar a árvore para entender o motivo prático do erro, descobrindo que o `n5_timeout = 3` foi ofuscado pela regra de amostra mínima por folha. | Pretendo manter essa análise profunda de erros concretos em vez de olhar apenas para as métricas gerais, pois isso nos mostra exatamente onde a topologia falha. |
| **Samara Fernandes Soares** | Fiz a curadoria da entrada dos dados, garantindo que colunas proibidas (como `fluxo_id`, `rota_id`, IPs e timestamps) ficassem de fora das 8 features utilizadas no fit do modelo oficial. | Validar os limiares de divisão (como `z_robusto` em 2,10 e 3,50) para comprovar se a árvore estava de fato reaprendendo a tabela da Tarefa 2 sem vazar o alvo original. | Vou manter nossos scripts de carregamento rígidos quanto à exclusão de colunas absolutas, garantindo a independência de rota do nosso preditor para as próximas fases. |
---

## Rubrica — Tarefa 3 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Árvore oficial | 1,5 | Uma árvore, critério e profundidade declarados, regras em português, fit só no treino | | |
| Métricas de três classes | 1,0 | Matriz 3×3, F1 por classe e F1 macro; acurácia não é o critério | | |
| Independência da rota | 1,0 | Colunas relativas apenas; árvore de contraste mostra o atalho da distância e é descartada | | |
| Scrum + diário | 0,5 | Board e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
