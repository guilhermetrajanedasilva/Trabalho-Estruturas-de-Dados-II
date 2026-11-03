# RFC: Preditor de degradação de rede com RTT normalizado

> Um RFC formaliza o problema, o contrato dos dados e o critério de decisão antes de se investir no classificador. Este documento escolhe a **representação** do fenômeno (RTT normalizado por fluxo). A família do algoritmo (árvore, floresta, boosting ou outro) ficou para a etapa de modelagem; a disciplina adotou a árvore de decisão (ver a atualização de 02/11/2026).
---

## 1. Resumo

O projeto constrói um classificador de três estados — **OK**, **RISCO** e **FALHA** — para medições ICMP de pares origem–destino. O estado descreve o afastamento do fluxo em relação ao seu próprio comportamento normal, estimado num período anterior e depois congelado.

A distância da rota entra na física do RTT e na chance de haver mais saltos, congestionamento e perda. Ela não entra na classe. Um RTT de 180 ms pode ser o normal de um caminho transoceânico saudável; um salto de 25 ms para 58 ms pode ser degradação num caminho curto. O modelo aprende esse desvio, em conjunto com perda, jitter relativo, timeouts e persistência.

---



## 2. Contexto e motivação

Uma rede em operação precisa distinguir três coisas que aparecem juntas numa série de ping:

1. **Latência estrutural.** A propagação na fibra tem limite físico. Mais quilômetros e mais roteadores aumentam o RTT mesmo com o caminho saudável. Cruzar o Atlântico em cerca de 150–200 ms é atraso esperado, não defeito. O mesmo vale para os caminhos longos medidos neste projeto: Belo Horizonte→Dubai e Cochabamba→Dubai têm mediana de cerca de 368 e 373 ms no Período A, e Beauharnois→Melbourne, 229 ms. No extremo oposto, Minsk→Klagenfurt tem mediana de 26 ms.
2. **Degradação.** O caminho continua respondendo, mas piorou em relação a si mesmo: RTT sobe além da variação típica, o jitter deixa de ser estável ou surge perda moderada e persistente. Causas típicas: congestionamento, enlace saturado, hardware no limite, interferência.
3. **Indisponibilidade.** Perda total ou ausência persistente de resposta. É falha independentemente da distância.
4. **Mudança de rota.** O encaminhamento troca de caminho (tromboning, failover, novo trânsito). O RTT muda de patamar e permanece estável, com perda e jitter baixos. O enlace novo pode estar saudável; o que envelheceu foi o baseline.

Tratar “RTT alto” como falha ensina geografia. Na regra absoluta antiga (OK ≤ 50 ms, FALHA > 100 ms), caminhos longos estáveis viravam FALHA permanente e um enlace curto que quadruplicasse a latência ainda podia sair como OK. No Período B desta coleta (20.130 medições), 12.508 medições que seriam FALHA absoluta (RTT > 100 ms ou timeout) são OK no critério relativo, e 60 que seriam OK absoluta (RTT ≤ 50 ms) são FALHA relativa. A regra absoluta classificaria 87,5% do Período B como FALHA, quase só por causa da distância.

O usuário do alerta é quem opera a rede (campus, provedor ou NOC). O alerta apoia a decisão de investigar o enlace agora, observar, ou recalibrar o “normal” porque o caminho mudou.

---



## 3. Problema e evento a ser previsto


| Pergunta                     | Resposta                                                                                                                                                                                                                                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Qual evento será previsto?   | Degradação ou indisponibilidade de um fluxo ICMP em relação ao baseline daquele fluxo.                                                                                                                                                                                                            |
| Como será definida a classe? | Regra híbrida, auditável, relativa ao fluxo: desvio robusto do RTT, aumento relativo, jitter relativo, perda e persistência. Perda de 100% ou ausência persistente de RTT é FALHA mesmo sem baseline. Os rótulos são operacionais: o modelo reproduz essa política, não um ticket de equipamento. |
| Qual é o horizonte?          | Dois alvos, em arquivos separados. **Detector:** `status_atual` da janela corrente (a coluna `classe` do `dataset_rotulado_B.csv`, gerado na Tarefa 2). **Preditor:** `status_futuro` em 12 minutos (três intervalos do mesh, de 240 s), a ser derivado desse dataset nas etapas seguintes. O preditor só é útil se superar a persistência do estado atual.                                                              |
| Qual é a unidade de análise? | Uma medição de um fluxo, enriquecida com a janela causal recente do mesmo fluxo. O fluxo é `fluxo_id = probe_id                                                                                                                                                                                   |


Estados:


| Classe    | Significado operacional                                                                    |
| --------- | ------------------------------------------------------------------------------------------ |
| **OK**    | RTT, jitter e perda compatíveis com o normal daquele fluxo.                                |
| **RISCO** | Aumento relevante e persistente de latência, jitter ou perda, ainda sem indisponibilidade. |
| **FALHA** | Desvio extremo e persistente, perda elevada ou ausência de resposta.                       |


Há um quarto estado **operacional**, fora do alvo supervisionado de três classes: **RECALIBRAR**. Ele marca mudança estável de patamar de RTT (rota nova saudável). Não é falha e não deve ser ensinado como FALHA.

---



## 4. Escopo


| Pergunta         | Resposta                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Recorte          | Overlay lógica sobre o *Anchoring Mesh* público do RIPE Atlas (ping IPv4). 8 fluxos `probe → anchor` (8 IPs de destino), em 6 combinações de país de origem e destino (BO→AE, BR→AE, BR→AT, BY→AT, CA→AU e CH→AU), com um caminho curto (Minsk→Klagenfurt) e sete longos. Foram formados 10 pares; os pares Camaçari→185.34.2.114 e Mississauga→92.60.13.86 foram retirados porque a medição mesh devolveu JSON vazio para eles. A classe não usa o país nem a categoria geográfica.                                                                                                                                                          |
| Período          | 06/09/2026 04:32 UTC a 20/09/2026 04:32 UTC. Sete dias de baseline (Período A) e sete dias posteriores de dataset (Período B), sem sobreposição. O Período B vai de 13/09/2026 04:32 UTC a 20/09/2026 04:32 UTC.                                                                                                                                                                                                                          |
| Dentro do escopo | Leitura de medições já existentes; baseline congelado por fluxo; features relativas; rótulos OK / RISCO / FALHA; split temporal e split por fluxo; comparação com a persistência; contrato para um monitor local futuro com o mesmo esquema.                                                                                                                              |
| Fora de escopo   | Criar medições (`POST`) ou gastar créditos RIPE Atlas. IPv6, traceroute e HTTP na mesma coluna de latência. Limiar global de RTT (50 ms, 100 ms ou qualquer outro). País, IP ou `rota_id` como feature do modelo. Balancear o dataset escolhendo rotas que “fabricam” uma classe. Preencher RTT ausente com 0. Split aleatório de linhas. Escolher o algoritmo neste RFC. |


---



## 5. Usuários e decisão apoiada

O alerta é para quem administra o enlace monitorado. Com **FALHA**, a ação é investigar perda, timeout ou desvio extremo persistente. Com **RISCO**, a ação é observar e priorizar, sem tratar o evento como queda. Com **OK**, nenhuma intervenção. Com **RECALIBRAR**, a ação é abrir um novo período de baseline para o fluxo e não abrir chamado de falha só porque o RTT mudou de patamar.

O mesmo contrato vale para o `log_rede.csv` da instituição, depois de um aquecimento de pelo menos 1.500 amostras válidas naquele fluxo. Sem esse aquecimento não há mediana confiável, e o modelo normalizado não opera.

---



## 6. Dados e fontes


| Fonte                                                     | O que fornece                                                                                           | Papel                                      |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| RIPE Atlas v2, mesh de Anchors, ping IPv4 (`GET` público) | Timestamp, `probe_id`, destino, RTT da rajada (tipicamente 3 pacotes), enviados/recebidos, timeout      | Medição bruta. Feature e insumo do alvo.   |
| Período A, por `fluxo_id`                                 | Mediana e MAD do RTT, jitter típico, perda típica, cobertura                                            | Baseline congelado. Não é linha de treino. |
| Período B                                                 | Features absolutas e relativas, janela de cerca de 20 minutos, `status_atual`, `status_futuro` (12 min) | Dataset do detector e do preditor.         |


Volume observado: 39.677 registros brutos (19.547 no Período A e 20.130 no Período B), 88 timeouts preservados e nenhuma duplicata. Os 8 fluxos têm baseline suficiente (mínimo de 1.500 RTT válidos no Período A; o menor tem 1.970), então nenhum foi excluído por esse critério. O `dataset_rotulado_B.csv` tem 20.130 linhas. No Período B a distribuição relativa é 74,0% OK (14.897), 12,2% RISCO (2.447) e 13,8% FALHA (2.786). A malha passa a maior parte do tempo no próprio normal, mas o desbalanceamento varia muito por fluxo (ver seção 10).

Cadência nativa do mesh: 240 segundos (nos dados coletados os instantes não são múltiplos exatos de 240 s; cada sonda tem seu próprio deslocamento). Jitter da amostra é o desvio-padrão dos RTTs da rajada somente quando há pelo menos duas respostas; com 0 ou 1 resposta o jitter fica vazio.

O material sobre distância das rotas recomenda, para um agente local, rajadas de 10 a 20 pings espaçados de 1 segundo a cada 5 minutos, jitter no sentido da RFC 3550 e um baseline de cerca de 5 dias. Esse desenho é o contrato do **monitor local futuro**. A coleta deste projeto não o replica: o mesh já amostra a cada 4 minutos com 3 pacotes, a leitura é somente `GET`, e um ping contínuo a cada segundo criaria carga inútil. Cinco dias são o piso citado para um perfil dinâmico; sete dias foram adotados para cobrir um ciclo semanal em cada período e ficar acima de 1.500 amostras por fluxo.

**Dicionário de dados:** a ser versionado junto com `COLUNAS_MODELO`. País, endereço e identificador de rota permanecem na auditoria e saem da matriz do modelo.

---



## 7. Custo dos erros


| Tipo de erro            | O que significa                                                                      | Consequência                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Falso negativo de FALHA | Indisponibilidade ou desvio extremo persistente classificado como OK ou RISCO        | O enlace degrada sem investigação. É o erro mais grave.                              |
| Falso negativo de RISCO | Início de saturação tratado como OK                                                  | Atraso na priorização. Grave, e mais difícil porque RISCO é a classe menos frequente (12,2%).    |
| Falso positivo de FALHA | Rota longa saudável, pico isolado ou mudança estável de caminho rotulados como queda | Fadiga de alerta e chamado indevido. Foi o modo de falha da regra absoluta.          |
| Falso positivo de RISCO | Oscilação normal do fluxo disparando alerta                                          | Ruído operacional. A persistência (2 de 5 medições) existe para cortar pico isolado. |


A métrica principal é o **F1 macro**, com recall de FALHA e a confusão RISCO↔FALHA reportados à parte. Acurácia isolada é enganosa com 74% de OK. O limiar de decisão do modelo, quando houver probabilidade, escolhe-se na validação; o teste é usado uma vez.

---



## 8. Abordagem proposta

O tipo de modelo adequado é o **Modelo RTT normalizado**: um único modelo treinado com muitos fluxos, cada um descrito pelo desvio em relação ao seu baseline. Um modelo por fluxo exigiria série e manutenção próprias para cada caminho. Um modelo único com RTT absoluto confunde distância com falha.

Caminho, sem escolha de algoritmo:

ingestão do mesh (JSON bruto preservado) → Período A só para baseline → congelamento → features relativas no Período B → rótulo híbrido → split temporal e split por fluxo → baselines de regra (persistência e classe majoritária) → um `Pipeline` (pré-processamento + classificador) → limiar na validação → model card.

### 8.1 O que a distância explica

A distância aumenta a chance de falha de entrega porque o pacote atravessa mais saltos, acumula atraso de propagação e fica exposto a mais pontos de congestionamento. Em meio sem fio ou em cabo fora do padrão, a distância também degrada o sinal. Congestionamento, cabo, conector, interferência e hardware continuam sendo causas mesmo em rota curta.

Por isso o RTT médio bruto não classifica. Ele mistura o comprimento do caminho com o incidente. O que classifica é o comportamento estatístico do RTT **daquele** fluxo, junto com perda e instabilidade (jitter), sustentados no tempo.

Exemplos que o modelo tem de tratar como OK quando estáveis:


| Caminho                                                   | RTT normal observado (mediana do Período A) | Leitura                                                                 |
| --------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| Minsk (BY) → Klagenfurt (AT)                              | 26 ms                                       | Caminho curto; normal baixo.                                            |
| Osasco (BR) → Feldkirch (AT)                              | 199 ms                                      | Transatlântico, saudável se estável.                                    |
| Beauharnois (CA) → Melbourne (AU)                         | 229 ms                                      | Longo; ver observação sobre mudança de patamar na seção 8.5.            |
| Satigny (CH) → Sydney (AU) / Richterswil (CH) → Perth (AU) | 300 ms e 338 ms                             | Longos; normal do fluxo.                                                |
| Feira de Santana, Belo Horizonte e Cochabamba → Dubai (AE) | 343, 368 e 373 ms                           | Normal do fluxo. Majoritariamente OK no rótulo relativo (ver seção 10). |


O caso didático do material de rotas (SP→Espanha→RJ, RTT estável perto de 180 ms, contra 5–15 ms no caminho direto) é mudança de encaminhamento, tratada na seção 8.5, não como falha de hardware.

### 8.2 Baseline por fluxo

O baseline é uma ficha por `fluxo_id` (`probe_id|dst_addr`), calculada só no Período A e depois congelada. O Período B não entra nessa conta e não é rotulado com dados de A.


| Passo | O que fazer                                                                                                                                                                  |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Separar o fluxo. Ordenar as medições pelo timestamp.                                                                                                                         |
| 2     | Cortar o tempo. Período A: 06/09/2026 04:32 UTC até 13/09/2026 04:32 UTC (7 dias). Período B: o instante seguinte até 20/09/2026 04:32 UTC. Sem amostra nos dois períodos.   |
| 3     | Marcar RTT válido. Entra na ficha só a medição com RTT presente. RTT ausente e perda de 100% ficam de fora da mediana e do MAD. Continuam no dataset como evento de timeout. |
| 4     | Exigir volume. Menos de 1.500 RTT válidos no Período A: o fluxo é `baseline_insuficiente` e não recebe classe.                                                               |
| 5     | Calcular a ficha e gravar uma linha em `baseline_por_fluxo.csv` (com `status`, contagens e o IQR usado no caso MAD = 0). O script confere a ficha congelada a cada execução e só a regrava com `--recalcular-baseline`. Não recalcular com o Período B.                                                                             |



| Campo da ficha  | Fórmula, só com o Período A                                               |
| --------------- | ------------------------------------------------------------------------- |
| `mediana`       | mediana dos RTT válidos                                                   |
| `MAD`           | mediana(abs(RTT − mediana)) dos RTT válidos                               |
| `jitter_tipico` | mediana do jitter nas medições com jitter presente                        |
| `perda_tipica`  | mediana de `perda_pct` em todas as medições do período, inclusive timeout |
| `prop_resposta` | medições com RTT válido / medições do período                             |


Essa ficha é o “normal” do fluxo. Um RTT de 370 ms pode ser a mediana de Cochabamba→Dubai e, nesse caso, é o valor de referência, não um defeito. A rotulagem da seção 8.4 só começa depois que a ficha existe.

A média e o desvio-padrão clássicos, sugeridos no material de rotas como “média ± 1, 2 ou 3 desvios”, descrevem a mesma ideia (uma janela de normalidade própria da rota). Eles são substituídos por mediana e MAD porque picos — justamente os incidentes — inflam a média e o desvio e alargam o “normal” até engolir a falha. O escore robusto é a versão estável da regra dos três sigmas:

$$z_{\text{robusto}} = \frac{x - \operatorname{mediana}}{1{,}4826 \times \mathrm{MAD}}$$

O fator 1,4826 torna o MAD comparável ao desvio-padrão quando a distribuição é aproximadamente normal. Assim, os gatilhos “cerca de 2 desvios” e “cerca de 3 desvios” do material de rotas sobrevivem, sem herdar a sensibilidade da média.

Se MAD = 0 e a latência corrente é a mediana, z = 0. Caso contrário usa-se IQR/1,349 ou um piso de 1 ms, para não dividir por zero.

### 8.3 Features

Cada linha do modelo leva o vetor relativo, não o mapa:

$$X = [\text{latência relativa}, z_{\text{robusto}}, \text{perda}, \text{jitter relativo}, \text{timeouts}, \text{tendência}, \text{persistência}]$$

Definições:

```text
latencia_relativa   = latencia_atual / mediana_A
aumento_latencia_pct = (latencia_atual - mediana_A) / mediana_A * 100
z_robusto           = (latencia_atual - mediana_A) / (1,4826 * MAD_A)
jitter_relativo     = jitter_atual / jitter_tipico_A
```

Uma razão de latência igual a 1,0 é “no normal” tanto para Minsk→Klagenfurt (26 ms) quanto para Cochabamba→Dubai (373 ms). Tendência e persistência olham as últimas janelas do mesmo fluxo (cerca de cinco medições, ~20 minutos), contadas só dentro do Período B: as 4 primeiras medições de cada fluxo têm janela menor, e nenhum dado do Período A entra no B. País, IP e identificador de rota ficam de fora: a árvore aprenderia “Japão = FALHA” e o contrato quebraria no log local.

RTT ausente permanece vazio, com `timeout_atual = 1`. Zero milissegundo seria um OK falso e ainda contaminaria qualquer média futura.

### 8.4 Regra de rotulagem

A classe nasce de uma política explícita, não de agrupamento sobre o RTT. O aluno calcula as métricas e aplica a primeira linha que for verdadeira. Não há empate: FALHA ganha de RISCO, e RISCO ganha de OK.

**Métricas, calculadas por fluxo com o baseline do Período A congelado.**


| Métrica           | Fórmula                                                                           | Valor que entra na regra |
| ----------------- | --------------------------------------------------------------------------------- | ------------------------ |
| `mediana`         | mediana dos RTT válidos do Período A                                              | ms                       |
| `MAD`             | mediana(abs(RTT − mediana)) dos RTT válidos do Período A                          | ms                       |
| `z_robusto`       | (RTT atual − mediana) / (1,4826 × MAD)                                            | número sem unidade       |
| `aumento_pct`     | (RTT atual − mediana) / mediana × 100                                             | %                        |
| `jitter_relativo` | jitter atual / jitter típico do baseline                                          | número sem unidade       |
| `perda_pct`       | (enviados − recebidos) / enviados × 100                                           | %                        |
| `timeout_atual`   | 1 se não há RTT ou `perda_pct` = 100; senão 0                                     | 0 ou 1                   |
| `n5_timeout`      | quantos `timeout_atual` = 1 nas últimas 5 medições deste fluxo, incluindo a atual | 0 a 5                    |
| `n5_aumento80`    | quantas das últimas 5 têm `aumento_pct` > 80                                      | 0 a 5                    |
| `n5_risco`        | quantas das últimas 5 cumprem o critério de risco da linha 5                      | 0 a 5                    |


Casos de conta, para o resultado não depender de quem calcula:


| Situação                                  | O que fazer                                                                               |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| RTT ausente                               | Não calcular `z_robusto` nem `aumento_pct`. `timeout_atual` = 1. Não preencher RTT com 0. |
| MAD = 0 e RTT atual = mediana             | `z_robusto` = 0                                                                           |
| MAD = 0 e RTT atual ≠ mediana             | Trocar o denominador por max(IQR / 1,349, 1 ms)                                           |
| Jitter atual vazio (menos de 2 respostas) | O critério de jitter não dispara                                                          |
| Jitter típico = 0 e jitter atual = 0      | `jitter_relativo` = 1                                                                     |
| Jitter típico = 0 e jitter atual > 0      | Tratar como `jitter_relativo` ≥ 3                                                         |
| Menos de 1.500 RTT válidos no Período A   | Não rotular. Fluxo `baseline_insuficiente`                                                |


**Regra de rótulo. Parar na primeira linha verdadeira.**


| Ordem | Classe    | Métrica                                                                                                          | Limiar exato                                                       |
| ----- | --------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1     | **FALHA** | `perda_pct`                                                                                                      | ≥ 10 nesta medição (inclui 33%, 67% e 100% da rajada de 3 pacotes) |
| 2     | **FALHA** | `n5_timeout`                                                                                                     | ≥ 3                                                                |
| 3     | **FALHA** | `z_robusto`                                                                                                      | ≥ 3,5 nesta medição, com RTT presente                              |
| 4     | **FALHA** | `n5_aumento80`                                                                                                   | ≥ 2                                                                |
| 5     | **RISCO** | nesta medição, pelo menos um destes: `2 ≤ z_robusto < 3,5`, ou `30 ≤ aumento_pct ≤ 80`, ou `jitter_relativo ≥ 3` | e `n5_risco` ≥ 2                                                   |
| 6     | **OK**    | nenhuma linha anterior                                                                                           | pico isolado também fica OK                                        |


Leitura das linhas 5 e 6: um único desvio moderado não vira RISCO. Dois desvios moderados nas últimas cinco medições viram RISCO. `z_robusto` ≥ 3,5 vira FALHA já na medição corrente. Perda de um pacote em três (≥ 33%) vira FALHA na hora, porque 33 ≥ 10.

`status_absoluto` (OK ≤ 50 ms, FALHA > 100 ms) não entra nesta tabela.

Regra crítica, independente do baseline e alinhada ao material de rotas (“perda é o primeiro gatilho”):

```text
perda = 100% ou ausência persistente de RTT  =>  FALHA
```

A persistência existe porque uma rajada isolada é ruído. Um pico não sustenta FALHA.

Os limiares absolutos de perda do material de rotas (estável até 0,5%, risco de 0,5% a 2%, falha acima de 2%) e de jitter (estável abaixo de 10–20 ms, risco de 20–50 ms, falha acima de 50 ms) descrevem bem uma rajada de 15 pacotes num enlace que se quer apto a voz e vídeo. Eles não são o contrato desta coleta, por dois motivos de medida:

- Com 3 pacotes ICMP, a perda observável é 0%, 33%, 67% ou 100%. Faixas de 0,5% e 2% não aparecem na amostra.
- Um teto global de jitter em milissegundos repete o erro do teto global de RTT: o jitter típico cresce com o caminho. O que entra no rótulo é o jitter dividido pelo jitter do próprio baseline.

Quando o monitor local passar a usar rajadas de 10 a 20 pacotes, a perda pode descer à granularidade do material de rotas, sempre comparada também à perda típica do fluxo. O espírito permanece: perda e instabilidade disparam alerta; o valor bruto do RTT não dispara sozinho.

A regra absoluta antiga permanece só em `status_absoluto`, para auditoria.

No Período B, o mecanismo dominante de FALHA deixou de ser “RTT > 100 ms”. Pela ordem da tabela, as 2.786 linhas de FALHA se dividem em desvio robusto (2.629 linhas, linha 3), perda ≥ 10% (153, linha 1) e 3 ou mais timeouts nas últimas 5 medições (4, linha 2); a linha 4 não disparou. Das 2.447 linhas de RISCO, 1.571 têm jitter relativo ≥ 3 e 1.537 têm 2 ≤ z_robusto < 3,5 (os dois critérios se sobrepõem em parte); nenhuma depende só do aumento de 30–80%. Houve 29 timeouts no Período B.

### 8.5 Mudança de rota

O material de rotas acrescenta um caso que o baseline fixo de sete dias não cobre. Se o RTT muda de patamar e **permanece estável**, com perda próxima de zero e jitter baixo por uma janela longa (no material, mais de uma hora; na cadência de 4 minutos, da ordem de 15 amostras), a evidência é de novo encaminhamento, não de saturação.

Critério operacional proposto:

```text
se |z_robusto| alto
   e perda próxima do normal do fluxo
   e jitter_relativo baixo
   por uma janela sustentada (ordem de 1 hora)
então RECALIBRAR
senão aplicar a regra híbrida da seção 8.4
```

RECALIBRAR descarta o uso da ficha antiga para aquele fluxo e abre um novo período de baseline (o material sugere 24–48 h nesse caso excepcional; o piso de 1.500 amostras válidas continua valendo antes de voltar a classificar). Queda de RTT estável (fim de um tromboning) segue a mesma regra. Essas janelas não entram como FALHA no treino: ensinar “patamar novo e estável = pane” recria a confusão entre distância e defeito.

O fluxo Beauharnois→Melbourne mostra o padrão nesta coleta: a mediana diária de RTT foi de 228,6 ms no Período A, 247,0 ms em 13 e 14/09, voltou a 228,6 ms de 15 a 18/09 e subiu para 242,9 ms em 19 e 20/09. Com MAD de 0,065 ms no Período A, esses patamares estáveis viram z_robusto alto e 43% das medições desse fluxo saem como FALHA (1.090 de 2.516), todas pela linha 3. É compatível com troca de rota (não verificada por traceroute) e é o caso que a seção prevê encaminhar a RECALIBRAR. O dataset já rotulado do Período B ainda não separa esse estado. Introduzir a coluna é decisão da próxima revisão de rótulos, feita só com o passado de cada fluxo, sem usar o período de teste.

O fluxo é identificado pelo par probe e endereço de destino, não por um nome DNS re-resolvido a cada ciclo. Troca de IP é outro fluxo e exige baseline próprio.

### 8.6 Como o modelo deve ser lido

O modelo não aprende que RTT alto significa falha. Aprende que risco ou falha ocorrem quando o comportamento recente do fluxo se afasta do normal daquele mesmo fluxo, com perda, instabilidade ou ausência de resposta, e que um patamar novo porém estável pede recalibração.

Para um fluxo nunca visto, o procedimento é de calibração, não de retreino: observa-se o período inicial, congela-se a ficha e só então se aplicam as features relativas. Sem esse período o modelo não opera naquele fluxo.

---



## 9. Avaliação

Dois protocolos, com resultados separados.

**Protocolo A — tempo.** Dentro de cada fluxo do Período B, o passado treina, um bloco posterior valida e o bloco mais recente testa. Sem sorteio de linhas. Janelas com lag respeitam uma folga entre os blocos. Qualquer imputação, escala ou balanceamento aprende-se só no treino. Proporção de partida 50% / 20% / 30% dentro de B, ajustada para respeitar a cronologia e o suporte de RISCO.

**Protocolo B — fluxos novos.** Grupos inteiros por `fluxo_id` (GroupShuffleSplit ou GroupKFold, semente fixa). Nenhum fluxo de teste aparece no treino. O baseline do fluxo de teste sai só do período inicial dele. O conjunto de teste precisa continuar cobrindo caminho curto e caminho longo. Com 8 fluxos e um único caminho curto (Minsk→Klagenfurt), reservar esse fluxo para teste deixa o treino sem caminho curto, e mantê-lo no treino deixa o teste sem ele; essa limitação deve ser registrada nos resultados.

Métricas: matriz 3×3, precisão, recall e F1 por classe, F1 macro, balanced accuracy, e o mesmo corte por fluxo. Comparar o preditor de 12 minutos com a regra que copia `status_atual`. Essa persistência **não foi medida** nas Tarefas 3 a 5, porque o alvo de 12 minutos não foi construído (atualização de 02/11/2026). Sem ganho sobre a persistência, o artefato é um detector, e o nome preditor não se sustenta.

---



## 10. Riscos e limitações

- Rótulos heurísticos. O modelo aprende a política de degradação, não uma falha confirmada em log de roteador.
- Anchors são melhor provisionados que um CPE de campus. Perda e jitter de último quilômetro ficam sub-representados. O log local continua necessário para a rede da instituição.
- Amostras do mesmo fluxo a cada 4 minutos são autocorrelacionadas. Os dois protocolos de split são a mitigação; um split aleatório inflaria o resultado.
- Rajada de 3 pacotes estima mal o jitter. O jitter relativo ainda assim passou a marcar RISCO; a RFC 3550 fica reservada ao agente local, quando a rajada tiver pacotes suficientes.
- Baseline fixo de 7 dias não acompanha deriva lenta nem troca de rota. A seção 8.5 é a correção prevista; até lá, uma mudança estável de caminho pode ser rotulada como desvio extremo.
- Sete mais sete dias cobrem um ciclo semanal em cada período, não a estabilidade entre semanas.
- A 12 minutos o futuro ainda é, em grande parte, o estado atual.
- Dois dos 10 pares formados (sondas 7457 e 7682) vieram sem nenhum registro e foram retirados; nenhum fluxo ficou abaixo do piso de 1.500 RTT válidos. A coleta tem só 8 fluxos e um único caminho curto, o que limita o Protocolo B.
- Desbalanceamento por fluxo. Com MAD muito pequeno (0,05 a 0,19 ms em Minsk, Beauharnois, Osasco e Satigny), qualquer mudança de patamar de poucos milissegundos vira z_robusto alto. Beauharnois→Melbourne tem 43% de FALHA e 0% de RISCO; Richterswil→Perth tem 38% de FALHA, 46% de RISCO e só 16% de OK. A fórmula do rótulo segue a política da Tarefa 2; o efeito deve ser levado em conta na avaliação por fluxo.
- Dois fluxos mostram a sonda hoje fora do ar (`Disconnected` e `Written Off` na validação de 01/11/2026), mas tinham dados completos em setembro.
- RISCO é a classe menos frequente. F1 macro e o suporte dessa classe precisam aparecer no relatório; rebalancear por rota ensinaria o mapa de novo.

---



## 11. Critérios de sucesso

1. Nenhum fluxo de teste contribui para o próprio baseline, e nenhuma feature usa país, IP ou rota.
2. No teste temporal, o detector separa OK, RISCO e FALHA com F1 macro acima da classe majoritária, e o recall de FALHA fica explícito. **Atendido:** F1 macro 0,9995 e recall de FALHA 1,0000 (com a ressalva de que a árvore reaprende a tabela de rótulo).
3. O preditor de 12 minutos supera a persistência de `status_atual` no mesmo teste. Se não superar, a entrega declara o sistema como detector. **Não avaliado:** o preditor não foi treinado; a entrega é declarada como detector.
4. No teste por fluxos novos, depois do aquecimento, um caminho longo estável não colapsa em FALHA e um caminho curto degradado não colapsa em OK. **Atendido na maior parte:** com cada fluxo separado do treino, o recall de OK ficou entre 0,9985 e 1,0000 e o fluxo curto (Minsk→Klagenfurt) teve 100% de acerto. Exceção: Feira de Santana→Dubai, com recall de FALHA de 0,4483 (perda parcial).
5. Exemplos auditáveis: um caminho longo estável (por exemplo Cochabamba→Dubai ou Satigny→Sydney) como OK; um fluxo curto (Minsk→Klagenfurt) com aumento persistente como RISCO ou FALHA; timeout persistente como FALHA; um patamar novo e estável encaminhado a RECALIBRAR quando essa regra estiver ativa.
6. Model card e dicionário alinhados às colunas que o `Pipeline` de fato consome.

---



## 12. Alternativas consideradas


| Alternativa                                                                                               | Consequência que levou à rejeição                                                                                                                                                                                   |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Limiar global de RTT (50/100 ms, ou “acima de 100 ms é falha”)                                            | A classe vira distância. Rota longa estável fica sempre em FALHA; rota curta pode degradar centenas de por cento e continuar OK.                                                                                    |
| Um modelo só com RTT absoluto misturando todos os fluxos                                                  | O algoritmo usa o comprimento do caminho como atalho para a classe.                                                                                                                                                 |
| Um modelo separado por fluxo                                                                              | Válido para um único enlace, e caro em dados e manutenção para um preditor reutilizável.                                                                                                                            |
| Média e desvio-padrão do material de rotas como estatística do baseline                                   | A intuição (janela de 2 e 3 sigmas) é a certa; a média e o desvio são arrastados pelos picos que se quer detectar. Mediana e MAD preservam a mesma escala via o fator 1,4826.                                       |
| Jitter absoluto de 20/50 ms e perda de 0,5/2% como lei universal                                          | Jitter absoluto reintroduz a distância. Perda de 0,5% não é observável em rajada de 3 pacotes. Ficam como meta do agente local, relativas ao fluxo.                                                                 |
| Baseline de 5 dias com rajadas de 15 pings a cada 5 minutos, ping local a um único alvo (RJ–SP ou BR–EUA) | Adequado a um app de um enlace. Esta coleta precisa de muitos fluxos, série já existente e zero crédito: mesh público, 7+7 dias, 240 s. O desenho local permanece como contrato futuro, com o mesmo vetor relativo. |
| Preencher timeout com 0 ms                                                                                | 0 ms parece latência excelente e polui a média.                                                                                                                                                                     |
| k-means sobre o RTT, ou percentil global do lote                                                          | O alvo deixa de ser uma política operacional e passa a depender do lote futuro, que o monitor não tem.                                                                                                              |
| Split aleatório de linhas                                                                                 | Janelas vizinhas do mesmo fluxo caem em treino e teste.                                                                                                                                                             |
| Probes aleatórios do mesh, ou superamostrar rotas longas para “balancear” FALHA                           | Com limiar absoluto, 87,5% do Período B desta coleta viraria FALHA. Com limiar relativo, rota longa estável é justamente o OK que o modelo precisa ver.                                                                                 |
| IPv4 e IPv6 na mesma coluna `latencia_ms`                                                                 | Dois regimes físicos no mesmo número.                                                                                                                                                                               |
| Medições próprias no RIPE Atlas                                                                           | Crédito, série curta e viés da sonda de quem coleta.                                                                                                                                                                |


---



## 13. Perguntas em aberto

1. A coluna RECALIBRAR entra numa re-rotulagem do Período B antes do treino, ou só no monitor em operação? Até a resposta, o treino usa as três classes já gravadas e documenta o viés de mudança de rota.
2. Os limiares (z = 2 e 3,5, aumento de 30% e 80%, jitter relativo ≥ 3, perda ≥ 10%) podem ser ajustados na validação. O teste não escolhe limiar.
3. Baseline móvel causal (somente os 14 ou 28 dias anteriores a t) substitui a ficha fixa quando houver série mais longa que 7+7.
4. Qual classificador entra no `Pipeline` decide-se na validação, contra persistência e classe majoritária.
5. No agente local, o tamanho da rajada (10 a 20 pacotes) e o uso da RFC 3550 dependem de uma coleta própria; não alteram o contrato do CSV já fechado.

---



## 14. Encadeamento


| Etapa             | Produz                                                                                          | A etapa seguinte usa           |
| ----------------- | ----------------------------------------------------------------------------------------------- | ------------------------------ |
| Coleta            | JSON bruto (`data/raw/json/`), `ping_bruto.csv` dos Períodos A e B, `config_coleta.json`, sem classe na ingestão | Este bruto                     |
| Baseline e rótulo | `baseline_por_fluxo.csv`, `dataset_rotulado_B.csv` (com `split`), `corte_temporal.csv`, `config_rotulagem.json` (regra versionada); `dataset_predicao` (`status_futuro`) a derivar | Estes rótulos e estas features |
| Divisão           | Protocolos A e B, mapa de `fluxo_id`, auditoria de vazamento                                    | O mesmo split em todo retreino |
| Modelo            | `Pipeline`, comparação com persistência, limiar na validação, model card                        | —                              |


Não se rotula o período que estimou o baseline. Não se sorteia linha para o teste final.

---




