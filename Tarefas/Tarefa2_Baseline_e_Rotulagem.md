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

- [X] O script `baseline_rotulagem.py` lê o bruto da Tarefa 1 (`data/raw/ping_bruto.csv`)

---



## 1. Inspeção do bruto (ainda sem rótulo)

`data/raw/` permanece intocado. A auditoria vai para o diário; a tabela de trabalho, para `data/interim/`.

- [x] Contagem de linhas, fluxos, duplicatas e RTT vazio
- [x] Nenhum RTT ausente foi gravado como 0
- [x] Período A e Período B não compartilham timestamp do mesmo fluxo

**N bruto:** 39.677 registros (19.547 no Período A e 20.130 no Período B)

**N de fluxos:** 8 fluxos

**Evidências:**

- Script: `baseline_rotulagem.py` (https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II). Resumo da execução em `reports/resumo_tarefa2.json`.
- Auditoria do bruto: 0 duplicatas; 88 RTT vazios (todos timeouts); 0 RTT gravado como zero ou negativo; 0 jitter igual a 0 com menos de 2 respostas; 0 linhas fora dos Períodos A e B; 0 fluxos com o mesmo timestamp nos dois períodos; os SHA-256 de todos os JSON brutos conferem com `data/raw/metadados_coleta.json`.
- O período de cada linha é recalculado pelo timestamp (A: 06/09 04:32 a 13/09 04:32 UTC; B: 13/09 04:32 a 20/09 04:32 UTC), sem confiar só na coluna da Tarefa 1. A tabela de trabalho vai para `data/interim/ping_trabalho.csv`.
- Versão anterior (histórico): notebook https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/blob/principal/2_Coleta_de_dados.ipynb

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
| `MAD`           | mediana(|RTT-mediana|)                                     |
| `jitter_tipico` | mediana do jitter nas medições em que o jitter existe (ms) |
| `perda_tipica`  | mediana de `perda_pct`, inclusive timeout (%)              |
| `prop_resposta` | medições com RTT válido / medições do período              |


- [x] Ficha conferida em pelo menos um fluxo curto e um fluxo longo (as medianas podem ser muito diferentes; as duas são “normal”)
- [x] Lista dos fluxos excluídos e o motivo (contagem abaixo de 1.500)

**Fluxos com ficha:** 8 fluxos, todos com pelo menos 1.500 RTT válidos no Período A (o menor tem 1.970, em Minsk → Klagenfurt). A ficha foi gravada em `data/processed/baseline_por_fluxo.csv` e fica congelada: a cada execução o script recalcula a ficha só com o Período A, compara com o arquivo e interrompe se houver diferença (só regrava com `--recalcular-baseline`).

**Fluxos excluídos:** 0 fluxos excluídos por contagem abaixo de 1.500. Os 2 pares que vieram sem nenhum registro (sondas 7457 e 7682) foram retirados já na Tarefa 1 e não aparecem como fluxo.

**Fichas (somente Período A):**

| Fluxo | Rota | RTT válidos (A) | mediana (ms) | MAD (ms) | jitter_tipico (ms) | perda_tipica (%) | prop_resposta |
|---|---|---|---|---|---|---|---|
| 6878\|143.205.170.32 | Minsk → Klagenfurt | 1.970 | 26,03 | 0,054 | 0,069 | 0,0 | 1,000 |
| 7508\|94.199.170.201 | Osasco → Feldkirch | 2.506 | 199,25 | 0,143 | 0,071 | 0,0 | 1,000 |
| 6719\|203.41.0.51 | Beauharnois → Melbourne | 2.518 | 228,61 | 0,065 | 0,149 | 0,0 | 0,999 |
| 7656\|103.153.238.101 | Satigny → Sydney | 2.520 | 299,65 | 0,187 | 0,267 | 0,0 | 1,000 |
| 7258\|202.87.175.244 | Richterswil → Perth | 2.518 | 338,10 | 2,762 | 0,101 | 0,0 | 0,999 |
| 7307\|37.252.245.94 | Feira de Santana → Dubai | 2.420 | 343,49 | 9,289 | 0,446 | 0,0 | 0,978 |
| 6891\|63.222.248.5 | Belo Horizonte → Dubai | 2.518 | 367,70 | 5,103 | 0,170 | 0,0 | 1,000 |
| 7586\|80.77.4.60 | Cochabamba → Dubai | 2.518 | 373,12 | 3,218 | 0,071 | 0,0 | 1,000 |

**Exemplo auditável (fluxo curto: mediana; fluxo longo: mediana):**

* **Fluxo curto (Minsk → Klagenfurt):** mediana = 26,03 ms | MAD = 0,054 ms | jitter_tipico = 0,069 ms | perda_tipica = 0,0%
* **Fluxo longo (Cochabamba → Dubai):** mediana = 373,12 ms | MAD = 3,218 ms | jitter_tipico = 0,071 ms | perda_tipica = 0,0%

As duas medianas são muito diferentes e as duas são o "normal" do respectivo fluxo.

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
| `n5_risco   `     | quantas das últimas 5 cumprem o critério da linha 5 da tabela de rótulo |



| Situação                               | Conta                                                                           |
| -------------------------------------- | ------------------------------------------------------------------------------- |
| RTT ausente                            | Não calcular `z_robusto` nem `aumento_pct`.`timeout_atual` = 1. Não usar 0 ms. |
| MAD = 0 e RTT atual = mediana          | `z_robusto` = 0                                                                 |
| MAD = 0 e RTT atual ≠ mediana          | Denominador = max(IQR / 1,349, 1 ms)                                            |
| Jitter atual vazio                     | O critério de jitter não dispara                                                |
| `jitter_tipico` = 0 e jitter atual = 0 | `jitter_relativo` = 1                                                           |
| `jitter_tipico` = 0 e jitter atual > 0 | Tratar como `jitter_relativo` ≥ 3                                               |




**Janela das últimas 5 medições:** `n5_*` conta apenas medições do próprio Período B. As 4 primeiras de cada fluxo têm janela menor, e nenhum dado do Período A entra no B. `jitter_tipico` = 0 com jitter atual > 0 é gravado como `jitter_relativo` = 3. Os limiares ficam em `config/config_rotulagem.json`.

## 4. Tabela de rotulagem — parar na primeira linha verdadeira

Cada linha do Período B, de um fluxo que tenha ficha. FALHA ganha de RISCO; RISCO ganha de OK.

| Ordem | Classe | Métrica | Limiar exato |
| :---: | :---: | :--- | :--- |
| **1** | **FALHA** | `perda_pct` | ≥ 10 nesta medição (em 3 pacotes, 1 perda já é 33%) |
| **2** | **FALHA** | `n5_timeout` | ≥ 3 |
| **3** | **FALHA** | `z_robusto` | ≥ 3,5 nesta medição, com RTT presente |
| **4** | **FALHA** | `n5_aumento80` | ≥ 2 |
| **5** | **RISCO** | nesta medição, pelo menos um: 2 ≤ `z_robusto` < 3,5 , ou 30 ≤ `aumento_pct` ≤ 80 , ou `jitter_relativo` ≥ 3 | e `n5_risco` ≥ 2 |
| **6** | **OK** | nenhuma linha anterior | pico isolado também é OK |

- [x] Três exemplos auditáveis no diário: um OK de caminho longo (RTT alto e `z_robusto` baixo), um RISCO, um FALHA de caminho curto ou de timeout
- [x] Contagem OK / RISCO / FALHA no Período B
- [x] A classe **não** foi definida por "RTT > 100 ms" nem pelo nome da rota
- [x] O Período A **não** foi rotulado
- [x] Dicionário v0.2 lista as colunas proibidas na árvore: país, IP, `rota_id`, `fluxo_id`, RTT absoluto como substituto das métricas relativas

---

**Contagem OK / RISCO / FALHA:**

*   **OK:** 14.897 registros (74,0%)
*   **RISCO:** 2.447 registros (12,2%)
*   **FALHA:** 2.786 registros (13,8%) *(Total de 20.130 linhas rotuladas, todas do Período B)*

Linha da tabela que decidiu a classe: FALHA pela linha 3 (`z_robusto`) em 2.629 linhas, pela linha 1 (`perda_pct`) em 153 e pela linha 2 (`n5_timeout`) em 4; a linha 4 não disparou. RISCO pela linha 5 em 2.447 linhas e OK pela linha 6 em 14.897.

| Fluxo | OK | RISCO | FALHA |
|---|---|---|---|
| Minsk → Klagenfurt | 2.389 | 71 | 60 |
| Osasco → Feldkirch | 2.153 | 182 | 178 |
| Beauharnois → Melbourne | 1.426 | 0 | 1.090 |
| Satigny → Sydney | 2.276 | 32 | 207 |
| Richterswil → Perth | 407 | 1.153 | 956 |
| Feira de Santana → Dubai | 2.434 | 23 | 58 |
| Belo Horizonte → Dubai | 2.019 | 415 | 82 |
| Cochabamba → Dubai | 1.793 | 571 | 155 |

---

**Evidências (três linhas reais, com as métricas e a ordem que disparou a classe):** (`reports/exemplos_auditaveis.csv`)

*   **Exemplo OK (caminho longo, Cochabamba → Dubai, 13/09/2026 04:33:48 UTC):**
    *   **Métricas:** RTT = 369,9 ms | mediana = 373,1 ms | z_robusto = −0,68 | aumento_pct = −0,87% | jitter_relativo = 0,49 | perda_pct = 0% | n5_risco = 0
    *   **Ordem que disparou:** Linha 6 (OK) — nenhuma condição das linhas 1 a 5 foi satisfeita. O RTT absoluto é alto (> 100 ms) e mesmo assim não gerou alarme, porque está no patamar normal do fluxo.

*   **Exemplo RISCO (caminho curto, Minsk → Klagenfurt, 13/09/2026 14:34:00 UTC):**
    *   **Métricas:** RTT = 26,3 ms | mediana = 26,0 ms | z_robusto = 3,22 | aumento_pct = 0,99% | jitter_relativo = 4,34 | perda_pct = 0% | n5_risco = 2
    *   **Ordem que disparou:** Linha 5 (RISCO) — `2 ≤ z_robusto < 3,5` e `jitter_relativo ≥ 3` nesta medição, com `n5_risco ≥ 2`. As linhas 1 a 4 não foram satisfeitas (`z_robusto` < 3,5, sem perda).

*   **Exemplo FALHA (timeout, Belo Horizonte → Dubai, 13/09/2026 21:47:03 UTC):**
    *   **Métricas:** RTT = vazio | perda_pct = 100% | timeout_atual = 1 | n5_timeout = 1 | z_robusto e aumento_pct não calculados
    *   **Ordem que disparou:** Linha 1 (FALHA) — `perda_pct ≥ 10`. O RTT ausente não foi gravado como 0 ms.

## 5. Recorte para a árvore (ainda sem treinar)

Dentro do Período B, por fluxo, em ordem de tempo:

- [x] Treino = trecho mais antigo; validação = trecho do meio; teste = trecho mais recente
- [x] Proporção de partida 50% / 20% / 30%, ajustada se um bloco ficar sem RISCO
- [x] Nenhum registro do Período A no treino
- [x] Corte com data e N de cada bloco

**Corte (datas e N treino / validação / teste):** o recorte foi feito estritamente dentro do Período B (13/09/2026 04:32 UTC a 20/09/2026 04:32 UTC), por `fluxo_id`, em ordem de timestamp. A proporção de partida 50% / 20% / 30% foi mantida, porque os três blocos têm RISCO. O detalhe por fluxo está em `data/processed/corte_temporal.csv`, e cada linha do `dataset_rotulado_B.csv` tem a coluna `split`.

*   **Treino (50% — bloco mais antigo):**
    *   Intervalo: 13/09/2026 04:32 UTC a 16/09/2026 16:29 UTC
    *   Amostras (N): 10.067 registros
    *   Classes: 7.730 OK, 1.074 RISCO e 1.263 FALHA

*   **Validação (20% — bloco intermediário):**
    *   Intervalo: 16/09/2026 16:20 UTC a 18/09/2026 02:05 UTC
    *   Amostras (N): 4.029 registros
    *   Classes: 3.056 OK, 553 RISCO e 420 FALHA

*   **Teste (30% — bloco mais recente):**
    *   Intervalo: 18/09/2026 01:58 UTC a 20/09/2026 04:31 UTC
    *   Amostras (N): 6.034 registros
    *   Classes: 4.111 OK, 820 RISCO e 1.103 FALHA

Os intervalos se sobrepõem por alguns minutos porque o corte é feito em cada fluxo, e as sondas não medem no mesmo segundo. Dentro de cada fluxo os blocos não se misturam. Nenhum registro do Período A entra no dataset rotulado nem no treino.

**Observações da execução:** o desbalanceamento varia muito por fluxo. Em Beauharnois → Melbourne, 43% das medições são FALHA e nenhuma é RISCO; em Richterswil → Perth, só 16% são OK. A causa é o MAD muito pequeno de alguns fluxos (0,05 a 0,19 ms), que torna `z_robusto` sensível a mudanças de patamar de poucos milissegundos. Em Beauharnois a mediana diária foi de 228,6 ms no Período A, 247,0 ms em 13 e 14/09, 228,6 ms de 15 a 18/09 e 242,9 ms em 19 e 20/09, compatível com troca de rota (não verificada por traceroute). A tabela de rotulagem foi aplicada como definida na tarefa.

## 6. Scrum e diário

**Link do Scrum:** https://github.com/users/guilhermetrajanedasilva/projects/7

- [X] Board atualizado

**Link do board:** https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/blob/principal/doc/dicionario_v0.2.md


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


