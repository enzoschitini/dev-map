<!-- Gerado de pages/clean-code/estruturais/composite/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Composite — Uso

*Clean Code / Design Pattern / Composite*

Quatro situações em que o Composite resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o composto unifica em cada caso.

<a id="como-escolhi"></a>
## Por que quatro

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Composite. Árvore de categorias com contagem de produtos, organograma com custo por área e kit com preço são o mesmo raciocínio do primeiro exemplo (agregar sobre uma árvore), então só um fica. Sobraram quatro motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o Composite unifica |
|---|---|---|
| 1 | [Várias operações sobre a mesma árvore](#pastas-e-arquivos) | Arquivo e pasta, diante de qualquer operação |
| 2 | [Regras que se combinam com E, OU e NÃO](#regras-combinaveis) | A regra simples e a regra composta |
| 3 | [Avisar uma pessoa ou um grupo de grupos](#um-ou-varios-destinatarios) | Um destinatário e vários |
| 4 | [Menu com itens que o usuário não pode ver](#menu-com-permissoes) | O link e o submenu, ao filtrar |

<a id="pastas-e-arquivos"></a>
## 1. Várias operações sobre a mesma árvore

**Situação.** Um serviço de armazenamento guarda arquivos e pastas, e as pastas contêm outras pastas. A tela precisa do tamanho total de uma pasta, da contagem de arquivos e da busca por extensão. Cada operação foi escrita por uma pessoa diferente, quando precisou.

**sem o pattern — cada função refaz a pergunta de tipo**

```python
def tamanho(no):
    if isinstance(no, Pasta):
        return sum(tamanho(f) for f in no.filhos)
    return no.bytes

def contar_arquivos(no):
    if isinstance(no, Pasta):
        return sum(contar_arquivos(f) for f in no.filhos)
    return 1

def buscar(no, extensao, caminho=""):
    if isinstance(no, Pasta):
        achados = []
        for f in no.filhos:
            achados += buscar(f, extensao, caminho + no.nome + "/")
        return achados
    return [caminho + no.nome] if no.nome.endswith(extensao) else []
```

**O que dói.** A recursão e o `isinstance` estão copiados em cada função. Quando o produto ganha um `Atalho` (um link para outra pasta, sem bytes próprios), é preciso lembrar de editar as três: a que for esquecida cai no `return no.bytes` e quebra com `AttributeError` em produção, no dia em que alguém tiver um atalho.

**com o pattern — cada nó sabe responder às três perguntas**

```python
class No(ABC):
    nome: str

    @abstractmethod
    def tamanho(self) -> int: ...
    @abstractmethod
    def contar_arquivos(self) -> int: ...
    @abstractmethod
    def buscar(self, extensao: str, caminho: str = "") -> list[str]: ...

class Arquivo(No):
    def __init__(self, nome, bytes_):
        self.nome, self._bytes = nome, bytes_

    def tamanho(self):
        return self._bytes

    def contar_arquivos(self):
        return 1

    def buscar(self, extensao, caminho=""):
        return [caminho + self.nome] if self.nome.endswith(extensao) else []

class Pasta(No):
    def __init__(self, nome, filhos: list[No]):
        self.nome, self._filhos = nome, filhos

    def tamanho(self):
        return sum(f.tamanho() for f in self._filhos)

    def contar_arquivos(self):
        return sum(f.contar_arquivos() for f in self._filhos)

    def buscar(self, extensao, caminho=""):
        achados = []
        for f in self._filhos:
            achados += f.buscar(extensao, caminho + self.nome + "/")
        return achados
```

**O que o composto unifica.** Arquivo e pasta diante de *qualquer* operação. A pergunta de tipo some do cliente, e a recursão passa a ser consequência de a pasta pedir a cada filho. O `Atalho` vira uma classe nova: como `No` é abstrata, esquecer uma das três operações dá erro na criação do objeto, não um bug silencioso meses depois.

> **Cuidado.** A troca é real: antes, uma operação nova era uma função; agora é um método em cada classe. Se as operações mudam mais que os tipos de nó (um relatório novo por semana, e os nós parados há anos), o Visitor tira as operações de dentro dos nós.

<a id="regras-combinaveis"></a>
## 2. Regras que se combinam com E, OU e NÃO

**Situação.** O marketing cria cupons por um painel e define quem tem direito: "primeira compra", "pedido acima de R$ 100", e agora também combinações — "primeira compra *e* acima de R$ 100", "acima de R$ 100 *ou* cliente premium". A regra de cada cupom precisa vir do cadastro, sem deploy.

**sem o pattern — cada combinação pedida vira um tipo**

```python
def elegivel(cupom, cliente, pedido):
    if cupom.tipo == "primeira_compra":
        return cliente.pedidos == 0
    if cupom.tipo == "valor_minimo":
        return pedido.total >= cupom.valor
    if cupom.tipo == "primeira_compra_e_valor_minimo":
        return cliente.pedidos == 0 and pedido.total >= cupom.valor
    if cupom.tipo == "premium_ou_valor_minimo":
        return cliente.premium or pedido.total >= cupom.valor
    # "primeira compra, mas não premium"? mais um tipo, mais um deploy
```

**O que dói.** Cada pedido do marketing vira código e deploy. Três regras simples geram dezenas de combinações, e o nome do tipo passa a ser uma expressão booleana em texto. Ninguém consegue montar "A e (B ou não C)" sem pedir ao time de engenharia.

**com o pattern — regras simples e regras que combinam regras**

```python
class Regra(Protocol):
    def vale(self, cliente, pedido) -> bool: ...

# folhas: uma pergunta cada
class PrimeiraCompra:
    def vale(self, cliente, pedido):
        return cliente.pedidos == 0

class ValorMinimo:
    def __init__(self, minimo):
        self._minimo = minimo

    def vale(self, cliente, pedido):
        return pedido.total >= self._minimo

# compostos: combinam outras regras, de qualquer tipo
class Todas:      # E
    def __init__(self, *regras):
        self._regras = regras

    def vale(self, cliente, pedido):
        return all(r.vale(cliente, pedido) for r in self._regras)

class Alguma:     # OU
    def __init__(self, *regras):
        self._regras = regras

    def vale(self, cliente, pedido):
        return any(r.vale(cliente, pedido) for r in self._regras)

class Nao:        # NÃO
    def __init__(self, regra):
        self._regra = regra

    def vale(self, cliente, pedido):
        return not self._regra.vale(cliente, pedido)

# a árvore vem do cadastro: {"tipo": "todas", "regras": [...]}
def montar(spec) -> Regra:
    tipo = spec["tipo"]
    if tipo == "todas":
        return Todas(*[montar(s) for s in spec["regras"]])
    if tipo == "alguma":
        return Alguma(*[montar(s) for s in spec["regras"]])
    if tipo == "nao":
        return Nao(montar(spec["regra"]))
    if tipo == "primeira_compra":
        return PrimeiraCompra()
    if tipo == "valor_minimo":
        return ValorMinimo(spec["valor"])
    raise ValueError(f"regra desconhecida: {tipo}")
```

**O que o composto unifica.** A regra simples e a regra composta, que respondem a `vale()` do mesmo jeito. O que este exemplo ensina e o anterior não: os compostos têm **semântica própria** (E, OU, NÃO), e a árvore é construída em tempo de execução, a partir de dado. Quem monta o cupom no painel pode aninhar o quanto quiser sem que o código mude. E `all` e `any` param na primeira resposta que decide, então regras caras no fim da lista só rodam quando precisam.

<a id="um-ou-varios-destinatarios"></a>
## 3. Avisar uma pessoa ou um grupo de grupos

**Situação.** O sistema de avisos manda e-mail para uma pessoa, mas o time de RH quer mandar para "Engenharia", que contém "Backend" e "Frontend", que têm gente. Alguns grupos entram em outros por engano, e há gente em mais de um grupo.

**sem o pattern — a função decide se é um ou vários, e vai só até o segundo nível**

```python
def avisar(destino, texto):
    if isinstance(destino, Pessoa):
        correio.enviar(destino.email, texto)
    elif isinstance(destino, Grupo):
        for m in destino.membros:
            if isinstance(m, Pessoa):
                correio.enviar(m.email, texto)
            else:
                for mm in m.membros:   # grupo dentro de grupo: um nível
                    correio.enviar(mm.email, texto)
```

**O que dói.** Um grupo dentro de um grupo dentro de um grupo ainda quebra. Quem está em "Backend" e em "Plantão" recebe o aviso duas vezes. E se alguém colocar "Engenharia" dentro de "Backend", a recursão (quando alguém a escrever) não termina.

**com o pattern — todo destino sabe listar as pessoas, sem repetir**

```python
class Destino(ABC):
    @abstractmethod
    def pessoas(self, vistos: set[str] | None = None) -> Iterator[Pessoa]: ...

class Pessoa(Destino):
    def __init__(self, id_, email):
        self.id, self.email = id_, email

    def pessoas(self, vistos=None):
        vistos = set() if vistos is None else vistos
        if self.id not in vistos:
            vistos.add(self.id)
            yield self

class Grupo(Destino):
    def __init__(self, id_, membros: list[Destino]):
        self.id, self._membros = id_, membros

    def pessoas(self, vistos=None):
        vistos = set() if vistos is None else vistos
        if self.id in vistos:      # já passou por aqui: ciclo ou repetição
            return
        vistos.add(self.id)
        for m in self._membros:
            yield from m.pessoas(vistos)

def avisar(destino: Destino, texto):
    for p in destino.pessoas():
        correio.enviar(p.email, texto)
```

**O que o composto unifica.** Uma pessoa e vários, para quem chama `avisar`: a função não sabe mais o que recebeu. O que este exemplo ensina é que dados reais raramente são árvores puras. "Mesma pessoa em dois grupos" e "grupo que contém a si mesmo" são grafos, e quem trata isso é o nó, com um conjunto de `vistos` que acompanha a travessia. O cliente continua sem saber.

> **Cuidado.** O Composite pressupõe árvore. Se a estrutura aceita compartilhamento ou ciclos, e a de grupos aceita, carregue o conjunto de visitados na operação. Sem ele, a recursão envia duas vezes ou não termina.

<a id="menu-com-permissoes"></a>
## 4. Menu com itens que o usuário não pode ver

**Situação.** O menu lateral do painel tem links e submenus que contêm outros submenus. Cada item pode exigir uma permissão. Usuário sem a permissão não deve ver o link, e um submenu que ficou sem nenhum link visível deve sumir, não aparecer vazio.

**sem o pattern — o filtro conhece exatamente dois níveis**

```typescript
function filtrar(menu: ItemMenu[], perms: Set<string>): ItemMenu[] {
  const saida: ItemMenu[] = [];
  for (const item of menu) {
    if (item.filhos) {
      const filhos = item.filhos.filter((f) => !f.perm || perms.has(f.perm));
      if (filhos.length > 0) saida.push({ ...item, filhos });
    } else if (!item.perm || perms.has(item.perm)) {
      saida.push(item);
    }
  }
  return saida;
}
```

**O que dói.** Um submenu dentro de um submenu passa sem filtro: os links do terceiro nível aparecem para quem não tem permissão. A permissão do próprio submenu é ignorada. E a regra "grupo vazio some" só vale para o primeiro nível, então aparece um submenu com título e sem itens.

**com o pattern — filtrar devolve o nó filtrado, ou nada**

```typescript
interface NoMenu {
  /** o nó que sobrou para estas permissões, ou null se ele some */
  filtrar(perms: Set<string>): NoMenu | null;
  renderizar(): string;
}

class Link implements NoMenu {
  constructor(private rotulo: string, private href: string, private perm?: string) {}

  filtrar(perms: Set<string>) {
    return !this.perm || perms.has(this.perm) ? this : null;
  }

  renderizar() {
    return `<li><a href="${this.href}">${this.rotulo}</a></li>`;
  }
}

class Submenu implements NoMenu {
  constructor(private rotulo: string, private filhos: NoMenu[]) {}

  filtrar(perms: Set<string>) {
    const visiveis = this.filhos
      .map((f) => f.filtrar(perms))
      .filter((f): f is NoMenu => f !== null);
    return visiveis.length > 0 ? new Submenu(this.rotulo, visiveis) : null;
  }

  renderizar() {
    return `<li>${this.rotulo}<ul>${this.filhos.map((f) => f.renderizar()).join("")}</ul></li>`;
  }
}

// o cliente: duas linhas, qualquer profundidade
const visivel = raiz.filtrar(permissoesDoUsuario);
const html = visivel ? visivel.renderizar() : "";
```

**O que o composto unifica.** O link e o submenu diante de uma operação que **devolve uma árvore nova**, e não um número ou um booleano. Aqui o composto decide pelo que sobrou dos filhos: a regra "submenu sem nada visível some" está escrita uma vez e vale em todos os níveis. A árvore original não é alterada, então o mesmo menu serve a todos os usuários e cada um recebe a sua versão.

> **Cuidado.** Esconder o link não é controle de acesso. Quem sabe a URL ainda chega na rota, e o servidor precisa checar a permissão de novo. O filtro do menu cuida de quem *vê*, não de quem *pode*.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos quatro:

| Caso | Já coberto por |
|---|---|
| Kit com kits dentro, com preço e peso | 1 — operações sobre uma árvore; é o exemplo da [explicação](explicacao.md#o-problema) |
| Árvore de categorias com contagem de produtos | 1 — operações sobre uma árvore |
| Organograma com custo por área | 1 — operações sobre uma árvore |
| Formulário com seções e campos, validando tudo | 2 — a validação composta responde "vale?" como as regras |
| Macro: uma lista de comandos executada como um só | 3 — um comando e vários, tratados igual |
| Formas vetoriais com grupos de formas | 1 e 3 — operações sobre uma árvore, com o mesmo cuidado se um nó entra em dois grupos |
| Árvore de componentes de UI (o DOM, o React) | 4 — a operação desce e devolve uma árvore nova; o DOM já é um Composite |

E um caso que parece Composite, mas não é: o carrinho que contém produtos. É uma lista de coisas de um nível só, e nenhum item contém outros itens. Se ela virar uma árvore (kits dentro de kits), aí sim. E um objeto que embrulha outro da mesma interface para acrescentar log ou cache é Decorator. Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.
