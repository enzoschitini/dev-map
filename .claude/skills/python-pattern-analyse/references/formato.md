# Formato do `relatorio.json`

O `scripts/gerar_relatorio.py` lê este arquivo, valida e gera o `relatorio.html`. O exemplo completo está em `exemplo/relatorio.json` (análise de `exemplo/loja/`). Leia-o antes de escrever o seu.

## Sumário

- Texto dos campos
- Estrutura geral
- Campos, seção por seção
- O que o validador exige

## Texto dos campos

Todo campo de texto aceita um Markdown mínimo:

| Escreva | Vira |
|---|---|
| `` `GerenciadorDePedidos` `` | código inline |
| `**palavra**` | negrito |
| `*palavra*` | itálico |
| `[texto](https://…)` | link |
| `[[A2]]`, `[[R1]]`, `[[B3]]` | atalho para o achado, a recomendação ou o bug, colorido pela severidade. O validador recusa um id que não existe. |

Campos marcados como **bloco** aceitam também parágrafos (separados por linha em branco) e listas (linhas começando com `- `). Também podem receber uma lista JSON de strings, que vira uma lista com marcadores.

## Estrutura geral

```json
{
  "titulo": "Fluxo de checkout da loja",
  "projeto": "loja",
  "data": "2026-10-14",
  "autor": "opcional",
  "escopo": { },
  "resumo": { },
  "fluxo": { },
  "elementos": [ ],
  "contrato": [ ],
  "achados": [ ],
  "recomendacoes": [ ],
  "descartados": [ ],
  "arquitetura": { },
  "roteiro": [ ],
  "riscos": [ ],
  "bugs": [ ],
  "fica_como_esta": [ ]
}
```

Obrigatórios: `titulo`, `data`, `escopo`, `resumo`, `fluxo`, `achados`, `recomendacoes`, `roteiro`. Os outros são opcionais para o script, mas um relatório sênior quase sempre tem `elementos`, `contrato`, `descartados`, `arquitetura`, `riscos` e `fica_como_esta`. O script avisa quando faltam.

## Campos, seção por seção

### `escopo`

| Campo | Tipo | Conteúdo |
|---|---|---|
| `descricao` | texto | Uma ou duas frases sobre o que o fluxo faz para quem o usa. Vira o subtítulo do relatório. |
| `ponto_de_entrada` | texto ou lista | `arquivo.py:Classe.metodo` ou `arquivo.py:funcao`. Com mais de um chamador (uma CLI e um job, por exemplo), use uma lista. |
| `arquivos` | lista | `{"caminho": "loja/pedidos.py", "papel": "…"}`. O caminho é relativo à raiz do projeto, e o script conta as linhas. Deixe de fora os `__init__.py` vazios. |
| `fora_do_escopo` | lista de textos | O que foi lido só para entender o contrato |
| `testes` | bloco | Os testes que existem e o resultado ao rodar, ou "Não há testes." |

### `resumo`

Escreva por último, depois de todo o resto.

| Campo | Tipo | Conteúdo |
|---|---|---|
| `veredito` | texto | Uma frase com a decisão: "Refatoração recomendada antes do próximo gateway". |
| `prioridade` | `alta` \| `media` \| `baixa` | Define a cor do veredito |
| `texto` | bloco | Um ou dois parágrafos para quem só vai ler o topo: o estado do código, o risco de deixar como está e a proposta em linhas gerais. |
| `destaques` | lista de textos | De três a cinco frases, cada uma com uma conclusão. Quando houver um achado, recomendação ou bug por trás, cite-o com `[[A1]]`, `[[R1]]` ou `[[B1]]`. |
| `esforco` | texto | Estimativa total: "3 a 4 dias" |
| `risco` | texto | O risco da refatoração em si e o que o reduz |

### `fluxo`

| Campo | Tipo | Conteúdo |
|---|---|---|
| `descricao` | bloco | Opcional. Contexto do fluxo. |
| `etapas` | lista | Uma por etapa, na ordem em que acontecem |

Cada etapa:

```json
{
  "id": "E4",
  "nome": "Cobrar no gateway",
  "onde": "loja/pedidos.py:60-85",
  "descricao": "Escolhe o gateway pelo texto do pedido e faz a cobrança por HTTP.",
  "entrada": "`total`, `cartao`, `gateway`",
  "saida": "`transacao`",
  "efeitos": ["rede", "env"],
  "achados": ["A2"]
}
```

Valores de `efeitos`: `banco`, `rede`, `email`, `disco`, `relogio`, `aleatorio`, `env`, `stdout`, `fila`, `cache`.

### `elementos`

```json
{
  "nome": "GerenciadorDePedidos",
  "tipo": "classe",
  "onde": "loja/pedidos.py:15",
  "responsabilidades": [
    {"descricao": "Calcular desconto e frete", "ator": "Comercial"},
    {"descricao": "Cobrar no gateway", "ator": "Financeiro"}
  ]
}
```

O relatório marca em amarelo todo elemento com mais de um `ator`.

### `contrato`

Lista de textos: o que a refatoração não pode mudar (assinaturas públicas, retornos, exceções e mensagens, ordem dos efeitos, esquema do banco, formatos).

### `achados`

```json
{
  "id": "A2",
  "titulo": "Os gateways de pagamento moram dentro da regra do pedido",
  "severidade": "alta",
  "categoria": "acoplamento",
  "principios": ["dependency-inversion", "open-closed"],
  "sinal": "Dois fornecedores para a mesma operação: `if gateway == \"pagfacil\"` … `elif`",
  "evidencias": [
    {"arquivo": "loja/pedidos.py", "linhas": [61, 85], "destaque": [62, 73, [80, 82]], "nota": "opcional"}
  ],
  "impacto": "bloco: a consequência concreta",
  "recomendacoes": ["R3"]
}
```

- `id`: `A` + número.
- `severidade`: `alta`, `media` ou `baixa`. Os critérios estão no SKILL.md.
- `principios`: slugs SOLID (`single-responsibility`, `open-closed`, `liskov-substitution`, `interface-segregation`, `dependency-inversion`; também aceita `srp`, `ocp`, `lsp`, `isp`, `dip`).
- `sinal`: o texto da coluna "Como reconhecer" de `sinais.md` que você encontrou, adaptado ao código.
- `evidencias`: o script lê as linhas do arquivo real, numera e destaca. `linhas` é `[inicio, fim]`, com as duas pontas incluídas. `destaque` aceita números e pares `[a, b]`. Para mostrar algo que não é um trecho de arquivo, use `{"titulo": "…", "codigo": "…"}`.
- Prefira trechos curtos (até 25 linhas) e várias evidências a um bloco de cem linhas.

### `recomendacoes`

```json
{
  "id": "R3",
  "titulo": "Um adaptador por gateway, atrás de uma interface do pedido",
  "pattern": "adapter",
  "achados": ["A2"],
  "prioridade": 3,
  "impacto": "alto",
  "esforco": "M",
  "onde": ["`loja/pedidos.py:61-85` sai da regra", "novo `loja/pagamentos.py`"],
  "porque": "bloco",
  "teste_rapido": [
    {"pergunta": "Já existe algo pronto que resolve?", "resposta": "Sim: as APIs da PagFácil e da PayMundi.", "ok": true}
  ],
  "papeis": [{"papel": "Alvo", "no_codigo": "`Gateway` (Protocol) com `cobrar(valor, cartao) -> str`"}],
  "codigo_proposto": {"titulo": "proposta — loja/pagamentos.py", "codigo": "…"},
  "quando_nao_usar": "bloco: as linhas de Quando não usar que você conferiu e por que não se aplicam",
  "custo": "bloco: o custo que o pattern traz para este código"
}
```

- `pattern`: o slug da pasta do pattern (`adapter`, `strategy`, `factory-method`, `chain-of-responsibility`…) ou de um princípio. O script busca o nome, o grupo e os links da documentação.
- `teste_rapido`: as perguntas da página do pattern, na ordem, com a resposta para **este** código. `ok: false` marca a pergunta que pediria para parar. Uma recomendação com `ok: false` precisa explicar no `porque` por que segue mesmo assim. Para um princípio, que não tem Teste rápido, use a pergunta central de "A ideia" e as linhas de "Quando não aplicar" como perguntas.
- `codigo_proposto.codigo`: o esboço do "depois", com os nomes reais do código. Mostre a forma, sem implementar tudo. Para código longo, use `"arquivo": "esbocos/r3.py"` (relativo à pasta do JSON) no lugar de `codigo`.
- `impacto`: `alto`, `medio` ou `baixo`. `esforco`: `P`, `M` ou `G`, pelo tempo e não pelo número de arquivos (os critérios estão no SKILL.md). Os dois posicionam a recomendação na matriz.
- `prioridade`: a ordem dos cartões no relatório.

### `descartados`

```json
{
  "pattern": "observer",
  "achados": ["A4"],
  "sinal": "Um fato (pedido pago) dispara um e-mail",
  "motivo": "Teste rápido, pergunta 1: só uma parte reage, e sempre a mesma. Injete o notificador e chame.",
  "gatilho": "Quando um segundo interessado aparecer (estoque, fiscal, analytics)"
}
```

### `arquitetura`

| Campo | Tipo | Conteúdo |
|---|---|---|
| `descricao` | bloco | Opcional |
| `antes` | texto | A árvore de módulos de hoje, com comentário curto por linha |
| `depois` | texto | A árvore proposta |
| `montagem` | bloco | Onde as implementações concretas são criadas e como a API pública continua funcionando |

### `roteiro`

```json
{
  "passo": 0,
  "titulo": "Rede de segurança",
  "recomendacoes": [],
  "bugs": [],
  "esforco": "M",
  "descricao": "bloco",
  "verificacao": "Os testes passam no código original."
}
```

Toda recomendação precisa aparecer em algum passo. Bugs só entram no roteiro num passo próprio, depois da refatoração e com "decidido à parte" no título, porque corrigir muda o contrato.

### `bugs`

```json
{
  "id": "B2",
  "severidade": "alta",
  "onde": "loja/pedidos.py:61-93",
  "descricao": "A cobrança acontece antes do INSERT…",
  "impacto": "Cobrança sem pedido; reprocessar cobra de novo."
}
```

- `id`: `B` + número, para citar como `[[B2]]` no resumo, nos riscos ou no roteiro.
- `severidade`: `alta`, `media` ou `baixa`, com os mesmos critérios dos achados.
- Diga na `descricao` se o bug foi confirmado num experimento ou só lido no código.

### `riscos`, `fica_como_esta`

```json
"riscos": [{"risco": "…", "mitigacao": "…"}],
"fica_como_esta": [{"elemento": "loja/util.py", "motivo": "…"}]
```

## O que o validador exige

O script não gera o HTML enquanto houver erro. Ele confere:

- os campos obrigatórios;
- arquivos e intervalos de linha de cada evidência, a partir de `--raiz`;
- ids únicos e referências válidas entre etapas, achados, recomendações, bugs, descartados e roteiro;
- todo `[[A1]]`, `[[R1]]` e `[[B1]]` escrito nos textos;
- o arquivo citado no `onde` de etapas, elementos e bugs (só aviso);
- que todo achado seja tratado por uma recomendação ou por um descartado;
- que toda recomendação cite pelo menos um achado, tenha `teste_rapido`, `quando_nao_usar`, `porque` e `onde`, e apareça no roteiro;
- valores válidos de severidade, impacto, esforço e princípios.

Pattern fora da documentação do DevMap gera aviso, não erro: o relatório mostra o nome e marca "fora do catálogo do DevMap".
