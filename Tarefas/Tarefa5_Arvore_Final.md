# Diário da Tarefa 5 — Árvore final e teste único

**Período:** 12/10/2026 a 25/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:**  NetVision - Visualização e análise de dados de rede 

**Integrantes** Mariana Moreira Barbosa, Samara Fernandes Soares, Leandro do Nascimento Lemes, Guilherme Trajane da Silva, Vitor Julião Diogo dos Santos

**Scrum Master da tarefa:** Samara Fernandes Soares

**Repositório GitHub:**  https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II

> A árvore que entra aqui é a da Tarefa 4. O baseline e o rótulo são os da Tarefa 2. O teste, guardado desde a Tarefa 2, é medido **uma vez**.
>
> Continua sendo uma árvore de decisão. O grupo entrega as regras, a matriz e o que a árvore faz num fluxo que ela não viu — desde que esse fluxo tenha a própria ficha de baseline, calculada só no período inicial dele.

### Contrato desta tarefa

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Corte da Tarefa 2 e ficha de baseline | Tarefa 2 |
| **Entra** | Árvore ajustada e regras | Tarefa 4 |
| **Sai** | Teste único: matriz 3×3, F1 por classe, F1 macro | Entrega |
| **Sai** | Checagem de fluxo não visto, com baseline próprio | Entrega |
| **Sai** | Ficha da árvore (abaixo) e dicionário v0.4 igual às colunas usadas | Entrega |

Não há tarefa seguinte.

- [x] A profundidade não foi escolhida de novo olhando o teste
- [x] O baseline do teste não usou medição do próprio teste

---

## 1. Árvore que será medida

- [x] Critério, profundidade, mínimo de amostras na folha, colunas
- [x] Três regras em português, as mesmas da Tarefa 4 ou as revistas **antes** de abrir o teste
- [x] Confirmação de que país, IP, rota e RTT absoluto não estão na árvore

**Parâmetros (os da Tarefa 4, em `config/config_arvore.json`):**
Critério: Gini |
Profundidade máxima (`max_depth`): `5` (obtida: 5) |
Mínimo de amostras na folha (`min_samples_leaf`): `2` |
Poda de complexidade (`ccp_alpha`): `0` |
Peso de classes: nenhum |
Semente (`random_state`): `42` |
Folhas: 12

**Colunas (8, todas relativas ao baseline do fluxo):** `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`. O alvo é `classe`. A coluna `delta_z_robusto`, testada na Tarefa 4, não foi adotada.

**Regras** (lidas da árvore; as 12 folhas estão em `reports/t5_regras.txt` e a figura em `reports/arvore_final.png`, onde o vetor `value` de cada nó segue a ordem [FALHA, OK, RISCO]):

1. Se `z_robusto` > 3,50 (RTT muito acima do normal do próprio fluxo), classificar como **FALHA** (1.239 amostras de treino).
2. Se `2,10 < z_robusto ≤ 3,50` e `perda_pct` ≤ 16,67 e `n5_risco` > 1,5 (desvio moderado repetido nas últimas 5 medições), ou se `z_robusto` ≤ 2,10 e `jitter_relativo` > 3,00 e `n5_risco` > 1,5, classificar como **RISCO** (631 e 430 amostras).
3. Se `z_robusto` ≤ 2,01, `jitter_relativo` ≤ 3,00, `perda_pct` ≤ 16,67 e `n5_timeout` ≤ 2,5, classificar como **OK** (7.334 amostras). Perda acima de 16,67% (uma perda de 1 pacote em 3 já é 33%) ou `n5_timeout` ≥ 3 viram **FALHA** nas folhas restantes.

Confirmado no script: país, IP, rota, `fluxo_id` e RTT absoluto não estão na árvore.

## 2. Teste temporal (uma vez)## 2. Teste temporal (uma vez)

Fluxos conhecidos, período mais recente do Período B (18/09/2026 01:58 UTC a 20/09/2026 04:31 UTC, 6.034 linhas). O script `arvore_final.py` grava `reports/t5_teste_unico.json` e se recusa a medir o teste de novo sem `--repetir`.

- [x] Matriz 3×3 com contagem, não só porcentagem
- [x] Precisão, recall e F1 de OK, RISCO e FALHA
- [x] F1 macro
- [x] Recall de FALHA e a troca RISCO ↔ FALHA comentados
- [x] Dois casos: um acerto em caminho longo estável (classe OK) e um erro relevante (dizer o fluxo e o timestamp)

**Matriz (contagem absoluta):**

| Real \ Previsto | OK | RISCO | FALHA | Total real |
|---|---:|---:|---:|---:|
| **OK** | 4.111 | 0 | 0 | 4.111 |
| **RISCO** | 2 | 818 | 0 | 820 |
| **FALHA** | 0 | 0 | 1.103 | 1.103 |
| **Total previsto** | 4.113 | 818 | 1.103 | 6.034 |

| | OK | RISCO | FALHA |
|---|---:|---:|---:|
| Precisão | 0,9995 | 1,0000 | 1,0000 |
| Recall | 1,0000 | 0,9976 | 1,0000 |
| F1 | 0,9998 | 0,9988 | 1,0000 |

**F1 macro no teste:** 0,9995  
**Recall de FALHA:** 1,0000  
**Acurácia:** 0,9997 (balanceada: 0,9992)

**Troca RISCO ↔ FALHA:** nenhuma (0 de RISCO para FALHA e 0 de FALHA para RISCO). Todas as 1.103 FALHA do teste foram acertadas. O único tipo de erro foi RISCO previsto como OK (2 linhas).

**Casos analisados:**
1. **Acerto em caminho longo estável:** fluxo `7586|80.77.4.60` (Cochabamba → Dubai, mediana do Período A de 373,1 ms), 18/09/2026 02:09:47 UTC. RTT = 377,4 ms, `z_robusto` = 0,90, `aumento_pct` = 1,15%, `jitter_relativo` = 0,73, `perda_pct` = 0. Classe verdadeira OK e previsão OK. O RTT é alto em termos absolutos e a árvore não deu alarme, porque está no patamar normal daquele fluxo.
2. **Erro relevante:** fluxo `6878|143.205.170.32` (Minsk → Klagenfurt, caminho curto), 18/09/2026 19:50:01 UTC. `z_robusto` = 2,0101, `n5_risco` = 2, RTT = 26,2 ms. Classe verdadeira RISCO, previsão OK. O outro erro é parecido: fluxo `7508|94.199.170.201` (Osasco → Feldkirch), 18/09/2026 07:40:45 UTC, `z_robusto` = 2,0020, `n5_risco` = 4. Os dois estão a menos de 0,02 de `z_robusto` do limiar 2,0 da tabela de rotulagem. A árvore aprendeu o corte em 2,011 (ponto entre os valores vistos no treino), e a tabela usa 2,0 exato. É uma diferença de limiar aprendido, não um desvio relevante da rede. Arquivo: `reports/t5_erros_teste.csv`.

## 3. Fluxo que a árvore não viu

Separar um ou mais `fluxo_id` inteiros que não estejam no treino. A ficha desse fluxo sai só do período inicial dele (o mesmo piso: 1.500 RTT válidos; abaixo disso o fluxo não é avaliado).

- [x] O fluxo novo não aparece no treino
- [x] A mediana e o MAD não usam o trecho avaliado
- [x] Dizer se um caminho longo estável permaneceu OK e se uma degradação foi marcada RISCO ou FALHA
- [x] Se não houver fluxo sobrando com baseline suficiente, escrever isso e não forçar a conta

Cada um dos 8 fluxos foi separado por vez (*leave-one-flow-out*): a árvore é treinada com o treino dos outros 7 fluxos (parâmetros da Tarefa 4) e avaliada em todo o Período B do fluxo separado. O fluxo separado nunca aparece no treino (conferido por `assert` no script). A ficha dele vem só do Período A dele, a mesma da Tarefa 2 (todos têm mais de 1.500 RTT válidos); a mediana e o MAD não usam o trecho avaliado.

**Fluxos separados:** os 8 fluxos, um de cada vez (`reports/t5_fluxos_nao_vistos.csv`).

| Fluxo | Rota | Mediana A (ms) | Linhas B | OK / RISCO / FALHA reais | Acurácia | F1 macro* | Recall OK | Recall RISCO | Recall FALHA | Erros |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 6719\|203.41.0.51 | Beauharnois → Melbourne | 228,6 | 2.516 | 1.426 / 0 / 1.090 | 1,0000 | 1,0000 | 1,0000 | — | 1,0000 | 0 |
| 6878\|143.205.170.32 | Minsk → Klagenfurt (curto) | 26,0 | 2.520 | 2.389 / 71 / 60 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 0 |
| 6891\|63.222.248.5 | Belo Horizonte → Dubai | 367,7 | 2.516 | 2.019 / 415 / 82 | 0,9956 | 0,9899 | 0,9985 | 0,9807 | 1,0000 | 11 |
| 7258\|202.87.175.244 | Richterswil → Perth | 338,1 | 2.516 | 407 / 1.153 / 956 | 0,9964 | 0,9971 | 1,0000 | 1,0000 | 0,9906 | 9 |
| 7307\|37.252.245.94 | Feira de Santana → Dubai | 343,5 | 2.515 | 2.434 / 23 / 58 | 0,9873 | 0,8708 | 1,0000 | 1,0000 | 0,4483 | 32 |
| 7508\|94.199.170.201 | Osasco → Feldkirch | 199,3 | 2.513 | 2.153 / 182 / 178 | 0,9988 | 0,9970 | 0,9991 | 0,9945 | 1,0000 | 3 |
| 7586\|80.77.4.60 | Cochabamba → Dubai | 373,1 | 2.519 | 1.793 / 571 / 155 | 0,9996 | 0,9996 | 0,9994 | 1,0000 | 1,0000 | 1 |
| 7656\|103.153.238.101 | Satigny → Sydney | 299,6 | 2.515 | 2.276 / 32 / 207 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 0 |

\* F1 macro só sobre as classes que existem no fluxo (Beauharnois → Melbourne não tem RISCO).

**Resultado:**
- **Caminhos longos estáveis permaneceram OK:** o recall de OK ficou entre 0,9985 e 1,0000 em todos os fluxos longos, sem a árvore ter visto o fluxo. O fluxo curto (Minsk → Klagenfurt), quando separado, deixa o treino sem nenhum caminho curto e mesmo assim saiu com 100% de acerto: as métricas relativas não dependem do comprimento do caminho.
- **Degradações foram marcadas:** o recall de RISCO foi de 0,98 a 1,00 e o de FALHA ficou em 1,00 em 6 dos 8 fluxos. Richterswil → Perth teve recall de FALHA de 0,9906 (9 de 956 FALHA previstas como RISCO).
- **Pior caso: Feira de Santana → Dubai**, recall de FALHA de **0,4483** (32 de 58 FALHA previstas como OK). 30 dos 32 erros são medições com perda parcial de 33%, 50% ou 67% (1 a 2 pacotes perdidos em 3) e RTT dentro do normal, que a tabela de rotulagem classifica como FALHA. Explicação provável, não testada: Feira de Santana → Dubai concentra boa parte da perda parcial do projeto, e sem ele no treino a árvore vê poucos exemplos disso. Detalhe em `reports/t5_fluxos_nao_vistos_erros.csv`.
- **Limite do experimento:** com 8 fluxos e um único caminho curto, o resultado de cada fluxo separado depende muito de quantos exemplos raros (perda, timeout) os outros 7 fluxos têm.

## 4. O que declarar

- [x] **A árvore repete a tabela de rótulo.** O rótulo da Tarefa 2 foi feito com as mesmas métricas que a árvore recebe, então ela reaprende a política de rotulagem: F1 macro de 0,9995 no teste e 0,9991–1,0000 na validação mostram que a política é quase perfeitamente aprendível só com colunas relativas, não que a árvore descobriu algo sobre a rede. Não é um modelo de "ticket de roteador". Os 2 erros do teste vêm de a árvore aprender o corte de `z_robusto` em 2,011 em vez de 2,0.
- [x] **Detector, não preditor.** O alvo desta entrega é o estado **atual** da medição (a coluna `classe`). Não foi treinado o alvo "12 minutos à frente" nem feita a comparação com a regra "repetir a classe atual". Por isso o artefato é um **detector** do estado atual, e o nome preditor não se aplica.
- [x] **O teste foi medido uma vez** para esta árvore. O script rodou duas vezes (a segunda com `--repetir`, só para corrigir o cálculo do F1 macro dos fluxos não vistos quando falta uma classe); a árvore, os dados e os números do teste são idênticos nas duas. A profundidade e a folha mínima foram escolhidas só na validação. Antes do ajuste da Tarefa 4 foi feita uma contagem de linhas com `n5_timeout` ≥ 3 por bloco, inclusive no teste (0 linhas); ela não entrou na escolha dos parâmetros.
- [x] **O teste é fácil para os casos raros:** não tem nenhuma linha com `n5_timeout` ≥ 3, então não mede a correção feita na Tarefa 4. Essa correção só aparece na validação.
- [x] **Limitações:** baseline fixo de 7 dias não acompanha troca de rota (Beauharnois → Melbourne tem 43% de FALHA no Período B, o que sugere mudança de patamar ou MAD muito pequeno; não foi investigado a fundo); a rajada de 3 pacotes estima mal o jitter e só permite perda de 0, 33, 67 ou 100%; Anchors não são a rede do campus; são só 8 fluxos e um caminho curto; o desbalanceamento por fluxo vem do MAD pequeno de alguns fluxos.

## 5. Ficha da árvore

| Campo | Conteúdo |
|---|---|
| Problema | Detectar o estado (OK, RISCO ou FALHA) de uma medição pelo desvio do RTT, da perda e do jitter em relação ao baseline do próprio fluxo |
|---|---|
| Unidade | Uma medição de um `fluxo_id` no Período B |
| Baseline | Período A (mediana, MAD, jitter típico e perda típica, com piso de 1.500 RTT válidos), congelado |
| Colunas | `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco` |
| Árvore | `DecisionTreeClassifier(criterion='gini', max_depth=5, min_samples_leaf=2, ccp_alpha=0.0, random_state=42)`; 12 folhas; fit só no treino |
| Teste (uma vez) | 6.034 linhas; F1 macro 0,9995; recall de FALHA 1,0000; recall de RISCO 0,9976; 2 erros (RISCO previsto como OK) |
| Fluxos não vistos | 8 fluxos separados um a um; recall de OK ≥ 0,9985; pior caso Feira de Santana → Dubai, recall de FALHA 0,4483 |
| O que ela não faz | Não prevê o estado 12 minutos à frente; não opera em fluxo sem ficha de baseline (menos de 1.500 RTT válidos no período inicial); não acompanha troca de rota; não descobre falhas que a tabela de rotulagem não define |
| Como reproduzir | `pip install -r requirements.txt`, depois `coleta_bruta.py`, `baseline_rotulagem.py`, `arvore_inicial.py`, `ajuste_arvore.py` e `arvore_final.py`; parâmetros em `config/` (`config_arvore.json`) |

## 6. Scrum e diário

- [x] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| **Vitor Julião Diogo dos Santos** | Assegurei que o fluxo de trabalho terminaria na Tarefa 5 sem modificações no algoritmo, orquestrei a revisão do relatório de limitações e supervisionei a execução única do script de teste. | Garantir a disciplina da equipe para rodar o teste temporal uma única vez e reportar os números friamente (mesmo que apresentassem falhas em casos específicos). | Manter a transparência total sobre as limitações do projeto, como o fato de sermos um "detector" do estado atual e não um preditor. |
| **Mariana Moreira Barbosa** | Programei e executei a rotina *leave-one-flow-out* para a validação dos 8 fluxos não vistos, estruturando os resultados de recall de OK, RISCO e FALHA para cada iteração. | Compreender as quedas acentuadas de recall, como o caso específico de Feira de Santana → Dubai (recall de FALHA de 0,4483) devido a perda parcial não absorvida pelo restante do dataset. | Registrar que em projetos futuros precisaremos de um número maior e mais diversificado de rotas no baseline para evitar dependência estatística de poucos fluxos. |
| **Guilherme Trajane da Silva** | Avaliei e cataloguei os dois únicos erros reportados no teste temporal (`reports/t5_erros_teste.csv`), demonstrando que o problema foi o desvio na tolerância decimal do limiar aprendido (2,011 ao invés de 2,0). | Tentar encontrar erros clássicos de aprendizado no teste, sendo que o que ocorreu foi apenas um desvio de aproximação de ponto flutuante na árvore. | Conservar a metodologia rigorosa de debugar manualmente os erros de classificação nos logs brutos em oposição a confiar cegamente nas métricas agregadas. |
| **Leandro do Nascimento Lemes** | Compilei a Ficha Técnica Final da árvore, descrevendo todos os artefatos de entrada, hiperparâmetros, regras de reprodutibilidade e as limitações declaradas do modelo para o escopo final. | Sistematizar claramente a diferença conceitual do nosso artefato, deixando claro que se trata da detecção de desvios relativos no presente (detector) e não previsão com deslocamento de tempo (preditor). | Manter a escrita acadêmica voltada para os dados reais, evitando jargões promissórios sobre a inteligência da árvore em interpretar fisicamente o hardware da rede. |
| **Samara Fernandes Soares (Scrum Master)** | Defini hiperparâmetros da árvore (`max_depth=5`, `min_samples_leaf=2`) e criei as regras (OK/RISCO/FALHA), removendo colunas de rota/IP/país. | Ajustar o suporte das folhas sem perder a clareza das regras, especialmente mantendo o controle total sobre o que entrava no nó folha para cada decisão. | Manter as configurações em `config/` e ajustar scripts se o escopo de teste temporal vier a exigir novas rodadas no futuro. |
---

## Rubrica — Tarefa 5 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Árvore final legível | 1,0 | Regras em português, colunas relativas, parâmetros da Tarefa 4 | | |
| Teste único | 1,5 | Matriz 3×3 em contagem, F1 por classe, F1 macro, casos curto/longo; teste não escolheu a árvore | | |
| Fluxo novo com baseline próprio | 1,0 | Ficha só no período inicial; ou limitação declarada se faltou fluxo | | |
| Ficha + diário | 0,5 | Ficha preenchida e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
