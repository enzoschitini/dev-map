<!-- Gerado de pages/clean-code/comportamentais/chain-of-responsibility/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Chain of Responsibility — Uso

*Clean Code / Design Pattern / Chain of Responsibility*

Quatro situações em que o Chain of Responsibility resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a cadeia esconde de quem faz o pedido.

<a id="como-escolhi"></a>
## Por que quatro

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Chain of Responsibility. Quando dois casos se resolvem com o mesmo raciocínio — o escalonamento do suporte e a aprovação de despesas, por exemplo — só um fica. Seguindo essa regra, sobraram quatro motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a cadeia esconde de quem pede |
|---|---|---|
| 1 | [Quem aprova depende do valor e do organograma](#alcada-por-valor) | Quantos níveis existem e o limite de cada um |
| 2 | [As mesmas verificações antes de toda rota](#middleware) | Quais verificações existem e em que ordem |
| 3 | [O clique precisa ser tratado por quem está mais perto](#evento-que-sobe) | Qual componente, entre os da tela, cuida do evento |
| 4 | [Fontes de dado com custos diferentes](#fontes-em-camadas) | Quantas camadas de leitura existem, e quais |

> **Nota.** As chamadas de biblioteca estão simplificadas para caber na página. O formato do Express e do cliente Redis é o real; configuração e parâmetros opcionais foram omitidos. Funções como `verificarToken` e `excedeuLimite` são fictícias.

<a id="alcada-por-valor"></a>
## 1. Quem aprova depende do valor e do organograma

**Situação.** Despesas de viagem sobem para aprovação. Até R$ 500, o gestor direto; até R$ 5.000, o gestor dele; acima disso, o financeiro. Os limites variam por cargo, e a hierarquia vem do cadastro de pessoas: cada uma tem um `gestor`. Na Explicação a cadeia era montada em código; aqui ela já existe, nos dados.

**sem o pattern — o código presume a profundidade do organograma**

```python
def encaminhar(despesa):
    gestor = despesa.autor.gestor
    if despesa.valor <= 500:
        gestor.notificar(despesa)
    elif despesa.valor <= 5000:
        gestor.gestor.notificar(despesa)         # e se o gestor estiver de férias?
    else:
        gestor.gestor.gestor.notificar(despesa)  # e se só houver dois níveis?
```

**O que dói.** O código presume que há três níveis acima de todo mundo; em um time pequeno, `gestor.gestor.gestor` é `None` e vira um `AttributeError`. Os limites são os mesmos para todos, embora o limite do diretor seja diferente do de um líder. E cada exceção (delegação, férias) vira outro `if` nesta função.

**com o pattern — o organograma é a cadeia**

```python
@dataclass
class Pessoa:
    nome: str
    limite: Decimal                 # quanto este cargo aprova
    gestor: "Pessoa | None" = None

    def aprovador_de(self, despesa) -> "Pessoa":
        if despesa.valor <= self.limite:
            return self
        if self.gestor is None:
            raise SemAlcada(despesa)   # topo do organograma e ainda não basta
        return self.gestor.aprovador_de(despesa)

def encaminhar(despesa):
    despesa.autor.gestor.aprovador_de(despesa).notificar(despesa)
```

**O que a cadeia esconde.** A profundidade do organograma e o limite de cada pessoa. A função `encaminhar` não sabe se há dois ou sete níveis, e não precisa saber: ela entrega ao primeiro gestor e recebe de volta quem aprova. Mudar a hierarquia é editar o cadastro, sem tocar em código.

Uma delegação, como "o gestor está de férias, passe para o diretor", é um elo que se comporta diferente — por exemplo, um que sempre repassa — e não mais um `if` na escada.

> **Cuidado.** O fim da cadeia é decisão de design, e aqui é uma exceção explícita: `SemAlcada`. Retornar `None` daria uma despesa que "foi encaminhada" para ninguém, e nada avisaria que ela está parada.

<a id="middleware"></a>
## 2. As mesmas verificações antes de toda rota

**Situação.** A API de pedidos, em Node com Express, tem uma dúzia de rotas. Toda rota precisa autenticar, limitar requisições por usuário e validar o corpo. Cada verificação pode encerrar a resposta com um erro, e uma delas depende do resultado da anterior: o limite é por usuário, então só dá para aplicá-lo depois de saber quem é.

**sem o pattern — o mesmo prólogo copiado em cada rota**

```typescript
app.post("/pedidos", async (req, res) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) return res.status(401).json({ erro: "sem token" });
  const usuario = await verificarToken(token);
  if (!usuario) return res.status(401).json({ erro: "token inválido" });
  if (await excedeuLimite(usuario.id)) return res.status(429).json({ erro: "muitas requisições" });
  if (!req.body.itens?.length) return res.status(400).json({ erro: "sem itens" });

  res.status(201).json(await criarPedido(usuario, req.body));
});

app.get("/pedidos/:id", async (req, res) => {
  // mesmos três blocos — só que aqui alguém esqueceu o limite de requisições
});
```

**O que dói.** Para saber quais rotas exigem autenticação é preciso ler todas. Uma verificação esquecida não dá erro nenhum: a rota funciona, só que sem a proteção. E trocar o limite de requisições é uma caça por todas as cópias.

**com o pattern — cada verificação é um elo, a rota só declara a fila**

```typescript
const autenticar: RequestHandler = async (req, res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  const usuario = token && (await verificarToken(token));
  if (!usuario) return res.status(401).json({ erro: "não autenticado" });  // encerra a cadeia
  res.locals.usuario = usuario;
  next();                                                            // passa ao próximo elo
};

const limitar: RequestHandler = async (req, res, next) => {
  if (await excedeuLimite(res.locals.usuario.id)) {
    return res.status(429).json({ erro: "muitas requisições" });
  }
  next();
};

const exigirItens: RequestHandler = (req, res, next) => {
  if (!req.body.itens?.length) return res.status(400).json({ erro: "sem itens" });
  next();
};

// a ordem da fila é a ordem em que as verificações acontecem
app.use("/pedidos", autenticar, limitar);
app.post("/pedidos", exigirItens, async (req, res) => {
  res.status(201).json(await criarPedido(res.locals.usuario, req.body));
});
```

**O que a cadeia esconde.** A rota não sabe quais verificações existem. Aqui os elos funcionam de um jeito diferente do exemplo anterior: quase todos *fazem algo* e passam adiante com `next()`, e qualquer um pode encerrar a resposta e impedir que o resto aconteça. A regra de negócio, no fim da fila, roda só se todos deixaram passar.

Uma rota nova ganha autenticação e limite sem que ninguém precise lembrar. Uma verificação nova — log, CORS, idempotência — é mais um elo, em um lugar só.

> **Cuidado.** A ordem passa a ser parte do contrato: `limitar` lê `res.locals.usuario`, e quem o preenche é `autenticar`. Invertê-los quebra sem nenhum aviso do compilador. E um elo que não chama `next()` nem responde deixa a requisição pendurada até o timeout.

<a id="evento-que-sobe"></a>
## 3. O clique precisa ser tratado por quem está mais perto

**Situação.** A tela de pedidos tem um menu de ações por linha, e a página pode abrir uma modal sobre um fundo escurecido. Clicar em um item do menu executa a ação e fecha o menu; clicar no fundo fecha a modal; clicar em qualquer lugar fora do menu o fecha. Aqui ninguém precisa montar a cadeia: o navegador já faz isso, porque o evento sobe pela árvore do DOM, do elemento clicado até o `document`.

**sem o pattern — um listener global que conhece todos os componentes**

```typescript
document.addEventListener("click", (ev) => {
  const alvo = ev.target as HTMLElement;

  if (alvo.closest(".menu-item")) {
    executar(alvo.closest<HTMLElement>(".menu-item")!.dataset.acao!);
    fecharMenus();
  } else if (alvo.closest(".menu-gatilho")) {
    alternarMenu(alvo.closest(".menu")!);
  } else if (alvo.closest(".modal")) {
    // clique dentro da modal: não fecha nada
  } else if (alvo.closest(".fundo")) {
    fecharModal();
  } else {
    fecharMenus();
  }
});
```

**O que dói.** O `document` conhece a estrutura interna de todo componente: cada componente novo é outro `else if` aqui, em um arquivo que não é o dele. A ordem dos testes importa, porque a modal está dentro do fundo; trocar duas linhas muda o comportamento. E nada impede que dois componentes escolham a mesma classe CSS.

**com o pattern — cada nível trata o que é seu e deixa o resto subir**

```typescript
// o menu cuida dos próprios itens
menu.addEventListener("click", (ev) => {
  const item = (ev.target as HTMLElement).closest<HTMLElement>("[data-acao]");
  if (!item) return;                 // não é comigo: deixa subir
  executar(item.dataset.acao!);
  fecharMenus();
  ev.stopPropagation();            // tratei: ninguém acima precisa saber
});

// a modal impede que o clique dentro dela chegue ao fundo
modal.addEventListener("click", (ev) => ev.stopPropagation());

// o fundo trata o clique que chegou até ele
fundo.addEventListener("click", fecharModal);

// o último elo: o que ninguém tratou fecha os menus abertos
document.addEventListener("click", fecharMenus);
```

**O que a cadeia esconde.** Qual componente cuida de qual clique. Cada listener conhece só o próprio componente, e o `document` vira o fim natural da cadeia: ele recebe o que sobrou, sem saber o que é um menu ou uma modal. Este é o caso em que a cadeia não é construída por ninguém: é a própria estrutura da página, e o padrão aparece como uma propriedade da plataforma.

> **Cuidado.** `stopPropagation()` também esconde o evento de quem não é parte da sua cadeia: a ferramenta de métricas, outro componente que escuta o `document`. Use só no elo que de fato tratou o pedido, e prefira checar `ev.defaultPrevented` quando bastar.

<a id="fontes-em-camadas"></a>
## 4. Fontes de dado com custos diferentes

**Situação.** A cotação de moedas vem de quatro lugares, do mais barato ao mais caro: um dicionário em memória, o Redis, o banco e a API do Banco Central, que cobra por chamada. Tentar na ordem e parar na primeira resposta é o óbvio. Quando a resposta vem de longe, é preciso ainda guardá-la nas camadas por onde ela passou. E em dev, onde não há Redis, a camada simplesmente não existe.

**sem o pattern — a descida e o preenchimento no mesmo bloco aninhado**

```python
def cotacao(moeda):
    if moeda in _memoria:
        return _memoria[moeda]

    valor = redis.get(f"cotacao:{moeda}")
    if valor is None:
        valor = db.buscar_cotacao(moeda)
        if valor is None:
            valor = api_bacen.cotacao(moeda)
            db.salvar_cotacao(moeda, valor)
        redis.setex(f"cotacao:{moeda}", 300, valor)

    _memoria[moeda] = valor
    return Decimal(valor)
```

**O que dói.** Cada camada nova é mais um nível de aninhamento. Rodar sem Redis significa comentar linhas, e isso acaba commitado. Para testar a regra "se o banco não tem, vai à API", é preciso ter o Redis e a memória no caminho. E a cotação de moedas não é a única coisa lida assim: o mesmo bloco, com outros nomes, aparece em quatro outros lugares.

**com o pattern — uma camada por elo, montadas por ambiente**

```python
class Elo:
    def __init__(self, proximo: "Elo | None" = None):
        self._proximo = proximo

    def obter(self, moeda: str) -> Decimal:
        valor = self._ler(moeda)
        if valor is None:
            if self._proximo is None:
                raise CotacaoIndisponivel(moeda)
            valor = self._proximo.obter(moeda)
            self._guardar(moeda, valor)   # a resposta volta preenchendo os elos de trás
        return valor

    def _ler(self, moeda): return None
    def _guardar(self, moeda, valor): pass

class EloMemoria(Elo):
    def __init__(self, proximo=None):
        super().__init__(proximo)
        self._itens = {}

    def _ler(self, moeda):          return self._itens.get(moeda)
    def _guardar(self, moeda, valor): self._itens[moeda] = valor

class EloRedis(Elo):
    def __init__(self, redis, proximo=None):
        super().__init__(proximo)
        self._redis = redis

    def _ler(self, moeda):
        bruto = self._redis.get(f"cotacao:{moeda}")
        return Decimal(bruto) if bruto else None

    def _guardar(self, moeda, valor):
        self._redis.setex(f"cotacao:{moeda}", 300, str(valor))

class EloApi(Elo):
    def __init__(self, cliente, proximo=None):
        super().__init__(proximo)
        self._cliente = cliente

    def _ler(self, moeda):
        return self._cliente.cotacao(moeda)

# a montagem é a única coisa que muda entre ambientes
cotacoes = EloMemoria(EloRedis(redis, EloApi(bacen)))   # produção
cotacoes = EloMemoria(EloApi(bacen))                  # dev, sem Redis
```

**O que a cadeia esconde.** Quantas camadas existem. Quem chama `cotacoes.obter("USD")` não sabe se a resposta veio da memória ou do outro lado da internet. Aqui, "não tratei" não é erro: é um *miss* comum, e a ordem dos elos expressa o custo. A resposta, ao voltar, preenche cada camada por onde passou, o que a escada aninhada fazia misturado com a leitura.

> **Dica.** Com uma camada só, nada disso se justifica: `functools.lru_cache` resolve "memória na frente de uma função". A cadeia começa a valer na segunda camada, e principalmente quando a lista muda por ambiente.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos quatro:

| Caso | Já coberto por |
|---|---|
| Suporte em níveis (N1, N2, N3), cada um resolvendo ou escalando | 1 — o primeiro com alçada trata; os demais não são consultados |
| Importar arquivos por formato: cada elo pergunta "sei ler isto?" | 1 — a escada vira uma fila de candidatos, e um formato novo é um elo novo |
| Filtros de moderação de comentários, cada um rejeitando ou deixando passar | 2 — cada elo pode barrar o pedido |
| Exceção que sobe a pilha até um `except` que sabe tratá-la | 3 — a cadeia é a estrutura que já existe |
| Loggers hierárquicos: um registro sobe de `app.pedidos` para `app` e para a raiz | 3 — mesma propagação, pela hierarquia de nomes |

E um caso que parece Chain of Responsibility, mas não é: publicar "pedido criado" para o e-mail, o estoque e a nota fiscal. Os três recebem o aviso, e nenhum decide se o outro recebe. Quando o pedido precisa chegar a todos, o nome é Observer — veja a seção [Parecidos](explicacao.md#parecidos) da explicação.
