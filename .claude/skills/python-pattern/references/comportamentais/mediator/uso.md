<!-- Gerado de pages/clean-code/comportamentais/mediator/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Mediator — Uso

*Clean Code / Design Pattern / Mediator*

Três situações em que o Mediator resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o mediador concentra.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Mediator. Quando dois casos se resolvem com o mesmo raciocínio, só um fica. Os campos de formulário, o caso mais comum, já são o exemplo da [Explicação](explicacao.md#o-problema). Sobraram três motivos aqui, e os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o mediador concentra |
|---|---|---|
| 1 | [Participantes que trocam mensagens entre si](#sala-de-chat) | Quem recebe cada mensagem, e as regras do grupo |
| 2 | [Serviços que se chamam em cadeia](#orquestracao-de-pedido) | A ordem do processo e o que fazer quando algo falha |
| 3 | [Regras que dependem de quem encontra quem](#regras-entre-pares) | O que acontece quando dois tipos se encontram |

<a id="sala-de-chat"></a>
## 1. Participantes que trocam mensagens entre si

**Situação.** Uma sala de chat. Quem escreve fala para todos; `@ana oi` vai só para Ana; um moderador pode silenciar alguém; pessoas entram e saem o tempo todo. Na Explicação, os objetos reagiam uns aos outros; aqui eles se *mandam coisas*.

**sem o pattern — cada usuário guarda todos os outros**

```python
class Usuario:
    def __init__(self, nome):
        self.nome = nome
        self.outros: list["Usuario"] = []       # cada um guarda todos os outros
        self.silenciado = False

    def enviar(self, texto):
        if self.silenciado:
            return
        for outro in self.outros:
            if texto.startswith("@") and not texto.startswith("@" + outro.nome):
                continue                    # mensagem privada: o filtro mora no remetente
            outro.receber(self.nome, texto)

def entrar(novo, sala):
    for u in sala:
        novo.outros.append(u)
        u.outros.append(novo)              # e quem sai? precisa sair da lista de todos
    sala.append(novo)
```

**O que dói.** Com *n* pessoas são *n × n* referências, e sair da sala exige remover-se da lista de todos. A regra de moderação (silenciar) e a de mensagem privada estão dentro de cada usuário, copiadas e fáceis de divergir. E uma regra nova, como "máximo de dez mensagens por minuto", significa mexer em todos.

**com o pattern — a sala é o único que conhece todos**

```python
class Sala:
    def __init__(self):
        self._membros: dict[str, "Participante"] = {}
        self._silenciados: set[str] = set()

    def entrar(self, p):
        self._membros[p.nome] = p
        p.sala = self

    def sair(self, p):
        self._membros.pop(p.nome, None)

    def silenciar(self, nome):
        self._silenciados.add(nome)

    def enviar(self, de, texto):
        if de in self._silenciados:
            return
        if texto.startswith("@"):
            destino, _, corpo = texto[1:].partition(" ")
            if destino in self._membros:
                self._membros[destino].receber(de, corpo)
            return
        for nome, p in self._membros.items():
            if nome != de:
                p.receber(de, texto)

class Participante:
    def __init__(self, nome):
        self.nome, self.sala = nome, None

    def enviar(self, texto):
        self.sala.enviar(self.nome, texto)   # só conhece a sala

    def receber(self, de, texto): ...
```

**O que o mediador concentra.** O roteamento e as regras do grupo: quem recebe, quem pode falar, quem entrou. As *n × n* referências viram *n* ligações com a sala, e um participante novo entra sem nenhum dos outros ser tocado. A regra de limite de mensagens é um `if` em `enviar`.

> **Cuidado.** Em um sistema distribuído, o mediador é um ponto único: se a sala cai, ninguém conversa. Nesse caso, ele deixa de ser um objeto e vira um serviço, um *message broker*, com os mesmos papéis em outra escala.

<a id="orquestracao-de-pedido"></a>
## 2. Serviços que se chamam em cadeia

**Situação.** Fechar um pedido passa por três serviços: reservar o estoque, cobrar o pagamento e agendar a entrega. Se o pagamento for recusado, a reserva precisa ser devolvida. Cada serviço foi escrito por um time, e cada um termina chamando o próximo.

**sem o pattern — cada serviço dispara o seguinte**

```python
class Estoque:
    def __init__(self, pagamento):
        self._pagamento = pagamento

    def reservar(self, pedido):
        self._baixar(pedido.itens)
        self._pagamento.cobrar(pedido)          # o Estoque decide o que vem depois

    def devolver(self, pedido): ...

class Pagamento:
    def __init__(self, envio, estoque):
        self._envio, self._estoque = envio, estoque   # o Pagamento conhece o passo anterior E o seguinte

    def cobrar(self, pedido):
        if not self._cobrar(pedido):
            self._estoque.devolver(pedido)
            return
        self._envio.agendar(pedido)
```

**O que dói.** A ordem do processo não existe em lugar nenhum: para descobri-la é preciso seguir as chamadas de um serviço para o outro. Cada serviço conhece o anterior e o seguinte, o que forma um ciclo. Inserir uma etapa de antifraude entre o estoque e o pagamento obriga a mexer em *dois* serviços, de dois times.

**com o pattern — os serviços avisam o que aconteceu, o mediador decide o que vem**

```python
class Pagamento:
    def __init__(self, mediador=None):
        self.mediador = mediador

    def cobrar(self, pedido):
        ok = self._cobrar(pedido)
        self.mediador.notificar("pagamento.aprovado" if ok else "pagamento.recusado", pedido)

# Estoque e Envio seguem o mesmo formato: fazem o seu trabalho e avisam

class FechamentoDePedido:
    """O único lugar que conhece a ordem do processo."""

    def __init__(self, estoque, pagamento, envio):
        self.estoque, self.pagamento, self.envio = estoque, pagamento, envio
        for servico in (estoque, pagamento, envio):
            servico.mediador = self

    def fechar(self, pedido):
        self.estoque.reservar(pedido)

    def notificar(self, evento, pedido):
        if evento == "estoque.reservado":
            self.pagamento.cobrar(pedido)
        elif evento == "pagamento.aprovado":
            self.envio.agendar(pedido)
        elif evento == "pagamento.recusado":
            self.estoque.devolver(pedido)     # a compensação mora aqui, não no Pagamento
```

**O que o mediador concentra.** A ordem do processo e o que fazer quando uma etapa falha. Cada serviço passa a conhecer só "avisei que terminei"; nenhum sabe quem vem antes ou depois dele. A etapa de antifraude é um `elif` novo no mediador, e nenhum serviço existente muda.

> **Cuidado.** O `if evento == …` é o ponto fraco. Passando de meia dúzia de eventos, o mediador vira uma máquina de estados escrita à mão: use uma tabela de evento para passo, ou uma biblioteca de workflow, em vez de continuar a cadeia de `elif`.

<a id="regras-entre-pares"></a>
## 3. Regras que dependem de quem encontra quem

**Situação.** Uma simulação com naves, asteroides, tiros e itens. Quando dois objetos se tocam, o resultado depende do *par*: nave com asteroide causa dano, tiro com asteroide destrói os dois, nave com item aplica o item. Cada nova espécie de objeto cria regras com todas as outras.

**sem o pattern — a regra do par escrita nos dois lados**

```python
class Nave:
    def colidir_com(self, outro):
        if isinstance(outro, Asteroide):
            self.vida -= 30
        elif isinstance(outro, Tiro) and outro.dono is not self:
            self.vida -= outro.dano
        elif isinstance(outro, Item):
            outro.aplicar(self)

class Asteroide:
    def colidir_com(self, outro):
        if isinstance(outro, Tiro):
            self.destruido = True
        elif isinstance(outro, Nave):
            self.destruido = True      # a regra Nave × Asteroide, de novo: o que o outro lado diz?
```

**O que dói.** A regra "nave com asteroide" existe em duas classes, e é fácil uma dizer que o asteroide some e a outra, que ele sobrevive. Adicionar um `Escudo` significa abrir todas as classes. E ninguém sabe onde procurar a regra de um par: ela está em um lado, no outro, ou nos dois.

**com o pattern — o mundo decide o que acontece em cada encontro**

```python
from itertools import combinations

class Mundo:
    def __init__(self):
        self._entidades = []
        self._regras = {                                  # (tipo, tipo) -> o que acontece
            (Nave, Asteroide): lambda nave, ast: nave.dano(30),
            (Tiro, Asteroide): lambda tiro, ast: (ast.destruir(), tiro.destruir()),
            (Nave, Item):      lambda nave, item: item.aplicar(nave),
        }

    def passo(self):
        for a, b in combinations(self._entidades, 2):
            if a.colide(b):
                self._resolver(a, b)

    def _resolver(self, a, b):
        regra = self._regras.get((type(a), type(b)))
        if regra:
            regra(a, b)
            return
        regra = self._regras.get((type(b), type(a)))
        if regra:
            regra(b, a)
```

**O que o mediador concentra.** As regras de encontro, uma por par e escrita uma vez. As entidades só sabem de geometria (`colide`), e não se conhecem. Um `Escudo` novo são duas linhas na tabela, e a pergunta "o que acontece quando A encontra B?" tem um único lugar como resposta.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na Explicação):

| Caso | Já coberto por |
|---|---|
| Campos de formulário que se mostram, preenchem e habilitam | O exemplo da [Explicação](explicacao.md#o-problema) |
| Wizard de várias etapas, em que cada tela libera a próxima | 2 — a ordem do fluxo em um lugar só |
| Torre de controle: decidir quem usa a pista, a sala ou o recurso | 2 — a decisão depende do estado de todos, que só o mediador vê |
| Interações entre personagens, ou entre peças de um tabuleiro | 3 — a regra do par, em uma tabela |
| Barramento de eventos entre módulos de uma aplicação | 1, se há regra de quem recebe o quê. Sem regra, é só Observer |

E um caso que parece Mediator, mas não é: uma classe `PedidoService` que reúne chamadas a três outras. Se os três objetos de dentro não conhecem essa classe e não a chamam de volta, a comunicação é de mão única, e o nome certo é Facade — veja a seção [Parecidos](explicacao.md#parecidos) da explicação.
