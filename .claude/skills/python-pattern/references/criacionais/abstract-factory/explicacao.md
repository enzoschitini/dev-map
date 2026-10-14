<!-- Gerado de pages/clean-code/criacionais/abstract-factory/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Abstract Factory — Explicação

*Clean Code / Design Pattern / Abstract Factory*

Como criar um conjunto de objetos que precisam combinar entre si, sem que o código principal escolha cada peça e sem o risco de misturar peças de conjuntos diferentes.

<a id="o-problema"></a>
## O problema

Um serviço recebe uploads: salva o arquivo e publica uma mensagem na fila para um worker processar. Em produção, o arquivo vai para o S3 e a mensagem vai para o SQS. Na máquina de quem desenvolve, o arquivo vai para uma pasta e a mensagem fica em uma fila em memória.

A saída mais curta é perguntar o ambiente na hora de criar cada peça:

**antes — cada peça pergunta o ambiente por conta própria**

```python
class ProcessadorDeUploads:
    def processar(self, nome, dados):
        if AMBIENTE == "prod":
            armazenamento = ArmazenamentoS3("uploads-prod")
        else:
            armazenamento = ArmazenamentoLocal("./tmp")
        caminho = armazenamento.salvar(nome, dados)

        if AMBIENTE == "prod":
            fila = FilaSqs("uploads")
        else:
            fila = FilaEmMemoria()
        fila.publicar({"arquivo": caminho})
```

O mesmo critério (`AMBIENTE`) decide duas coisas em sequência — e vai decidir de novo em cada arquivo que precisar de armazenamento ou de fila. As peças **precisam combinar**: o caminho que o armazenamento devolve é o que o worker vai ler. Basta um `if` esquecido, ou um ambiente novo (`"staging"`) tratado em um lugar e não no outro, para a fila de nuvem receber `./tmp/relatorio.pdf`. O worker não acha o arquivo, e nada falha até alguém olhar.

Três coisas aparecem: o critério fica espalhado; é possível montar uma combinação que nunca devia existir; e adicionar um ambiente é caçar cada `if`.

<a id="a-solucao"></a>
## A solução

Em vez de criar cada peça, o código recebe uma **fábrica** que cria todas elas — e que só sabe criar peças de uma família. Escolher o ambiente passa a ser escolher a fábrica, uma vez. São cinco papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Produto abstrato | A interface de cada tipo de peça | `Armazenamento`, `Fila` |
| Produto concreto | A peça de uma família específica | `ArmazenamentoS3`, `FilaSqs`, `ArmazenamentoLocal`, `FilaEmMemoria` |
| Fábrica abstrata | A interface que cria uma peça de cada tipo | `FabricaDeInfra` |
| Fábrica concreta | Cria as peças de uma família, e só dela | `InfraAws`, `InfraLocal` |
| Cliente | Usa a fábrica e as interfaces, sem conhecer nada concreto | `ProcessadorDeUploads` |

O ponto é que **a combinação passa a ser uma propriedade da fábrica**, não da atenção de quem escreve o código. `InfraAws` não tem como entregar um `ArmazenamentoLocal`. A mistura deixa de ser um bug possível e vira algo que o código não consegue expressar.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. os produtos abstratos: o que o cliente conhece
class Armazenamento(ABC):
    @abstractmethod
    def salvar(self, nome: str, dados: bytes) -> str: ...

class Fila(ABC):
    @abstractmethod
    def publicar(self, mensagem: dict) -> None: ...

# 2. a fábrica abstrata: um método por tipo de produto
class FabricaDeInfra(ABC):
    @abstractmethod
    def criar_armazenamento(self) -> Armazenamento: ...

    @abstractmethod
    def criar_fila(self) -> Fila: ...

# 3. as fábricas concretas: cada uma cria uma família inteira
class InfraAws(FabricaDeInfra):
    def criar_armazenamento(self):
        return ArmazenamentoS3("uploads-prod")

    def criar_fila(self):
        return FilaSqs("uploads")

class InfraLocal(FabricaDeInfra):
    def criar_armazenamento(self):
        return ArmazenamentoLocal("./tmp")

    def criar_fila(self):
        return FilaEmMemoria()

# 4. o cliente: só conhece a fábrica e as interfaces
class ProcessadorDeUploads:
    def __init__(self, infra: FabricaDeInfra):
        self._armazenamento = infra.criar_armazenamento()
        self._fila = infra.criar_fila()

    def processar(self, nome, dados):
        caminho = self._armazenamento.salvar(nome, dados)
        self._fila.publicar({"arquivo": caminho})

# a única decisão, no ponto de entrada da aplicação
infra = InfraAws() if AMBIENTE == "prod" else InfraLocal()
processador = ProcessadorDeUploads(infra)
```

> **Dica.** O teste ganha uma terceira família de graça: um `InfraDeTeste` cujo `criar_fila()` devolve uma fila que guarda o que recebeu e cujo `criar_armazenamento()` devolve um armazenamento que guarda o que gravou. O teste confere, com os dois à mão, que o caminho publicado é o que foi salvo.

> **Nota.** Em Python, uma "fábrica" às vezes é só uma função ou um módulo com duas funções. A interface formal vale quando existem mesmo duas famílias e você quer que o verificador de tipos garanta que as duas entregam as mesmas peças.

<a id="quando-usar"></a>
## Quando usar

A Abstract Factory vale quando as três coisas acontecem ao mesmo tempo: existem **várias famílias** de variantes (dois ambientes, dois temas, dois países), as peças de uma família **só funcionam bem juntas**, e o cliente precisa criar **várias peças** sem conhecer a família.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Peças escolhidas pelo mesmo critério, uma depois da outra | Dois ou três `if tema == …` ou `if AMBIENTE == …` em sequência, com a mesma condição | [Uso #1](uso.md#pecas-que-combinam) |
| Bugs de "peça de um conjunto com peça de outro" | Texto claro sobre fundo claro; caminho de disco em uma fila de nuvem; um ternário invertido em um dos componentes | [Uso #1](uso.md#pecas-que-combinam) |
| Objetos que precisam do mesmo contexto, criados em lugares separados | Cada repositório ou cliente chama `connect()` por conta própria, e as operações deviam estar na mesma transação | [Uso #2](uso.md#contexto-compartilhado) |
| O mesmo critério repetido em vários arquivos e funções | `if pais == "BR"` em `emitir()`, em `cancelar()`, em `reemitir()`… | [Uso #3](uso.md#familia-por-pedido) |
| Um ambiente novo exige mexer em muitos lugares | Uma busca por `"staging"` devolve 15 arquivos | [Uso #3](uso.md#familia-por-pedido) |

> **Dica.** O que os sinais têm em comum: o **mesmo critério** decide **vários objetos**. Se você tem um `if` só, é um problema de Factory Method; se tem o mesmo `if` várias vezes, é de Abstract Factory.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Você cria mais de um tipo de objeto com o mesmo critério?** Se é um tipo só, use Factory Method ou uma função.
2. **Misturar peças de variantes diferentes é um erro, ou só algo estranho?** Se misturar não faz mal, injete cada peça separada.
3. **Existem pelo menos duas famílias completas?** Se só existe uma, não há o que escolher: crie direto.
4. **A lista de peças é estável?** Se um produto novo aparece toda semana, cada um mexe na interface e em todas as fábricas — pese isso antes de seguir.

<a id="quando-nao-usar"></a>
## Quando não usar

A Abstract Factory troca simplicidade por uma garantia, e o preço tem um formato específico: **adicionar uma família é fácil, adicionar um produto é caro**. Um tipo novo de peça exige um método novo na interface e uma implementação em cada fábrica concreta. Com 3 produtos e 2 famílias, são 1 interface, 2 fábricas e 6 produtos concretos — antes de existir qualquer regra de negócio.

| Situação | Por que não | Faça isto |
|---|---|---|
| Há um tipo de produto só | Uma fábrica com um método é um Factory Method com mais um nível | Factory Method, ou uma função fábrica |
| Só existe uma família (hoje) | A interface abstrata não protege de nada, só adiciona um nível | Crie direto; extraia quando a segunda família aparecer |
| As peças não precisam combinar entre si | A garantia que o padrão vende não é necessária | Injete cada peça separada |
| Os produtos mudam com frequência | Cada produto novo altera a interface e toda fábrica concreta | Injete cada peça, ou agrupe em um objeto de configuração |
| A "fábrica" teria 20 métodos | Virou uma classe que sabe tudo, e toda família implementa tudo | Fábricas menores, uma por área |

<a id="sinais-de-abuso"></a>
### Sinais de que a Abstract Factory saiu do lugar

- **Uma fábrica com um único produto.** Não há família: é um Factory Method com um nome maior.
- **Uma família de uma única variante.** "Vai que criamos um segundo ambiente" é palpite. Enquanto existe uma só, a interface não protege nada.
- **A fábrica concreta decide com `if`.** Se `InfraAws.criar_fila()` escolhe entre duas filas, a família deixou de ser uma família.
- **O cliente pergunta qual fábrica recebeu.** Um `isinstance(infra, InfraAws)` no meio do fluxo mostra que a abstração não segura a diferença.
- **A interface cresce a cada feature.** Uma `FabricaDeTudo` acumula métodos que só uma família usa, e as outras devolvem `None` ou lançam `NotImplementedError`.

> **Perigo.** O sinal mais comum: uma fábrica abstrata com uma só fábrica concreta. O padrão acrescentou duas classes e nenhuma garantia.

> **Nota.** Na dúvida, reúna a criação em um lugar só (uma função `montar_infra()` no ponto de entrada) e passe as peças adiante. Quando a segunda família chegar, essa função já é a fábrica; basta extrair a interface.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Factory Method](../factory-method/explicacao.md) | Cria *um* produto e entrega a escolha à subclasse. A Abstract Factory cria uma *família* e costuma ser implementada com vários métodos fábrica |
| Builder | Monta *um* objeto complexo, passo a passo. A Abstract Factory entrega *vários* objetos, cada um de uma vez |
| Strategy | Troca *um* comportamento por composição. A Abstract Factory troca um *conjunto* de objetos coerentes |
| [Singleton](../singleton/explicacao.md) | Decide *quantos* objetos existem. Uma fábrica concreta costuma ser um Singleton (uma por ambiente), mas os problemas são diferentes |
| Contêiner de injeção de dependência | Resolve *quem recebe* cada objeto. Não garante que as peças combinem entre si; uma fábrica garante |

Regra prática: se a pergunta é "qual objeto criar", é Factory Method. Se é "qual conjunto de objetos criar para que combinem", é Abstract Factory.
