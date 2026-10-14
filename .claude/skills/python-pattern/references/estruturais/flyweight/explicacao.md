<!-- Gerado de pages/clean-code/estruturais/flyweight/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Flyweight — Explicação

*Clean Code / Design Pattern / Flyweight*

Como manter centenas de milhares de objetos na memória sem repetir, em cada um, o que é igual para todos do mesmo tipo.

<a id="o-problema"></a>
## O problema

O painel de logística desenha no mapa toda a frota em tempo real: 500 mil marcadores, entre motos, carros, vans, caminhões e drones. Cada marcador tem uma posição e, conforme o tipo, um ícone e uma cor.

Escrito do jeito óbvio, cada marcador carrega o próprio ícone:

**antes — cada marcador guarda uma cópia do que é do tipo**

```python
class Marcador:
    def __init__(self, lat, lng, tipo):
        self.lat, self.lng, self.tipo = lat, lng, tipo
        self.icone = carregar_icone(f"icones/{tipo}.png")  # 32×32 RGBA: 4 KB decodificados
        self.cor = CORES[tipo]

    def desenhar(self, tela, projecao):
        x, y = projecao(self.lat, self.lng)
        tela.blit(self.icone, (x - 16, y - 16))

marcadores = [Marcador(v.lat, v.lng, v.tipo) for v in frota]   # 500 mil
```

A conta é simples: 500 mil marcadores com 4 KB de ícone cada são cerca de **2 GB**, para guardar cinco imagens diferentes. Abrir o painel decodifica meio milhão de PNGs, e o navegador ou o servidor fica sem memória antes de a frota crescer. Trocar o ícone das vans é percorrer todos os marcadores para achar as vans. O dado que muda por marcador (a posição) é uma fração do que se guarda.

<a id="a-solucao"></a>
## A solução

Separe o que é *do tipo* (igual para milhares de marcadores) do que é *do marcador* (a posição). O primeiro vira um objeto **compartilhado e imutável**, criado uma vez por tipo. O segundo fica no marcador, que só guarda uma referência para o compartilhado. Os papéis são quatro:

| Papel | Quem é | No exemplo |
|---|---|---|
| Flyweight | O objeto compartilhado, com o estado igual para muitos (o *intrínseco*). É imutável | `EstiloDeMarcador`: ícone e cor |
| Fábrica | Entrega o flyweight de uma chave, criando-o só na primeira vez | `FabricaDeEstilos` |
| Contexto | O objeto que existe aos milhares. Guarda o estado próprio (o *extrínseco*) e uma referência ao flyweight | `Marcador`: posição e estilo |
| Cliente | Quem cria os contextos pedindo os flyweights à fábrica | O painel |

O ponto é a **linha entre os dois estados**. Só cabe no flyweight o que *não depende de qual marcador* o usa. O que depende, como a posição na tela, chega como argumento na hora de desenhar. É essa regra que permite compartilhar com segurança: um objeto que muitos enxergam, e que nenhum pode alterar.

<a id="implementacao"></a>
## Implementação

```python
from dataclasses import dataclass

# 1. o flyweight: o que é do tipo, imutável, compartilhado
@dataclass(frozen=True)
class EstiloDeMarcador:
    tipo: str
    icone: bytes
    cor: str

    def desenhar(self, tela, x: int, y: int):   # o extrínseco chega como argumento
        tela.blit(self.icone, (x - 16, y - 16))

# 2. a fábrica: um flyweight por tipo, criado na primeira vez
class FabricaDeEstilos:
    def __init__(self):
        self._estilos: dict[str, EstiloDeMarcador] = {}

    def obter(self, tipo: str) -> EstiloDeMarcador:
        if tipo not in self._estilos:
            self._estilos[tipo] = EstiloDeMarcador(
                tipo, carregar_icone(f"icones/{tipo}.png"), CORES[tipo]
            )
        return self._estilos[tipo]

# 3. o contexto: o que é do marcador, mais uma referência
class Marcador:
    __slots__ = ("lat", "lng", "estilo")

    def __init__(self, lat: float, lng: float, estilo: EstiloDeMarcador):
        self.lat, self.lng, self.estilo = lat, lng, estilo

    def desenhar(self, tela, projecao):
        x, y = projecao(self.lat, self.lng)
        self.estilo.desenhar(tela, x, y)

# 4. o cliente: 500 mil marcadores, 5 estilos
estilos = FabricaDeEstilos()
marcadores = [Marcador(v.lat, v.lng, estilos.obter(v.tipo)) for v in frota]
```

> **Dica.** O compartilhamento é testável como qualquer outra regra: `estilos.obter("van") is estilos.obter("van")`. E o `EstiloDeMarcador` é testado sem tela: basta um `tela` falso que registra a chamada de `blit` com as coordenadas recebidas.

<a id="quando-usar"></a>
## Quando usar

O Flyweight vale quando quatro coisas acontecem ao mesmo tempo: há **muitos objetos** (dezenas de milhares ou mais), uma parte relevante do estado deles é **igual** entre muitos, essa parte pode ser **imutável**, e a memória (ou o custo de criar) é um problema que você **mediu**.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Muitos objetos, cada um com a mesma cópia de algo pesado | `self.icone = carregar(...)` no `__init__` de algo criado em laço de milhares; a memória cresce com a contagem | [Implementação, acima](#implementacao) |
| Registros com os mesmos valores repetidos | Colunas de texto de poucos valores (país, status, categoria) em milhões de linhas; `len(set(coluna))` muito menor que o total | [Uso #1](uso.md#valores-repetidos) |
| Um objeto imutável e caro de construir, criado de novo a cada uso | Um construtor que lê arquivo ou compila regra, chamado dentro de um laço ou de cada requisição | [Uso #2](uso.md#objeto-caro-de-criar) |
| Uma grade ou uma lista enorme de itens que só variam por tipo | `[[Tile(...) for x in ...] for y in ...]`: um objeto por célula, com os mesmos campos de textura e de custo | [Uso #3](uso.md#grade-de-tiles) |

> **Dica.** O que os sinais têm em comum: o número de objetos cresce com os dados, mas o número de objetos *diferentes* não. O Flyweight faz a memória acompanhar o segundo número, em vez do primeiro.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Você mediu, e o problema é memória ou custo de criação?** Se não mediu, pare. O Flyweight troca clareza por economia, e economia hipotética não paga.
2. **Boa parte do estado é igual entre muitos objetos?** Compare o total com `len(set(...))` do campo. Se cada objeto é único, não há o que compartilhar.
3. **Esse estado pode ser imutável?** Se alguém precisa alterar o ícone de *um* marcador, o compartilhamento quebra: a alteração apareceria em todos.
4. **O que varia é fácil de passar como argumento?** Se cada método precisaria de oito argumentos de contexto, o custo em leitura pesa mais que a memória economizada.

<a id="quando-nao-usar"></a>
## Quando não usar

O Flyweight tem um custo de design: você precisa separar dois estados que estavam juntos, o contexto passa a carregar uma referência, os métodos recebem o estado extrínseco por argumento, e a identidade muda (dois marcadores "com o mesmo ícone" compartilham o *mesmo* objeto). Se a fábrica for mal escrita, ainda vira um cache que nunca esvazia.

| Situação | Por que não | Faça isto |
|---|---|---|
| Poucos objetos (centenas) | A memória economizada não compensa a separação de estados | Objetos comuns |
| Cada objeto tem o próprio estado, e ele é único | Não há nada para compartilhar | Estrutura compacta: `__slots__`, `@dataclass(slots=True)`, arrays |
| O estado compartilhado precisa mudar por objeto | O Flyweight pressupõe imutabilidade; mudar um muda todos | Troque a *referência* por outro flyweight, ou guarde o valor no contexto |
| Você não mediu | Troca clareza por um ganho que talvez não exista | Meça (`tracemalloc`, perfil) e comece por `__slots__` |
| Você quer reaproveitar objetos caros e mutáveis (conexões, buffers) | O Flyweight compartilha valores imutáveis ao mesmo tempo; não empresta objetos um de cada vez | Object Pool |

<a id="sinais-de-abuso"></a>
### Sinais de que o Flyweight saiu do lugar

- **O flyweight ganhou um *setter*.** Alguém altera "só o desta van", e todas as vans mudam de cor. Um objeto compartilhado precisa ser imutável de verdade, e não só por convenção.
- **A fábrica nunca esvazia.** Com chaves abertas (texto digitado pelo usuário, por exemplo) o cache cresce sem limite, e o pattern que devia economizar memória a vaza.
- **O estado extrínseco foi para dentro do flyweight.** Quando a posição entra "só desta vez", o objeto deixa de ser compartilhável e há um por marcador de novo.
- **Existem duas fábricas.** Cada uma tem o seu cache, e o "compartilhado" se divide em dois objetos iguais.
- **Foi aplicado sem medir.** O código ficou mais difícil de ler e ninguém sabe quantos megabytes foram poupados.

> **Perigo.** O sinal mais comum: um método que altera o flyweight. Em um objeto que milhares de contextos enxergam, a mutação é um bug de ação à distância, e o pior tipo, porque só aparece em um marcador que ninguém estava olhando.

> **Nota.** Na dúvida, comece com objetos comuns e `__slots__`. É uma mudança de uma linha e costuma cortar a memória pela metade. Introduza o Flyweight onde o perfil mostrar que ainda é preciso.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Singleton](../../criacionais/singleton/explicacao.md) | Garante uma instância para a classe inteira. O Flyweight tem uma instância *por valor da chave* (uma por tipo de marcador), e várias vivem juntas |
| Object Pool | Empresta objetos mutáveis, um uso de cada vez, e os recebe de volta. O Flyweight entrega o mesmo objeto imutável a todos, ao mesmo tempo, e ninguém devolve |
| [Composite](../composite/explicacao.md) | Organiza objetos em árvore. Os dois aparecem juntos com frequência: as folhas de uma árvore enorme podem ser flyweights |
| Cache | Guarda o resultado de uma operação por entrada para não recalcular. No Flyweight o objeto compartilhado faz parte do *modelo*, e a identidade (o mesmo objeto) é o objetivo |

Regra prática: se muitos objetos apontam para a mesma instância imutável por valor de uma chave, é Flyweight; se só existe uma instância para a classe toda, é Singleton.
