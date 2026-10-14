<!-- Gerado de pages/clean-code/comportamentais/iterator/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Iterator — Explicação

*Clean Code / Design Pattern / Iterator*

Como percorrer uma coleção, ou uma fonte de dados, um elemento por vez, sem que quem percorre precise saber como ela guarda os elementos.

<a id="o-problema"></a>
## O problema

A loja organiza os produtos em categorias que contêm outras categorias: Roupas, dentro dela Camisetas, e dentro dela Camisetas Infantis. Três telas precisam passar por todas elas: o sitemap, a busca do menu e o relatório de estoque.

A saída preguiçosa é cada tela escrever a própria recursão, lendo direto o campo `filhos`:

**antes — cada chamador percorre a árvore à sua maneira**

```python
def listar_nomes(cat):
    nomes = [cat.nome]
    for filho in cat.filhos:
        nomes += listar_nomes(filho)
    return nomes

def contar_produtos(cat):
    total = len(cat.produtos)
    for filho in cat.filhos:
        total += contar_produtos(filho)
    return total

def achar(cat, nome):
    if cat.nome == nome:
        return cat
    for filho in cat.filhos:
        achado = achar(filho, nome)
        if achado:
            return achado
```

Três coisas quebram daqui a pouco. A estrutura vazou: no dia em que as categorias vierem do banco como uma tabela plana com `pai_id`, ou em que `filhos` passar a ser carregado sob demanda, toda função que lê `filhos` precisa mudar. Cada percurso novo é mais uma recursão copiada. E as funções que listam tudo montam a lista inteira antes de entregá-la, mesmo quando quem pediu só queria o primeiro resultado.

<a id="a-solucao"></a>
## A solução

Tire o percurso de quem consome e entregue-o à própria coleção. Ela passa a oferecer um objeto que sabe percorrê-la e responde a duas perguntas: "tem mais?" e "qual é o próximo?". Quem percorre usa só isso. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Iterável | A coleção: sabe criar um iterador sobre si mesma | `Categoria` |
| Iterador | Guarda a posição do percurso e entrega o próximo elemento | O gerador devolvido por `__iter__` |
| Estrutura interna | Como a coleção guarda os elementos; fica escondida | O campo `_filhos` |
| Cliente | Percorre pedindo "o próximo", sem saber de onde ele vem | Um `for`, um `sum`, um `next` |

O ponto é onde mora a **posição**. Ela é do iterador, não da coleção nem do cliente. Por isso dois percursos da mesma coleção, ao mesmo tempo, não se atrapalham, e por isso a coleção pode mudar a forma como guarda tudo sem que nenhum cliente perceba.

<a id="implementacao"></a>
## Implementação

```python
# 1. o iterável: a coleção sabe criar um iterador sobre si mesma
class Categoria:
    def __init__(self, nome, filhos=(), produtos=()):
        self.nome = nome
        self.produtos = list(produtos)
        self._filhos = list(filhos)      # 2. a estrutura interna: ninguém de fora lê isto

    # 3. o iterador: o gerador guarda a posição e entrega uma categoria por vez
    def __iter__(self):
        yield self
        for filho in self._filhos:
            yield from filho

# 4. o cliente: não sabe se é árvore, lista ou consulta ao banco
nomes = [c.nome for c in raiz]
total = sum(len(c.produtos) for c in raiz)
achada = next((c for c in raiz if c.nome == "Camisetas"), None)   # para na primeira
```

> **Dica.** Se as categorias passarem a vir de uma tabela plana com `pai_id`, só o `__iter__` muda. E qualquer função que receba "um iterável de categorias" aceita, nos testes, uma lista comum de três itens, sem montar a árvore.

<a id="quando-usar"></a>
## Quando usar

O Iterator vale quando três coisas acontecem ao mesmo tempo: existe uma coleção, ou uma fonte, com **estrutura própria**; **vários lugares** precisam percorrê-la; e eles **não devem depender** de como ela guarda os elementos, seja porque a forma pode mudar, seja porque ela é grande ou lenta demais para entregar de uma vez.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Cada chamador reimplementa o percurso | A mesma recursão, ou o mesmo `while pilha:`, copiada em várias funções, mudando só o que fazem com cada nó | [Uso #1](uso.md#varios-percursos) |
| O código de fora lê o campo interno | `cat.filhos`, `lista._itens` ou `resp["data"]` aparecendo fora da classe que os define | [Uso #1](uso.md#varios-percursos) |
| Mais de uma ordem de percurso | Funções chamadas `em_profundidade`, `em_largura`, `so_folhas`, cada uma com a própria lógica | [Uso #1](uso.md#varios-percursos) |
| Carrega tudo para usar só um pedaço | `readlines()` ou `list(...)` seguido de `[:10]`, `if` e `break` | [Uso #2](uso.md#fonte-grande) |
| Precisa parar e continuar depois | Um `offset` ou `posicao` passado à mão entre chamadas e salvo em algum lugar | [Uso #3](uso.md#retomar-de-onde-parou) |

> **Dica.** O que os sinais têm em comum: o chamador carrega junto uma peça do funcionamento interno da coleção, uma recursão, um cursor ou um `offset`. O iterador é o lugar para onde essa peça se muda.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **O que você percorre é uma lista, um dicionário ou um conjunto da linguagem?** Use o `for`: eles já são iteráveis.
2. **Mais de um lugar percorre isso?** Se só um, um laço local basta.
3. **Quem percorre precisa conhecer a estrutura, ou ela pode mudar?** Se a estrutura é pública e estável, deixe o laço ler direto.
4. **O percurso precisa ser sob demanda, ter mais de uma ordem ou ser retomado?** Se sim, é Iterator. Se é só "todos os elementos, de uma vez, em uma ordem", devolva uma lista.

<a id="quando-nao-usar"></a>
## Quando não usar

Em linguagens com geradores, o Iterator custa quase nada para escrever, e por isso o custo real passa despercebido. Ele aparece na hora de depurar. O iterador é de **uso único**: percorrê-lo uma segunda vez não dá nada. O trabalho acontece no meio do laço de quem consome, então erros e I/O surgem ali, longe de onde o iterador foi criado. E uma coleção que muda durante o percurso dá resultados que ninguém previu.

| Situação | Por que não | Faça isto |
|---|---|---|
| A coleção é uma lista, um dicionário ou um conjunto | Eles já são iteráveis; uma classe para isso só acrescenta cerimônia | Use o `for` direto |
| Filtrar ou transformar uma coleção pequena | Um gerador esconde, com preguiça, o que uma linha resolve | Uma compreensão de lista |
| Você precisa de acesso por posição, ordenar ou saber o tamanho | O iterador é sequencial e de passagem única | Devolva uma lista (ou um objeto com `__len__` e `__getitem__`) |
| A coleção é pequena e o consumidor percorre mais de uma vez | O iterador esvazia depois da primeira passagem | Devolva uma lista |
| A coleção muda enquanto é percorrida | Elementos podem ser pulados ou repetidos, e na maioria das linguagens isso nem dá erro | Percorra uma cópia, ou junte as mudanças e aplique depois |

<a id="sinais-de-abuso"></a>
### Sinais de que o Iterator saiu do lugar

- **O iterador faz efeito colateral.** Gravar, enviar ou apagar a cada passo deixa o laço com um trabalho que ninguém vê.
- **Um iterador de uso único é tratado como coleção.** A função percorre duas vezes, e a segunda vem vazia, sem erro.
- **Uma classe onde um gerador bastava.** Um `__next__` escrito à mão, com estado manual, para algo que um `yield` resolve em três linhas.
- **Tudo vira lista logo na chegada.** Se o consumidor faz `list(it)` na primeira linha, a preguiça foi paga e não usada.
- **O resultado muda a cada percurso.** Um iterador que depende da hora, de estado global ou de uma fonte que muda sob ele torna a depuração um jogo de adivinhação.

> **Perigo.** O sinal mais comum: o iterador cobra, envia ou apaga a cada `next()`. Um `list(...)` para inspecionar, ou o depurador da IDE mostrando o valor, dispara o efeito sem ninguém ter pedido.

> **Nota.** Na dúvida, devolva uma lista. Trocar um `return lista` por `yield` é uma mudança de uma linha, e os consumidores que só usam `for` nem percebem. Faça a troca quando a lista ficar grande, lenta ou impossível de montar.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Composite](../../estruturais/composite/explicacao.md) | É a estrutura em árvore: folhas e grupos tratados do mesmo jeito. O Iterator é a forma de percorrê-la, e os dois aparecem juntos com frequência |
| Visitor | Aplica uma operação a cada nó, e conhece os tipos dos nós. O Iterator só entrega os elementos, e quem o usa decide o que fazer com cada um |
| Observer | A fonte *empurra* cada novidade para quem escuta, no ritmo dela. No Iterator, o cliente *puxa* o próximo, no ritmo dele |
| [Adapter](../../estruturais/adapter/explicacao.md) | Converte uma interface em outra. Um iterador sobre uma API paginada é um Adapter cujo alvo é o protocolo de iteração da linguagem |

Regra prática: se o cliente pede o próximo elemento, quando quer, é Iterator. Se a fonte avisa o cliente quando há um, é Observer.
