<!-- Gerado de pages/clean-code/estruturais/decorator/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Decorator — Explicação

*Clean Code / Design Pattern / Decorator*

Como acrescentar comportamento a um objeto sem mexer nele e sem criar uma subclasse para cada combinação de extras.

<a id="o-problema"></a>
## O problema

O sistema busca produtos em uma API do ERP: `catalogo.buscar(sku)`. Ela é lenta e, de vez em quando, cai. Então alguém põe um cache. Depois, o time de operações pede o tempo de cada chamada no log. Depois, uma tentativa extra quando a API falha.

Cada pedido é pequeno e vai para o mesmo lugar: a classe que já existe, com mais um parâmetro.

**antes — cada extra vira uma flag e um if dentro do mesmo método**

```python
class CatalogoHttp:
    def __init__(self, url, usar_cache=False, tentativas=1, logar=False):
        self._url, self._cache = url, {}
        self._usar_cache, self._tentativas, self._logar = usar_cache, tentativas, logar

    def buscar(self, sku):
        if self._usar_cache and sku in self._cache:
            return self._cache[sku]

        for tentativa in range(self._tentativas):
            inicio = time.perf_counter()
            try:
                resp = requests.get(f"{self._url}/produtos/{sku}", timeout=3)
                resp.raise_for_status()
                break
            except requests.RequestException:
                if tentativa == self._tentativas - 1:
                    raise
            finally:
                if self._logar:
                    log.info("buscar %s: %.0f ms", sku, (time.perf_counter() - inicio) * 1000)

        produto = Produto(**resp.json())
        if self._usar_cache:
            self._cache[sku] = produto
        return produto
```

Funciona, e o próximo extra (métricas, circuit breaker) cabe em mais um `if`. O problema está no que a classe virou: **uma** classe que busca na rede, guarda cache, mede tempo e repete tentativa, o que quebra o Single Responsibility e o Open/Closed ao mesmo tempo. O cache só pode ser testado com a rede, ou com a classe inteira falsificada. Quem só quer o log paga a complexidade do resto. E a ordem das camadas, que é uma decisão ("o log mede só a rede ou também o cache?"), ficou enterrada na ordem das linhas.

<a id="a-solucao"></a>
## A solução

Uma peça por extra, e todas com a **mesma interface** do objeto original. Cada uma guarda outro objeto dessa interface, faz o seu trabalho e repassa a chamada. O cliente monta a pilha que quiser. Os papéis são quatro:

| Papel | Quem é | No exemplo |
|---|---|---|
| Componente | A interface que todos implementam | `Catalogo` |
| Componente concreto | O objeto de verdade, no fundo da pilha | `CatalogoHttp` |
| Decorador | Implementa o componente *e* guarda outro componente; acrescenta algo antes ou depois de repassar | `ComCache`, `ComRetry`, `ComLog` |
| Cliente | Quem monta a pilha e usa o resultado como um `Catalogo` qualquer | A montagem da aplicação |

O ponto é que o decorador é **um** componente e **tem um** componente. É isso que permite empilhar: quem usa a pilha não sabe quantas camadas existem, e quem escreve uma camada não sabe o que está embaixo dela. A ordem de embrulho é a ordem de execução, e fica visível em uma linha.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod
import time

# 1. o componente: a interface que todas as camadas respeitam
class Catalogo(ABC):
    @abstractmethod
    def buscar(self, sku: str) -> Produto: ...

# 2. o componente concreto: só sabe falar com a API
class CatalogoHttp(Catalogo):
    def __init__(self, url: str):
        self._url = url

    def buscar(self, sku):
        try:
            resp = requests.get(f"{self._url}/produtos/{sku}", timeout=3)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise CatalogoIndisponivel(sku) from e
        return Produto(**resp.json())

# 3. os decoradores: cada um faz uma coisa e repassa o resto
class ComCache(Catalogo):
    def __init__(self, interno: Catalogo):
        self._interno, self._cache = interno, {}

    def buscar(self, sku):
        if sku not in self._cache:
            self._cache[sku] = self._interno.buscar(sku)
        return self._cache[sku]

class ComRetry(Catalogo):
    def __init__(self, interno: Catalogo, tentativas: int = 3):
        self._interno, self._tentativas = interno, tentativas

    def buscar(self, sku):
        for tentativa in range(self._tentativas):
            try:
                return self._interno.buscar(sku)
            except CatalogoIndisponivel:
                if tentativa == self._tentativas - 1:
                    raise

class ComLog(Catalogo):
    def __init__(self, interno: Catalogo):
        self._interno = interno

    def buscar(self, sku):
        inicio = time.perf_counter()
        try:
            return self._interno.buscar(sku)
        finally:
            log.info("buscar %s: %.0f ms", sku, (time.perf_counter() - inicio) * 1000)

# 4. o cliente monta a pilha, de fora para dentro: log, cache, retry, rede
catalogo = ComLog(ComCache(ComRetry(CatalogoHttp(URL_DO_ERP))))
```

> **Dica.** Cada camada passa a ser testada com um `Catalogo` falso embaixo dela. O teste do `ComCache` é um falso que conta quantas vezes foi chamado: duas buscas do mesmo SKU, uma chamada. Nenhuma rede e nenhum mock de biblioteca.

<a id="quando-usar"></a>
## Quando usar

O Decorator vale quando três coisas acontecem ao mesmo tempo: você quer **acrescentar** algo a um objeto que já tem uma interface, o acréscimo é **independente** do que está sendo embrulhado (cache vale para qualquer catálogo), e as **combinações variam** conforme o uso, ou você não pode (ou não quer) alterar a classe.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Recursos transversais ligados e desligados por parâmetro | Um construtor com `usar_cache=`, `logar=`, `tentativas=` e um `if self._logar` dentro de cada método | [Implementação, acima](#implementacao) |
| Subclasses cujo nome lista os extras | `IngressoMeiaComCombo`, `IngressoMeiaComComboVip`: um "Com" acumulando | [Uso #1](uso.md#adicionais-no-checkout) |
| Adicionais que o usuário escolhe em tempo de execução | Booleanos na assinatura (`combo=False, vip=False`) e um `if` para cada um, repetido em preço e em descrição | [Uso #1](uso.md#adicionais-no-checkout) |
| Comportamento a acrescentar a um objeto que passa por vários consumidores | Contagem, limite ou hash misturados ao laço que lê; `.read()` chamado duas vezes | [Uso #2](uso.md#upload-com-limite) |
| O mesmo trecho no início e no fim de dezenas de funções | O `try/finally` de métrica ou o `if not permitido` copiado em cada handler | [Uso #3](uso.md#funcoes-de-handler) |

> **Dica.** Os sinais têm uma coisa em comum: "o que a coisa faz" e "o que acontece em volta dela" estão no mesmo corpo. O Decorator move o "em volta" para fora, e o corpo volta a ser só o que a coisa faz.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **O acréscimo é independente do que está embrulhado?** Se ele precisa de campos privados ou de detalhes internos, não dá para fazer de fora: é subclasse, ou uma mudança na própria classe. Pare.
2. **A interface pode continuar a mesma?** Se o acréscimo exige que o cliente chame um método novo, deixou de ser decorador: é outra interface, e o nome do que você quer é Adapter ou Facade.
3. **O acréscimo é opcional ou varia por uso?** Se todo uso precisa dele, sempre, e a classe é sua, escreva dentro dela. A camada só custa mais um salto.
4. **Existe mais de um acréscimo, ou ele vai ser usado em mais de um lugar?** Se é um só, em um lugar só, deixe no corpo. Se são dois ou mais, ou o mesmo em vários lugares, é Decorator.

<a id="quando-nao-usar"></a>
## Quando não usar

O Decorator tem um custo que se paga em depuração: cada camada é um salto a mais na pilha de chamadas, e o objeto que você tem na mão deixa de ser o que você criou (`isinstance` e igualdade por identidade mudam). A ordem das camadas altera o resultado e não aparece no tipo. E, se a interface for grande, cada decorador precisa repassar todos os métodos para mudar um.

| Situação | Por que não | Faça isto |
|---|---|---|
| A interface tem dez métodos ou mais | Cada decorador repassa todos para alterar um; o código é quase todo delegação | Reduza a interface, ou use um Proxy que repassa o resto automaticamente (`__getattr__`) |
| O acréscimo é sempre ligado e usado em um lugar só | A camada só acrescenta um salto na leitura | Escreva no corpo. Extraia quando o segundo caso aparecer |
| O acréscimo precisa do estado interno do objeto | O decorador só enxerga a interface pública | Subclasse, ou mude a própria classe |
| Você precisa mudar a interface | O Decorator mantém a interface; converter é outro problema | Adapter |
| Você precisa controlar *se e quando* o objeto real é usado (criação sob demanda, permissão) | É a mesma forma, com outra intenção: gerenciar o acesso | Proxy |

<a id="sinais-de-abuso"></a>
### Sinais de que o Decorator saiu do lugar

- **O decorador conhece o que embrulha.** Um `isinstance(self._interno, CatalogoHttp)` dentro do cache mostra que a camada depende de um tipo, e a pilha deixou de ser intercambiável.
- **A pilha é montada em cinco lugares, cada um de um jeito.** A ordem passa a ser um acidente. Monte em uma função só, com nome.
- **A ordem foi descoberta por tentativa e erro.** Sem comentário e sem teste, o próximo a mexer inverte duas camadas e o cache passa a guardar erros.
- **O decorador faz o trabalho do componente.** Se `ComCache` também sabe falar com a API, virou uma subclasse com outro nome.
- **Camada que só repassa.** Um decorador que ficou sem comportamento depois de uma refatoração é uma indireção sem função.

> **Perigo.** O sinal mais comum: o cliente faz um *cast* para o decorador para chamar um método que só ele tem (`catalogo.limpar_cache()`). A interface deixou de ser a mesma, e o pattern virou uma forma complicada de herança.

> **Nota.** Na dúvida, comece com o comportamento dentro do corpo, em um lugar só. A extração é pequena quando o segundo uso ou a segunda combinação aparecem: o trecho vira uma classe que implementa a mesma interface e recebe a original no construtor.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Proxy | Tem a mesma forma, mas controla o *acesso*: cria o objeto real sob demanda, checa permissão, fala com algo remoto. O Decorator acrescenta comportamento e é empilhado por quem usa |
| [Adapter](../adapter/explicacao.md) | Muda a interface e não acrescenta nada. O Decorator mantém a interface e acrescenta |
| [Composite](../composite/explicacao.md) | Mesma estrutura de "objeto que guarda outro da mesma interface", mas guarda *vários* e combina as respostas. O Decorator guarda um e o repassa |
| [Chain of Responsibility](../../comportamentais/chain-of-responsibility/explicacao.md) | Cada elo decide se trata o pedido ou passa adiante, e ele termina em um. No Decorator todas as camadas acrescentam algo e o componente real responde |
| Strategy | Troca o miolo do algoritmo, por dentro. O Decorator envolve por fora, sem mexer no miolo |

Regra prática: se o objeto que embrulha implementa a mesma interface para acrescentar algo, e quem usa escolhe de fora quais embrulhos empilhar, é Decorator; se ele decide se e quando o objeto real é usado, é Proxy.
