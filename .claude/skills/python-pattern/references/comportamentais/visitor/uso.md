<!-- Gerado de pages/clean-code/comportamentais/visitor/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Visitor — Uso

*Clean Code / Design Pattern / Visitor*

Três situações em que o Visitor resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o visitante absorve.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Visitor. "Várias operações sobre uma estrutura estável" é o exemplo da [Explicação](explicacao.md#o-problema), e gerar HTML, Markdown ou texto de um documento em árvore se resolve com o mesmo raciocínio. O Visitor é um pattern estreito, e a página prefere ser curta a inventar um quarto motivo. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o visitante absorve |
|---|---|---|
| 1 | [Um relatório que precisa de antes e depois de cada pasta](#relatorio-de-arquivos) | O que fazer antes e depois de cada tipo, e o estado acumulado |
| 2 | [Analisar uma árvore que não é sua](#ast-nodevisitor) | A operação, para nós que você não pode alterar |
| 3 | [Reescrever uma árvore sem mutá-la](#simplificar-regras) | A recursão de reconstruir a árvore, para cada transformação |

> **Nota.** O exemplo 2 usa o módulo `ast` da biblioteca padrão do Python; os nomes de classe e de método são os reais. Os exemplos 1 e 3 usam classes fictícias, definidas na própria página.

<a id="relatorio-de-arquivos"></a>
## 1. Um relatório que precisa de antes e depois de cada pasta

**Situação.** Uma ferramenta de limpeza de disco imprime a árvore de arquivos, com recuo, e mostra ao lado de cada pasta o total ocupado por tudo o que há dentro dela. O tamanho da pasta só se sabe *depois* de visitar os filhos, mas a linha dela precisa aparecer *antes*. Ao mesmo tempo, o relatório conta quantos arquivos há por extensão.

**sem o pattern — o total de cada pasta é recalculado em cada nível**

```python
def tamanho_total(no):
    if isinstance(no, Pasta):
        return sum(tamanho_total(f) for f in no.filhos)
    return no.tamanho

def imprimir(no, nivel=0):
    if isinstance(no, Pasta):
        print("  " * nivel + f"{no.nome}/ — {tamanho_total(no)} B")   # percorre a subárvore inteira
        for filho in no.filhos:
            imprimir(filho, nivel + 1)
    else:
        print("  " * nivel + f"{no.nome} ({no.tamanho} B)")

def por_extensao(no, acc=None):
    acc = {} if acc is None else acc
    if isinstance(no, Pasta):
        for f in no.filhos:
            por_extensao(f, acc)
    else:
        acc[no.extensao] = acc.get(no.extensao, 0) + 1
    return acc
```

**O que dói.** Para imprimir o total de cada pasta, `imprimir` chama `tamanho_total`, que percorre toda a subárvore, e isso se repete em cada nível: o custo cresce com o quadrado da profundidade. Cada operação percorre a árvore por conta própria, com o mesmo esqueleto, e o acumulador vira um argumento extra passado por todos os níveis.

**com o pattern — um visitante que desce, acumula e sobe com o resultado**

```python
class Arquivo:
    def __init__(self, nome, tamanho):
        self.nome, self.tamanho = nome, tamanho
        self.extensao = nome.rpartition(".")[2] if "." in nome else ""

    def aceitar(self, v):
        return v.visitar_arquivo(self)

class Pasta:
    def __init__(self, nome, filhos):
        self.nome, self.filhos = nome, filhos

    def aceitar(self, v):
        return v.visitar_pasta(self)

class Relatorio:
    def __init__(self):
        self.linhas = []
        self.por_extensao = {}
        self._nivel = 0

    def visitar_arquivo(self, arquivo):
        self.linhas.append("  " * self._nivel + f"{arquivo.nome} ({arquivo.tamanho} B)")
        self.por_extensao[arquivo.extensao] = self.por_extensao.get(arquivo.extensao, 0) + 1
        return arquivo.tamanho

    def visitar_pasta(self, pasta):
        posicao = len(self.linhas)
        self.linhas.append("")                    # reserva a linha: o total ainda não existe
        self._nivel += 1
        total = sum(f.aceitar(self) for f in pasta.filhos)
        self._nivel -= 1
        self.linhas[posicao] = "  " * self._nivel + f"{pasta.nome}/ — {total} B"
        return total

relatorio = Relatorio()
raiz.aceitar(relatorio)                  # uma única passada
print("\n".join(relatorio.linhas), relatorio.por_extensao)
```

**O que o visitante absorve.** O que fazer antes e depois de cada tipo de nó, e o estado que se acumula pelo caminho. O `visitar_pasta` tem o *antes* (reservar a linha e descer um nível) e o *depois* (somar, subir e preencher), e devolve o total para a pasta de cima. Nada é calculado duas vezes, e o acumulador é um campo do visitante, não um argumento que passa por todos.

> **Dica.** Um [Iterator](../iterator/explicacao.md) sozinho não faz isto: ele entrega cada nó uma vez, e não tem como "voltar" a uma pasta depois de visitar os filhos. É esse "antes e depois por tipo" que o Visitor oferece a mais.

<a id="ast-nodevisitor"></a>
## 2. Analisar uma árvore que não é sua

**Situação.** O time quer um verificador simples, rodado no CI: acusar qualquer chamada a `eval` ou `exec` e qualquer função com mais de cinco parâmetros. O código a analisar é Python, e as classes que o descrevem, `ast.Call`, `ast.FunctionDef`, são da biblioteca padrão: não há onde pôr um método novo.

**sem o pattern — expressões regulares sobre o texto**

```python
import re

def auditar(codigo: str):
    achados = []
    for n, linha in enumerate(codigo.splitlines(), 1):
        if re.search(r"\beval\(", linha):
            achados.append((n, "chamada a eval"))
        m = re.match(r"\s*def \w+\((.*)\):", linha)
        if m and len(m.group(1).split(",")) > 5:
            achados.append((n, "função com mais de 5 parâmetros"))
    return achados
```

**O que dói.** O texto não tem estrutura. `eval(` dentro de um comentário ou de uma string é acusado; uma assinatura escrita em várias linhas escapa; um parâmetro com valor padrão como `(1, 2)` conta como dois. Cada regra nova é mais uma expressão regular, e cada uma tem os seus furos.

**com o pattern — ast.NodeVisitor despacha por tipo de nó**

```python
import ast
from pathlib import Path

class Auditor(ast.NodeVisitor):
    def __init__(self):
        self.achados = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            self.achados.append((node.lineno, f"chamada a {node.func.id}"))
        self.generic_visit(node)             # continua descendo pelos argumentos

    def visit_FunctionDef(self, node):
        if len(node.args.args) > 5:
            self.achados.append((node.lineno, f"{node.name} tem {len(node.args.args)} parâmetros"))
        self.generic_visit(node)             # funções aninhadas também

arvore = ast.parse(Path("servico.py").read_text())
auditor = Auditor()
auditor.visit(arvore)
print(auditor.achados)
```

**O que o visitante absorve.** A operação inteira, para nós que você não pode alterar. As classes `ast.Call` e `ast.FunctionDef` não ganham método nenhum; a biblioteca escolhe `visit_Call` pelo nome da classe do nó. O `generic_visit` faz a descida padrão, e você só escreve o método dos tipos que lhe interessam. Um comentário ou uma string nunca é acusado, porque não existem como nós de chamada.

Sem `generic_visit`, a descida para: é assim que um visitante poda uma parte da árvore, por exemplo ignorando o corpo de funções de teste.

<a id="simplificar-regras"></a>
## 3. Reescrever uma árvore sem mutá-la

**Situação.** As regras de segmentação da página do [Interpreter](../interpreter/explicacao.md) são árvores de `E`, `Ou` e `Nao`. Quem monta as regras na tela produz formas desajeitadas: um `E` dentro de outro `E`, uma negação dupla. Antes de salvar, o sistema simplifica a árvore, e mais regras de simplificação chegam a cada mês.

**sem o pattern — uma função recursiva que reconstrói tudo, e outra para cada regra**

```python
def achatar_e(no):
    if isinstance(no, E):
        partes = []
        for p in no.partes:
            p = achatar_e(p)
            partes.extend(p.partes if isinstance(p, E) else [p])
        return E(*partes)
    if isinstance(no, Ou):
        return Ou(*[achatar_e(p) for p in no.partes])
    if isinstance(no, Nao):
        return Nao(achatar_e(no.parte))
    return no

def remover_dupla_negacao(no):
    if isinstance(no, Nao):
        interno = remover_dupla_negacao(no.parte)
        return interno.parte if isinstance(interno, Nao) else Nao(interno)
    if isinstance(no, E):
        return E(*[remover_dupla_negacao(p) for p in no.partes])
    if isinstance(no, Ou):
        return Ou(*[remover_dupla_negacao(p) for p in no.partes])
    return no
```

**O que dói.** A parte que muda em cada regra é pequena: um `if`. O resto, descer pelos filhos e reconstruir cada nó, é copiado em cada função. Um nó novo (`Xor`) cai no `return no` final e passa por todas as regras sem ser visitado, e nenhuma falha avisa.

**com o pattern — a recursão mora na base, cada regra escreve só o que muda**

```python
# cada nó: Comparacao, E, Ou e Nao ganham um aceitar, como este
class E:
    def __init__(self, *partes):
        self.partes = partes

    def aceitar(self, v):
        return v.visitar_e(self)

class Transformador:
    """Reconstrói a árvore igual. Cada regra sobrescreve só o que quer mudar."""

    def visitar_e(self, no):
        return E(*[p.aceitar(self) for p in no.partes])

    def visitar_ou(self, no):
        return Ou(*[p.aceitar(self) for p in no.partes])

    def visitar_nao(self, no):
        return Nao(no.parte.aceitar(self))

    def visitar_comparacao(self, no):
        return no

class AchatarE(Transformador):
    def visitar_e(self, no):
        partes = []
        for p in (p.aceitar(self) for p in no.partes):
            partes.extend(p.partes if isinstance(p, E) else [p])
        return E(*partes)

class RemoverDuplaNegacao(Transformador):
    def visitar_nao(self, no):
        interno = no.parte.aceitar(self)
        return interno.parte if isinstance(interno, Nao) else Nao(interno)

simplificada = regra.aceitar(AchatarE()).aceitar(RemoverDuplaNegacao())
```

**O que o visitante absorve.** O trabalho mecânico de percorrer e reconstruir. A base `Transformador` faz a recursão uma vez; cada regra nova sobrescreve só o método do tipo que lhe interessa, e escrever `RemoverDuplaNegacao` são cinco linhas. A árvore original não é alterada: cada passada devolve uma árvore nova, e as regras se encadeiam.

É o mesmo desenho do `ast.NodeTransformer` da biblioteca padrão, que faz isso para a árvore sintática do Python.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na Explicação):

| Caso | Já coberto por |
|---|---|
| Gerar HTML, Markdown e texto de um documento em árvore | A [Explicação](explicacao.md#o-problema) — uma operação por formato, em uma classe cada |
| Imposto, frete, nota fiscal e etiqueta sobre os itens de um pedido | A Explicação |
| Contar nós, medir a profundidade ou achar o maior elemento | 1 — estado acumulado durante a descida |
| Verificadores de estilo, linters, buscas por padrões de risco | 2 — operação sobre uma árvore que não é sua |
| Minificadores, otimizadores e migrações automáticas de código | 3 — reescrever a árvore sem mutá-la |

E um caso que parece Visitor, mas não é: `for item in itens: item.imposto()`. Se cada classe já sabe calcular o próprio imposto, é polimorfismo comum, e é a solução certa enquanto os tipos mudarem mais do que as operações. Veja as seções [Quando não usar](explicacao.md#quando-nao-usar) e [Parecidos](explicacao.md#parecidos) da explicação.
