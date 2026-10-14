<!-- Gerado de pages/clean-code/comportamentais/command/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Command — Explicação

*Clean Code / Design Pattern / Command*

Como transformar um pedido de ação em um objeto, para poder guardá-lo, desfazê-lo, enfileirá-lo ou repeti-lo, em vez de apenas executá-lo na hora.

<a id="o-problema"></a>
## O problema

A tela do carrinho tem os botões Adicionar e Remover, e agora pediram um terceiro: **Desfazer**. Chamar `carrinho.adicionar(produto)` é fácil; voltar atrás exige lembrar o que foi feito, com quê e como se reverte.

A saída preguiçosa é anotar a última ação na própria tela e deixar o "desfazer" decidir o que fazer:

**antes — o desfazer adivinha o que aconteceu**

```python
class TelaCarrinho:
    def __init__(self, carrinho):
        self.carrinho = carrinho
        self._ultima = None              # (tipo, dado) da última ação

    def adicionar(self, produto):
        self.carrinho.adicionar(produto)
        self._ultima = ("adicionar", produto)

    def remover(self, produto):
        self.carrinho.remover(produto)
        self._ultima = ("remover", produto)

    def desfazer(self):
        tipo, produto = self._ultima
        if tipo == "adicionar":
            self.carrinho.remover(produto)
        elif tipo == "remover":
            self.carrinho.adicionar(produto)  # volta para o fim da lista, não para o lugar de onde saiu
```

Três coisas quebram daqui a pouco. Só dá para desfazer a última ação, porque há um único campo para lembrá-la. Cada ação nova (aplicar cupom, trocar quantidade) exige mexer em dois lugares: no método que a faz e no `if` que a desfaz. E o conhecimento de "como voltar" mora longe do conhecimento de "como fazer", então os dois divergem sem ninguém notar.

<a id="a-solucao"></a>
## A solução

Faça cada ação virar um objeto que guarda o que é preciso para executá-la **e** para desfazê-la. A tela deixa de saber o que cada botão faz: ela cria o comando e o entrega a quem executa e lembra. São cinco papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Comando | A interface: sabe executar e desfazer | `Comando` |
| Comando concreto | Um pedido específico, com os dados dele | `AdicionarItem`, `RemoverItem` |
| Receptor | Quem faz o trabalho de verdade | `Carrinho` |
| Invocador | Executa comandos e guarda o que foi feito | `Historico` |
| Cliente | Cria o comando certo e o entrega ao invocador | A tela do carrinho |

O ponto é que o pedido virou **uma coisa**: dá para guardá-la em uma lista, passá-la adiante e usá-la de novo mais tarde. O histórico é só uma pilha de comandos, e não precisa saber o que nenhum deles faz.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. o comando: um pedido que sabe se executar e se desfazer
class Comando(ABC):
    @abstractmethod
    def executar(self) -> None: ...

    @abstractmethod
    def desfazer(self) -> None: ...

# 2. os comandos concretos: o receptor e os dados do pedido
class AdicionarItem(Comando):
    def __init__(self, carrinho, produto):
        self._carrinho, self._produto = carrinho, produto

    def executar(self):
        self._carrinho.adicionar(self._produto)

    def desfazer(self):
        self._carrinho.remover(self._produto)

class RemoverItem(Comando):
    def __init__(self, carrinho, produto):
        self._carrinho, self._produto = carrinho, produto
        self._posicao = None

    def executar(self):
        self._posicao = self._carrinho.remover(self._produto)   # devolve de onde saiu

    def desfazer(self):
        self._carrinho.inserir(self._posicao, self._produto)

# 3. o invocador: executa e lembra, sem saber o que cada comando faz
class Historico:
    def __init__(self):
        self._feitos: list[Comando] = []

    def executar(self, comando: Comando):
        comando.executar()
        self._feitos.append(comando)

    def desfazer(self):
        if self._feitos:
            self._feitos.pop().desfazer()

# 4. o cliente: só cria comandos e os entrega
historico.executar(AdicionarItem(carrinho, camiseta))
historico.desfazer()
```

> **Dica.** Cada comando se testa sem tela nenhuma: execute, confira o carrinho, desfaça, confira de novo. E o `Historico` se testa com um comando falso que só conta chamadas. Uma ação nova é uma classe nova; nem a tela nem o histórico mudam.

<a id="quando-usar"></a>
## Quando usar

O Command vale quando três coisas acontecem ao mesmo tempo: o pedido precisa existir **separado** de quem o dispara e de quando ele roda; alguém precisa fazer **algo com o pedido** além de executá-lo (guardar, desfazer, enfileirar, repetir, mostrar o nome); e existem **várias ações** desse tipo, ou várias origens para a mesma.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Desfazer e refazer | Um campo como `_ultima_acao` e um `if tipo == …` dentro do `desfazer`; ou uma cópia da tela inteira a cada alteração | [Uso #1](uso.md#desfazer-refazer) |
| A ação precisa rodar depois, ou em outro processo | Um dicionário com `"tipo"` e `"dados"` despachado por `if`; ou uma `Thread` com meia dúzia de argumentos que se perde quando o servidor reinicia | [Uso #2](uso.md#fila-de-tarefas) |
| O histórico de "o que aconteceu" não pode ser reaplicado | Uma lista de textos de log que ninguém consegue transformar de volta na ação | [Uso #2](uso.md#fila-de-tarefas) |
| A mesma ação, vários gatilhos | `salvar(doc)` escrito no botão, no menu e no atalho; a regra de "desabilitado" repetida em cada um | [Uso #3](uso.md#varios-gatilhos) |
| Passos que valem por inteiro ou nada | Uma lista "o que já fiz" dentro de um `except`, para desfazer à mão na ordem inversa | [Uso #4](uso.md#lote-tudo-ou-nada) |

> **Dica.** O que os sinais têm em comum: alguém precisa tratar a ação como um *dado*, e hoje ela só existe como uma chamada que já aconteceu. Se nada precisa olhar a ação depois que ela roda, ela pode continuar sendo só uma chamada.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Você só precisa chamar a ação agora?** Chame o método. Não há pedido a representar.
2. **Precisa fazer algo com a ação além de executá-la?** Desfazer, guardar, enfileirar, repetir, mostrar o nome. Se não, basta passar uma função.
3. **Há mais de uma ação, ou mais de uma origem para a mesma?** Se é uma ação só, com um gatilho só, um método resolve.
4. **O pedido consegue levar tudo de que precisa?** Se ele depende de estado global ou de um objeto vivo que não viaja, resolva isso primeiro; senão o comando guardado já nasce quebrado.

<a id="quando-nao-usar"></a>
## Quando não usar

O custo do Command é uma classe a mais por ação, e, quando há desfazer, um segundo método que precisa ser mantido em sincronia com o primeiro. O `desfazer` é código que ninguém exercita no dia a dia, e por isso é onde os bugs ficam escondidos.

| Situação | Por que não | Faça isto |
|---|---|---|
| Só passar uma ação para ser chamada depois (um callback) | Uma classe com um método `executar` é uma função com cerimônia | Passe uma função ou um `lambda` |
| Desfazer significa "restaurar o objeto inteiro", e ele é pequeno | Escrever o inverso de cada ação é mais código, e mais chance de divergir, que copiar o estado | Guarde um snapshot (Memento) |
| A ação não tem volta e não precisa de fila (cobrar, enviar e-mail) | O `desfazer` não existe de verdade; sem ele, o objeto só repassa uma chamada | Chame direto. Se precisa de "compensação", ela é outro comando, com outro nome |
| Uma ação, um gatilho | Não há o que desacoplar | Um método |
| Escolher entre jeitos de fazer a mesma coisa | O que varia é o algoritmo, não o pedido | Strategy |

<a id="sinais-de-abuso"></a>
### Sinais de que o Command saiu do lugar

- **O comando só repassa.** Se o `executar` é uma linha que chama outro método, sem desfazer, sem fila e sem nome, ele é só uma camada.
- **O `desfazer` não desfaz.** Ele reverte o que está na memória e deixa de fora o e-mail enviado, o estoque reservado, a nota emitida. O usuário confia no botão e o botão mente.
- **O comando guarda o mundo.** Ele aponta para um objeto global ou para uma sessão em vez de guardar os dados do pedido. Serializado, ou executado de novo mais tarde, ele já não encontra o que precisava.
- **A regra de negócio mora no comando.** O comando deveria chamar o receptor; se ele calcula desconto, valida estoque e decide, virou um serviço com outro nome.
- **O histórico não tem fim.** Uma pilha de comandos sem limite guarda para sempre os objetos que cada um segura.

> **Perigo.** O sinal mais comum: o botão Desfazer restaura o carrinho, mas o cupom, a reserva de estoque e o e-mail continuam valendo. Um desfazer parcial é pior que nenhum, porque o sistema passa a ficar em um estado que ninguém pediu.

> **Nota.** Na dúvida, comece com uma função. O primeiro "desfazer" ou "enfileirar" é o sinal para extrair a classe: nesse ponto a refatoração é pequena, porque a ação já está concentrada em um lugar.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Chain of Responsibility](../chain-of-responsibility/explicacao.md) | Decide *quem* recebe o pedido; o Command é o próprio pedido. Combinam bem: o que viaja pela cadeia costuma ser um Command |
| Strategy | É um jeito intercambiável de fazer algo, usado na hora. O Command é uma ação concreta, com seus dados, que pode ser guardada e executada depois |
| Memento | Guarda o *estado* para voltar a ele; o Command guarda a *operação* e como revertê-la. Aparecem juntos quando o comando precisa lembrar o valor anterior |
| Observer | Avisa quem estiver interessado de que algo aconteceu; o Command pede que algo aconteça |

Regra prática: se o objeto significa "faça isto", com dados e talvez um inverso, é Command. Se significa "este é o jeito de fazer", é Strategy.
