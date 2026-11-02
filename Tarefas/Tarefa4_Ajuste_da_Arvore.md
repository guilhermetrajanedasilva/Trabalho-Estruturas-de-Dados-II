# Diário da Tarefa 4 — Ajuste da árvore a partir do erro

**Período:** 05/10/2026 a 11/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:** NetVision - Visualização e análise de dados de rede

**Integrantes:** Mariana Moreira Barbosa, Samara Fernandes Soares, Leandro do Nascimento Lemes, Guilherme Trajane da Silva, Vitor Julião Diogo dos Santos

**Scrum Master:** Guilherme Trajane da Silva

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

Na Tarefa 3 a árvore errou só 2 das 4.029 linhas da validação, as duas do mesmo tipo:

1. **FALHA prevista como OK por persistência de timeout.** Fluxo `7656|103.153.238.101` (Satigny → Sydney), 16/09/2026 21:34:41 e 21:38:47 UTC, com `n5_timeout` = 3, `perda_pct` = 0 e `z_robusto` muito negativo (−15,8 e −19,6). A tabela de rotulagem manda FALHA (linha 2), mas a árvore caiu na folha de `n5_timeout` > 0,50 (26 amostras, pureza 0,92), que é majoritariamente OK.
2. **Pouco suporte para o caso raro.** Só 8 linhas do treino têm `n5_timeout` ≥ 3, e `min_samples_leaf` = 5 impede a árvore de criar uma folha própria para elas.

Não houve falso alarme de RISCO em caminho longo estável nem confusão entre RISCO e FALHA na validação; por isso não havia o que corrigir nesses pontos.

**Erro da Tarefa 3 → mudança na árvore:**

| Erro observado | Mudança (profundidade, folha, critério ou métrica relativa nova) | Resultado na validação |
|---|---|---|
| 2 FALHA por `n5_timeout` ≥ 3 previstas como OK (folha sem suporte para o caso raro) | `min_samples_leaf` de 5 para **2**, para a árvore poder isolar as linhas com 3 ou mais timeouts nas últimas 5 medições | Os 2 erros somem; surge a folha `n5_timeout` > 2,50 → FALHA |
| Árvore com 14 folhas, várias pequenas, e dúvida se poda ou peso de classe ajudam | Testados `ccp_alpha` de 0,0005 a 0,002, `class_weight='balanced'` e critério entropia | Nenhum supera a configuração acima. Melhor com poda: F1 macro 0,9996 (8 folhas); com `balanced`: 0,9996 (8 folhas); com entropia: 0,9996 (9 folhas). Não adotados |
| Falta de uma visão de tendência do desvio | Testada a coluna relativa nova `delta_z_robusto` (`z_robusto` da medição menos o da anterior do mesmo fluxo, só passado) | Empata: F1 macro 1,0000 com 12 folhas, igual à árvore sem ela. **Não adotada** (não melhora e acrescenta uma coluna) |
| Profundidade | Varridas 3, 4, 5, 6 e 8 | Profundidades 5, 6 e 8 empatam; mantida **5** (a menor) |

Ao todo foram avaliadas 960 combinações só na validação (`reports/t4_busca_validacao.csv`); 6 chegaram a F1 macro 1,0000, todas com `min_samples_leaf` = 2 e Gini.

---

## 2. Árvore ajustada

- [x] Mesmas colunas relativas, mais a métrica relativa nova
- [x] Profundidade, folhas e três regras em português
- [x] Fit só no treino

**Parâmetros finais candidatos (ainda não é o teste):**
- **Algoritmo / Critério:** CART / impureza de Gini, sem peso de classes
- **Colunas:** as 8 oficiais da Tarefa 3 (`z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`); `delta_z_robusto` testada e não adotada
- **Profundidade pedida (`max_depth`):** 5
- **Profundidade obtida:** 5
- **Mínimo de amostras por folha (`min_samples_leaf`):** 2
- **Complexidade de poda (`ccp_alpha`):** 0
- **Semente (`random_state`):** 42
- **Número de folhas:** 12
- **Arquivos:** `models/arvore_tarefa4.joblib`, regras em `reports/t4_regras.txt` e parâmetros em `config/config_arvore.json` (chave `final`)
- **Fit só no treino** (10.067 linhas); o teste não foi carregado

**Regras** (as 7 folhas com mais amostras; as 12 estão em `reports/t4_regras.txt`):

1. SE z_robusto <= 2,01 E jitter_relativo <= 3,00 E perda_pct <= 16,67 E n5_timeout <= 2,50 ENTÃO OK  *(folha com 7334 amostras)*
2. SE z_robusto > 3,50 ENTÃO FALHA  *(folha com 1239 amostras)*
3. SE 2,10 < z_robusto <= 3,50 E perda_pct <= 16,67 E n5_risco > 1,50 ENTÃO RISCO  *(folha com 631 amostras)*
4. SE z_robusto <= 2,10 E jitter_relativo > 3,00 E n5_risco > 1,50 ENTÃO RISCO  *(folha com 430 amostras)*
5. SE z_robusto <= 2,10 E jitter_relativo > 3,00 E perda_pct <= 16,67 E n5_risco <= 1,50 ENTÃO OK  *(folha com 269 amostras)*
6. SE 2,10 < z_robusto <= 3,50 E n5_risco <= 1,50 ENTÃO OK  *(folha com 114 amostras)*
7. SE 2,01 < z_robusto <= 2,10 E jitter_relativo <= 3,00 E perda_pct <= 16,67 E n5_risco <= 1,50 ENTÃO OK  *(folha com 13 amostras)*

Há também a regra nova, com 2 amostras: SE `z_robusto` ≤ 2,01 E `jitter_relativo` ≤ 3,00 E `perda_pct` ≤ 16,67 E `n5_timeout` > 2,50 ENTÃO **FALHA**. Ela é a correção do erro da Tarefa 3.

---

## 3. Comparação na validação

| Modelo | F1 macro | Recall de FALHA | Recall de RISCO | Recall de OK | Folhas |
|---|:---:|:---:|:---:|:---:|:---:|
| **Árvore da Tarefa 3** (`depth=5`, `leaf=5`) | 0,9991 | 0,9952 | 1,0000 | 1,0000 | 14 |
| **Árvore desta tarefa** (`depth=5`, `leaf=2`) | **1,0000** | **1,0000** | 1,0000 | 1,0000 | 12 |

- [x] Matriz 3×3 da árvore desta tarefa, na validação:

| Real \ Previsto | OK | RISCO | FALHA | Total real |
|---|---:|---:|---:|---:|
| **OK** | 3.056 | 0 | 0 | 3.056 |
| **RISCO** | 0 | 553 | 0 | 553 |
| **FALHA** | 0 | 0 | 420 | 420 |
| **Total previsto** | 3.056 | 553 | 420 | 4.029 |

**Leitura do ganho (ou da falta de ganho):**
O ganho é real, mas pequeno: duas linhas. O recall de FALHA subiu de 0,9952 para 1,0000 e o F1 macro de 0,9991 para 1,0000, porque a árvore passou a ter uma folha para 3 ou mais timeouts nas últimas 5 medições. A árvore também ficou menor (12 folhas contra 14).

Duas ressalvas. Primeiro, esta comparação foi feita na mesma validação que escolheu os parâmetros (960 combinações), então 1,0000 é otimista e só o teste da Tarefa 5 diz se isso se sustenta. Segundo, a validação tem só 3 linhas com `n5_timeout` ≥ 3 e o treino, 8: a correção se apoia em pouquíssimos casos. A coluna `delta_z_robusto` não trouxe ganho, o que é coerente com a árvore já usar `z_robusto`, `n5_risco` e `jitter_relativo`, que descrevem o mesmo desvio.

---

## 4. Revisão com o docente

**O que foi mostrado:**  
*(a preencher pelo grupo depois da revisão com a docente)*. Sugestão do que mostrar: a tabela da seção 1 (erro → mudança), a comparação Tarefa 3 → Tarefa 4 da seção 3, o resultado negativo da coluna `delta_z_robusto`, da poda e do `class_weight`, e a confirmação de que nenhuma coluna de rota, país, IP ou RTT absoluto entrou.

**O que foi pedido para ajustar antes da Tarefa 5:**  
*(a preencher pelo grupo)*

---

## 5. Scrum e diário

- [x] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| **Vitor Julião Diogo dos Santos** | Facilitei a organização do board, conduzi as sessões de revisão dos 960 testes de hiperparâmetros e preparei a documentação para a revisão com o docente. | Garantir que a equipa não mudasse o algoritmo nem abrisse o conjunto de teste, mantendo o foco rigoroso apenas no ajuste da árvore de decisão da Tarefa 3. | Vou manter o rigor na blindagem do conjunto de teste para a Tarefa 5, garantindo que as decisões reflitam apenas os dados de validação. |
| **Mariana Moreira Barbosa** | Atualizei o script de treino para testar o parâmetro `min_samples_leaf=2`, além de executar os testes de poda (`ccp_alpha`), critério de entropia e pesos de classe (`balanced`). | Encontrar o equilíbrio perfeito para evitar o sobreajuste (*overfitting*) ao reduzir as amostras por folha para acomodar os casos raros de `n5_timeout`. | Pretendo manter a validação baseada na impureza de Gini e sem poda extra, uma vez que se mostrou a configuração mais limpa e eficaz para o nosso modelo. |
| **Guilherme Trajane da Silva (scrum master)** | Executei a rotina de validação estrita, gerei as métricas (onde o F1 macro alcançou 1,0000) e consolidei a tabela de comparação Tarefa 3 → Tarefa 4. | Ajustar e avaliar a complexidade da poda sem causar a perda de *recall* na classe crítica de FALHA, o que exigiu muitas iterações. | Manter a rotina de validação puramente baseada nas métricas macro e no *recall* das classes minoritárias, sem olhar os dados de teste. |
| **Leandro do Nascimento Lemes** | Idealizei, codifiquei e testei a nova variável `delta_z_robusto` para tentar captar a tendência temporal de degradação do fluxo. | Aceitar que a nova *feature* não trouxe ganhos reais de F1 face ao modelo base e decidir descartá-la para não adicionar complexidade desnecessária. | Continuar com a análise crítica e objetiva das *features*, privilegiando a simplicidade do modelo e rejeitando o que não traz melhoria métrica evidente. |
| **Samara Fernandes Soares** | Fiz a auditoria dos dados de entrada nas novas execuções, compus as regras finais geradas pelas 12 folhas da árvore e extraí a matriz de confusão atualizada. | Assegurar que, durante a bateria de quase mil testes, o pipeline se mantinha estritamente focado em métricas relativas (sem IPs, rotas ou RTT absoluto). | Manter a curadoria restrita aos limiares do *baseline*, garantindo a completa independência de rota do nosso preditor para a validação final. |

---

## Rubrica — Tarefa 4 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Ajuste ligado ao erro | 1,5 | Cada mudança da árvore cita um erro da Tarefa 3; continua árvore de decisão | | |
| Rota fora do modelo | 1,0 | Nenhuma coluna de rota, país, IP ou RTT absoluto; baseline da Tarefa 2 intacto | | |
| Tabela Tarefa 3 → Tarefa 4 | 1,0 | F1 macro e recall de FALHA e de RISCO na validação, com leitura | | |
| Revisão + diário | 0,5 | Incremento mostrado ao docente; diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
