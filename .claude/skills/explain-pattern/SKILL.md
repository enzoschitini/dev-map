---
name: explain-pattern
description: Gera as duas páginas de um design pattern no DevMap — "Explicação" e "Uso" — no formato das páginas do Adapter, e registra as duas no mapa do site (assets/js/site.js). Recebe o nome do pattern e o grupo (criacionais, estruturais, comportamentais). Use sempre que o usuário pedir para documentar, criar páginas, escrever a explicação ou os exemplos de uso de um design pattern no site (Facade, Strategy, Observer, Factory Method, Decorator…), mesmo que ele não diga "skill" nem "explain-pattern".
argument-hint: <pattern> <grupo>
---

# explain-pattern

Cria `pages/clean-code/<grupo>/<pattern>/explicacao.html` e `uso.html` e registra as duas em `assets/js/site.js`.

As páginas do Adapter são o **padrão de referência**:

- `pages/clean-code/estruturais/adapter/explicacao.html`
- `pages/clean-code/estruturais/adapter/uso.html`

Leia as duas antes de escrever qualquer coisa. Reproduza a forma (estrutura, tom, densidade, componentes), não o texto. Os componentes HTML, o esqueleto da página e as regras de realce de sintaxe estão em `references/html.md`.

## Entrada

- **Pattern**: o nome como é conhecido (`Facade`, `Factory Method`, `Chain of Responsibility`). O rótulo no site mantém o nome original em inglês, como no catálogo GoF.
- **Grupo**: aceite em português ou inglês e normalize para a pasta:

  | Recebido | Pasta | Rótulo no menu |
  |---|---|---|
  | criacional, criacionais, creational | `criacionais` | Criacionais |
  | estrutural, estruturais, structural | `estruturais` | Estruturais |
  | comportamental, comportamentais, behavioral | `comportamentais` | Comportamentais |

- **Pasta do pattern**: minúsculas, sem acento, palavras separadas por hífen (`factory-method`, `chain-of-responsibility`).

Se o grupo não vier, use a classificação GoF e diga qual usou. Se o grupo vier diferente da classificação GoF (por exemplo, "Strategy, estrutural"), avise qual é a classificação usual e pergunte qual usar: é uma decisão do usuário, e corrigir em silêncio esconde a discordância. Se o pattern não for do catálogo GoF (Repository, MVC, Unit of Work), pergunte em que grupo e pasta ele deve morar.

## Passo a passo

### 1. Ver o estado atual

- Leia `assets/js/site.js`.
- Verifique se `pages/clean-code/<grupo>/<pattern>/` já existe. Se alguma das duas páginas já existir, mostre o que tem lá e pergunte antes de sobrescrever.
- Veja quais outros patterns já têm página. Eles podem virar links na seção "Parecidos".

### 2. Planejar antes de escrever HTML

É aqui que se decide a clareza. Escrever direto no HTML produz exemplos parecidos entre si e uma página "Quando usar" genérica.

1. **Exemplo condutor da Explicação.** Escolha uma situação de domínio concreta (pedido, pagamento, notificação, relatório, cadastro) em que a falta do pattern dói de verdade. A mesma situação atravessa "O problema", "A solução" e "Implementação", para o leitor acompanhar um caso só.
2. **Forças para a página Uso.** Liste de 10 a 15 situações candidatas e agrupe-as pelo **motivo** (a força) que faz o pattern ser a resposta certa. Duas situações com o mesmo raciocínio são uma força só: fica a mais clara, a outra vai para "O que ficou de fora".
3. **O número.** No máximo 10, um exemplo por força. O número tem que ser honesto: se o pattern tem quatro forças distintas, a página tem quatro exemplos. Encher com variações da mesma ideia é exatamente o que essa página existe para evitar.
4. **Ligações.** Dê um `id` a cada exemplo e decida em qual linha da tabela "Quando usar" ele entra. Todo exemplo da página Uso precisa ser citado pelo menos uma vez nessa tabela.

### 3. Escrever `explicacao.html`

Estrutura na ordem abaixo. Os `id`s são fixos, porque as páginas se ligam por eles.

**Cabeçalho**
- `.eyebrow`: `Clean Code / Design Pattern / <Pattern>`
- `h1`: `Explicação`
- `.lead`: uma frase que diz que problema o pattern resolve, em palavras simples. Não use a definição do GoF: ela explica o pattern para quem já o conhece.

**`#o-problema` — O problema**
- A situação do exemplo condutor em 1 ou 2 parágrafos.
- O código "preguiçoso", sem o pattern. Título do bloco: `antes — <o defeito em poucas palavras>`.
- Um parágrafo com 2 ou 3 consequências concretas do que quebra. Cite o princípio SOLID violado quando ele de fato estiver em jogo.

**`#a-solucao` — A solução**
- A ideia em uma ou duas frases.
- Tabela de papéis: `Papel | Quem é | No exemplo`.
- Um parágrafo com o ponto central ("O ponto é…"): a decisão de design que faz o pattern funcionar.

**`#implementacao` — Implementação**
- Bloco com abas, **Python** e **TypeScript**, implementando o exemplo condutor.
- Comentários numerados marcando os papéis (`# 1. o alvo: …`, `# 2. o adaptador: …`).
- Termine com um callout `tip` sobre a consequência prática mais útil (quase sempre: como fica o teste).

**`#quando-usar` — Quando usar**
- Um parágrafo com a regra em uma frase: as condições que precisam acontecer **ao mesmo tempo** para o pattern valer.
- Tabela `Situação | Como reconhecer no código | Exemplo`. A coluna do meio é o que dá noção ao leitor: sinais que ele consegue encontrar no próprio código (`if tipo == …` repetido, `import` de SDK no domínio, um construtor com 9 parâmetros), escritos com `<code>`. A coluna Exemplo leva para `uso.html#<id>`; use `—` quando a linha não tiver exemplo.
- Callout `tip` com o que os sinais têm em comum.
- `h3#teste-rapido` "Um teste rápido": lista numerada com 3 a 5 perguntas de sim ou não, em ordem, onde a primeira resposta que manda parar decide.

**`#quando-nao-usar` — Quando não usar**
- Um parágrafo com o **custo** concreto do pattern (classes a mais, indireção, leitura mais difícil). É contra esse custo que o leitor decide.
- Tabela `Situação | Por que não | Faça isto`. Toda linha diz a alternativa: código mais simples, outro pattern, mudar na origem.
- `h3#sinais-de-abuso` "Sinais de que o <pattern> saiu do lugar": lista em que cada item começa com uma frase curta em negrito e depois explica.
- Callout `danger` com o sinal de abuso mais comum.
- Callout `note` com a postura padrão na dúvida (normalmente: comece sem e extraia quando o segundo caso aparecer, se isso for verdade para esse pattern).

**`#parecidos` — Parecidos**
- Tabela `Padrão | Diferença` com 3 a 5 vizinhos. Cada diferença contrasta o vizinho com **este** pattern, em vez de definir o vizinho isoladamente.
- Se o vizinho já tem página no site, o nome vira link. Não edite a página do vizinho sem pedir.
- Feche com `Regra prática:` uma frase que separa este pattern do vizinho mais confundido.

### 4. Escrever `uso.html`

**Cabeçalho**
- `.eyebrow` igual ao da Explicação; `h1`: `Uso`.
- `.lead`: `<N por extenso> situações em que o <Pattern> resolve o problema. Cada uma traz o código sem o pattern, o código com ele e <o que o pattern faz em cada caso>.`

**`#como-escolhi` — "Por que <N por extenso>"** (por exemplo, "Por que sete")
- Um parágrafo com o critério: cada exemplo traz um motivo diferente; quando dois casos se resolvem com o mesmo raciocínio, fica um só. Link para `#fora-da-lista`.
- Tabela-resumo `# | Situação | O que o <pattern> <verbo>`, com o nome de cada situação ligado ao seu `#id`. O verbo depende do pattern: o Adapter *traduz*, o Strategy *isola*, o Observer *desacopla*.
- Callout `note` avisando que as chamadas de SDK estão simplificadas, mas só se houver SDKs reais na página.

**Um `h2` por exemplo**, precedido de um comentário separador (`<!-- 3 ───── -->`). O título é `N. <a situação>`: nomeie o problema, não a solução ("Vários provedores para a mesma operação", e não "Usando Adapter para provedores"). Dentro dele, nesta ordem:

1. `<p><strong>Situação.</strong> …` — cenário concreto: quem, o quê e a restrição real (por que não dá para simplesmente mudar).
2. Código com o título `sem o pattern — <o defeito em poucas palavras>`.
3. `<p><strong>O que dói.</strong> …` — 2 ou 3 consequências concretas.
4. Código com o título `com o pattern — <a ideia em poucas palavras>`.
5. `<p><strong>Por que funciona.</strong> …` — o que o pattern absorve **neste** caso. Pode trocar o rótulo por um que nomeie o mecanismo do pattern (no Adapter é "O que o adaptador absorve"), desde que seja o mesmo em todos os exemplos.
6. Opcional: mais um parágrafo e no máximo um callout.

**`#fora-da-lista` — O que ficou de fora**
- Tabela `Caso | Já coberto por` com os candidatos descartados no passo 2, cada um apontando o exemplo que já cobre o raciocínio dele.
- Um parágrafo sobre um caso que **parece** este pattern mas não é, com link para `explicacao.html#parecidos`.

### 5. Registrar no `site.js`

A árvore fica dentro da aba `clean-code`, no grupo `Design Pattern`:

```js
{
  group: 'Design Pattern',
  pages: [
    {
      folder: 'estruturais',          // crie se ainda não existir
      label: 'Estruturais',
      pages: [
        {
          folder: 'adapter',
          label: 'Adapter',
          pages: [
            { id: 'explicacao', label: 'Explicação', summary: '<uma linha: o problema que ele resolve>' },
            { id: 'uso',        label: 'Uso',        summary: '<N por extenso> situações reais, com o código antes e depois do <Pattern>.' }
          ]
        }
      ]
    }
  ]
}
```

- Pastas de grupo na ordem Criacionais, Estruturais, Comportamentais.
- Pastas de pattern em ordem alfabética pelo rótulo dentro do grupo.
- Não use `empty`: as páginas nascem com conteúdo.

### 6. Verificar

Rode, a partir da raiz do repositório:

```
python .claude/skills/explain-pattern/scripts/check_pages.py pages/clean-code/<grupo>/<pattern>
```

O script confere tags balanceadas, `id` nos `h2`/`h3`, abas casando com os `<pre>`, `data-root`/`data-tab`/`data-page`, links entre as páginas e o registro no `site.js`. Corrija tudo o que ele apontar e rode de novo.

Depois, releia as duas páginas como alguém que nunca ouviu falar do pattern. Essa pessoa conseguiria dizer, olhando o próprio código, se deve ou não usá-lo? Se não, o problema quase sempre está na coluna "Como reconhecer no código" ou nas alternativas de "Faça isto".

### 7. Relatar

Mensagem curta: os arquivos criados, o número de exemplos e o critério, uma tabela com os exemplos (situação e o que o pattern faz em cada uma), o que ficou de fora e o resultado da verificação. Não faça commit sem pedido.

## Critérios de clareza

Estes critérios são o motivo de a skill existir. Cada um corrige um defeito comum em páginas de design pattern.

- **O código "sem o pattern" é realista.** É o código que uma pessoa competente escreveria com pressa, não um espantalho. O defeito aparece no próprio código, e um comentário pode apontá-lo (`# e nos outros 40 except?`). Se o "antes" é obviamente ruim, o leitor não aprende a reconhecer o problema no código dele.
- **O código "com o pattern" é mínimo** e usa os mesmos nomes de domínio do "antes", para a diferença ser legível de relance.
- **Cada exemplo ensina algo que os outros não ensinam.** Teste: se o parágrafo "Por que funciona" de um exemplo pudesse ser colado em outro, os dois são a mesma força. Funda os dois ou corte um.
- **APIs reais com o formato real.** Prefira o que o leitor conhece: biblioteca padrão, APIs do navegador, SDKs conhecidas. Se não tiver certeza da assinatura exata, simplifique e diga que simplificou. Nunca invente uma API apresentando-a como real. Para código interno, use módulos claramente fictícios (`legado`, `crm`).
- **Linguagem.** Python por padrão; TypeScript quando a situação é de front-end ou Node. A Implementação da Explicação mostra as duas, em abas. Nomes de domínio em português (`Pedido`, `Checkout`, `Cotacao`); palavras-chave e nomes de API como são.
- **Escrita.** Português do Brasil, falando com "você". Frases curtas, uma ideia por parágrafo, sem enchimento ("é importante notar que", "vale ressaltar") e sem emoji. Explique o porquê em vez de dar ordens. Negrito só na palavra que carrega a frase.
- **Defina pelo problema, não pela definição.** O leitor entende o pattern quando vê a dor que ele resolve, não quando lê "converte a interface de uma classe em outra interface esperada pelos clientes".
- **"Quando não usar" vale tanto quanto "Quando usar".** Todo pattern tem um custo, e a página precisa dizer qual é e o que fazer no lugar dele.
