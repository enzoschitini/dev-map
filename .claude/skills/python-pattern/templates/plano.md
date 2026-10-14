# Plano de refatoração — <nome do fluxo ou da pasta>

> Análise: [analise.md](analise.md) · Status: aguardando aprovação | em execução | concluído

## Objetivo

<Duas ou três frases: o que fica mais fácil de mudar ou de testar depois, nos termos do domínio. Ex.: "Um gateway novo de pagamento entra com uma classe nova, sem tocar no cálculo do pedido; o cálculo é testado sem rede nem banco.">

## Estrutura final

```text
<árvore de módulos depois da refatoração>
```

**Ponto de montagem**: `<arquivo:função>` cria <as implementações concretas> e as entrega a <quem>. É o único lugar que conhece as classes concretas de infraestrutura.

**API pública preservada**: <como cada chamada do contrato continua funcionando>

## Passos

Cada passo deixa os testes verdes. A ordem segue o retorno: rede de segurança → Single Responsibility → Dependency Inversion → patterns → ajustes de O/L/I.

### [ ] Passo 0 — Rede de segurança

- **Por quê**: <o contrato da análise, seção 5, não está coberto por testes>
- **O que muda**: cria `<tests/...>` com testes de caracterização para <itens do contrato>. Banco, rede, SMTP e relógio trocados por falsos na fronteira.
- **Verificação**: os testes passam no código **original**.

### [ ] Passo 1 — <o problema que o passo resolve, não o nome do pattern>

- **Princípio / pattern**: <nome> — `references/<caminho>.md`
- **Justificativa**: D<n> da análise
- **O que muda**: <arquivos, classes e funções que nascem ou mudam>
- **O que não muda**: <o que fica igual de propósito>
- **Verificação**: <testes; o que conferir à mão>

## Considerados e descartados

| Princípio / pattern | Sinal visto | Por que não agora | Gatilho para rever |
|---|---|---|---|
| <nome> | D<n> | <a linha de "Quando não usar" ou a resposta do Teste rápido que pesou> | <"quando o segundo X aparecer"> |

## Riscos

- <o que pode quebrar e como o plano se protege>

## Registro de execução

| Passo | Nota |
|---|---|
| <n> | <feito; ou o desvio do plano e o porquê> |

## Resultado

<!-- Preenchido na Fase 4. -->

### Antes e depois

| Diagnóstico | Antes | Depois | Onde |
|---|---|---|---|
| D<n> | <a dor> | <o que mudou> | `<arquivos>` |

### Testes

<comando, número de testes e resultado>

### Mudanças de comportamento

<nenhuma | lista, cada uma ligada ao passo que a previu>

### Para depois

<o que foi adiado, com o gatilho de cada um>
