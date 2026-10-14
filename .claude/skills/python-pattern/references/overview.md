<!-- Gerado de pages/clean-code/overview.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Overview

*Clean Code*

O que entra nesta aba, como ela está dividida e o formato que toda página segue.

<a id="o-que-e"></a>
## O que é código limpo

Código que a próxima pessoa entende sem precisar perguntar nada. Essa pessoa quase sempre sou eu, meses depois, então o critério é prático e não estético: se eu preciso reconstruir o raciocínio inteiro para mudar uma linha, o código não está limpo.

Nada aqui é regra absoluta. Cada princípio tem um custo, e metade do estudo é saber quando o custo não compensa.

<a id="divisao"></a>
## Como esta aba está dividida

| Sessão | O que entra |
|---|---|
| SOLID | Os cinco princípios de projeto orientado a objetos, um por página |
| Design Pattern | Padrões de projeto; cada padrão é uma pasta com as suas páginas |

A diferença entre as duas: **SOLID diz onde cortar** as responsabilidades; **os padrões dizem como ligar** as peças depois do corte. Costumam aparecer juntos — boa parte dos padrões é um princípio do SOLID aplicado a um caso concreto.

<a id="formato"></a>
## O formato de cada página

Toda página segue a mesma ordem de seções, para dar para comparar dois assuntos lado a lado sem reler tudo.

```
Nome do princípio ou padrão
├─ O problema          o código que dói, antes
├─ A solução           as peças e o papel de cada uma
├─ Implementação       um exemplo curto que roda
├─ Quando usar         os sinais de que é este o caso
├─ Quando não usar     o custo e as alternativas mais simples
└─ Parecidos           o que se confunde com este
```

A seção **Parecidos** é a que mais ajuda: boa parte da confusão com padrões é não saber diferenciar dois que resolvem coisas próximas, como Strategy e State.

<a id="pastas"></a>
## Por que cada padrão é uma pasta

Um padrão raramente cabe em uma página só: tem a explicação, e depois exemplos em linguagens diferentes, armadilhas e comparações. Cada padrão vira uma pasta em `pages/clean-code/`, e a explicação é a primeira página de dentro.

> **Nota.** No menu lateral, as pastas abrem e fecham. A que guarda a página aberta já começa aberta.
