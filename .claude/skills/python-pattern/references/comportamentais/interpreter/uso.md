<!-- Gerado de pages/clean-code/comportamentais/interpreter/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Interpreter — Uso

*Clean Code / Design Pattern / Interpreter*

Três situações em que o Interpreter resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a gramática garante.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Interpreter. Quando dois casos se resolvem com o mesmo raciocínio — permissões por regra e feature flags com segmentação, por exemplo — só um fica. O Interpreter é um pattern estreito: seguindo essa regra, sobraram três motivos, e a página prefere ser curta a inventar um quarto. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a gramática garante |
|---|---|---|
| 1 | [Regra que não-programadores mudam, guardada no banco](#regra-configuravel) | Que a regra só pode ser o que a linguagem permite |
| 2 | [Filtro digitado pelo usuário em uma caixa de texto](#filtro-digitado) | Que o erro aparece ao digitar, com a posição |
| 3 | [A mesma regra no código, no banco e na tela](#varias-leituras) | Que as várias leituras da regra não divergem |

<a id="regra-configuravel"></a>
## 1. Regra que não-programadores mudam, guardada no banco

**Situação.** O marketing monta segmentos de clientes para campanhas de e-mail: "mais de cinco compras e moram em SP ou RJ". Os segmentos ficam em uma tabela, e a equipe quer criá-los e alterá-los em uma tela, sem pedir deploy. A Explicação montava a árvore em código; aqui ela já vem dos dados.

**sem o pattern — a regra é um texto Python avaliado com eval**

```python
# segmento.regra é um texto, salvo pela tela do marketing:
#   "cliente['compras'] > 5 and cliente['uf'] in ('SP', 'RJ')"
def pertence(cliente, segmento):
    return eval(segmento.regra, {}, {"cliente": cliente})
```

**O que dói.** Quem salva um segmento pode executar qualquer código no servidor, não só "compras > 5". Um erro de digitação só aparece quando a campanha roda, no meio do envio. E a tela não consegue oferecer um formulário "campo, operador, valor", porque o que ela gera é um texto que só um programador sabe escrever.

**com o pattern — a regra é uma árvore em JSON, validada ao montar**

```python
# o que a tela salva (e o banco guarda) — dados, não código:
#   {"e": [{"campo": "compras", "op": ">=", "valor": 6},
#          {"campo": "uf", "op": "in", "valor": ["SP", "RJ"]}]}

CAMPOS = {"compras", "uf", "vip", "ultima_compra_dias"}
OPERADORES = {">=", "<=", "==", "in"}

def montar(no: dict) -> Condicao:
    if "e" in no:
        return E(*[montar(n) for n in no["e"]])
    if "ou" in no:
        return Ou(*[montar(n) for n in no["ou"]])
    if "nao" in no:
        return Nao(montar(no["nao"]))
    if no.get("campo") not in CAMPOS or no.get("op") not in OPERADORES:
        raise RegraInvalida(no)
    return Comparacao(no["campo"], no["op"], no["valor"])

# ao salvar o segmento: se a regra é inválida, o erro é na tela, agora
regra = montar(json.loads(segmento.regra_json))

def pertence(cliente, regra):
    return regra.avaliar(cliente)
```

**O que a gramática garante.** Que uma regra só pode ser uma das coisas que a linguagem permite: campos da lista, operadores da lista, e combinações por E, OU e NÃO. Não há como escrever "apague a tabela". A validação acontece em `montar`, ao salvar, e o formulário da tela é uma forma direta de produzir o JSON.

As classes são as da Explicação. A regra mudou de lugar: foi do código para o banco, e o que deploy troca agora é só a lista de campos e operadores, que é de fato uma decisão técnica.

<a id="filtro-digitado"></a>
## 2. Filtro digitado pelo usuário em uma caixa de texto

**Situação.** O gerenciador de tarefas tem uma caixa de busca avançada: `status == aberto E prazo < 7`, ou `(dono == ana OU dono == rui) E prioridade >= 2`. O usuário escreve em texto, e a lista na tela precisa filtrar na hora.

**sem o pattern — o texto fatiado à mão**

```typescript
function filtrar(tarefas: Tarefa[], texto: string) {
  const partes = texto.split(" E ");
  return tarefas.filter((t) =>
    partes.every((p) => {
      const [campo, valor] = p.split("==");
      return String(t[campo.trim()]) === valor.trim();
    }),
  );
}

// "prazo < 7" não tem "==", então campo = "prazo < 7" e valor = undefined: quebra.
// "A OU B" não existe. Parênteses, nem pensar. E o erro só aparece em runtime.
```

**O que dói.** Cada recurso novo (comparação, OU, parênteses) obriga a reescrever a função inteira, porque o `split` não entende estrutura. Texto incompleto, como `status ==`, quebra com um erro genérico, no meio da digitação. E a precedência (E antes de OU) não está em lugar nenhum: o código simplesmente a ignora.

**com o pattern — o texto vira árvore uma vez, a árvore filtra a lista**

```typescript
// Condicao, Comparacao, E e Ou: as classes da Explicação,
// com "<" e ">" somados aos operadores da Comparacao.
//
// gramática (E tem precedência sobre OU):
//   ou    := e ("OU" e)*
//   e     := atomo ("E" atomo)*
//   atomo := "(" ou ")" | campo operador valor
function parse(texto: string): Condicao {
  const tokens = texto.match(/\(|\)|[<>=]=?|[^\s()<>=]+/g) ?? [];
  let i = 0;

  const ou = (): Condicao => {
    const partes = [e()];
    while (tokens[i] === "OU") { i++; partes.push(e()); }
    return partes.length === 1 ? partes[0] : new Ou(...partes);
  };

  const e = (): Condicao => {
    const partes = [atomo()];
    while (tokens[i] === "E") { i++; partes.push(atomo()); }
    return partes.length === 1 ? partes[0] : new E(...partes);
  };

  const atomo = (): Condicao => {
    if (tokens[i] === "(") {
      i++;
      const c = ou();
      if (tokens[i++] !== ")") throw new ErroDeSintaxe("faltou )", i);
      return c;
    }
    const [campo, op, valor] = tokens.slice(i, i + 3);
    if (!valor) throw new ErroDeSintaxe("regra incompleta", i);
    i += 3;
    return new Comparacao(campo, op, isNaN(+valor) ? valor : +valor);
  };

  const arvore = ou();
  if (i < tokens.length) throw new ErroDeSintaxe(`não esperava "${tokens[i]}"`, i);
  return arvore;
}

// na tela
try {
  const regra = parse(caixa.value);            // erra aqui, com a posição, antes de tocar em dado algum
  mostrar(tarefas.filter((t) => regra.avaliar(t)));
} catch (e) {
  if (e instanceof ErroDeSintaxe) sublinhar(caixa, e.posicao, e.message);
}
```

**O que a gramática garante.** Que o texto ou é uma sentença válida da linguagem, ou falha em `parse`, com a posição do problema, antes de qualquer tarefa ser avaliada. A árvore é construída uma vez e avaliada para cada tarefa. E a precedência e os parênteses vêm da forma da gramática, em vez de remendos: `A OU B E C` é `A OU (B E C)` porque `e` está abaixo de `ou`.

> **Nota.** O *parser* não faz parte do Interpreter do catálogo GoF: o padrão começa na árvore. Mas sem ele a regra em texto não existe, e é a parte mais trabalhosa. Se a linguagem passar de meia dúzia de construções, use uma biblioteca de parsing em vez de escrever à mão.

<a id="varias-leituras"></a>
## 3. A mesma regra no código, no banco e na tela

**Situação.** Os segmentos do primeiro exemplo agora precisam de mais duas leituras. A primeira: contar e listar os clientes do segmento no banco, que tem dois milhões deles, então carregar todos em memória para avaliar um a um está fora de questão. A segunda: a tela mostra a regra em palavras, para quem confere o que está valendo.

**sem o pattern — três implementações da mesma regra**

```python
def pertence(cliente, no):                   # em memória
    if "e" in no:
        return all(pertence(cliente, n) for n in no["e"])
    return OPS[no["op"]](cliente[no["campo"]], no["valor"])

def para_sql(no):                             # no banco — escrita meses depois, por outra pessoa
    if "e" in no:
        return "(" + " AND ".join(para_sql(n) for n in no["e"]) + ")"
    return f"{no['campo']} {no['op']} {no['valor']}"   # injeção de SQL; e como fica o "in" com lista?

def descrever(no):                           # na tela
    if "e" in no:
        return " e ".join(descrever(n) for n in no["e"])
    # ... e o "ou", e o "nao" — em três lugares
```

**O que dói.** A mesma lógica existe três vezes, em três arquivos, e cada uma tem os seus furos. Quando alguém acrescenta o `nao`, esquece de uma das três, e o segmento mostrado na tela deixa de ser o que o banco devolve. O valor entra no SQL colado ao texto, o que é uma injeção à espera de acontecer.

**com o pattern — cada nó sabe as três leituras**

```python
class Comparacao(Condicao):
    def avaliar(self, cliente):
        return self._OPERADORES[self._op](cliente[self._campo], self._valor)

    def para_sql(self):
        if self._op == "in":
            marcas = ", ".join("?" * len(self._valor))
            return f"{self._campo} IN ({marcas})", list(self._valor)
        op = "=" if self._op == "==" else self._op
        return f"{self._campo} {op} ?", [self._valor]    # o valor vai como parâmetro

    def descrever(self):
        return f"{self._campo} {self._op} {self._valor}"

class E(Condicao):
    def avaliar(self, cliente):
        return all(p.avaliar(cliente) for p in self._partes)

    def para_sql(self):
        pedacos = [p.para_sql() for p in self._partes]
        sql = "(" + " AND ".join(s for s, _ in pedacos) + ")"
        return sql, [v for _, vs in pedacos for v in vs]

    def descrever(self):
        return " e ".join(p.descrever() for p in self._partes)

# uma regra, três usos
regra.avaliar(cliente)                              # em memória
sql, params = regra.para_sql()
cur.execute(f"SELECT id FROM clientes WHERE {sql}", params)   # no banco (DB-API, ex.: sqlite3)
regra.descrever()                                 # "compras >= 5 e uf in ['SP', 'RJ']"
```

**O que a gramática garante.** Que existe uma única descrição da regra, a árvore, e que cada leitura é um método do nó. Um nó novo (`Nao`) obriga a pensar nas três leituras no mesmo lugar, em vez de em três arquivos. O campo no SQL é seguro porque passou pela lista fechada de `montar`; o valor vai como parâmetro.

> **Cuidado.** Com três leituras, o desenho ainda cabe nos nós. Com seis ou sete, cada classe fica inchada de operações que não têm a ver com ela. É o ponto de passar para o Visitor, que tira as leituras de dentro da árvore — veja [Parecidos](explicacao.md#parecidos).

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três:

| Caso | Já coberto por |
|---|---|
| Permissões por regra (`papel == admin OU dono == usuario`) | 1 — a regra guardada como dados, validada ao montar |
| Feature flags com segmentação por usuário | 1 — o mesmo segmento, vindo de configuração |
| Fórmulas de preço ou de campo calculado, digitadas por quem administra | 2 — o texto vira árvore uma vez e é avaliado muitas |
| Regras de roteamento de e-mails ou de chamados | 1 — regras guardadas no banco, avaliadas por mensagem |
| Mostrar a regra em linguagem natural para auditoria | 3 — mais uma leitura da mesma árvore |

E um caso que parece Interpreter, mas não é: ler um dicionário de configuração com `if config["modo"] == …`. A estrutura é plana, sem aninhamento e sem gramática: é só configuração, e um `if` ou um dicionário de funções basta. Veja a seção [Quando não usar](explicacao.md#quando-nao-usar) da explicação.
