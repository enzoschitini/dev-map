# Componentes HTML das páginas de pattern

Tudo o que as páginas usam já existe no design system (`assets/css/design-system.css` e `assets/js/ds.js`). Não escreva CSS nem JS próprio, e não adicione bibliotecas.

## Sumário

- Esqueleto da página
- Bloco de código simples
- Bloco de código com abas
- Realce de sintaxe e escape
- Callouts
- Tabelas
- Links

## Esqueleto da página

As páginas ficam em `pages/clean-code/<grupo>/<pattern>/`, quatro níveis abaixo da raiz. Por isso todo caminho de asset começa com `../../../../`.

Troque `<PATTERN>` (o rótulo, como `Facade`), `<GRUPO>` (a pasta, como `estruturais`), `<SLUG>` (a pasta do pattern, como `facade`) e `<PAGINA>` (`explicacao` ou `uso`). O resto é a moldura que o `shell.js` preenche; não mexa nela.

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explicação | <PATTERN> · DevMap</title>
<script>
  /* Define o tema antes de pintar a página, para não piscar. Mantenha em toda página. */
  (function () {
    var t = null;
    try { t = localStorage.getItem('devmap-theme'); } catch (e) {}
    if (!t) t = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = t;
  })();
</script>
<link rel="stylesheet" href="../../../../assets/css/design-system.css">
</head>
<body data-root="../../../../" data-tab="clean-code" data-page="<GRUPO>/<SLUG>/<PAGINA>">
<a class="skip" href="#main">Ir para o conteúdo</a>

<header class="header" id="header" data-shell="header"></header>

<div class="shell">
  <aside class="side-wrap" id="side" aria-label="Páginas de Clean Code" data-shell="side"></aside>
  <div class="main">
    <div class="main-row">
      <main class="article" id="main">
        <header>
          <div class="eyebrow">Clean Code / Design Pattern / <PATTERN></div>
          <h1 class="page-title" tabindex="-1">Explicação</h1>
          <p class="lead">…</p>
        </header>

        <div class="prose">
          <!-- conteúdo -->
        </div>

        <nav class="pager" data-shell="pager" aria-label="Páginas vizinhas"></nav>
      </main>
      <aside class="toc" id="toc" data-toc aria-label="Nesta página"></aside>
    </div>
    <footer class="site-foot" data-shell="footer"></footer>
  </div>
</div>

<div class="scrim"></div>
<dialog class="search" id="search" data-shell="search" aria-label="Buscar no DevMap"></dialog>

<script src="../../../../assets/js/site.js"></script>
<script src="../../../../assets/js/shell.js"></script>
<script src="../../../../assets/js/ds.js"></script>
</body>
</html>
```

Na página Uso, o `<title>` é `Uso | <PATTERN> · DevMap` e o `h1` é `Uso`.

O índice "Nesta página" é montado a partir de todos os `h2` e `h3` dentro de `.prose`. Por isso:

- todo `h2`/`h3` precisa de `id`;
- não use `h3` para "Situação", "Sem o pattern" e afins dentro dos exemplos da página Uso, ou o índice vira uma lista de 30 itens. Use `<p><strong>Situação.</strong> …`.

## Bloco de código simples

```html
<div class="code">
  <div class="code-head"><span class="code-title">sem o pattern — o checkout conhece as duas SDKs</span><button class="copy" type="button"></button></div>
  <div class="code-body">
    <pre><code>…</code></pre>
  </div>
</div>
```

O botão `.copy` fica vazio: o `ds.js` preenche o ícone e o comportamento.

O código começa na mesma linha do `<pre><code>` e termina colado no `</code></pre>`. Qualquer quebra de linha ou indentação ali vira uma linha em branco no bloco.

## Bloco de código com abas

Use na Implementação da Explicação (Python e TypeScript). O número de `.code-tab` tem que ser igual ao número de `<pre>`, na mesma ordem.

```html
<div class="code" data-tabs>
  <div class="code-head">
    <div class="code-tabs" role="tablist">
      <button class="code-tab" type="button">Python</button>
      <button class="code-tab" type="button">TypeScript</button>
    </div>
    <button class="copy" type="button"></button>
  </div>
  <div class="code-body">
    <pre><code>… python …</code></pre>
    <pre><code>… typescript …</code></pre>
  </div>
</div>
```

## Realce de sintaxe e escape

O realce é feito à mão, com `<span>`:

| Classe | Use para | Exemplos |
|---|---|---|
| `t-k` | palavras-chave e constantes da linguagem | `class`, `def`, `return`, `if`, `import`, `async`, `await`, `const`, `new`, `True`, `None`, `null` |
| `t-f` | nomes de classe, função e método (na definição e na chamada), tipos, decorators | `Checkout`, `.cobrar`, `str`, `Promise`, `@dataclass` |
| `t-s` | strings, inclusive f-strings, template strings e docstrings inteiras | `"brl"`, `` `Pedido ${id}` `` |
| `t-n` | números | `100`, `201` |
| `t-c` | comentários | `# centavos`, `// checkout.tsx` |

Variáveis, atributos e operadores ficam sem `span`. Siga o que as páginas do Adapter fazem; consistência importa mais que precisão.

**Escape dentro do `<pre>`.** O HTML interpreta o código, então:

| Caractere | Escreva | Onde aparece |
|---|---|---|
| `<` | `&lt;` | genéricos (`Promise&lt;void&gt;`), comparações |
| `>` | `&gt;` | `-&gt;` do Python, `=&gt;` do TS, genéricos |
| `&` | `&amp;` | `&&`, query strings (`?a=1&amp;b=2`) |

Um `<` sem escape faz o navegador abrir uma tag inventada e engolir o resto do bloco. O `check_pages.py` acusa isso como tag desbalanceada.

## Callouts

```html
<div class="callout" data-kind="tip"><p>…</p></div>
```

| `data-kind` | Quando usar |
|---|---|
| `tip` | Uma consequência boa ou um atalho: "o teste agora é uma classe de cinco linhas", "o Node já traz `util.promisify`" |
| `note` | Contexto neutro: "as chamadas de SDK estão simplificadas", "na dúvida, comece sem" |
| `warn` | Uma armadilha em que é fácil cair usando o pattern do jeito certo |
| `danger` | O sinal de que o pattern está sendo usado do jeito errado |

No máximo um callout por exemplo na página Uso. Callout em excesso deixa de chamar atenção.

## Tabelas

Sempre dentro de `.table-wrap`, para rolar no celular sem quebrar a página:

```html
<div class="table-wrap">
  <table>
    <thead><tr><th>Papel</th><th>Quem é</th><th>No exemplo</th></tr></thead>
    <tbody>
      <tr><td>Alvo</td><td>A interface que o seu código espera</td><td><code>Notificador</code></td></tr>
    </tbody>
  </table>
</div>
```

## Links

| De → para | `href` |
|---|---|
| Seção da mesma página | `#quando-usar` |
| Explicação → exemplo da Uso | `uso.html#varios-provedores` |
| Uso → seção da Explicação | `explicacao.html#parecidos` |
| Outro pattern do mesmo grupo | `../facade/explicacao.html` |
| Pattern de outro grupo | `../../comportamentais/strategy/explicacao.html` |

Só crie link para uma página que exista. O `check_pages.py` confere arquivos e âncoras.
