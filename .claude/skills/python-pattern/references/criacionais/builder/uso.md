<!-- Gerado de pages/clean-code/criacionais/builder/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Builder — Uso

*Clean Code / Design Pattern / Builder*

Três situações em que o Builder resolve o problema, além da montagem em etapas da Explicação. Cada uma traz o código sem o pattern, o código com ele e o que o Builder separa em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar um builder. A montagem em etapas com validação final já é o exemplo da [Explicação](explicacao.md#o-problema) (o e-mail), então não se repete aqui. Quando dois casos se resolvem com o mesmo raciocínio — montar uma URL por partes e montar uma consulta SQL, por exemplo —, só um fica. O Builder tem poucos motivos próprios: o problema "muitos parâmetros" quase sempre se resolve com argumentos nomeados, e está explicado em [Quando não usar](explicacao.md#quando-nao-usar). Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o Builder separa |
|---|---|---|
| 1 | [O mesmo roteiro, saídas diferentes](#mesmo-roteiro) | O passo a passo do formato final |
| 2 | [Estado interno que o chamador não deveria gerenciar](#estado-interno) | O que se pede do que precisa ficar em sincronia |
| 3 | [Dados de teste que só dizem o que importa](#dados-de-teste) | O que o teste afirma dos valores padrão |

> **Nota.** O exemplo 2 usa o marcador `%s` de parâmetros do `psycopg2`. Os modelos (`Pedido`, `Cliente`) e a função `db.execute` são fictícios.

<a id="mesmo-roteiro"></a>
## 1. O mesmo roteiro, saídas diferentes

**Situação.** O sistema gera o recibo de um pedido: um título, uma linha por item e o total. Primeiro era só texto para o e-mail; agora a tela também mostra o recibo em HTML, e o financeiro pede uma versão em Markdown. O roteiro — título, itens, total — é sempre o mesmo.

**sem o pattern — o formato decidido em cada passo**

```python
def gerar_recibo(pedido, formato):
    if formato == "html":
        saida = f"<h1>Recibo {pedido.id}</h1>"
    else:
        saida = f"RECIBO {pedido.id}\n"

    for item in pedido.itens:
        if formato == "html":
            saida += f"<p>{item.nome} — R$ {item.preco:.2f}</p>"
        else:
            saida += f"- {item.nome}: R$ {item.preco:.2f}\n"

    if formato == "html":
        saida += f"<p>Total: R$ {pedido.total:.2f}</p>"
    else:
        saida += f"Total: R$ {pedido.total:.2f}\n"
    return saida
```

**O que dói.** O formato é perguntado em cada passo, e Markdown vira um terceiro ramo em **todos** eles. O roteiro (a ordem das partes) está duplicado dentro de cada ramo, então uma mudança como "mostrar o desconto antes do total" precisa ser feita nas versões, e esquecer uma é fácil. E o HTML é montado sem escapar o nome do item.

**com o pattern — um roteiro, um builder por formato**

```python
from html import escape

class ConstrutorDeRecibo(ABC):
    @abstractmethod
    def titulo(self, texto: str) -> None: ...
    @abstractmethod
    def item(self, nome: str, preco: float) -> None: ...
    @abstractmethod
    def total(self, valor: float) -> None: ...
    @abstractmethod
    def resultado(self) -> str: ...

class ReciboEmHtml(ConstrutorDeRecibo):
    def __init__(self):
        self._partes = []

    def titulo(self, texto):
        self._partes.append(f"<h1>{escape(texto)}</h1>")

    def item(self, nome, preco):
        self._partes.append(f"<p>{escape(nome)} — R$ {preco:.2f}</p>")

    def total(self, valor):
        self._partes.append(f"<p>Total: R$ {valor:.2f}</p>")

    def resultado(self):
        return "\n".join(self._partes)

# ReciboEmTexto e ReciboEmMarkdown: a mesma forma, com outra sintaxe

# o roteiro, escrito uma vez
def montar_recibo(pedido, construtor: ConstrutorDeRecibo) -> str:
    construtor.titulo(f"Recibo {pedido.id}")
    for item in pedido.itens:
        construtor.item(item.nome, item.preco)
    construtor.total(pedido.total)
    return construtor.resultado()

montar_recibo(pedido, ReciboEmHtml())
```

**O que o Builder separa.** O **roteiro** do **formato**. `montar_recibo` sabe a ordem e não sabe nada de HTML; cada builder sabe uma sintaxe e não sabe a ordem. Este é o desenho original do GoF: quem escreve o roteiro (o *diretor*) é uma função à parte, e vários builders concretos produzem representações diferentes do mesmo processo.

> **Cuidado.** Repare no `escape(nome)`: texto de usuário em HTML sem escapar é uma falha de segurança (XSS). Em um builder, isso fica em um lugar só — o que também é um argumento para o padrão.

<a id="estado-interno"></a>
## 2. Estado interno que o chamador não deveria gerenciar

**Situação.** A tela de pedidos tem filtros opcionais: cliente, status, data inicial e limite de resultados. A consulta SQL é montada conforme o que o usuário preencheu.

**sem o pattern — o SQL e os parâmetros, mantidos em paralelo à mão**

```python
def buscar_pedidos(cliente_id=None, status=None, desde=None, limite=None):
    sql = "SELECT * FROM pedidos WHERE 1=1"
    params = []
    if cliente_id is not None:
        sql += " AND cliente_id = %s"
        params.append(cliente_id)
    if status:
        sql += " AND status = %s"
        params.append(status)
    if desde:
        sql += " AND criado_em >= %s"
        params.append(desde)
    if limite:
        sql += " ORDER BY criado_em DESC LIMIT %s"   # e sem limite, sem ordem?
        params.append(limite)
    return db.execute(sql, params)
```

**O que dói.** Cada ramo precisa acrescentar o trecho de SQL **e** o valor, na mesma ordem; esquecer um dos dois dá um erro só em tempo de execução, e só para quem marcou aquele filtro. A ordenação ficou presa ao limite sem querer. O `WHERE 1=1` é um truque que todo mundo repete. E quando outra tela precisa de uma busca parecida, copia a função — ou alguém a "simplifica" com `f"... {status}"` e abre uma injeção de SQL.

**com o pattern — o builder guarda o SQL e os parâmetros juntos**

```python
class ConsultaDePedidos:
    def __init__(self):
        self._filtros = []     # trechos de SQL, já com %s
        self._params = []      # os valores, na mesma ordem
        self._limite = None

    def do_cliente(self, cliente_id):
        self._filtrar("cliente_id = %s", cliente_id)
        return self

    def com_status(self, status):
        self._filtrar("status = %s", status)
        return self

    def desde(self, data):
        self._filtrar("criado_em >= %s", data)
        return self

    def limitar(self, n):
        self._limite = n
        return self

    def _filtrar(self, trecho, valor):    # o único lugar que mexe nas duas listas
        self._filtros.append(trecho)
        self._params.append(valor)

    def montar(self):
        sql = "SELECT * FROM pedidos"
        params = list(self._params)
        if self._filtros:
            sql += " WHERE " + " AND ".join(self._filtros)
        sql += " ORDER BY criado_em DESC"
        if self._limite is not None:
            sql += " LIMIT %s"
            params.append(self._limite)
        return sql, params

# o chamador só diz o que quer
sql, params = (ConsultaDePedidos()
    .do_cliente(42)
    .com_status("pago")
    .limitar(20)
    .montar())
db.execute(sql, params)
```

**O que o Builder separa.** O que o chamador **pede** do que precisa **ficar em sincronia**. A regra "trecho e valor andam juntos" está em um método, `_filtrar`, e não pode ser quebrada de fora; a ordem das cláusulas (`WHERE`, `ORDER BY`, `LIMIT`) é decidida em `montar()`, e o chamador pode chamar as etapas em qualquer ordem. Como o valor sempre vai por parâmetro, não há concatenação de dado do usuário no SQL.

> **Dica.** Para consultas de verdade, use o que já existe: o `select(Pedido).where(...)` do SQLAlchemy é exatamente este padrão, mantido por outras pessoas. Escreva o seu quando as buscas forem poucas e específicas demais para justificar um ORM.

<a id="dados-de-teste"></a>
## 3. Dados de teste que só dizem o que importa

**Situação.** A regra de frete diz que pedidos acima de R$ 200 têm frete grátis. O teste precisa de um `Pedido`, e o `Pedido` exige cliente, itens, endereço, cupom e status — nenhum dos quais tem a ver com a regra.

**sem o pattern — dez linhas para afirmar sobre um campo**

```python
def test_frete_gratis_acima_de_200():
    pedido = Pedido(
        id=1,
        cliente=Cliente(id=1, nome="Ana", email="ana@exemplo.com", cidade="SP", vip=False),
        itens=[Item("Caneta", 250.0, 1)],
        endereco=Endereco("Rua A", "100", "01000-000", "SP"),
        cupom=None,
        status="novo",
    )
    assert calcular_frete(pedido) == 0
```

**O que dói.** Quem lê não sabe o que importa: o `vip=False` é relevante? O CEP? Só o total de 250 é. E quando `Pedido` ganha um campo obrigatório, **todos** os testes que o constroem quebram, mesmo os que não têm nada a ver com ele.

**com o pattern — valores padrão válidos, e o teste diz só o que muda**

```python
class PedidoBuilder:
    def __init__(self):
        # tudo começa válido e neutro
        self._itens = [Item("Produto", 10.0, 1)]
        self._vip = False
        self._cidade = "SP"
        self._cupom = None

    def com_total(self, valor):
        self._itens = [Item("Produto", valor, 1)]
        return self

    def com_item(self, nome, preco, quantidade=1):
        self._itens.append(Item(nome, preco, quantidade))
        return self

    def vip(self):
        self._vip = True
        return self

    def construir(self) -> Pedido:
        return Pedido(
            id=1,
            cliente=Cliente(id=1, nome="Ana", email="ana@exemplo.com", cidade=self._cidade, vip=self._vip),
            itens=list(self._itens),
            endereco=Endereco("Rua A", "100", "01000-000", self._cidade),
            cupom=self._cupom,
            status="novo",
        )

def test_frete_gratis_acima_de_200():
    pedido = PedidoBuilder().com_total(250).construir()
    assert calcular_frete(pedido) == 0
```

**O que o Builder separa.** O que o teste **afirma** do que é **padrão**. A linha `com_total(250)` é a única informação do teste; todo o resto é neutro e vive em um lugar só. Quando `Pedido` ganha um campo obrigatório, o `construir()` é o único ponto a atualizar, e não os cem testes.

> **Nota.** Em Python, uma função com argumentos nomeados — `um_pedido(total=250)` — faz o mesmo e é mais curta. O builder compensa quando há *acúmulo*, como o `com_item()` chamado três vezes.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três, na Explicação, ou porque a resposta certa é outra:

| Caso | Já coberto por |
|---|---|
| Cliente HTTP com nove opções (timeout, retries, headers…) | Argumentos nomeados ou um objeto de opções. Veja "Quando não usar"; só vira Builder se houver validação cruzada, como na Explicação |
| Montar um PDF ou uma planilha por partes (cabeçalho, linhas, rodapé) | 1 — o mesmo roteiro, saídas diferentes |
| Montar uma URL com host, caminho e parâmetros de busca | 2 — estado interno que o chamador não deveria gerenciar |
| Configuração da aplicação carregada por camadas (arquivo, ambiente, flags) | Explicação — montagem em etapas com validação final |
| Dados de teste para qualquer entidade | 3 — dados de teste |

E um caso que parece Builder, mas não é: o encadeamento fluente que não monta nada, como `texto.strip().lower().split()` ou `lista.filter(...).map(...)`. Cada chamada devolve um objeto novo, e não há produto a validar nem montagem final. É só a sintaxe — a seção [Parecidos](explicacao.md#parecidos) da explicação mostra a diferença.
