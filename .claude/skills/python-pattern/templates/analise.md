# Análise — <nome do fluxo ou da pasta>

> Escopo: `<arquivos ou pasta>` · Ponto de entrada: `<arquivo:função>` · Data: <AAAA-MM-DD>

## 1. Escopo

- **Dentro** (pode mudar): <arquivos>
- **Fora, só lido** (para entender o contrato): <chamadores, dependências do projeto>
- **Testes existentes**: <quais e o resultado ao rodar> | não há

## 2. O fluxo

<Uma ou duas frases: o que o fluxo faz para quem o usa.>

| # | Etapa | Onde | Entra → sai | Efeitos colaterais |
|---|---|---|---|---|
| 1 | <verbo + objeto: "Validar o pedido"> | `<arquivo:linhas>` | `<entrada>` → `<saída>` | <banco, rede, e-mail, relógio, env, print… ou —> |

<!-- Se o fluxo tiver desvios (erros, ramos por tipo), acrescente um diagrama mermaid. -->

## 3. Elementos

| Elemento | Tipo | Responsabilidades | Quem pede mudança (ator) |
|---|---|---|---|
| `<Nome>` | classe / função / módulo | <uma por linha, se forem várias> | <comercial, dados, financeiro, marketing, infraestrutura…> |

## 4. Dependências e pontos de variação

| O quê | Onde | Natureza |
|---|---|---|
| <SQLite, SDK, HTTP, SMTP, relógio, `if` por tipo, flag de modo…> | `<arquivo:linha>` | <I/O · terceiro · não determinístico · variação por tipo/status/configuração> |

## 5. Contrato a preservar

- **API pública**: <assinaturas chamadas de fora do escopo, e quem chama>
- **Retornos**: <formato exato>
- **Exceções**: <tipo e mensagem de que alguém depende>
- **Efeitos e ordem**: <o que acontece, em que ordem; o que acontece quando uma etapa falha>
- **Persistência e formatos**: <tabelas, colunas, payloads, arquivos>

## 6. Diagnóstico

Cada linha nasce de um sinal de `references/sinais.md` encontrado no código.

| # | Sinal | Evidência | O que dói | Hipótese |
|---|---|---|---|---|
| D1 | <texto da coluna "Como reconhecer"> | `<arquivo:linhas>` — `<trecho curto>` | <a consequência concreta: o que fica difícil de mudar ou testar> | <princípio ou pattern> |

## 7. Validação das hipóteses

### Descartadas de cara

Hipóteses que pararam na pergunta 1 do Teste rápido. Uma linha cada, sem seção própria.

| Hipótese | Sinal | Pergunta 1 e resposta |
|---|---|---|
| <pattern> | <o que lembrou o pattern> | <"Existe mais de um jeito de verdade?" — não, há só um> |

### D1 — <pattern ou princípio>

- **Teste rápido** (`references/<caminho>/explicacao.md#teste-rapido`). Para um princípio, use a pergunta central de "A ideia" e as linhas de "Quando não aplicar":
  1. <pergunta> — <resposta e por quê>
  2. …
- **Quando não usar**: <nenhuma linha se aplica> | <"linha" se aplica porque…>
- **Parecidos**: <só se houve dúvida entre dois patterns: qual ficou e pela Regra prática>
- **Exemplo mais parecido**: `references/<caminho>/uso.md#<id>`
- **Veredito**: aplicar | não aplicar | adiar — <motivo; se adiar, o gatilho que faria valer>

## 8. Bugs e comportamentos estranhos

Registrados aqui, e **não** corrigidos durante a refatoração (a não ser que o plano tenha um passo explícito para isso).

| Onde | O que acontece | Impacto |
|---|---|---|

## 9. O que fica como está

| Elemento | Por que não mexer |
|---|---|
