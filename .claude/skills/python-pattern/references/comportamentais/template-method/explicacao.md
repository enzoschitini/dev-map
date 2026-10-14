<!-- Gerado de pages/clean-code/comportamentais/template-method/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Template Method — Explicação

*Clean Code / Design Pattern / Template Method*

Como escrever uma vez só a ordem dos passos de um processo, e deixar cada variação preencher apenas o passo que é diferente dela.

<a id="o-problema"></a>
## O problema

A loja importa catálogo de fornecedores. O primeiro manda CSV; o segundo, JSON. O roteiro é o mesmo nos dois: ler o arquivo, conferir os preços, gravar tudo em uma transação e registrar o que entrou. Só a leitura é diferente.

A saída preguiçosa é copiar a primeira função e trocar o miolo:

**antes — o roteiro copiado, e já divergindo**

```python
def importar_csv(caminho):
    with open(caminho, newline="") as f:
        produtos = [Produto(l["sku"], Decimal(l["preco"])) for l in csv.DictReader(f)]
    for p in produtos:
        if p.preco <= 0:
            raise ImportacaoInvalida(p.sku)
    with db.transacao():
        for p in produtos:
            db.salvar(p)
    log.info("importados %d produtos", len(produtos))

def importar_json(caminho):
    with open(caminho) as f:
        itens = json.load(f)["itens"]
    produtos = [Produto(i["codigo"], Decimal(str(i["valor"]))) for i in itens]
    for p in produtos:
        if p.preco <= 0:
            raise ImportacaoInvalida(p.sku)
    for p in produtos:          # a transação ficou para trás
        db.salvar(p)
    log.info("importados %d produtos", len(produtos))
```

Três coisas quebram daqui a pouco. As duas cópias já divergiram: a do JSON grava sem transação, e uma importação que falha no meio deixa o catálogo pela metade. Um terceiro formato é a terceira cópia, com a terceira chance de esquecer algo. E qualquer regra nova (rejeitar SKU repetido, por exemplo) é uma edição em cada função, sem nada que avise quando uma ficar de fora.

<a id="a-solucao"></a>
## A solução

Escreva o roteiro uma vez, em uma classe base, e deixe os passos que variam como buracos para as subclasses preencherem. Quem chama é a classe base: ela decide a ordem e, em cada ponto, pergunta à subclasse o que fazer. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Classe base | Dona do roteiro e dos passos que são iguais para todos | `Importador` |
| Método-template | O método que fixa a ordem dos passos | `importar()` |
| Passo variável | O buraco: obrigatório, ou com um padrão que pode ser trocado | `ler()`, `validar()` |
| Subclasse concreta | Preenche só o que é diferente dela | `ImportadorCsv`, `ImportadorJson` |

O ponto é a **direção da chamada**: o pai chama o filho, e não o contrário. A subclasse nunca decide quando seu passo roda nem o que vem antes ou depois dele. Por isso a transação, a ordem e o log não dependem de ninguém lembrar deles.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. a classe base: dona do roteiro
class Importador(ABC):

    # 2. o método-template: a ordem dos passos, escrita uma vez
    def importar(self, caminho):
        produtos = self.ler(caminho)
        self.validar(produtos)
        with db.transacao():
            for produto in produtos:
                db.salvar(produto)
        log.info("importados %d produtos", len(produtos))

    # 3. o passo que muda: a subclasse é obrigada a escrever
    @abstractmethod
    def ler(self, caminho) -> list[Produto]: ...

    # 4. um passo comum, com padrão que a subclasse pode trocar
    def validar(self, produtos):
        for p in produtos:
            if p.preco <= 0:
                raise ImportacaoInvalida(p.sku)

# 5. as subclasses: só o que é diferente
class ImportadorCsv(Importador):
    def ler(self, caminho):
        with open(caminho, newline="") as f:
            return [Produto(l["sku"], Decimal(l["preco"])) for l in csv.DictReader(f)]

class ImportadorJson(Importador):
    def ler(self, caminho):
        with open(caminho) as f:
            itens = json.load(f)["itens"]
        return [Produto(i["codigo"], Decimal(str(i["valor"]))) for i in itens]

ImportadorJson().importar("fornecedor-b.json")
```

> **Dica.** O roteiro agora se testa uma vez, com uma subclasse de cinco linhas cujo `ler` devolve uma lista fixa: confira que a transação envolve a gravação e que um preço zero aborta antes. Cada `ler` se testa sozinho, com um arquivo pequeno. Um formato novo é uma classe com um método.

<a id="quando-usar"></a>
## Quando usar

O Template Method vale quando três coisas acontecem ao mesmo tempo: existem **duas ou mais variantes** do mesmo processo; a **ordem** dos passos é a mesma em todas; e o que muda cabe em **poucos passos** bem nomeados, enquanto o resto é igual.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Funções quase iguais, com um miolo diferente | Duas funções com 80% das linhas iguais; uma correção feita em uma delas e esquecida na outra | [Uso #1](uso.md#mesmo-roteiro) |
| Um passo que nenhuma variante pode pular | `verificar_assinatura()` repetido em cada handler (e faltando em um); um `try/finally` copiado | [Uso #2](uso.md#passo-obrigatorio) |
| A política do processo varia pouco, de forma pontual | `if self.ativo:`, parâmetros `antes=None, depois=None` ou comentários "este job pula fim de semana" | [Uso #3](uso.md#ganchos-opcionais) |
| O mesmo roteiro com um tipo novo à vista | Um `if tipo == …` em cada passo do mesmo processo | [Uso #1](uso.md#mesmo-roteiro) |

> **Dica.** O que os sinais têm em comum: você encontra o *mesmo esqueleto* escrito mais de uma vez, e a diferença entre as cópias é pequena e fácil de apontar. Se for difícil dizer "o que muda é só isto", ainda não há um template.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Existe mais de uma variante do processo?** Se só há uma, escreva uma função. Ainda não há o que separar.
2. **A ordem dos passos é a mesma em todas?** Se a ordem muda de uma variante para outra, o esqueleto não é fixo: escreva cada fluxo, ou componha os passos de fora.
3. **O que varia cabe em um ou três passos?** Se quase tudo muda, sobra um esqueleto fino demais para valer uma classe base.
4. **Dá para passar o passo como função?** Se o que varia é uma ação sem estado, passe uma função como parâmetro. Herança só se paga quando as variantes têm vários passos e dados próprios.

<a id="quando-nao-usar"></a>
## Quando não usar

O custo do Template Method é a **herança**. A subclasse fica presa à classe base: qualquer mudança no esqueleto atinge todas, e o fluxo fica dividido em dois arquivos, de modo que, para saber o que acontece, é preciso abrir o pai e o filho. Cada hierarquia ainda varia em uma dimensão só.

| Situação | Por que não | Faça isto |
|---|---|---|
| Há uma variante só, sem segunda à vista | A classe base nasce sem ter o que compartilhar | Uma função. Extraia a classe base quando a segunda variante aparecer |
| O que varia é um passo único e simples | Uma hierarquia para uma ação é cerimônia | Passe uma função como parâmetro |
| A variação precisa mudar em tempo de execução | A herança é fixada quando o objeto é criado | Strategy: guarde o passo como objeto e troque-o |
| Duas coisas variam de forma independente (formato *e* destino) | A herança explode em uma subclasse por combinação | Composição, ou Bridge |
| A ordem dos passos muda entre as variantes | O método-template deixa de ser um esqueleto e vira um `if` disfarçado | Escreva cada fluxo, ou monte a sequência fora, como dados |
| Só abrir e fechar um recurso em volta de um trecho | É um roteiro de dois passos | `with` / `try/finally` |

<a id="sinais-de-abuso"></a>
### Sinais de que o Template Method saiu do lugar

- **A subclasse sobrescreve o próprio roteiro.** Se `importar` é redefinido, o esqueleto deixou de garantir qualquer coisa: cada subclasse tem o seu, e a garantia voltou a depender de cada autor.
- **Ganchos demais.** Doze pontos de extensão, cada um com um padrão, e ninguém sabe qual sobrescrever. Cada gancho é uma promessa que a classe base precisa manter para sempre.
- **Passos que viram `pass`.** Se várias subclasses implementam um passo abstrato com `pass` ou levantando `NotImplementedError`, o esqueleto não serve para todas.
- **"Lembre de chamar `super()`."** O passo só funciona se a subclasse chamar o pai na hora certa. Esse contrato fica na cabeça de quem escreve, não no código.
- **Hierarquia em três níveis.** A classe do meio redefine parte do roteiro e os netos redefinem outra parte. Ninguém sabe mais em que ordem as coisas rodam.

> **Perigo.** O sinal mais comum: subclasses que sobrescrevem o método-template inteiro "só desta vez". Python e TypeScript não têm `final` para impedir; proteja com um teste que falhe se alguma subclasse redefinir o roteiro, ou com uma convenção que a revisão de código cobre.

> **Nota.** Na dúvida, comece com uma função que recebe os passos que mudam como parâmetros. Quando as variantes ganharem estado próprio e vários passos, a classe base se paga, e a refatoração é pequena porque o roteiro já está escrito em um lugar.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Strategy | Troca o algoritmo inteiro por composição, até em tempo de execução. O Template Method fixa o esqueleto e varia as partes por herança, no momento em que a classe é escrita |
| [Factory Method](../../criacionais/factory-method/explicacao.md) | É um Template Method especializado em um passo só: criar o objeto. O roteiro usa o que a subclasse criou |
| [Decorator](../../estruturais/decorator/explicacao.md) | Acrescenta comportamento *em volta* de um objeto, por composição, sem herdar. No Template Method o pai chama a subclasse no meio do roteiro |
| [Observer](../observer/explicacao.md) | Avisa vários ouvintes que não podem mudar o fluxo; o gancho do Template Method é uma subclasse só, que preenche (e às vezes altera) um passo do roteiro |

Regra prática: se o esqueleto é herdado e os passos são métodos que o pai chama, é Template Method. Se o algoritmo é um objeto que se passa de fora, é Strategy.
