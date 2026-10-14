<!-- Gerado de pages/clean-code/estruturais/proxy/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Proxy — Explicação

*Clean Code / Design Pattern / Proxy*

Como pôr um representante no lugar de um objeto, para decidir se, quando ou onde o objeto de verdade é usado, sem que quem o usa perceba a troca.

<a id="o-problema"></a>
## O problema

A tela de clientes lista 200 nomes por página. Cada `Cliente` tem um histórico de pedidos, e o histórico é pesado: uma consulta que junta pedidos, itens e pagamentos. A tela, porém, só mostra o histórico de *um* cliente, quando alguém clica nele.

O jeito direto de escrever é carregar o que o objeto tem, no construtor:

**antes — a consulta pesada roda para todos, sempre**

```python
class Cliente:
    def __init__(self, id, nome, repo):
        self.id, self.nome = id, nome
        self.historico = repo.carregar_historico(id)   # o SELECT pesado, no construtor

def listar_clientes(repo):
    return [Cliente(r.id, r.nome, repo) for r in repo.todos()]  # 200 consultas pesadas
```

A tela que só mostra nomes dispara 200 consultas pesadas, e 199 delas são jogadas fora. A correção "rápida" costuma piorar: um parâmetro `carregar_historico=False`, e a partir daí todo uso de `cliente.historico` precisa lembrar de um `if cliente.historico is None`. A pergunta "já foi carregado?" se espalha por todo o código que usa o cliente, que nem devia saber que existe um carregamento.

<a id="a-solucao"></a>
## A solução

Ponha, no lugar do histórico, um objeto com **a mesma interface** que só vai buscar o histórico de verdade quando alguém pedir pela primeira vez. Para o `Cliente` e para a tela, é um histórico como outro qualquer. Os papéis são quatro:

| Papel | Quem é | No exemplo |
|---|---|---|
| Sujeito | A interface que o cliente usa e que real e proxy implementam | `Historico` |
| Sujeito real | O objeto que faz o trabalho de verdade | `HistoricoDoBanco` |
| Proxy | Tem a mesma interface, guarda o que precisa para criar ou alcançar o real e controla quando isso acontece | `HistoricoPreguicoso` |
| Cliente | Quem usa o sujeito sem saber qual dos dois recebeu | `Cliente` e a tela |

O ponto é que o proxy **é** o objeto, do ponto de vista de quem o usa, e **decide** o que fazer com cada chamada: criar o real agora, recusar, mandar para outro processo. O real não sabe que existe um proxy na frente dele. Isso é o que o separa do Decorator, que acrescenta algo em *toda* chamada; o proxy controla o *alcance*.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. o sujeito: o que o cliente usa
class Historico(ABC):
    @abstractmethod
    def pedidos(self) -> list[Pedido]: ...

    @abstractmethod
    def total_gasto(self) -> Decimal: ...

# 2. o sujeito real: a consulta pesada acontece ao criar
class HistoricoDoBanco(Historico):
    def __init__(self, repo, cliente_id):
        self._pedidos = repo.pedidos_do_cliente(cliente_id)

    def pedidos(self):
        return self._pedidos

    def total_gasto(self):
        return sum((p.total for p in self._pedidos), Decimal(0))

# 3. o proxy: mesma interface, cria o real só na primeira chamada
class HistoricoPreguicoso(Historico):
    def __init__(self, repo, cliente_id):
        self._repo, self._cliente_id = repo, cliente_id
        self._real: HistoricoDoBanco | None = None

    def _carregado(self) -> HistoricoDoBanco:
        if self._real is None:
            self._real = HistoricoDoBanco(self._repo, self._cliente_id)
        return self._real

    def pedidos(self):
        return self._carregado().pedidos()

    def total_gasto(self):
        return self._carregado().total_gasto()

# 4. o cliente: recebe um Historico e não sabe qual
class Cliente:
    def __init__(self, id, nome, historico: Historico):
        self.id, self.nome, self.historico = id, nome, historico

def listar_clientes(repo):
    return [
        Cliente(r.id, r.nome, HistoricoPreguicoso(repo, r.id))   # nenhuma consulta ainda
        for r in repo.todos()
    ]
```

> **Dica.** O teste do `Cliente` e da tela usa um `Historico` falso com a lista pronta, como com qualquer outra implementação. E o teste do proxy conta chamadas no repositório: zero ao listar, uma ao pedir `pedidos()`, e ainda uma só ao pedir `total_gasto()` logo depois.

<a id="quando-usar"></a>
## Quando usar

O Proxy vale quando três coisas acontecem ao mesmo tempo: já existe (ou vai existir) um objeto real com uma interface estável, você precisa controlar **se, quando ou onde** ele é alcançado, e quem o usa **não deve precisar saber** disso.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um objeto caro criado antes de saber se será usado | Consulta, leitura de arquivo ou chamada de rede no `__init__`; N consultas para uma tela que usa uma | [Implementação, acima](#implementacao) |
| A mesma checagem de permissão antes de cada chamada ao mesmo objeto | `if usuario.papel in (...)` repetido em controllers e relatórios; um deles esqueceu | [Uso #1](uso.md#acesso-por-papel) |
| Um serviço foi para outro processo, e o código continua chamando como se fosse local | `requests.get(...)` com URL, *timeout* e parse copiados onde antes havia `estoque.disponivel(sku)` | [Uso #2](uso.md#servico-extraido) |
| Observar o que acontece com um objeto sem mexer na classe dele | `copy.deepcopy` antes e comparação depois; `UPDATE` com todas as colunas | [Uso #3](uso.md#mudancas-de-campos) |

> **Dica.** Os sinais têm uma coisa em comum: alguém está fazendo trabalho de porteiro (checar, adiar, localizar, observar) no meio do código que devia só usar o objeto. O Proxy põe o porteiro entre os dois, com a cara do objeto, e nenhum lado muda.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Você quer controlar *se, quando ou onde* o objeto real é alcançado?** Se o que você quer é acrescentar algo que roda em toda chamada (log, cache, métrica), é Decorator. Pare.
2. **A interface do proxy pode ser exatamente a do real?** Se o chamador precisaria de um método novo para usá-lo, é uma API nova, e o nome do que você quer é Facade ou Adapter.
3. **Há um motivo concreto?** Custo de criar medido, uma regra de acesso ou uma fronteira de processo. Sem isso, o proxy é só uma indireção.
4. **Quem usa o proxy só consegue chegar ao real por ele?** Se o real continua acessível por outro caminho, um proxy de proteção não protege nada.

<a id="quando-nao-usar"></a>
## Quando não usar

O Proxy tem custos que aparecem na depuração. É um objeto a mais, e uma pilha a mais para atravessar. O proxy *mente* sobre o objeto: um proxy remoto parece local, mas tem latência e falhas que o real não tem. E o carregamento preguiçoso adianta o prazer e atrasa o erro: se a consulta falhar, a exceção aparece na primeira leitura, longe do ponto onde o objeto foi criado.

| Situação | Por que não | Faça isto |
|---|---|---|
| O objeto é barato de criar | Adiar não economiza nada e atrasa os erros | Crie direto |
| Você quer acrescentar cache, log ou métrica em toda chamada | Não controla o alcance do real; só acrescenta comportamento | Decorator |
| A interface do que existe não é a que o código espera | O problema é conversão, não controle | Adapter |
| A chamada remota vai ser feita em laço, ou o chamador precisa decidir o que fazer em caso de falha | A interface "local" esconde custo e falha que o chamador precisa ver | Uma interface explícita para o remoto (assíncrona, com erro e *timeout* à vista) |
| A regra de permissão é complexa, com muita lógica de negócio | O proxy deve aplicar a regra, e não calculá-la | Um serviço de autorização que o proxy só consulta |

<a id="sinais-de-abuso"></a>
### Sinais de que o Proxy saiu do lugar

- **O proxy decide regra de negócio.** Se ele calcula quem pode ver o quê, virou o lugar onde a regra mora, sem nome nem teste próprio.
- **O proxy conhece o interior do real.** Se ele acessa campos privados ou depende da ordem em que o real é montado, os dois mudam juntos.
- **O proxy tem métodos que o real não tem.** Quem chama `proxy.recarregar()` precisa saber que é um proxy, e a transparência acabou.
- **Falha remota disfarçada de valor.** Um proxy que engole o *timeout* e devolve `0` faz o chamador decidir com um dado falso.
- **O real vaza por outro caminho.** Um atributo `proxy.real` público, ou o real injetado diretamente em alguns lugares, desfaz o controle.

> **Perigo.** O sinal mais comum: um proxy remoto que parece local e esconde o custo. O chamador faz 200 chamadas a `estoque.disponivel(sku)` em um laço, como se cada uma fosse uma leitura de memória, e cada uma é uma viagem de rede.

> **Nota.** Na dúvida, comece com o objeto real e a chamada direta. O Proxy entra quando o motivo aparece medido: a consulta que deixa a tela lenta, o incidente de acesso, o serviço que foi extraído. Como a interface não muda, introduzi-lo depois é barato.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Decorator](../decorator/explicacao.md) | Tem a mesma forma, mas acrescenta algo em *toda* chamada (log, cache) e é empilhado por quem usa. O Proxy controla se, quando e onde o real é alcançado, e costuma criar ou localizar o real sozinho |
| [Adapter](../adapter/explicacao.md) | Muda a interface de um objeto existente para outra. O Proxy mantém a interface idêntica |
| [Facade](../facade/explicacao.md) | Cria uma interface nova e menor sobre várias peças. O Proxy tem a interface de *um* objeto e fala por ele |
| [Flyweight](../flyweight/explicacao.md) | Compartilha objetos imutáveis entre muitos contextos para poupar memória. O Proxy (virtual) adia a criação de *um* objeto até que ele seja necessário |

Regra prática: se o objeto intermediário existe para decidir se, quando ou onde o real é usado, é Proxy; se existe para acrescentar algo a cada chamada, é Decorator.
