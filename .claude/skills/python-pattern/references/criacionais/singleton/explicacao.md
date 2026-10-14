<!-- Gerado de pages/clean-code/criacionais/singleton/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Singleton — Explicação

*Clean Code / Design Pattern / Singleton*

Como garantir que um objeto existe uma vez só e que todo mundo chega nele, em vez de cada parte do sistema criar a sua própria cópia do que deveria ser único.

<a id="o-problema"></a>
## O problema

A aplicação lê um arquivo de configuração: host do SMTP, modo de manutenção, limites. Vários pontos do código precisam desses valores — o envio de e-mails, os relatórios, a API. A saída mais curta é cada um criar o seu `Configuracao()` quando precisa:

**antes — cada cliente cria e lê a sua própria cópia**

```python
class Configuracao:
    def __init__(self):
        with open("config.json", encoding="utf-8") as f:
            self.dados = json.load(f)

class Mailer:
    def __init__(self):
        self.config = Configuracao()   # lê o disco de novo

class Relatorio:
    def __init__(self):
        self.config = Configuracao()   # e de novo

# em algum ponto do painel de administração
config = Configuracao()
config.dados["modo_manutencao"] = True  # só esta cópia ficou sabendo
```

Nada na classe diz que ela deveria ser única, então ninguém a trata assim. Três coisas aparecem aos poucos: o arquivo é lido uma vez por cliente; as cópias **divergem** — o modo de manutenção ligado em uma não chega nas outras; e cada novo cliente decide sozinho como obter a configuração, sem ninguém no controle.

<a id="a-solucao"></a>
## A solução

Faça a própria classe controlar a criação: ela guarda a única instância e entrega sempre a mesma. Quem precisa dela não cria — pede. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Singleton | A classe que controla a própria criação | `Configuracao` |
| Instância única | O único objeto que existe, guardado na classe | O que `instancia()` devolve |
| Ponto de acesso | Como os clientes chegam nela | `Configuracao.instancia()` |
| Cliente | Quem usa, sem criar | `Mailer`, `Relatorio` |

O ponto é **quem decide quantos objetos existem**. Antes, a decisão estava espalhada em quem usa; agora está na classe, em um lugar só. Quem usa não consegue criar uma segunda cópia por distração.

<a id="implementacao"></a>
## Implementação

```python
import json
import threading

class Configuracao:
    # 1. a instância única, guardada na própria classe
    _instancia = None
    _trava = threading.Lock()

    def __init__(self):
        with open("config.json", encoding="utf-8") as f:
            self.dados = json.load(f)

    # 2. o ponto de acesso: cria na primeira vez, devolve sempre a mesma
    @classmethod
    def instancia(cls):
        if cls._instancia is None:
            with cls._trava:
                if cls._instancia is None:  # de novo: outra thread pode ter criado
                    cls._instancia = cls()
        return cls._instancia

# 3. os clientes: nunca chamam Configuracao()
class Mailer:
    def enviar(self, destino, texto):
        host = Configuracao.instancia().dados["smtp_host"]
        ...
```

> **Cuidado.** O Python não tem construtor privado: nada impede alguém de escrever `Configuracao()` e criar uma segunda instância. A garantia é de convenção. Se isso incomoda, o [exemplo 5 do Uso](uso.md#sem-global) mostra o caminho: criar uma vez, na inicialização, e passar adiante.

> **Dica.** Em Python e em JavaScript, **o módulo já é um Singleton**: ele é executado uma vez e o resultado fica em cache. Um `config = Configuracao()` no fim de `config.py`, com `from config import config` nos clientes, entrega a mesma instância sem nenhuma das linhas acima.

<a id="quando-usar"></a>
## Quando usar

O Singleton vale quando as três coisas acontecem ao mesmo tempo: ter **duas instâncias é um erro** (ou um custo alto demais), **vários pontos distantes** do código precisam da mesma, e o objeto vive **o processo inteiro**.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Recurso caro criado de novo a cada uso | `connect()` ou `load()` dentro de método de repositório ou de construtor de serviço | [Uso #1](uso.md#recurso-caro) |
| Duas cópias de um estado que deveria ser um só | `new Limitador()` em mais de um arquivo; o bug "só acontece em algumas telas" | [Uso #2](uso.md#estado-compartilhado) |
| Várias partes mexendo no mesmo recurso exclusivo | Ler, somar e gravar no mesmo arquivo; dois números iguais em registros diferentes | [Uso #3](uso.md#recurso-exclusivo) |
| Objeto pesado, nem sempre necessário | `global _modelo` com `if _modelo is None`; carga no `import` que atrasa o início | [Uso #4](uso.md#criacao-concorrente) |
| Unicidade desejada, mas o acesso global atrapalha | Teste que altera `X.instancia()` e contamina os seguintes; `reset()` só para teste | [Uso #5](uso.md#sem-global) |

> **Dica.** O que os sinais têm em comum: o problema nunca é "tenho um objeto só". É "**dois objetos** quebram alguma coisa". Se duas instâncias convivem bem, você não precisa de Singleton.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Ter duas instâncias quebra algo, ou só desperdiça um pouco?** Se só desperdiça, crie normalmente.
2. **Dá para criar uma na inicialização e passá-la a quem precisa?** Se sim, faça isso: você tem a unicidade sem o acesso global.
3. **Uma variável de módulo resolve?** Em Python e em JavaScript, quase sempre resolve.
4. **Só depois disso:** Singleton, com criação preguiçosa e trava, se houver concorrência.

<a id="quando-nao-usar"></a>
## Quando não usar

O Singleton é o padrão mais usado e o mais criticado, pelo mesmo motivo: ele é **estado global com uma roupa de objeto**. O custo é pago todo dia: dependências escondidas dentro dos métodos, testes que contaminam uns aos outros e código que não funciona com duas instâncias nem quando você precisa de duas.

| Situação | Por que não | Faça isto |
|---|---|---|
| Você só quer evitar passar um parâmetro | É conveniência, não necessidade. A dependência continua existindo, só ficou invisível | Receba pelo construtor |
| O objeto guarda estado mutável | Os testes alteram e o estado vaza para o teste seguinte | Uma instância por teste, injetada |
| Pode haver mais de uma no futuro (um por cliente, por tenant, por região) | "Uma só" vira premissa espalhada pelo código e custa caro de desfazer | Um objeto por chave, em um registro |
| A aplicação roda em vários processos ou servidores | O Singleton é "um por processo". Com 8 workers, são 8 instâncias — e nenhuma sabe das outras | Um recurso externo (banco, Redis) que seja a fonte única |
| Python ou JavaScript e o objeto não tem lógica de criação | O módulo já entrega isso, sem classe nem trava | Uma variável de módulo |

<a id="sinais-de-abuso"></a>
### Sinais de que o Singleton saiu do lugar

- **Virou depósito de estado global.** Um `Contexto.instancia()` com 40 campos, onde todo mundo pendura o que precisa. Isso é uma variável global com nome de classe.
- **Aparece dentro de tudo.** Se a leitura de um método exige saber que ele chama `Algo.instancia()` lá no meio, a assinatura mente sobre as dependências.
- **Tem `reset()` só para os testes.** Um método que existe para desfazer a própria unicidade é o sintoma de que ela não cabe naquele código.
- **Ganhou subclasses.** Singleton de uma hierarquia obriga a decidir qual das classes é "a" única, e quase sempre o resultado é um `if` escondido.
- **Existe "por precaução".** "Vai que criam duas" não é motivo: se duas não quebram nada, o Singleton só acrescenta um acoplamento.

> **Perigo.** O sinal mais comum: você escreveu `Singleton.reset()` para os testes passarem. O padrão está cobrando o preço de ser global.

> **Nota.** Na dúvida, crie a instância uma vez, na inicialização, e passe pelo construtor. Você tem "um só" na prática, e nada impede um teste de criar outra — que é exatamente o que um Singleton clássico impede.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Variável global / de módulo | É a versão sem cerimônia. Perde o controle explícito da criação, mas em Python e JS costuma ser suficiente |
| Injeção de dependência | Resolve *quem recebe* o objeto; o Singleton resolve *quantos existem*. Combinam: um contêiner de DI costuma ter escopo "singleton" |
| Flyweight | Compartilha muitas instâncias imutáveis, uma por valor diferente; o Singleton é uma só, quase sempre mutável |
| Classe estática / utilitária | Não tem instância: não implementa interface, não pode ser trocada em teste e não tem ciclo de vida |
| Factory Method / Abstract Factory | Decidem *qual* objeto criar. É comum a fábrica ser um Singleton, mas são problemas diferentes |

Regra prática: se a pergunta é "quantos objetos existem", é Singleton. Se é "quem recebe o objeto", é injeção.
