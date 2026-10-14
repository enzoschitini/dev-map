<!-- Gerado de pages/clean-code/introducao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Introdução

*Clean Code / SOLID*

Os cinco princípios, o problema que cada um resolve e por onde começar a aplicar.

<a id="o-que-e"></a>
## O que é SOLID

Cinco princípios de projeto orientado a objetos, reunidos sob essa sigla por Robert C. Martin. Todos atacam o mesmo inimigo: a **mudança que se espalha**. Código rígido é aquele em que mexer num lugar obriga a mexer em outros cinco.

Nenhum deles é sobre deixar o código bonito. São sobre onde colocar as costuras, para que a próxima mudança caiba em um arquivo só.

<a id="os-cinco"></a>
## Os cinco princípios

| Sigla | Princípio | Em uma linha |
|---|---|---|
| `S` | Single Responsibility | Uma classe muda por um motivo só |
| `O` | Open/Closed | Dá para estender sem editar o que já funciona |
| `L` | Liskov Substitution | Um filho pode substituir o pai sem quebrar quem chama |
| `I` | Interface Segregation | Ninguém depende de método que não usa |
| `D` | Dependency Inversion | Depender da abstração, não da implementação |

<a id="por-onde-comecar"></a>
## Por onde começar

Na ordem de retorno, não na ordem da sigla:

1. **Single Responsibility.** É o que mais muda o dia a dia e o mais fácil de ver: classe grande demais, com métodos que não conversam entre si.
2. **Dependency Inversion.** É o que destrava os testes. Sem ele, testar qualquer coisa exige banco, rede e relógio de verdade.
3. **Open/Closed** e **Liskov**, que quase sempre caem junto com algum padrão de projeto.
4. **Interface Segregation**, o mais situacional dos cinco.

> **Cuidado.** O erro mais comum não é ignorar SOLID: é aplicar os cinco de uma vez em código que ainda não mudou nenhuma vez. Abstração criada antes da segunda mudança costuma ser a abstração errada.

<a id="relacao"></a>
## Relação com os padrões

Os princípios dizem *onde* cortar; os padrões dão o *formato* do corte. O [Adapter](estruturais/adapter/explicacao.md), por exemplo, é Dependency Inversion aplicado quando a interface de fora não é a que o seu código espera.

> **Nota.** Cada princípio tem a sua página, nesta ordem: [Single Responsibility](single-responsibility.md), [Open/Closed](open-closed.md), [Liskov Substitution](liskov-substitution.md), [Interface Segregation](interface-segregation.md) e [Dependency Inversion](dependency-inversion.md).
