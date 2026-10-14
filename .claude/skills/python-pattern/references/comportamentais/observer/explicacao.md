<!-- Gerado de pages/clean-code/comportamentais/observer/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Observer — Explicação

*Clean Code / Design Pattern / Observer*

Como avisar várias partes do sistema de que algo aconteceu, sem que quem avisa precise saber quem são elas, nem quantas.

<a id="o-problema"></a>
## O problema

Quando o pedido é pago, três coisas precisam acontecer: o cliente recebe o recibo, o estoque dá baixa e a nota fiscal é emitida. O lugar mais óbvio para fazer isso é o próprio método que marca o pedido como pago.

A saída preguiçosa é chamar cada uma das três de dentro dele:

**antes — o pedido conhece todo mundo que reage a ele**

```python
class Pedido:
    def pagar(self, transacao):
        self.status = "pago"
        self.transacao = transacao

        # tudo o que depende de "pago" mora aqui dentro
        EmailDeRecibo().enviar(self)
        Estoque().baixar(self.itens)
        NotaFiscal().emitir(self)
        # e os pontos de fidelidade que o marketing pediu?
```

Três coisas quebram daqui a pouco. Cada reação nova é uma edição em `Pedido`, a classe que menos devia mudar por causa de e-mail ou de nota fiscal. O `pagar` não se testa sem as três dependências. E, se o e-mail falha, o pedido já está marcado como pago, mas ficou sem baixa de estoque e sem nota: a exceção interrompeu o que vinha depois. É o Single Responsibility e o Open/Closed quebrados no mesmo método.

<a id="a-solucao"></a>
## A solução

Faça o pedido guardar uma lista de interessados e **avisar** cada um quando algo acontece. Ele não sabe o que cada interessado faz com o aviso, nem quantos são. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Assunto | Quem tem o fato e a lista de interessados; avisa quando ele acontece | `Pedido` |
| Observador | A interface mínima que o assunto exige de quem escuta | `OuvintePedido` |
| Observador concreto | Uma reação ao fato, com as dependências dela | `EnviarRecibo`, `BaixarEstoque` |
| Montagem | O único lugar que inscreve os observadores no assunto | O código que cria o pedido |

O ponto é o **sentido da frase**. O assunto diz "isto aconteceu", e não "faça aquilo". Quem decide o que fazer com o aviso é o observador, e quem decide *quais* observadores existem é a montagem. O pedido termina o que tinha a fazer mesmo que ninguém esteja ouvindo.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. o observador: tudo o que o pedido sabe sobre quem escuta
class OuvintePedido(ABC):
    @abstractmethod
    def pedido_pago(self, pedido: "Pedido") -> None: ...

# 2. o assunto: guarda a lista e avisa; não sabe o que cada um faz
class Pedido:
    def __init__(self):
        self.status = "aberto"
        self._ouvintes: list[OuvintePedido] = []

    def inscrever(self, ouvinte: OuvintePedido):
        self._ouvintes.append(ouvinte)

    def pagar(self, transacao):
        self.status = "pago"
        self.transacao = transacao
        for ouvinte in self._ouvintes:
            ouvinte.pedido_pago(self)

# 3. os observadores concretos: uma reação cada, com as dependências dela
class EnviarRecibo(OuvintePedido):
    def __init__(self, email):
        self._email = email

    def pedido_pago(self, pedido):
        self._email.enviar(pedido.cliente.email, f"Recibo do pedido {pedido.id}")

class BaixarEstoque(OuvintePedido):
    def __init__(self, estoque):
        self._estoque = estoque

    def pedido_pago(self, pedido):
        self._estoque.baixar(pedido.itens)

# 4. a montagem: o único lugar que liga os dois lados
pedido = Pedido()
pedido.inscrever(EnviarRecibo(email))
pedido.inscrever(BaixarEstoque(estoque))
pedido.pagar("tx_123")
```

> **Dica.** O teste de `Pedido` agora é um ouvinte falso que guarda o que recebeu: `pagar`, e conferir que o ouvinte foi chamado uma vez. Cada observador se testa chamando `pedido_pago` direto, sem pedido de verdade. Uma reação nova é uma classe nova e uma linha na montagem; `Pedido` não muda.

<a id="quando-usar"></a>
## Quando usar

O Observer vale quando três coisas acontecem ao mesmo tempo: **mais de uma parte** precisa reagir ao mesmo fato; quem o produz **não deveria saber** quem são elas (porque a lista cresce, muda em execução ou pertence a outros); e a reação é uma **consequência**, não parte do trabalho: o assunto está completo mesmo que ninguém ouça.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um fato dispara várias reações independentes | Um método que termina com quatro chamadas a módulos diferentes; um `import` para cada reação nova | [Uso #1](uso.md#varios-interessados) |
| A tela precisa acompanhar o modelo | `atualizarHeader(); atualizarMiniCarrinho();` depois de cada alteração, ou um `setInterval` que pergunta "mudou?" | [Uso #2](uso.md#tela-acompanha-modelo) |
| Quem escuta entra e sai durante a execução | Uma lista com `append` e sem `remove`; widget fechado que continua recebendo dados | [Uso #3](uso.md#entram-e-saem) |
| Código de outros precisa reagir a algo seu | `if config.plugin_x_ativo:` dentro do núcleo; PR em seu repositório para cada extensão | [Uso #4](uso.md#plugins) |
| Código reutilizável precisa reportar o que está fazendo | Parâmetros `barra=None, logger=None, modo_cli=False` em uma função de biblioteca; `print` no meio da regra | [Uso #5](uso.md#progresso) |

> **Dica.** O que os sinais têm em comum: a linha que dispara conhece nomes que não deviam ser dela, e quem escreveu essa linha não é quem decide a lista. Se a lista é curta, fixa e sua, a chamada direta continua sendo mais honesta.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Só uma parte reage, e sempre a mesma?** Receba-a no construtor e chame o método. Uma lista de um item é cerimônia.
2. **A reação é parte da operação?** Se sem ela o pedido não está realmente pago (a baixa de estoque na mesma transação, por exemplo), não é um aviso: é um passo. Chame direto, onde a transação enxerga.
3. **Quem dispara precisa da resposta?** Aprovar, vetar, devolver um valor. O Observer não espera retorno; use uma chamada direta ou uma [Chain of Responsibility](../chain-of-responsibility/explicacao.md).
4. **A lista cresce, muda em execução ou é de outros?** Se sim, é Observer. Se é uma lista que você controla e vai mudar uma vez por ano, ainda dá para esperar.

<a id="quando-nao-usar"></a>
## Quando não usar

O Observer tem um custo que só aparece na leitura: o fluxo deixa de estar escrito em um lugar. Olhando `pagar`, não dá mais para responder "o que acontece quando o pedido é pago?". É preciso procurar quem se inscreveu, e a ordem, os erros e as cascatas passam a ser coisas que você tem de lembrar.

| Situação | Por que não | Faça isto |
|---|---|---|
| Um único interessado, fixo | A lista de um item só esconde a chamada; o fluxo fica mais difícil de seguir sem nenhum ganho | Injete o colaborador e chame o método. Extraia a lista quando o segundo aparecer |
| A reação precisa dar certo junto com a operação | O aviso não tem transação nem volta: se a reação falha, a operação já foi feita | Chame dentro da mesma transação, ou faça um caso de uso que orquestra os passos |
| Quem dispara precisa da resposta | O Observer avisa e segue em frente; retorno e veto não fazem parte dele | Chamada direta, ou Chain of Responsibility se for um "quem aprova?" |
| A ordem entre as reações é uma regra de negócio | A ordem de inscrição passa a ser a regra, e ninguém vê isso lendo o código | Escreva a sequência em um lugar só, em ordem, com nome |
| Os interessados estão em outros processos ou máquinas | O Observer vive na memória; se o processo cai, o aviso se perde | Fila ou broker (Pub/Sub), com entrega persistente e nova tentativa |
| Só quer ser chamado uma vez, quando algo termina | Assinar e cancelar é mais cerimônia do que o caso pede | Callback ou `Promise` |

<a id="sinais-de-abuso"></a>
### Sinais de que o Observer saiu do lugar

- **Tudo é um evento.** Quando cada chamada vira um aviso, ninguém consegue seguir o que acontece ao clicar em pagar. Evento é para o que acontece *depois*, não para esconder uma chamada comum.
- **A ordem importa em silêncio.** O observador B só funciona se o A rodou antes, e a única garantia é a ordem em que foram inscritos.
- **Um aviso dispara outro, que dispara outro.** Cascatas e ciclos: o observador altera o assunto, que avisa de novo, e o sistema entra em um laço que só aparece em produção.
- **Ninguém cancela.** Observadores que continuam na lista depois de terem saído de cena recebem avisos, mexem em telas que não existem e seguram memória.
- **Uma falha derruba os outros.** Se o laço de aviso não isola o erro, o terceiro observador nunca roda porque o segundo levantou uma exceção.

> **Perigo.** O sinal mais comum: um observador que muda o assunto que acabou de o avisar, ou que depende de outro ter rodado antes. Resposta e ordem são sinal de que aquilo era uma chamada direta com nome de evento. Escreva-a como chamada.

> **Nota.** Na dúvida, comece com a chamada direta. O segundo interessado, ou o primeiro que mora fora do seu módulo, é o momento de extrair a lista: a refatoração é pequena, porque as chamadas já estão juntas em um lugar.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Mediator | Põe um intermediário para decidir quem fala com quem, e pode ter regras próprias. No Observer não há coordenador: o assunto avisa e cada um decide por conta |
| [Chain of Responsibility](../chain-of-responsibility/explicacao.md) | O pedido passa de um em um até alguém tratar; o Observer entrega o aviso a *todos*, e ninguém "toma" o evento |
| [Command](../command/explicacao.md) | Pede que algo aconteça, a um destino, com os dados; o Observer informa que algo aconteceu, a quantos estiverem ouvindo |
| Publish/Subscribe (broker) | A mesma ideia, com um canal no meio e, em geral, entre processos, com entrega persistente. O Observer é em memória, e o assunto guarda a lista |

Regra prática: se o objeto diz "isto aconteceu" e não se importa com quem escuta, é Observer. Se diz "faça isto" a um destino, é Command.
