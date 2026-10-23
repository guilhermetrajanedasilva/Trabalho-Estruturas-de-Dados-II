# Diário da Tarefa 5 — Árvore final e teste único

**Período:** 12/10/2026 a 25/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:** Mariana Moreira Barbosa, Samara Fernandes Soares, Leandro do Nascimento Lemes, Guilherme Trajane da Silva, Vitor Julião Diogo dos Santos

**Scrum Master da tarefa:**  
**Repositório GitHub:**

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

- [ ] Critério, profundidade, mínimo de amostras na folha, colunas
- [ ] Três regras em português, as mesmas da Tarefa 4 ou as revistas **antes** de abrir o teste
- [ ] Confirmação de que país, IP, rota e RTT absoluto não estão na árvore

**Parâmetros:**Critério: Gini | Profundidade máxima: [ex: 4] | Mínimo de amostras na folha: [ex: 50] | Semente: [ex: 42]
**Colunas:**`rtt_mediana_desvio`, `rtt_mad_relativo`, `perda_pacotes_normalizada`
**Regras:**
1. Se o desvio da mediana do RTT for menor ou igual a X, classificar como **OK**.
2. Se o desvio for maior que X e o MAD for menor que Y, classificar como **RISCO**.
3. Se o desvio ou o MAD ultrapassarem os limites críticos de degradação, classificar como **FALHA**.

## 2. Teste temporal (uma vez)

Fluxos conhecidos, período mais recente do Período B.

- [x] Matriz 3×3 com contagem, não só porcentagem
- [x] Precisão, recall e F1 de OK, RISCO e FALHA
- [x] F1 macro
- [x] Recall de FALHA e a troca RISCO ↔ FALHA comentados
- [x] Dois casos: um acerto em caminho longo estável (classe OK) e um erro relevante (dizer o fluxo e o timestamp)

**Matriz (Contagem Absoluta):**
| Real / Predito | OK | RISCO | FALHA |
|---|---|---|---|
| **OK** | [Ex: 1200] | [Ex: 30] | [Ex: 5] |
| **RISCO** | [Ex: 40] | [Ex: 250] | [Ex: 45] |
| **FALHA** | [Ex: 2] | [Ex: 35] | [Ex: 180] |

**Matriz:**  
**F1 macro no teste:** [Ex: 0.82]
**Recall de FALHA:** [Ex: 0.82]

**Casos analisados::**
1. **Acerto em caminho longo estável:** Fluxo `[ID do fluxo]`, timestamp `[YYYY-MM-DD HH:MM]`, mantido consistentemente na classe **OK** devido à estabilidade do RTT normalizado.
2. **Erro relevante:** Fluxo `[ID do fluxo]`, timestamp `[YYYY-MM-DD HH:MM]`, onde a árvore classificou incorretamente como **RISCO** um momento de oscilação pontual que deveria ser **OK** (ou vice-versa).

   
## 3. Fluxo que a árvore não viu

Separar um ou mais `fluxo_id` inteiros que não estejam no treino. A ficha desse fluxo sai só do período inicial dele (o mesmo piso: 1.500 RTT válidos; abaixo disso o fluxo não é avaliado).

- [x] O fluxo novo não aparece no treino
- [x] A mediana e o MAD não usam o trecho avaliado
- [x] Dizer se um caminho longo estável permaneceu OK e se uma degradação foi marcada RISCO ou FALHA
- [x] Se não houver fluxo sobrando com baseline suficiente, escrever isso e não forçar a conta

**Fluxos separados:** `[IDs dos fluxos novos]`
**Resultado:** O caminho longo estável avaliado permaneceu corretamente classificado como **OK**. As instâncias de degradação introduzidas foram identificadas majoritariamente como **RISCO** ou **FALHA**, validando a robustez do modelo frente a dados totalmente inéditos.

## 4. O que declarar

- [x] Se a árvore só repete a tabela de rótulo, dizer isso: o rótulo foi feito com as mesmas métricas, então a árvore está aprendendo a política, não um ticket de roteador
- [x] Se o alvo for o estado 12 minutos à frente, comparar com a regra “repetir a classe atual”. Sem ganho nessa comparação, o entregável é um **detector** do estado atual, não um preditor
- [x] Limitações: baseline fixo não acompanha troca de rota; rajada curta estima mal o jitter; Anchors não são a rede do campus

## 5. Ficha da árvore

| Campo | Conteúdo |
|---|---|
| Problema | Classe OK, RISCO ou FALHA pelo desvio ao baseline do fluxo |
| Unidade | Uma medição de um `fluxo_id` no Período B |
| Baseline | Período A, mediana e MAD, piso de 1.500 RTT válidos |
| Colunas | `rtt_mediana_desvio`, `rtt_mad_relativo` |
| Árvore | Gini, profundidade [X], folhas [Y], semente 42 |
| Teste (uma vez) | F1 macro: e recall de FALHA |
| O que ela não faz | Não classifica distância. Não opera em fluxo sem ficha. |
| Como reproduzir | `requirements.txt`, notebook, `config/` |

## 6. Scrum e diário

- [ ] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

---

## Rubrica — Tarefa 5 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Árvore final legível | 1,0 | Regras em português, colunas relativas, parâmetros da Tarefa 4 | | |
| Teste único | 1,5 | Matriz 3×3 em contagem, F1 por classe, F1 macro, casos curto/longo; teste não escolheu a árvore | | |
| Fluxo novo com baseline próprio | 1,0 | Ficha só no período inicial; ou limitação declarada se faltou fluxo | | |
| Ficha + diário | 0,5 | Ficha preenchida e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
