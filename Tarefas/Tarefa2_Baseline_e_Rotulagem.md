# Diário da Tarefa 2 — Baseline do fluxo e rotulagem OK, RISCO, FALHA

**Período:** 18/09/2026 a 30/09/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:**  NetVision - Visualização e análise de dados de rede 

Mariana Moreira Barbosa, Samara Fernandes Soares, Leandro do Nascimento Lemes, Guilherme Trajane da Silva, Vitor Julião Diogo dos Santos

**Scrum Master da tarefa:** Vitor Julião Diogo dos Santos

**Repositório GitHub:**  https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II

> Esta tarefa lê o `data/raw/` da Tarefa 1. Não troca a coleta sem versionar.
>
> O trabalho é **obter o baseline de cada fluxo e rotular o Período B** com a tabela desta página. A árvore não entra aqui. País, IP e rota não entram na tabela que a árvore vai ler.
>
> Ordem obrigatória: inspeção do bruto → ficha de baseline no Período A → métricas relativas no Período B → rótulo na ordem da tabela → só então o recorte temporal dentro de B.



### Contrato desta tarefa


|           | Artefato                                                              | Origem / destino                            |
| --------- | --------------------------------------------------------------------- | ------------------------------------------- |
| **Entra** | `data/raw/` e dicionário v0.1                                         | Tarefa 1                                    |
| **Sai**   | `baseline_por_fluxo.csv` (uma ficha por `fluxo_id`)                   | Tarefas 3 a 5                               |
| **Sai**   | Dataset rotulado do Período B, com a classe e as métricas abaixo      | Tarefa 3 **usa este arquivo e este rótulo** |
| **Sai**   | Recorte temporal dentro de B (treino mais antigo, teste mais recente) | Tarefas 3 a 5 — **o mesmo corte**           |
| **Sai**   | Dicionário v0.2 (bruto, ficha, métricas, classe, colunas proibidas)   | Tarefa 3                                    |


**Não sai daqui:** árvore treinada, profundidade escolhida, acurácia, F1.

- [X] O notebook lê o bruto da Tarefa 1

---



## 1. Inspeção do bruto (ainda sem rótulo)

`data/raw/` permanece intocado. A auditoria vai para o diário; a tabela de trabalho, para `data/interim/`.

- [x] Contagem de linhas, fluxos, duplicatas e RTT vazio
- [x] Nenhum RTT ausente foi gravado como 0
- [x] Período A e Período B não compartilham timestamp do mesmo fluxo

**N bruto:** 336.326 registros

**N de fluxos:** 67 fluxos totais coletados

**Evidências:**  [Link para o notebook no GitHub](https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/blob/principal/2_Coleta_de_dados.ipynb)


## 2. Como obter o baseline

Uma ficha por `fluxo_id`. Só o Período A. O Período B não entra na conta e não atualiza a ficha.


| Passo | O que fazer                                                                                                            |
| ----- | ---------------------------------------------------------------------------------------------------------------------- |
| 1     | Separar o fluxo e ordenar pelo timestamp.                                                                              |
| 2     | Período A = bloco inicial. Período B = bloco seguinte, sem amostra nos dois.                                           |
| 3     | RTT válido = medição com RTT presente. Timeout fica **fora** da mediana e do MAD, e **dentro** do dataset como evento. |
| 4     | Menos de **1.500** RTT válidos no A: `baseline_insuficiente`. Esse fluxo **não** recebe classe. Não inventar mediana.  |
| 5     | Gravar uma linha em `baseline_por_fluxo.csv` e congelar.                                                               |



| Campo da ficha  | Fórmula, somente Período A                                 |
| --------------- | ---------------------------------------------------------- |
| `mediana`       | mediana dos RTT válidos (ms)                               |
| `MAD`           | mediana(                                                   |
| `jitter_tipico` | mediana do jitter nas medições em que o jitter existe (ms) |
| `perda_tipica`  | mediana de `perda_pct`, inclusive timeout (%)              |
| `prop_resposta` | medições com RTT válido / medições do período              |


- [x] Ficha conferida em pelo menos um fluxo curto e um fluxo longo (as medianas podem ser muito diferentes; as duas são “normal”)
- [x] Lista dos fluxos excluídos e o motivo (contagem abaixo de 1.500)

**Fluxos com ficha:** 64 fluxos (apresentaram volume de amostras válidas $\ge 1.500$ no Período A).

**Fluxos excluídos:**  3 fluxos associados ao destino 170.81.100.114 (origem BR) foram marcados como baseline_insuficiente por apresentarem amostragem de RTT válido inferior ao limite mínimo de 1.500 registos no Período A.

**Exemplo auditável (fluxo curto: mediana; fluxo longo: mediana):**Fluxo Curto (DE→DE): mediana = 14,0 ms | MAD = 0,8 ms | jitter_tipico = 0,3 ms | perda_tipica = 0,0%

Fluxo Longo (BR→ZA): mediana = 344,0 ms | MAD = 2,1 ms | jitter_tipico = 0,6 ms | perda_tipica = 0,0%

## 3. Métricas de cada medição do Período B

Calcular só com a ficha congelada daquele `fluxo_id`.


| Métrica           | Fórmula                                                                 |
| ----------------- | ----------------------------------------------------------------------- |
| `z_robusto`       | (RTT atual − mediana) / (1,4826 × MAD)                                  |
| `aumento_pct`     | (RTT atual − mediana) / mediana × 100                                   |
| `jitter_relativo` | jitter atual / `jitter_tipico`                                          |
| `perda_pct`       | (enviados − recebidos) / enviados × 100                                 |
| `timeout_atual`   | 1 se não há RTT ou `perda_pct` = 100; senão 0                           |
| `n5_timeout`      | timeouts nas últimas 5 medições deste fluxo, incluindo a atual (0 a 5)  |
| `n5_aumento80`    | quantas das últimas 5 têm `aumento_pct` > 80                            |
| `n5_risco`        | quantas das últimas 5 cumprem o critério da linha 5 da tabela de rótulo |



| Situação                               | Conta                                                                           |
| -------------------------------------- | ------------------------------------------------------------------------------- |
| RTT ausente                            | Não calcular `z_robusto` nem `aumento_pct`. `timeout_atual` = 1. Não usar 0 ms. |
| MAD = 0 e RTT atual = mediana          | `z_robusto` = 0                                                                 |
| MAD = 0 e RTT atual ≠ mediana          | Denominador = max(IQR / 1,349, 1 ms)                                            |
| Jitter atual vazio                     | O critério de jitter não dispara                                                |
| `jitter_tipico` = 0 e jitter atual = 0 | `jitter_relativo` = 1                                                           |
| `jitter_tipico` = 0 e jitter atual > 0 | Tratar como `jitter_relativo` ≥ 3                                               |




## 4. Tabela de rotulagem — parar na primeira linha verdadeira

Cada linha do Período B, de um fluxo que tenha ficha. FALHA ganha de RISCO; RISCO ganha de OK.


| Ordem | Classe    | Métrica                                                                                                   | Limiar exato                                        |
| ----- | --------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 1     | **FALHA** | `perda_pct`                                                                                               | ≥ 10 nesta medição (em 3 pacotes, 1 perda já é 33%) |
| 2     | **FALHA** | `n5_timeout`                                                                                              | ≥ 3                                                 |
| 3     | **FALHA** | `z_robusto`                                                                                               | ≥ 3,5 nesta medição, com RTT presente               |
| 4     | **FALHA** | `n5_aumento80`                                                                                            | ≥ 2                                                 |
| 5     | **RISCO** | nesta medição, pelo menos um: `2 ≤ z_robusto < 3,5`, ou `30 ≤ aumento_pct ≤ 80`, ou `jitter_relativo ≥ 3` | e `n5_risco` ≥ 2                                    |
| 6     | **OK**    | nenhuma linha anterior                                                                                    | pico isolado também é OK                            |


- [x] Três exemplos auditáveis no diário: um OK de caminho longo (RTT alto e `z_robusto` baixo), um RISCO, um FALHA de caminho curto ou de timeout
- [x] Contagem OK / RISCO / FALHA no Período B
- [x] A classe **não** foi definida por “RTT > 100 ms” nem pelo nome da rota
- [x] O Período A não foi rotulado
- [x] Dicionário v0.2 lista as colunas proibidas na árvore: país, IP, `rota_id`, `fluxo_id`, RTT absoluto como substituto das métricas relativas

**Contagem OK / RISCO / FALHA:**  OK: 123.123 registros (76,8%)

RISCO: 8.336 registros (5,2%)

FALHA: 28.858 registros (18,0%)
(Total de 160.317 linhas rotuladas no Período B)


**Evidências (três linhas reais, com as métricas e a ordem que disparou a classe):** Exemplo OK (Caminho longo BR→JP):Métricas: RTT = 278,2 ms | mediana = 277,0 ms | z_robusto = 0,65 | perda_pct = 0% | n5_risco = 0
Ordem que disparou: Linha 6 (OK) — Nenhuma condição das linhas 1 a 5 foi satisfeita. O RTT absoluto alto (> 100 ms) não gerou alarme falso, pois a latência manteve-se no patamar normal do fluxo.

Exemplo RISCO (Caminho regional BR→BR):Métricas: RTT = 72,5 ms | mediana = 50,0 ms | aumento_pct = 45,0% | z_robusto = 2,40 | n5_risco = 3
Ordem que disparou: Linha 5 (RISCO) — Ativou o critério $2 \le z_{\text{robusto}} < 3,5$ combinado com persistência n5_risco $\ge 2$.

Exemplo FALHA (Caminho curto / Timeout):Métricas: RTT = NaN | perda_pct = 100% | timeout_atual = 1 | n5_timeout = 4
Ordem que disparou: Linha 1 / Linha 2 (FALHA) — Ativou perda_pct $\ge 10\%$ e persistência de timeouts n5_timeout $\ge 3$.


## 5. Recorte para a árvore (ainda sem treinar)

Dentro do Período B, por fluxo, em ordem de tempo:

- [x] Treino = trecho mais antigo; validação = trecho do meio; teste = trecho mais recente
- [x] Proporção de partida 50% / 20% / 30%, ajustada se um bloco ficar sem RISCO
- [x] Nenhum registro do Período A no treino
- [x] Corte com data e N de cada bloco

**Corte (datas e N treino / validação / teste):** O recorte temporal foi efetuado estritamente dentro do Período B (13/09/2026 04:32 UTC a 20/09/2026 04:32 UTC), ordenado por timestamp para cada fluxo_id, mantendo a proporção aproximada de 50% / 20% / 30%:Treino 
(50% — bloco mais antigo):Intervalo: 13/09/2026 04:32 UTC a 16/09/2026 16:32 UTCAmostras ($N$): 80.158 registosValidação

(20% — bloco intermédio):Intervalo: 16/09/2026 16:32 UTC a 17/09/2026 21:20 UTCAmostras ($N$): 32.063 registosTeste 

(30% — bloco mais recente):Intervalo: 17/09/2026 21:20 UTC a 20/09/2026 04:32 UTCAmostras ($N$): 48.096 registos


## 6. Scrum e diário

- [X] Board atualizado

**Link do board:**


| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
| ---------- | ---------------------- | ------------ | ----------------------------- |
| **Vitor Julião Diogo dos Santos** | Atuação como Scrum Master; cálculo do baseline do Período A, geração do `baseline_por_fluxo.csv` e validação do piso de 1.500 amostras. | Tratar o divisor do MAD quando $MAD=0$ sem gerar inconsistências. | Manter a revisão rigorosa dos contratos de dados e da ordem das regras de rotulagem. |
| **Samara Fernandes Soares** | Implementação das métricas relativas do Período B (`z_robusto`, `aumento_pct`, `jitter_relativo`) e lógica das janelas móveis `n5`. | Lógica de cálculo acumulado das janelas móveis $N_5$ sem perder o contexto por `fluxo_id`. | Vetorizar ainda mais o cálculo das janelas temporais para otimizar a execução. |
| **Leandro do Nascimento Lemes** | Aplicação da tabela de rotulagem (OK, RISCO, FALHA) na ordem exata dos critérios e auditoria das contagens. | Garantir que o `perda_pct` e timeouts tivessem prioridade sobre as regras de desvio estatístico. | Manter testes unitários e verificações em fluxos curtos e longos nas próximas tarefas. |
| **Guilherme Trajane da Silva** | Organização da estrutura de ficheiros (`data/interim/`), versão do repositório no GitHub e recorte temporal (50/20/30) no Período B. | Ajustar o recorte de datas do treino/validação/teste sem contaminar os blocos entre si. | Manter a estrutura de branchs do GitHub organizada para a integração da árvore de decisão. |
| **Mariana Moreira Barbosa** | Atualização e elaboração do Dicionário de Dados v0.2, mapeando colunas permitidas e garantindo a exclusão de variáveis proibidas. | Mapear claramente todas as variáveis relativas e isolar dados de rota (IP/País). | Assegurar que o dataset de entrada da árvore na Tarefa 3 contenha apenas as features autorizadas. |

---



## Rubrica — Tarefa 2 (0 a 4,0)


| Critério                  | Peso    | Nota máxima                                                                                     | Nota          | Observações |
| ------------------------- | ------- | ----------------------------------------------------------------------------------------------- | ------------- | ----------- |
| Baseline por fluxo        | 1,5     | Ficha só com o Período A, fórmulas desta página, piso de 1.500, exclusões listadas, A congelado |               |             |
| Rotulagem                 | 1,5     | Tabela aplicada na ordem, exemplos curto/longo, timeout sem RTT = 0, contagem das três classes  |               |             |
| Independência da rota     | 0,5     | Rota e RTT absoluto fora do rótulo e fora das colunas da futura árvore                          |               |             |
| Recorte temporal + diário | 0,5     | Corte dentro de B, com N; diário de todos                                                       |               |             |
| **Total**                 | **4,0** |                                                                                                 | **___ / 4,0** |             |


