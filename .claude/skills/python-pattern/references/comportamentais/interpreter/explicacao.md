<!-- Gerado de pages/clean-code/comportamentais/interpreter/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Interpreter — Explicação

*Clean Code / Design Pattern / Interpreter*

Como representar regras que mudam com frequência, ou que vêm de fora do código, como uma estrutura que se avalia sozinha, em vez de escrever uma função nova a cada variação.

<a id="o-problema"></a>
## O problema

O marketing muda a regra de frete grátis toda semana. Em março era "pedidos a partir de R$ 200, para clientes VIP ou com o cupom FRETE". Em abril, "a partir de R$ 150, para SP e RJ". Para o Dia das Mães, outra combinação.

A saída preguiçosa é uma função por campanha, escolhida por um nome:

**antes — cada campanha vira um trecho de código**

```python
def frete_gratis(pedido, campanha):
    if campanha == "marco":
        return pedido["total"] >= 200 and (pedido["vip"] or pedido["cupom"] == "FRETE")
    if campanha == "abril":
        return pedido["total"] >= 150 and pedido["uf"] in ("SP", "RJ")
    if campanha == "dia-das-maes":
        return (pedido["total"] >= 100 and pedido["categoria"] == "presentes") or pedido["vip"]
    return False
```

Cada campanha nova é um pull request e um deploy, para mudar uma regra que não tem nada de técnico. O marketing não consegue conferir o que está valendo sem pedir a um programador que leia o código. E a regra não pode morar junto da campanha, no banco, porque ela é código: ninguém salva um `if` em uma tabela.

<a id="a-solucao"></a>
## A solução

Descreva as regras possíveis como uma pequena linguagem: poucas peças que se combinam. Cada peça vira uma classe que sabe se avaliar. Uma regra concreta passa a ser uma **árvore** dessas peças, e avaliá-la é pedir à raiz que se avalie. Em palavras, a gramática do exemplo é:

`condição := comparação | E(condição, …) | OU(condição, …) | NÃO(condição)`

| Papel | Quem é | No exemplo |
|---|---|---|
| Expressão | A interface: toda peça sabe se avaliar | `Condicao` |
| Terminal | Uma peça que não contém outras: o fim de cada ramo | `Comparacao` |
| Não terminal | Uma peça feita de outras peças | `E`, `Ou`, `Nao` |
| Contexto | Os dados contra os quais a regra é avaliada | O pedido |
| Cliente | Monta (ou recebe) a árvore e a avalia | A tela de checkout |

O ponto é que o **"o quê"** deixou de ser código. A regra de março e a de abril usam as mesmas classes e só diferem na forma da árvore. Uma regra nova não exige uma classe nova: só uma árvore nova, e árvore pode vir de um formulário, de um arquivo ou do banco.

<a id="implementacao"></a>
## Implementação

```python
import operator
from abc import ABC, abstractmethod

# 1. a expressão: toda regra, simples ou composta, sabe se avaliar
class Condicao(ABC):
    @abstractmethod
    def avaliar(self, pedido: dict) -> bool: ...

# 2. o terminal: a menor regra, que olha um campo do pedido
class Comparacao(Condicao):
    _OPERADORES = {
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "in": lambda atual, valor: atual in valor,
    }

    def __init__(self, campo, op, valor):
        self._campo, self._op, self._valor = campo, op, valor

    def avaliar(self, pedido):
        return self._OPERADORES[self._op](pedido[self._campo], self._valor)

# 3. os não terminais: combinam outras condições
class E(Condicao):
    def __init__(self, *partes):
        self._partes = partes

    def avaliar(self, pedido):
        return all(p.avaliar(pedido) for p in self._partes)

class Ou(Condicao):
    def __init__(self, *partes):
        self._partes = partes

    def avaliar(self, pedido):
        return any(p.avaliar(pedido) for p in self._partes)

class Nao(Condicao):
    def __init__(self, parte):
        self._parte = parte

    def avaliar(self, pedido):
        return not self._parte.avaliar(pedido)

# 4. o cliente: a regra de março, montada como árvore
marco = E(
    Comparacao("total", ">=", 200),
    Ou(Comparacao("vip", "==", True), Comparacao("cupom", "==", "FRETE")),
)

marco.avaliar({"total": 250, "vip": False, "cupom": "FRETE"})   # True
```

> **Dica.** Cada peça se testa sozinha, com um pedido de uma linha. E as regras passam a ser dados: duas campanhas diferentes são duas árvores, comparáveis, guardáveis e testáveis com os mesmos pedidos, sem tocar nas classes.

<a id="quando-usar"></a>
## Quando usar

O Interpreter vale quando três coisas acontecem ao mesmo tempo: as regras formam uma **família pequena** de peças que se combinam e se aninham; as combinações **vêm de fora do código** (de uma pessoa, de uma configuração, do banco) ou mudam mais rápido que os deploys; e a mesma regra precisa ser **avaliada, ou lida de outro jeito, muitas vezes**.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Cada variação da regra é uma função nova | `if campanha == "marco"` … `if campanha == "abril"` …, e o pull request é só para mudar um número | [Uso #1](uso.md#regra-configuravel) |
| A regra é guardada como texto e avaliada na execução | `eval(regra)`, ou uma cadeia de `if` sobre um dicionário aninhado, lendo uma coluna de configuração | [Uso #1](uso.md#regra-configuravel) |
| O usuário digita um filtro ou uma fórmula | `texto.split(" E ")` e `split("=")`; parênteses e `OU` "ainda não suportados" | [Uso #2](uso.md#filtro-digitado) |
| A mesma regra existe em duas implementações | Uma função que filtra em memória e outra que monta um `WHERE`, escritas por pessoas diferentes | [Uso #3](uso.md#varias-leituras) |
| A regra precisa ser mostrada em palavras | Uma função que monta o texto "Frete grátis para…" paralela à função que decide | [Uso #3](uso.md#varias-leituras) |

> **Dica.** O que os sinais têm em comum: a regra é um *dado* disfarçado de código. Quando o "o quê" precisa mudar sem mexer no "como", o "o quê" é que deveria ser uma estrutura, e o código só sabe percorrê-la.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **A regra muda mais rápido que o deploy, ou quem a muda não programa?** Se só programadores mudam e o deploy é aceitável, escreva uma função.
2. **Você consegue listar todas as formas que a regra pode tomar?** Se são poucas e fixas, um `enum` com um `if` resolve.
3. **As peças se aninham (um E dentro de um OU dentro de um NÃO)?** Se é só uma lista de condições juntas por E, uma lista de funções com `all()` basta.
4. **A linguagem cabe em meia dúzia de construções?** Se já pede variáveis, laços ou funções, você está construindo uma linguagem de programação. Use uma que já existe.

<a id="quando-nao-usar"></a>
## Quando não usar

O Interpreter é o pattern mais raro do catálogo, e por um bom motivo. O custo é uma classe por construção da gramática, mais a parte que o padrão não cobre e que costuma ser a mais cara: o **parser**, quando a regra chega como texto. Somam-se a isso a documentação da linguagem, as mensagens de erro e o versionamento das regras antigas. Você passa a manter uma pequena linguagem, e linguagens crescem.

| Situação | Por que não | Faça isto |
|---|---|---|
| Poucas regras fixas, que só programadores mudam | O deploy já é o mecanismo de mudança, e a árvore só acrescentaria classes | Escreva as funções |
| A linguagem pede variáveis, laços ou funções | Você está desenhando uma linguagem de programação, com todos os problemas de uma | Use uma existente: SQL, CEL, JSONLogic, ou embuta uma linguagem de script |
| Deixar o usuário escrever "um pouco de Python" ou JavaScript | `eval` executa o que o usuário digitar, no seu servidor | Uma gramática fechada (o que o pattern dá) ou um interpretador isolado em sandbox |
| Só uma lista de condições combinadas por E | Não há aninhamento, então não há árvore | Uma lista de predicados e `all(...)` |
| Escolher um jeito de fazer uma coisa | O que varia é o algoritmo, e não uma sentença para avaliar | Strategy |

<a id="sinais-de-abuso"></a>
### Sinais de que o Interpreter saiu do lugar

- **A gramática cresce toda semana.** Uma construção nova a cada pedido do marketing é o começo de uma linguagem mal projetada, sem ninguém responsável por ela.
- **O `eval` voltou pela porta dos fundos.** Uma classe chamada `Expressao` que, por dentro, só chama `eval` sobre o texto não é o pattern: é a falha de segurança com outro nome.
- **Só programadores escrevem as regras.** Se o objetivo era tirar o programador do caminho e ele continua necessário, a linguagem não cumpriu o que prometeu.
- **O erro aparece na hora de avaliar.** A regra é validada quando alguém a usa em um pedido real, e não quando é salva.
- **As regras não têm versão nem teste.** Ninguém sabe o que a regra valia ontem, nem se a mudança de hoje quebrou os casos de sempre.

> **Perigo.** O sinal mais comum: avaliar o texto da regra com `eval`, "porque é mais rápido que montar a árvore". Quem pode salvar a regra passa a poder executar qualquer código no servidor.

> **Nota.** Na dúvida, comece com funções. A árvore se justifica quando a primeira regra vinda de fora do código chega, porque nesse ponto ela já é um dado. Antes disso, é uma gramática para um problema que talvez nunca apareça.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Composite | É a estrutura: folhas e grupos tratados do mesmo jeito. A árvore do Interpreter é um Composite, mas com uma gramática por trás e um significado: cada nó responde "qual é o seu valor?" |
| Visitor | Tira a operação de dentro dos nós, para somar novas leituras da árvore sem mexer nas classes. É a saída quando o Interpreter acumula muitas operações por nó |
| Strategy | Escolhe um algoritmo e o executa; o Interpreter avalia uma sentença montada com peças que se combinam |
| [Command](../command/explicacao.md) | Representa uma ação a executar, que pode ser desfeita ou enfileirada; o Interpreter avalia uma expressão e devolve um valor |

Regra prática: se você tem uma árvore de objetos em que cada nó sabe responder "qual é o seu valor?", é Interpreter. Se só importa agrupar e tratar igual, é Composite.
