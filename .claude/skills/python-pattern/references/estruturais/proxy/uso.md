<!-- Gerado de pages/clean-code/estruturais/proxy/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Proxy — Uso

*Clean Code / Design Pattern / Proxy*

Três situações em que o Proxy resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o proxy controla em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Proxy. O carregamento preguiçoso (o *proxy virtual*) já está inteiro na [explicação](explicacao.md#implementacao), e imagens, documentos e relações de ORM sob demanda são o mesmo raciocínio. Sobraram três motivos que ela não cobre: *quem* pode chamar, *onde* o objeto mora e *o que* acontece com os campos dele. Os casos que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o proxy controla |
|---|---|---|
| 1 | [A mesma folha de pagamento, vista por papéis diferentes](#acesso-por-papel) | Quem pode chamar cada método, e com quais argumentos |
| 2 | [Um módulo que virou serviço, com 40 chamadores](#servico-extraido) | Onde o objeto mora |
| 3 | [Salvar só o que o usuário mudou](#mudancas-de-campos) | O que acontece com os campos do objeto |

> **Nota.** Os módulos `estoque` e `folha` e o serviço de estoque do segundo exemplo são fictícios. As chamadas de `requests` usam o formato real, simplificado.

<a id="acesso-por-papel"></a>
## 1. A mesma folha de pagamento, vista por papéis diferentes

**Situação.** O RH vê o salário de todos. Cada gestor vê só o da própria equipe. Só a diretoria pode aplicar reajuste. A folha é usada por uma API, por três relatórios e por uma exportação mensal, escritos por pessoas diferentes.

**sem o pattern — cada chamador lembra (ou não) de checar**

```python
# relatorios/custo.py
def custo_por_area(folha, usuario, area):
    if usuario.papel not in ("rh", "diretoria"):
        raise Proibido()
    return sum(folha.salario_de(f.id) for f in area.funcionarios)

# api/salarios.py
def get_salario(folha, usuario, funcionario_id):
    if usuario.papel == "gestor" and not eh_subordinado(usuario, funcionario_id):
        raise Proibido()
    return folha.salario_de(funcionario_id)

# exportacao/mensal.py
def exportar(folha, funcionarios):
    return [(f.nome, folha.salario_de(f.id)) for f in funcionarios]   # sem checagem nenhuma
```

**O que dói.** A regra de acesso está em cada chamador, escrita de um jeito, e a exportação mensal não tem nenhuma. Um chamador novo nasce sem proteção, e nada falha: o dado só vaza. Quando a regra muda ("gestor também vê o salário do próprio gestor"), são seis lugares para achar.

**com o pattern — quem recebe a folha só recebe o proxy**

```python
class Folha(Protocol):
    def salario_de(self, funcionario_id: str) -> Decimal: ...
    def reajustar(self, funcionario_id: str, percentual: Decimal) -> None: ...

class FolhaDePagamento:
    """O objeto real: faz o trabalho e não sabe de papéis."""
    ...

class FolhaProtegida:
    def __init__(self, real: Folha, usuario, politica):
        self._real, self._usuario, self._politica = real, usuario, politica

    def salario_de(self, funcionario_id):
        if not self._politica.pode_ver_salario(self._usuario, funcionario_id):
            raise Proibido("salario_de", funcionario_id)
        return self._real.salario_de(funcionario_id)

    def reajustar(self, funcionario_id, percentual):
        if not self._politica.pode_reajustar(self._usuario):
            raise Proibido("reajustar", funcionario_id)
        self._real.reajustar(funcionario_id, percentual)

# na montagem da requisição: o real nunca sai daqui
folha: Folha = FolhaProtegida(FolhaDePagamento(db), usuario, politica)
```

**O que o proxy controla.** Quem pode chamar cada método, **com quais argumentos**. Isso é mais que o Decorator de permissão por função: a decisão depende do `funcionario_id` pedido, e o proxy carrega o *usuário* que faz a chamada. Relatórios, API e exportação recebem um `Folha` e não têm como esquecer a checagem, porque ela não está neles. A `FolhaDePagamento` real não sabe que existem papéis.

> **Cuidado.** A proteção só vale se o real não vaza. Se algum código ainda recebe a `FolhaDePagamento` diretamente, ou se o proxy expõe `.real`, o proxy protege os chamadores que o respeitam e ninguém mais. A montagem é o lugar onde isso se garante.

<a id="servico-extraido"></a>
## 2. Um módulo que virou serviço, com 40 chamadores

**Situação.** O módulo de estoque, que morava dentro do monólito, foi extraído para um serviço próprio. O monólito o chama em 40 lugares por `estoque.disponivel(sku)` e `estoque.reservar(sku, quantidade)`. A mudança de endereço não pode vir com uma reescrita dos 40.

**sem o pattern — cada chamador virou um cliente HTTP**

```python
# em 40 lugares, cada um de um jeito
resp = requests.get(f"{ESTOQUE_URL}/skus/{sku}/disponivel", timeout=2)
resp.raise_for_status()
disponivel = resp.json()["quantidade"]

# e em outros, sem timeout:
resp = requests.post(f"{ESTOQUE_URL}/skus/{sku}/reservas", json={"quantidade": qtd})
```

**O que dói.** A localização do serviço, o formato do JSON e o tratamento de falha estão em 40 lugares, alguns sem *timeout*. O código de domínio, que só queria saber se há estoque, agora conhece URLs. Voltar atrás ou migrar aos poucos (alguns chamadores no serviço, outros no módulo antigo) é impraticável. E testar qualquer um exige falsificar `requests`.

**com o pattern — o serviço remoto atrás da interface que sempre existiu**

```python
class Estoque(Protocol):
    def disponivel(self, sku: str) -> int: ...
    def reservar(self, sku: str, quantidade: int) -> Reserva: ...

class EstoqueRemoto:
    """O proxy: fala a interface de Estoque, mas o objeto real está em outro processo."""

    def __init__(self, base_url: str, sessao=None):
        self._url = base_url
        self._http = sessao or requests.Session()

    def disponivel(self, sku):
        corpo = self._chamar("GET", f"/skus/{sku}/disponivel")
        return corpo["quantidade"]

    def reservar(self, sku, quantidade):
        corpo = self._chamar("POST", f"/skus/{sku}/reservas", json={"quantidade": quantidade})
        return Reserva(corpo["id"], sku, quantidade)

    def _chamar(self, metodo, caminho, **kwargs):
        try:
            resp = self._http.request(metodo, self._url + caminho, timeout=2, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise EstoqueIndisponivel(caminho) from e

# na montagem: um flag escolhe o real local ou o proxy remoto
estoque: Estoque = EstoqueRemoto(ESTOQUE_URL) if USAR_SERVICO else EstoqueLocal(db)
```

**O que o proxy controla.** *Onde* o objeto mora. Os 40 chamadores continuam como estavam, e a decisão "local ou remoto" mora em uma linha de montagem, o que permite migrar por ambiente ou por percentual de tráfego. Os testes usam o `EstoqueLocal`, sem rede. É o *proxy remoto* do catálogo clássico: um representante local de algo que está em outro lugar, o mesmo papel dos *stubs* gerados por gRPC e por geradores de cliente OpenAPI.

> **Cuidado.** A interface é a mesma, mas a rede não é um método. `disponivel()` agora pode demorar e falhar, e `reservar()` repetido por causa de um *timeout* pode reservar duas vezes. Os chamadores precisam decidir o que fazer com `EstoqueIndisponivel`, e a reserva precisa ser idempotente (uma chave por tentativa). O proxy esconde a localização, e não a falha.

<a id="mudancas-de-campos"></a>
## 3. Salvar só o que o usuário mudou

**Situação.** A tela de pedido edita um `Pedido` com 20 campos. Duas pessoas trabalham no mesmo pedido: uma muda o status, a outra escreve uma observação. O salvamento grava o objeto inteiro.

**sem o pattern — o UPDATE leva os 20 campos, inclusive os que ninguém tocou**

```python
pedido = repo.buscar(pedido_id)        # 20 campos, lidos às 10:00:00
pedido.status = "enviado"              # só isto mudou
repo.salvar(pedido)
# UPDATE pedidos SET status=?, endereco=?, observacao=?, ... WHERE id=?
# a observação que a outra pessoa gravou às 10:00:03 foi sobrescrita pelo valor antigo
```

**O que dói.** O último a salvar apaga o trabalho de quem salvou antes, em campos que nem tocou, sem erro e sem aviso. Comparar com um `copy.deepcopy` feito ao carregar resolveria, mas cada objeto passaria a existir duas vezes, o que pesa em grafos grandes, e a comparação teria de ser escrita para cada classe.

**com o pattern — um proxy que anota cada campo alterado**

```python
class Rastreado:
    """Proxy dinâmico: repassa tudo ao alvo e anota o que foi alterado."""

    def __init__(self, alvo):
        object.__setattr__(self, "_alvo", alvo)
        object.__setattr__(self, "_mudancas", {})

    def __getattr__(self, nome):         # só é chamado para o que o proxy não tem
        return getattr(self._alvo, nome)

    def __setattr__(self, nome, valor):
        if getattr(self._alvo, nome) != valor:
            self._mudancas[nome] = valor
            setattr(self._alvo, nome, valor)

    def campos_alterados(self) -> dict:
        return dict(self._mudancas)

pedido = Rastreado(repo.buscar(pedido_id))
pedido.status = "enviado"
repo.atualizar(pedido_id, pedido.campos_alterados())
# UPDATE pedidos SET status=? WHERE id=?
```

**O que o proxy controla.** O que acontece com os campos do objeto, sem que a classe `Pedido` mude. Este é o *proxy dinâmico*: em vez de escrever um método por método da interface (como nos outros dois), ele intercepta o acesso a atributo e repassa o resto. Por isso serve a qualquer objeto, de 3 ou de 300 campos. O `Pedido` não sabe que está sendo observado, e a tela edita como sempre editou.

> **Cuidado.** O proxy dinâmico tem limites. `isinstance(pedido, Pedido)` é falso; mudanças dentro de uma lista aninhada (`pedido.itens.append(...)`) não passam pelo `__setattr__`; e métodos especiais como `len()` ou `==` não passam pelo `__getattr__`. Para ORM de verdade, use o que a biblioteca já traz (o *unit of work* do SQLAlchemy faz esse rastreamento).

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na explicação):

| Caso | Já coberto por |
|---|---|
| Imagem ou documento pesado, carregado só quando aparece na tela | Explicação — o proxy virtual |
| Relação de ORM carregada sob demanda (*lazy loading*) | Explicação — o proxy virtual |
| Cliente gerado por gRPC ou por OpenAPI | 2 — representante local de algo remoto |
| Limite de requisições ou cota por chave de API | 1 — a decisão depende de quem chama |
| Auditoria de quem leu qual registro | 1 — o proxy conhece o usuário e os argumentos |
| Espião ou *mock* em testes, que registra as chamadas | 3 — proxy que observa sem a classe saber |

E um caso que parece Proxy, mas não é: um cache, ou uma tentativa extra, na frente de um cliente. Tem a mesma forma (um objeto com a mesma interface na frente do real), mas não controla o alcance: acrescenta algo em *toda* chamada. É Decorator. Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.
