<!-- Gerado de pages/clean-code/comportamentais/observer/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Observer — Uso

*Clean Code / Design Pattern / Observer*

Cinco situações em que o Observer resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o assunto deixa de saber.

<a id="como-escolhi"></a>
## Por que cinco

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Observer. Quando dois casos se resolvem com o mesmo raciocínio — avisar o comprador e registrar auditoria na mesma mudança, por exemplo — só um fica. Seguindo essa regra, sobraram cinco motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o assunto deixa de saber |
|---|---|---|
| 1 | [Um fato, várias reações independentes](#varios-interessados) | Quem reage, e quantos são |
| 2 | [A tela acompanha o modelo](#tela-acompanha-modelo) | Que existe tela |
| 3 | [Quem escuta entra e sai](#entram-e-saem) | Quem está ouvindo agora |
| 4 | [Extensões de terceiros](#plugins) | Quais pacotes existem |
| 5 | [Biblioteca que reporta progresso](#progresso) | Quem consome: barra, log ou terminal |

<a id="varios-interessados"></a>
## 1. Um fato, várias reações independentes

**Situação.** No galpão, quando a quantidade de um produto cai abaixo do mínimo, três coisas precisam acontecer: compras abre um pedido ao fornecedor, o canal dos compradores é avisado no chat e o anúncio no marketplace é pausado para não vender o que não existe. Hoje as três moram dentro do método que baixa o estoque.

**sem o pattern — o estoque chama os três**

```python
class Estoque:
    def baixar(self, sku, quantidade):
        item = self._itens[sku]
        item.quantidade -= quantidade

        if item.quantidade < item.minimo:
            compras.abrir_pedido(sku, item.lote_ideal)
            chat.enviar("#compras", f"{sku} abaixo do mínimo")  # e se o chat cair?
            marketplace.pausar_anuncio(sku)
```

**O que dói.** O módulo mais básico do sistema importa compras, chat e marketplace. Se o chat estiver fora do ar, a exceção sobe e o anúncio nunca é pausado, com o produto já zerado. E quando o BI pedir "registre toda vez que algo ficar abaixo do mínimo", é mais uma edição no `baixar`.

**com o pattern — o estoque avisa; a montagem decide quem ouve**

```python
class Estoque:
    def __init__(self):
        self._itens = {}
        self._ao_ficar_baixo = []          # quem quer saber

    def ao_ficar_baixo(self, ouvinte):
        self._ao_ficar_baixo.append(ouvinte)

    def baixar(self, sku, quantidade):
        item = self._itens[sku]
        item.quantidade -= quantidade
        if item.quantidade < item.minimo:
            self._avisar(sku, item.quantidade)

    def _avisar(self, sku, restante):
        for ouvinte in self._ao_ficar_baixo:
            try:
                ouvinte(sku, restante)
            except Exception:
                log.exception("ouvinte de estoque baixo falhou")   # os outros seguem

# a montagem: o único lugar que conhece todo mundo
estoque.ao_ficar_baixo(lambda sku, q: compras.abrir_pedido(sku))
estoque.ao_ficar_baixo(lambda sku, q: chat.enviar("#compras", f"{sku}: {q} restantes"))
estoque.ao_ficar_baixo(lambda sku, q: marketplace.pausar_anuncio(sku))
```

**O que o assunto deixa de saber.** Que existem compras, chat e marketplace, e quantos deles há. O `Estoque` não importa nenhum dos três, e o BI vira mais uma linha na montagem. Repare que cada reação falha sozinha: o `try` dentro do laço é o que impede o chat fora do ar de segurar o anúncio. Aqui o ouvinte é uma função simples; uma interface com um método só seria cerimônia.

> **Cuidado.** Sem o `try`, o laço volta a ser o problema de antes: o primeiro ouvinte que levanta impede os seguintes. Decida o que fazer com a falha (registrar, tentar de novo, avisar alguém) *antes* de ter ouvintes demais.

<a id="tela-acompanha-modelo"></a>
## 2. A tela acompanha o modelo

**Situação.** Na loja web, o mesmo carrinho aparece em três lugares: o número no ícone do cabeçalho, o mini-carrinho lateral e o total no fim do checkout. Itens entram e saem por vários caminhos: botão da vitrine, página do produto, cupom, "comprar de novo".

**sem o pattern — quem altera é quem lembra de atualizar a tela**

```typescript
class Carrinho {
  itens: Item[] = [];

  adicionar(item: Item) {
    this.itens.push(item);
    renderBadgeDoHeader(this);
    renderMiniCarrinho(this);
    renderTotalDoCheckout(this);
  }

  remover(item: Item) {
    this.itens = this.itens.filter(i => i !== item);
    renderBadgeDoHeader(this);
    renderMiniCarrinho(this);
    // esqueceu o total do checkout
  }
}
```

**O que dói.** O modelo importa funções de tela: não roda em teste de unidade nem no servidor. Cada tela nova é uma edição em todo método que altera o carrinho, e `aplicarCupom` é o próximo a esquecer uma. O bug que isso produz é o pior tipo: o total do checkout fica desatualizado só depois de remover um item.

**com o pattern — todo caminho termina no mesmo aviso**

```typescript
type Ouvinte<T> = (valor: T) => void;

class Carrinho {
  private itens: Item[] = [];
  private ouvintes: Ouvinte<readonly Item[]>[] = [];

  aoMudar(ouvinte: Ouvinte<readonly Item[]>) {
    this.ouvintes.push(ouvinte);
  }

  adicionar(item: Item) {
    this.itens.push(item);
    this.avisar();
  }

  remover(item: Item) {
    this.itens = this.itens.filter(i => i !== item);
    this.avisar();
  }

  private avisar() {
    for (const ouvinte of this.ouvintes) ouvinte(this.itens);
  }
}

// cada pedaço da tela se registra; o carrinho não sabe que eles existem
carrinho.aoMudar(itens => badge.textContent = String(itens.length));
carrinho.aoMudar(itens => renderMiniCarrinho(itens));
carrinho.aoMudar(itens => renderTotal(itens));
```

**O que o assunto deixa de saber.** Que existe uma tela. O ganho aqui não é a lista, é o `avisar()`: um ponto só, chamado no fim de *todo* método que altera. Esquecer uma tela deixa de ser possível, porque nenhuma tela é lembrada por quem altera. O ouvinte recebe o estado novo como `readonly`, então ele lê e não consegue mexer no carrinho de volta.

<a id="entram-e-saem"></a>
## 3. Quem escuta entra e sai

**Situação.** Um painel de cotações recebe o preço do dólar por uma única conexão. Cada widget (gráfico, ticker, alerta de preço) mostra esse valor, e a pessoa abre e fecha widgets o dia inteiro.

**sem o pattern — dá para entrar, mas não dá para sair**

```typescript
class FeedDeCotacao {
  private widgets: Widget[] = [];

  registrar(widget: Widget) {
    this.widgets.push(widget);      // e para sair?
  }

  receber(preco: number) {
    for (const w of this.widgets) w.atualizar(preco);
  }
}

// a pessoa fecha o gráfico...
grafico.destruir();   // ...mas ele continua na lista: recebe preço e mexe em DOM que não existe
```

**O que dói.** Cada widget fechado fica na lista para sempre: a memória cresce, e cada preço novo tenta atualizar um elemento que já saiu da página e levanta erro. Abrir o mesmo widget dez vezes o registra dez vezes. E, para tirar um, quem fecha precisaria ter o feed e acesso à lista.

**com o pattern — assinar devolve o jeito de cancelar**

```typescript
type Cancelar = () => void;

class FeedDeCotacao {
  private ouvintes = new Set<(preco: number) => void>();

  assinar(ouvinte: (preco: number) => void): Cancelar {
    this.ouvintes.add(ouvinte);
    return () => this.ouvintes.delete(ouvinte);   // a saída vai com quem entrou
  }

  receber(preco: number) {
    for (const ouvinte of [...this.ouvintes]) ouvinte(preco);   // cópia: dá para cancelar durante o aviso
  }
}

class WidgetGrafico {
  private cancelar: Cancelar;

  constructor(feed: FeedDeCotacao, private el: HTMLElement) {
    this.cancelar = feed.assinar(preco => this.desenhar(preco));
  }

  destruir() {
    this.cancelar();
    this.el.remove();
  }
}
```

**O que o assunto deixa de saber.** Quem está ouvindo *agora*. A lista muda a cada clique e o feed não acompanha: quem assinou guarda a função de saída e a chama quando for embora, sem tocar na lista. O `Set` impede o registro duplicado, e a cópia no laço protege do ouvinte que se cancela no meio do aviso, caso comum em "avisar uma vez e sair".

> **Cuidado.** Toda assinatura precisa de um ponto onde o cancelamento acontece de verdade: `destruir`, o *cleanup* do `useEffect`, o `ngOnDestroy`. Um `assinar` sem `cancelar` correspondente é um vazamento, mesmo que hoje não pareça.

<a id="plugins"></a>
## 4. Extensões de terceiros

**Situação.** Um CMS é um pacote que outras equipes e fornecedores instalam. Quando um artigo é salvo, o time de SEO quer gerar o slug, a infraestrutura quer invalidar o cache do CDN e um plugin de terceiros quer postar no Twitter. O núcleo não é de nenhum deles, e não dá para editá-lo para cada extensão.

**sem o pattern — o núcleo sabe quais extensões existem**

```python
def salvar(artigo):
    artigo.slug = gerar_slug(artigo.titulo)              # SEO
    banco.gravar(artigo)

    if config.cdn_ativo:
        cdn.invalidar(artigo.url)                        # infraestrutura
    if config.twitter_ativo:
        twitter.postar(artigo.titulo, artigo.url)        # terceiro
```

**O que dói.** O núcleo importa o que não é dele, e há um `if config.x_ativo` a mais para cada extensão. O terceiro só entra abrindo PR no repositório do núcleo. E nada diz quais pontos do ciclo de vida são oferecidos: cada plugin pede o seu, e vira uma negociação caso a caso.

**com o pattern — eventos nomeados, e o núcleo não importa ninguém**

```python
from collections import defaultdict

class Ganchos:
    def __init__(self):
        self._ouvintes = defaultdict(list)

    def ao(self, evento: str):
        def registrar(funcao):
            self._ouvintes[evento].append(funcao)
            return funcao
        return registrar

    def disparar(self, evento: str, **dados):
        for funcao in self._ouvintes[evento]:
            funcao(**dados)

ganchos = Ganchos()

def salvar(artigo):
    ganchos.disparar("antes_de_salvar", artigo=artigo)
    banco.gravar(artigo)
    ganchos.disparar("depois_de_salvar", artigo=artigo)

# em outro pacote, que o núcleo nunca importa:
@ganchos.ao("depois_de_salvar")
def invalidar_cdn(artigo):
    cdn.invalidar(artigo.url)
```

**O que o assunto deixa de saber.** Que pacotes existem. Cada extensão é um módulo que se registra a si mesmo; instalar ou remover um plugin não toca no núcleo. O que o núcleo passa a prometer são os *nomes dos eventos* e os dados que cada um leva: `antes_de_salvar` deixa o plugin ajustar o artigo (o slug, por exemplo), e por isso o nome diz "antes"; `depois_de_salvar` só avisa.

> **Cuidado.** Os nomes dos eventos e o conteúdo de `**dados` passam a ser API pública. Renomear um evento ou tirar um campo quebra plugins que você nem sabe que existem. Ofereça poucos pontos, bem nomeados, e documente-os.

<a id="progresso"></a>
## 5. Biblioteca que reporta progresso

**Situação.** A equipe tem uma biblioteca interna que exporta o relatório anual (dois milhões de linhas) para CSV. Ela é usada pelo job noturno, que quer log; pela tela do admin, que quer uma barra; e por um CLI, que quer escrever no terminal.

**sem o pattern — um parâmetro para cada consumidor**

```python
def exportar(consulta, destino, barra=None, logger=None, modo_cli=False):
    total = consulta.contar()
    with open(destino, "w") as f:
        for i, linha in enumerate(consulta.linhas(), start=1):
            f.write(formatar(linha))
            if barra:
                barra.atualizar(i / total)
            if logger and i % 10_000 == 0:
                logger.info(f"{i}/{total}")
            if modo_cli:
                print(f"\r{i}/{total}", end="")
```

**O que dói.** A função que exporta conhece barras, loggers e terminal. O próximo consumidor (uma métrica no Prometheus) é mais um parâmetro e mais um `if` no laço. E uma biblioteca que escreve na tela por conta própria deixa de poder rodar dentro de outra aplicação.

**com o pattern — a biblioteca avisa; cada consumidor pluga o seu**

```python
class Exportador:
    def __init__(self):
        self._ouvintes = []

    def ao_progredir(self, ouvinte):
        self._ouvintes.append(ouvinte)

    def exportar(self, consulta, destino):
        total = consulta.contar()
        with open(destino, "w") as f:
            for i, linha in enumerate(consulta.linhas(), start=1):
                f.write(formatar(linha))
                for ouvinte in self._ouvintes:
                    ouvinte(i, total)

# cada consumidor pluga o que quer; quem não quer nada não escreve nada
exportador.ao_progredir(lambda i, t: barra.atualizar(i / t))                       # tela do admin
exportador.ao_progredir(lambda i, t: i % 10_000 or logger.info(f"{i}/{t}"))   # job noturno
exportador.ao_progredir(lambda i, t: print(f"\r{i}/{t}", end=""))            # CLI
```

**O que o assunto deixa de saber.** Quem consome. A dependência passa a apontar de fora para dentro: barra, log e terminal conhecem o exportador, e ele não conhece nenhum dos três. Sem ouvintes, a lista está vazia e o custo é zero. Repare que o aviso leva só números simples (`feito` e `total`), e não o próprio exportador, para ninguém poder mexer nele por dentro.

> **Cuidado.** O aviso é síncrono: um ouvinte lento atrasa a exportação inteira, a cada linha. Se o ouvinte precisa fazer algo caro (gravar uma métrica pela rede), aviste a cada N linhas, ou entregue o trabalho a uma fila.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos cinco:

| Caso | Já coberto por |
|---|---|
| Registrar auditoria de toda mudança de status | 1 — mais uma reação ao mesmo fato |
| Invalidar um cache quando o dado de origem muda | 1 — a reação é um efeito colateral independente |
| Total e subtotal recalculados quando um item muda | 2 — o valor derivado acompanha o modelo |
| `addEventListener` no DOM | 2 e 3 — é o Observer pronto; lembre do `removeEventListener`, que é o caso 3 |
| Cancelar a assinatura no *cleanup* de um componente | 3 — quem assina guarda a saída |
| Ganchos `before_save` de um ORM, ou *middlewares* | 4 — o dono do ciclo de vida oferece pontos nomeados |
| Barra de progresso de upload ou de download | 5 — o código reutilizável avisa, o consumidor pluga |
| Eventos de domínio entre módulos de um monólito | 1 e 4 — veja os [sinais de abuso](explicacao.md#sinais-de-abuso) antes de generalizar |

E um caso que parece Observer, mas não é: avisar outro *serviço*, em outra máquina, de que um pedido foi pago. O assunto e quem escuta já não vivem na mesma memória, e o aviso precisa sobreviver a uma queda e ser tentado de novo. Isso é fila ou broker, com entrega persistente; o Observer em memória perderia o aviso junto com o processo. Veja também [Quando não usar](explicacao.md#quando-nao-usar) e [Parecidos](explicacao.md#parecidos).
