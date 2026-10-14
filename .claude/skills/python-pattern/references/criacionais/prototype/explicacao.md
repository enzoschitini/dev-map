<!-- Gerado de pages/clean-code/criacionais/prototype/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Prototype — Explicação

*Clean Code / Design Pattern / Prototype*

Como criar um objeto novo copiando um que já existe, deixando a regra da cópia dentro do próprio objeto — para quem copia não precisar conhecer a classe nem os campos.

<a id="o-problema"></a>
## O problema

A ferramenta de marketing permite **duplicar uma campanha**: o usuário parte de uma campanha pronta (assunto, segmentos, anexos) e muda o que precisa. Existem campanhas de e-mail e de SMS, e o botão "Duplicar" aparece nas duas telas.

A saída mais curta é uma função que cria uma campanha nova, copiando os campos um a um:

**antes — a função de duplicar reconstrói o objeto à mão**

```python
class Campanha:
    def __init__(self, nome, assunto, segmentos, anexos):
        self.id = None
        self.nome = nome
        self.assunto = assunto
        self.segmentos = segmentos
        self.anexos = anexos

def duplicar(original):
    return Campanha(
        nome=original.nome + " (cópia)",
        assunto=original.assunto,
        segmentos=original.segmentos,    # a mesma lista do original
        anexos=original.anexos,          # idem
    )

# e a CampanhaDeSms, que tem numero_remetente?
# duplicar() devolve uma Campanha comum e o número se perde
```

Três coisas quebram, e nenhuma delas dá erro. As listas são **compartilhadas**: quem adiciona um segmento na cópia altera a campanha original, que já estava agendada. Quando alguém acrescenta um campo (`remetente`), a função de duplicar não o conhece, e a cópia sai sem ele. E a função só conhece `Campanha`: para `CampanhaDeSms` é preciso um `isinstance`, e para cada subclasse futura, outro.

<a id="a-solucao"></a>
## A solução

Em vez de uma função de fora que conhece os campos, faça cada objeto saber **copiar a si mesmo**. Quem quer uma cópia só pede `clonar()` e recebe um objeto independente, do mesmo tipo, sem saber qual é. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Protótipo | A interface (ou classe base) que declara a operação de copiar | `Campanha` |
| Protótipo concreto | Uma classe que implementa a cópia, ou herda a regra | `CampanhaDeEmail`, `CampanhaDeSms` |
| `clonar()` | A regra da cópia: o que copiar a fundo, o que zerar | Um método, em um lugar só |
| Cliente | Quem precisa de uma cópia e não conhece a classe | `duplicar()` |

O ponto é **quem sabe como copiar**. O objeto conhece os próprios campos, inclusive os que forem acrescentados depois, então a regra "o que é cópia, o que é compartilhado e o que é zerado" mora em um lugar. O cliente só depende da operação.

<a id="implementacao"></a>
## Implementação

```python
import copy

# 1. o protótipo: qualquer campanha sabe produzir uma cópia independente
class Campanha:
    def __init__(self, nome, assunto, segmentos, anexos):
        self.id = None
        self.nome = nome
        self.assunto = assunto
        self.segmentos = segmentos
        self.anexos = anexos

    # 2. a regra da cópia, escrita uma vez
    def clonar(self):
        copia = copy.deepcopy(self)   # listas e objetos internos, a fundo
        copia.id = None                  # a cópia é outra campanha
        copia.nome = f"{self.nome} (cópia)"
        return copia

# 3. o protótipo concreto: herda a regra; o campo novo vem junto
class CampanhaDeSms(Campanha):
    def __init__(self, nome, assunto, segmentos, anexos, numero_remetente):
        super().__init__(nome, assunto, segmentos, anexos)
        self.numero_remetente = numero_remetente

# 4. o cliente: não sabe qual subclasse tem nas mãos
def duplicar(campanha):
    return campanha.clonar()
```

> **Dica.** O teste é direto: clone uma campanha, adicione um segmento na cópia e confira que o original continua com a lista antiga. Um teste só cobre o erro mais comum do padrão (a cópia rasa) para todas as subclasses.

> **Nota.** Em TypeScript, `structuredClone(obj)` faz a cópia profunda, mas devolve um objeto **simples**: sem protótipo, sem métodos, e `instanceof` deixa de funcionar. Por isso o exemplo reconstrói a instância. Em Python, `copy.deepcopy` preserva a classe, e é por isso que basta chamá-lo.

<a id="quando-usar"></a>
## Quando usar

O Prototype vale quando as três coisas acontecem ao mesmo tempo: você precisa de uma **cópia independente** de um objeto que já existe, o **cliente não deveria conhecer** a classe nem os campos, e **copiar é melhor** que construir de novo — mais barato, mais fiel, ou a única coisa possível.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Uma função de duplicar que reconstrói campo a campo | `Campanha(nome=o.nome, assunto=o.assunto, …)`, com a lista de campos copiada à mão | — |
| Cópia que depende do tipo | `if isinstance(x, A): return A(…)` só para duplicar | — |
| A mesma montagem cara, repetida com o mesmo resultado | A mesma consulta ou o mesmo `parse()` a cada objeto novo; só o final muda | [Uso #1](uso.md#custo-de-criacao) |
| Uma subclasse para cada variante de configuração | Classes que só diferem em valores atribuídos no construtor | [Uso #2](uso.md#modelos-do-usuario) |
| Guardar o "estado anterior" campo a campo | `self._anterior = {"tema": c.tema, …}`, para poder cancelar a edição | [Uso #3](uso.md#rascunho-e-desfazer) |
| "Mexi na cópia e mudou o original" | Uma lista, um dicionário ou um objeto interno compartilhado entre os dois | — |

> **Dica.** O que os sinais têm em comum: alguém **fora do objeto** está fazendo o trabalho de copiá-lo. O Prototype leva esse trabalho para dentro, onde a lista de campos está.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Você precisa de uma cópia, ou de um objeto novo com valores novos?** Se é novo, é um construtor.
2. **O objeto é simples, com poucos campos de valor?** Então `dataclasses.replace(obj, nome="…")` (ou o spread `{ ...obj, nome }`) basta.
3. **O objeto guarda algo que não pode ser copiado** — conexão, arquivo, trava, thread? Então a cópia não faz sentido: crie um novo por uma fábrica.
4. **Existe uma regra do que a cópia leva, do que compartilha e do que zera?** Se sim, ela precisa morar em um método. É o Prototype.

<a id="quando-nao-usar"></a>
## Quando não usar

Copiar um objeto parece trivial e não é. O Prototype paga com **uma decisão por campo**: copia a fundo ou compartilha? Zera ou mantém? Um campo novo reabre a pergunta, e o erro é silencioso: a cópia "funciona" e divide uma lista com o original. A cópia profunda também carrega tudo o que estiver ligado ao objeto, inclusive o que ninguém lembrou.

| Situação | Por que não | Faça isto |
|---|---|---|
| O objeto é simples e de valores (poucos campos, sem listas) | Uma classe com `clonar()` para isso é cerimônia | `dataclasses.replace`, ou o spread |
| O objeto imutável pode ser compartilhado | Se ninguém altera, não é preciso copiar | Compartilhe a mesma instância |
| O objeto guarda conexão, arquivo, trava ou thread | A cópia profunda duplica o recurso, ou falha | Uma fábrica que crie o recurso novo |
| O objeto está ligado a um grafo grande (cache, ORM, referências cruzadas) | `deepcopy` leva o grafo todo, e duplica o que devia ser compartilhado | Copiar só os dados (um DTO) e remontar o resto |
| Você quer "outro do mesmo tipo", sem estado | Não há o que copiar | Factory Method, ou o construtor |

<a id="sinais-de-abuso"></a>
### Sinais de que o Prototype saiu do lugar

- **O `clonar()` faz cópia rasa sem avisar.** Aparece como "o clone funciona", até alguém mexer em uma lista da cópia.
- **Um `deepcopy` cego em um objeto com ligações para o mundo.** Se ele tem uma referência para o banco, para um cache ou para o objeto pai, a cópia leva tudo isso junto.
- **O clone mantém a identidade.** Duas campanhas com o mesmo `id` (ou a mesma data de criação) são um bug esperando para acontecer.
- **O protótipo guardado é alterado por quem o usa.** Em um catálogo de modelos, se o modelo é entregue sem cópia, a próxima pessoa clona um modelo "sujo".
- **Copiar para "ganhar desempenho" sem medir.** Se construir do zero é barato, o clone só acrescentou uma decisão.

> **Perigo.** O sinal mais comum: clonar sem decidir o que a cópia compartilha com o original. Os testes passam, e em produção alguém edita a cópia e a campanha original muda.

> **Nota.** Na dúvida, use `copy.deepcopy` ou `dataclasses.replace` direto no ponto de uso. Um método `clonar()` só se justifica quando a *regra* (o que zerar, o que compartilhar) precisa viver em um lugar e ser seguida por todos.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Factory Method](../factory-method/explicacao.md) | Cria um objeto *do zero*, pela classe que a subclasse escolhe. O Prototype parte de um objeto pronto e copia |
| [Abstract Factory](../abstract-factory/explicacao.md) | Entrega uma família de objetos. Uma fábrica pode ser implementada com protótipos — ela guarda um de cada e clona, em vez de instanciar |
| [Builder](../builder/explicacao.md) | Monta um objeto complexo *por etapas*, a cada vez. O Prototype parte de um objeto já montado |
| Memento | Guarda o estado para restaurá-lo depois, e a cópia não é usada como objeto vivo. O Prototype produz um objeto novo e independente |

Regra prática: se o objeto novo parte de um molde que já existe, é Prototype. Se parte de uma classe, é uma fábrica.
