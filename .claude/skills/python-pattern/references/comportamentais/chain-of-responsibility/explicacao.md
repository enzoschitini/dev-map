<!-- Gerado de pages/clean-code/comportamentais/chain-of-responsibility/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Chain of Responsibility — Explicação

*Clean Code / Design Pattern / Chain of Responsibility*

Como deixar um pedido percorrer uma sequência de candidatos até alguém tratá-lo, sem que quem pede precise saber quem são eles nem quantos existem.

<a id="o-problema"></a>
## O problema

Na loja, o atendente pode dar desconto de até 5%. Acima disso, só o supervisor, até 15%. Acima disso, só o gerente, até 30%. Mais que isso, ninguém: o pedido é recusado.

A saída preguiçosa é uma escada de `if` que sabe todos os níveis:

**antes — uma escada que conhece todos os níveis**

```python
def aprovar_desconto(pedido, percentual):
    if percentual <= 5:
        return Aprovacao("atendente", percentual)
    elif percentual <= 15:
        notificar("supervisor", pedido)
        return Aprovacao("supervisor", percentual)
    elif percentual <= 30:
        notificar("gerente", pedido)
        return Aprovacao("gerente", percentual)
    else:
        raise DescontoRecusado(percentual)
```

Não é um código ruim, e é isso que o torna perigoso: funciona. O problema aparece quando a regra muda. Criar o cargo de coordenador, entre o atendente e o supervisor, significa abrir a escada no meio e torcer para não trocar um `<=` por `<`. A tela que mostra "quem precisa aprovar este desconto" precisa repetir os mesmos limites, e as duas cópias começam a divergir. E todo cargo novo é um motivo a mais para esta função mudar, o que o Open/Closed pede para evitar.

<a id="a-solucao"></a>
## A solução

Transforme cada nível em um elo que sabe uma coisa só: se o pedido é dele e, se não for, a quem entregar em seguida. Quem pede fala com o primeiro elo e espera. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Pedido | O que viaja pela cadeia | O `percentual` solicitado |
| Elo | Decide se trata; se não, passa ao próximo | `Alcada` |
| Fim da cadeia | O último elo, sem próximo: precisa tratar ou falhar de forma explícita | O gerente, que recusa o que passa de 30% |
| Cliente | Monta a cadeia e entrega o pedido ao primeiro elo | `cadeia.aprovar(12)` |

O ponto é quem sabe o quê. Quem pede conhece só o primeiro elo; cada elo conhece só o próximo; e a pergunta "é comigo?" mora no elo, e não numa escada central. Acrescentar um nível é encaixar um elo na montagem, sem mexer em nenhum dos outros.

<a id="implementacao"></a>
## Implementação

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Aprovacao:
    quem: str
    percentual: float

# 1. o elo: decide se é com ele e, se não for, passa adiante
@dataclass
class Alcada:
    cargo: str
    limite: float                       # percentual máximo que este cargo aprova
    proximo: "Alcada | None" = None

    def aprovar(self, percentual: float) -> Aprovacao:
        if percentual <= self.limite:
            return Aprovacao(quem=self.cargo, percentual=percentual)
        if self.proximo is None:        # 2. o fim da cadeia: ninguém aprova, e isso é dito
            raise DescontoRecusado(percentual)
        return self.proximo.aprovar(percentual)

# 3. o cliente monta a cadeia uma vez e entrega ao primeiro elo
cadeia = Alcada("atendente", 5,
    Alcada("supervisor", 15,
        Alcada("gerente", 30)))

cadeia.aprovar(12)   # Aprovacao(quem="supervisor", percentual=12)
cadeia.aprovar(45)   # DescontoRecusado
```

> **Dica.** Cada elo se testa sozinho: `Alcada("teste", 10)` sem próximo aprova até 10 e recusa o resto, sem precisar dos outros níveis. E o coordenador do exemplo acima vira uma linha na montagem, sem tocar em `Alcada`.

<a id="quando-usar"></a>
## Quando usar

O Chain of Responsibility vale quando três coisas acontecem ao mesmo tempo: **mais de um** objeto pode tratar o pedido, **qual deles trata** só se sabe na hora, e quem pede **não deve conhecer** os candidatos, ou a lista e a ordem deles mudam.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Uma escada decide quem trata o pedido | `if valor <= X` … `elif valor <= Y` …, ou a mesma escada copiada em dois lugares | [Uso #1](uso.md#alcada-por-valor) |
| As mesmas verificações no começo de cada handler | Autenticação, limite de requisições e validação repetidos no topo de toda rota, com pequenas diferenças | [Uso #2](uso.md#middleware) |
| O evento deve ser tratado por quem estiver mais perto | `closest()`, `parent`, ou um `if` global que testa de qual componente o evento veio | [Uso #3](uso.md#evento-que-sobe) |
| Fontes com custos diferentes, tentadas em ordem | `if x is None: x = outra_fonte()` aninhado, ou `try` dentro de `except` | [Uso #4](uso.md#fontes-em-camadas) |
| A ordem ou o conjunto de candidatos muda por ambiente | Flags como `if settings.USA_CACHE` espalhadas pelo caminho da chamada | [Uso #4](uso.md#fontes-em-camadas) |

> **Dica.** Repare no que os sinais têm em comum: quem pede está sabendo demais sobre quem responde. A escada, a repetição no topo e o `if` global são o mesmo conhecimento, escrito no lugar errado.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Mais de um objeto pode tratar o pedido?** Se só um pode, chame esse direto.
2. **Quem trata depende de algo que só se sabe na hora?** Se você sabe a chave de antemão (um tipo, um nome), escolha por ela com um dicionário.
3. **Os candidatos ou a ordem mudam, ou a escada aparece em mais de um lugar?** Se a lista é fixa, pequena e vive em um lugar só, um `if/elif` basta.
4. **Só o primeiro que pode deve tratar, ou qualquer um pode barrar?** Se sim, é Chain of Responsibility. Se todos devem receber o pedido, é Observer.

<a id="quando-nao-usar"></a>
## Quando não usar

O custo do Chain of Responsibility é a leitura. O fluxo deixa de estar em um lugar: para saber quem trata um pedido, é preciso achar onde a cadeia é montada e seguir os elos na ordem. Na depuração, a pilha de chamadas fica um degrau mais longa por elo. E existe um risco que a escada não tem: o pedido pode atravessar a cadeia inteira e ninguém tratá-lo.

| Situação | Por que não | Faça isto |
|---|---|---|
| Dois ou três casos fixos, em um lugar só | A escada inteira cabe na tela, e a cadeia só acrescenta classes e montagem | Escreva o `if/elif` |
| Você já sabe qual objeto trata | Percorrer a cadeia procurando algo que você conhece é trabalho à toa | Um dicionário de chave para tratador, ou Strategy |
| Todos os interessados precisam ser avisados | A cadeia para no primeiro que trata; o aviso não chega aos demais | Observer |
| Etapas fixas, cada uma transformando o dado da anterior | Não há "é comigo?", só uma sequência; o pedido nunca para no meio | Uma lista de funções chamadas em ordem |
| Um pedido que não pode ficar sem resposta, e não há fim definido | O silêncio no fim da cadeia vira um bug que ninguém vê | Um último elo que trata o que sobrou, ou que falha com a mensagem clara |

<a id="sinais-de-abuso"></a>
### Sinais de que a cadeia saiu do lugar

- **Ninguém sabe a ordem.** Se para entender o fluxo é preciso procurar em cinco arquivos onde os elos foram encaixados, a montagem deveria estar em um lugar só.
- **Um elo assume que outro já rodou.** Quando o elo C só funciona porque o A preencheu algo, a ordem virou parte do contrato sem ninguém ter escrito isso. Ou o dado viaja no pedido, ou os dois são um elo só.
- **O elo escolhe o próximo.** Um elo que chama "o elo de pagamento" por nome deixou de ser parte de uma cadeia: virou um grafo, com todos os problemas de um.
- **O pedido some.** Nenhuma resposta, nenhum erro, nenhum log: o pedido percorreu tudo e ninguém o tratou.
- **Uma cadeia de dois elos "por flexibilidade".** Dois casos fixos são um `if` com `else`. A flexibilidade que ninguém pediu tem o mesmo custo da que alguém pediu.

> **Perigo.** O sinal mais comum: o último elo retorna `None` e o chamador segue em frente como se algo tivesse sido feito. Toda cadeia precisa de um fim que trate ou que grite.

> **Nota.** Na dúvida, comece com o `if/elif`. Extrair a cadeia é uma refatoração pequena quando a escada aparece pela segunda vez ou quando o quarto nível chega. Montar a cadeia antes disso é pagar o custo de leitura por uma flexibilidade que talvez nunca seja usada.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Decorator | Também encadeia objetos com a mesma interface, mas todos participam e cada um acrescenta algo; na cadeia, cada elo decide se trata e pode encerrar o caminho |
| Observer | Todos os interessados recebem o aviso, e nenhum deles impede os outros; na cadeia, o pedido tem um destino só |
| Strategy | Você escolhe um algoritmo de antemão e o chama; na cadeia, você não sabe qual elo vai tratar |
| Command | Transforma o pedido em um objeto, para guardar, desfazer ou enfileirar; a cadeia decide quem recebe o pedido. Os dois combinam: o pedido que viaja pela cadeia costuma ser um Command |

Regra prática: se o pedido percorre os candidatos e o primeiro que pode tratar encerra o caminho, é Chain of Responsibility. Se todos recebem, é Observer.
