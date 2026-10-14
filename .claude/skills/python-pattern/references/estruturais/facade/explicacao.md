<!-- Gerado de pages/clean-code/estruturais/facade/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Facade — Explicação

*Clean Code / Design Pattern / Facade*

Como dar uma porta de entrada simples para um conjunto de peças que só funcionam quando chamadas na ordem certa, para que quem usa não precise conhecer cada uma.

<a id="o-problema"></a>
## O problema

Finalizar um pedido não é uma chamada: é uma sequência. Reservar o estoque, autorizar o pagamento, contratar o frete, emitir a nota fiscal, avisar o cliente. Cada passo é um serviço da empresa, com a sua própria interface, e se um deles falha, os anteriores precisam ser desfeitos.

Quem precisa finalizar um pedido (a API web, o app, o job de recompra) monta a sequência por conta própria:

**antes — cada chamador conhece as cinco peças, a ordem e o desfazer**

```python
def checkout_web(req):
    carrinho = carrinhos.buscar(req.carrinho_id)
    reservas = estoque.reservar(carrinho.itens)
    try:
        cobranca = pagamentos.autorizar(req.token, carrinho.total)
    except PagamentoRecusado:
        estoque.liberar(reservas)
        raise
    try:
        envio = frete.contratar(carrinho.endereco, carrinho.peso_kg)
    except FreteIndisponivel:
        pagamentos.estornar(cobranca)
        estoque.liberar(reservas)
        raise
    nota = fiscal.emitir(carrinho, cobranca)
    correio.enviar(carrinho.email, "Pedido confirmado", f"Nota {nota.numero}")
    return Pedido(carrinho, cobranca, envio, nota)

# api_mobile.checkout() e job_recompra.executar() repetem a mesma sequência.
# no job, alguém esqueceu o estornar() do except do frete.
```

Cada cópia funciona no dia em que é escrita. O problema aparece depois: quando o fiscal passa a exigir um passo a mais, são três lugares para editar, e o que for esquecido emite pedido sem nota. A regra "o que desfazer quando algo falha" mora em cada chamador, e uma delas já está errada. E testar o checkout web exige falsificar cinco serviços, quando o que ele quer testar é só a tradução de `req` em uma chamada.

<a id="a-solucao"></a>
## A solução

Escreva a sequência **uma vez**, em uma classe com um método nomeado pelo que o chamador quer: `finalizar`. As peças continuam existindo e continuam acessíveis; a fachada é só o caminho curto para o caso comum. Os papéis são três:

| Papel | Quem é | No exemplo |
|---|---|---|
| Subsistema | As peças que já existem, com suas próprias interfaces. Não mudam e não sabem da fachada | `Estoque`, `Pagamentos`, `Frete`, `Fiscal`, `Correio` |
| Fachada | Uma interface pequena que conhece as peças, a ordem entre elas e o que desfazer | `Checkout`, com `finalizar()` |
| Cliente | Quem usa a fachada no lugar de chamar as peças | A API web, o app, o job |

O ponto é a **direção do conhecimento**: a fachada conhece as peças, e as peças não conhecem a fachada. Por isso ela pode ser acrescentada sem mudar nada que já existe. Ela também não decide regra de negócio: coordena. Quem sabe se um pedido tem direito a frete grátis é outra classe.

<a id="implementacao"></a>
## Implementação

```python
# 1. o subsistema: estoque, pagamentos, frete, fiscal e correio já existem

# 2. a fachada: a sequência e o desfazer, em um lugar só
class Checkout:
    def __init__(self, estoque, pagamentos, frete, fiscal, correio):
        self._estoque, self._pagamentos = estoque, pagamentos
        self._frete, self._fiscal, self._correio = frete, fiscal, correio

    def finalizar(self, carrinho, token: str) -> Pedido:
        reservas = self._estoque.reservar(carrinho.itens)
        cobranca = None
        try:
            cobranca = self._pagamentos.autorizar(token, carrinho.total)
            envio = self._frete.contratar(carrinho.endereco, carrinho.peso_kg)
        except Exception:
            if cobranca:
                self._pagamentos.estornar(cobranca)
            self._estoque.liberar(reservas)
            raise

        nota = self._fiscal.emitir(carrinho, cobranca)
        self._correio.enviar(carrinho.email, "Pedido confirmado", f"Nota {nota.numero}")
        return Pedido(carrinho, cobranca, envio, nota)

# 3. o cliente: uma chamada, nenhuma peça à vista
def checkout_web(req, checkout: Checkout):
    carrinho = carrinhos.buscar(req.carrinho_id)
    return checkout.finalizar(carrinho, req.token)
```

> **Dica.** O teste muda de dono. O `Checkout` é testado uma vez, com as peças falsas, inclusive o caminho "o frete falhou, o pagamento foi estornado". Os chamadores passam a ser testados com um `Checkout` falso de uma linha, que devolve um pedido pronto.

<a id="quando-usar"></a>
## Quando usar

O Facade vale quando três coisas acontecem ao mesmo tempo: existe um subsistema com **várias peças**, os chamadores **repetem** a mesma sequência de uso (a ordem, a configuração, o desfazer), e a **maioria** deles só precisa do caminho comum.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um fluxo de vários passos copiado por vários chamadores | A mesma sequência `reservar → autorizar → contratar → emitir` em controller, app e job, com os `except` copiados junto | [Implementação, acima](#implementacao) |
| Uma ferramenta ou SDK com muitas opções, e um uso real pequeno | `subprocess.run([...flags...])` ou um cliente com dez parâmetros, repetido com pequenas variações | [Uso #1](uso.md#ffmpeg-e-ffprobe) |
| Módulos importando os internos uns dos outros | `from pagamentos.gateway.stripe_adapter import …` por todo o projeto; refatorar por dentro quebra imports distantes | [Uso #2](uso.md#fronteira-de-modulo) |
| Subir e derrubar vários componentes em ordem | Blocos de *setup* copiados entre testes e scripts; um `finally` que esquece um dos componentes | [Uso #3](uso.md#ambiente-de-teste) |

> **Dica.** Os sinais têm uma coisa em comum: o chamador sabe demais. Ele conhece as peças, a ordem entre elas e as exceções de cada uma. A fachada junta esse conhecimento em um lugar, para que quem usa precise saber apenas o que quer fazer.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **O chamador precisa combinar várias peças?** Se o subsistema é uma classe com um método, não há o que simplificar. Pare.
2. **Mais de um chamador repete a mesma combinação?** Se só um usa, uma função com nome já organiza. Se cada um combina de um jeito próprio, uma fachada não serve a nenhum deles.
3. **A maioria dos usos é o caminho comum?** Se a maioria precisa de controle fino sobre cada peça, a fachada vira obstáculo, e as pessoas passam a contorná-la.
4. **Você consegue nomear o método pelo que o chamador quer?** `finalizar` é um bom nome. `executar_fluxo_de_pedido` costuma ser sinal de que o caso de uso ainda não está claro.

<a id="quando-nao-usar"></a>
## Quando não usar

O Facade tem um custo que se acumula com o tempo: é uma camada a mais que precisa acompanhar o subsistema, e tende a crescer. Cada chamador pede "só mais um método", e a fachada vira um espelho do subsistema, ou um objeto que conhece o sistema inteiro. Esconder demais também custa: quem precisa de algo fora do caminho comum fica preso, ou copia o subsistema inteiro para dentro do próprio código.

| Situação | Por que não | Faça isto |
|---|---|---|
| O subsistema é uma classe ou uma função só | A fachada seria um repasse, só com outro nome | Chame direto |
| Cada chamador precisa de um controle diferente | A fachada vira espelho do subsistema, ou não serve a ninguém | Exponha as peças, e escreva um auxiliar por caso de uso, se ele repetir |
| Você quer encaixar uma interface em outra que já existia | O problema é compatibilidade, não simplificação | Adapter |
| Você quer acrescentar cache, log ou retry mantendo a interface | A interface antes e depois é a mesma | Decorator |
| O que há no meio é regra de negócio (decide, calcula, tem estados) | A fachada deve coordenar, e não decidir; a regra fica sem nome e sem teste próprio | Um serviço de domínio para a regra, e a fachada só o chama |

<a id="sinais-de-abuso"></a>
### Sinais de que o Facade saiu do lugar

- **A fachada espelha o subsistema.** Um método para cada método, só com nomes diferentes. Nada foi simplificado; foi acrescentado um salto.
- **A fachada tem regra de negócio.** Se ela calcula desconto ou decide elegibilidade, virou serviço, sem o nome nem o teste de um.
- **O subsistema importa a fachada.** A dependência circular transforma a fachada em um nó que todo mundo precisa conhecer.
- **Não há saída para o caso raro.** Quem precisa de uma opção que a fachada não expõe copia as peças inteiras, e agora há dois caminhos para manter.
- **Uma fachada para o sistema todo.** `Sistema.fazer_tudo()` é um *God object* com nome de pattern. Prefira uma fachada pequena por caso de uso.

> **Perigo.** O sinal mais comum: a fachada ganha um método novo para cada necessidade de cada chamador, até ser a soma da API de todas as peças. Quando isso acontece, ela deixou de simplificar, e só concentrou toda a dependência em um arquivo.

> **Nota.** Na dúvida, comece com uma função. Uma fachada com um método e sem estado é só `finalizar_pedido(carrinho, token)`. Vire classe quando precisar guardar as peças injetadas, ou quando ela passar a ter mais de um caso de uso.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Adapter](../adapter/explicacao.md) | Converte a interface de *uma* peça em outra que já era esperada. A fachada cria uma interface *nova*, mais simples, sobre várias peças |
| [Decorator](../decorator/explicacao.md) | Mantém a mesma interface e acrescenta comportamento. A fachada muda a interface e não acrescenta comportamento às peças |
| Mediator | Coordena objetos que conversam entre si, e todos conhecem o mediador. Na fachada as peças não sabem que ela existe, e ela só fala de fora para dentro |
| Proxy | Tem a interface do objeto que protege e controla o acesso a ele. A fachada tem interface própria e fala por várias peças |

Regra prática: se a interface nova é mais simples e fala por várias peças, é Facade; se só troca a interface de uma peça por outra que o código já esperava, é Adapter.
