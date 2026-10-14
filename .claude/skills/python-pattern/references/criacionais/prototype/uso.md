<!-- Gerado de pages/clean-code/criacionais/prototype/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Prototype — Uso

*Clean Code / Design Pattern / Prototype*

Três situações em que o Prototype resolve o problema, além da duplicação de objetos da Explicação. Cada uma traz o código sem o pattern, o código com ele e o que o Prototype evita em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para copiar em vez de construir. Duplicar um objeto sem conhecer a classe já é o exemplo da [Explicação](explicacao.md#o-problema), e não se repete aqui. Quando dois casos se resolvem com o mesmo raciocínio — spawn de inimigos e criação de documentos a partir de um modelo carregado, por exemplo —, só um fica. O Prototype tem poucos motivos próprios, e boa parte do que parece servir se resolve com `dataclasses.replace`, como mostra [Quando não usar](explicacao.md#quando-nao-usar). Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o Prototype evita |
|---|---|---|
| 1 | [Criar do zero é caro, copiar é barato](#custo-de-criacao) | Refazer a montagem cara a cada objeto |
| 2 | [Modelos que o usuário define em tempo de execução](#modelos-do-usuario) | Uma subclasse para cada variante |
| 3 | [Um rascunho que pode ser descartado](#rascunho-e-desfazer) | Reconstruir à mão o estado anterior |

> **Nota.** Os módulos `db` e `parse_template`, e as classes (`Contrato`, `Tarefa`, `Configuracao`), são fictícios. A API de cópia (`copy.deepcopy`, o spread) é a real.

<a id="custo-de-criacao"></a>
## 1. Criar do zero é caro, copiar é barato

**Situação.** No fim do mês, o sistema gera 2.000 contratos de renovação. Cada contrato parte do mesmo modelo: um template em arquivo, com 200 cláusulas guardadas no banco. Montar o modelo envolve uma consulta e um *parse* do template; a única coisa que muda de um contrato para outro são os dados do cliente.

**sem o pattern — o modelo é montado de novo a cada contrato**

```python
class GeradorDeContratos:
    def gerar(self, cliente):
        clausulas = db.consultar(
            "SELECT * FROM clausulas WHERE modelo = 'padrao'"   # 200 linhas
        )
        template = parse_template("contrato_padrao.docx")   # ~300 ms
        contrato = Contrato(template, [Clausula(c) for c in clausulas])
        contrato.preencher(cliente)
        return contrato
```

**O que dói.** Para 2.000 clientes, são 2.000 consultas idênticas e 2.000 *parses* do mesmo arquivo — o resultado de cada passo é sempre o mesmo, e só o `preencher` é diferente. O lote passa de minutos para dezenas de minutos, e o banco recebe uma carga que ninguém pediu.

**com o pattern — o modelo é montado uma vez e clonado**

```python
import copy

class GeradorDeContratos:
    def __init__(self):
        self._prototipo = None

    def _montar_modelo(self):
        clausulas = db.consultar("SELECT * FROM clausulas WHERE modelo = 'padrao'")
        template = parse_template("contrato_padrao.docx")
        return Contrato(template, [Clausula(c) for c in clausulas])

    def gerar(self, cliente):
        if self._prototipo is None:
            self._prototipo = self._montar_modelo()   # uma vez

        contrato = copy.deepcopy(self._prototipo)    # memória, sem rede nem disco
        contrato.preencher(cliente)                  # só na cópia
        return contrato
```

**O que o Prototype evita.** **Refazer a montagem**. O custo da consulta e do *parse* é pago uma vez, e cada contrato custa uma cópia em memória. O protótipo é o contrato "em branco" ideal: ninguém o preenche nem o entrega; ele só existe para ser copiado.

> **Cuidado.** Duas condições para isso valer. Primeira: **meça**. Se montar o modelo custa 2 ms, a cópia não ganha nada e só acrescenta um estado guardado. Segunda: o protótipo nunca pode ser alterado — um `preencher` acidental nele e todos os contratos seguintes saem com os dados do primeiro cliente.

<a id="modelos-do-usuario"></a>
## 2. Modelos que o usuário define em tempo de execução

**Situação.** O gerenciador de projetos tem "modelos de tarefa": um bug já vem com prioridade alta, a etiqueta *bug* e um checklist de reproduzir, corrigir e testar. Hoje os modelos são fixos. O pedido é que **cada equipe crie os seus**, a partir de uma tarefa que já existe.

**sem o pattern — cada modelo é uma classe, escrita pelo time de desenvolvimento**

```typescript
class TarefaDeBug extends Tarefa {
  constructor() {
    super("", "alta", ["bug"], ["reproduzir", "corrigir", "testar"]);
  }
}

class TarefaDeReuniao extends Tarefa {
  constructor() {
    super("", "media", ["reuniao"], ["pauta", "ata"]);
  }
}

function criarTarefa(modelo: string): Tarefa {
  switch (modelo) {
    case "bug": return new TarefaDeBug();
    case "reuniao": return new TarefaDeReuniao();
    default: throw new Error(modelo);
  }
}
```

**O que dói.** As classes não diferem em comportamento — só em *valores*. Cada modelo novo é uma classe, um `case` e uma implantação. E o que se pede ("salvar esta tarefa como modelo") é impossível: um modelo criado pelo usuário em tempo de execução não pode ser uma classe escrita antes.

**com o pattern — o modelo é uma tarefa, guardada e clonada**

```typescript
class Tarefa {
  constructor(
    public titulo: string,
    public prioridade: string,
    public etiquetas: string[],
    public checklist: string[],
  ) {}

  clonar(): Tarefa {
    return new Tarefa(this.titulo, this.prioridade, [...this.etiquetas], [...this.checklist]);
  }
}

class CatalogoDeModelos {
  private modelos = new Map<string, Tarefa>();

  salvar(nome: string, tarefa: Tarefa) {
    this.modelos.set(nome, tarefa.clonar());   // guarda uma cópia, não a tarefa viva
  }

  criar(nome: string): Tarefa {
    const modelo = this.modelos.get(nome);
    if (!modelo) throw new Error(`modelo desconhecido: ${nome}`);
    return modelo.clonar();
  }
}

// em tempo de execução, pela interface
catalogo.salvar("Bug", tarefaAtual);
const nova = catalogo.criar("Bug");
```

**O que o Prototype evita.** **Uma subclasse por variante**. Aqui a variação está nos dados, e não na classe, então o modelo é um objeto que qualquer pessoa pode produzir. Este é o uso em que o Prototype é insubstituível: com construtores e classes, um modelo definido por quem usa o sistema simplesmente não cabe. O `CatalogoDeModelos` é o "registro de protótipos" do padrão.

> **Dica.** Repare em `modelos.set(nome, tarefa.clonar())`: o catálogo guarda uma *cópia*. Se guardasse a tarefa viva, editá-la depois alteraria o modelo — o sinal de abuso "o protótipo guardado é alterado por quem o usa".

<a id="rascunho-e-desfazer"></a>
## 3. Um rascunho que pode ser descartado

**Situação.** A tela de configurações tem os botões *Salvar* e *Cancelar*. Quem cancela espera que nada tenha mudado, mesmo depois de ter alterado o tema, o idioma e os atalhos.

**sem o pattern — o objeto é editado direto, e o "anterior" é guardado à mão**

```python
class TelaDeConfiguracao:
    def abrir(self, config):
        self.config = config
        self._anterior = {
            "tema": config.tema,
            "idioma": config.idioma,
            "atalhos": config.atalhos,   # a mesma lista: vai mudar junto
        }

    def cancelar(self):
        self.config.tema = self._anterior["tema"]
        self.config.idioma = self._anterior["idioma"]
        self.config.atalhos = self._anterior["atalhos"]
```

**O que dói.** A lista `atalhos` é a mesma nos dois lados: o usuário remove um atalho, cancela, e o "anterior" já estava sem ele. O campo `notificacoes`, acrescentado semana passada, não está na lista, e cancelar não o desfaz. E a lista de campos existe em dois lugares (`abrir` e `cancelar`) além da própria classe.

**com o pattern — o usuário edita uma cópia, e descartar é largá-la**

```python
class Configuracao:
    def clonar(self):
        return copy.deepcopy(self)

class TelaDeConfiguracao:
    def __init__(self, repositorio):
        self._repo = repositorio
        self.rascunho = None

    def abrir(self):
        self.rascunho = self._repo.atual().clonar()   # o usuário edita isto

    def salvar(self):
        self._repo.substituir(self.rascunho)

    def cancelar(self):
        self.rascunho = None                              # nada a desfazer
```

**O que o Prototype evita.** **Reconstruir o estado anterior à mão**. A configuração original nunca foi tocada, então não existe "desfazer": existe um objeto que se descarta. Um campo novo na `Configuracao` entra na cópia sozinho, porque `clonar()` não tem lista de campos.

> **Nota.** Isso cobre *um* nível de "voltar". Um histórico de desfazer com vários passos tem outro nome — Memento, normalmente em conjunto com o Command — e o Prototype é só o mecanismo de copiar o estado.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três, na Explicação, ou porque a resposta certa é outra:

| Caso | Já coberto por |
|---|---|
| Duplicar uma linha ou entidade em uma tela ("duplicar pedido") | Explicação — copiar sem conhecer a classe |
| Copiar e colar formas em um editor gráfico | Explicação — copiar sem conhecer a classe |
| Criar inimigos ou partículas a partir de um modelo já carregado | 1 — criar do zero é caro |
| Presets de exportação, de tema ou de filtro criados pelo usuário | 2 — modelos em tempo de execução |
| Fixtures de teste a partir de um objeto-base com um campo diferente | `dataclasses.replace(base, status="pago")`. Veja "Quando não usar" |
| Histórico de desfazer com vários níveis | 3 — um nível; o histórico completo é Memento |

E um caso que parece Prototype, mas não é: copiar com `dict(obj)`, `{ ...obj }` ou `JSON.parse(JSON.stringify(obj))`. É uma cópia solta, sem contrato: a primeira é rasa, e a última perde tipos e métodos (datas viram texto). Não há uma regra do objeto dizendo o que compartilhar e o que zerar, que é o que o padrão acrescenta. A seção [Parecidos](explicacao.md#parecidos) da explicação mostra a diferença para o Factory Method.
