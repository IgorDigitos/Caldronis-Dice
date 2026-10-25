# Caldronis Dice e Rollem — comparação para decidir os próximos passos

Pesquisa pública em 25/10/2026. Estado atual após esclarecimento do usuário: manter/descartar foi
removido; repetição com `#` foi implementada conforme a nova imagem. Sem `#`, a apresentação é
decrescente em todas as rolagens, inclusive com `#`, mantendo uma linha por repetição.
Depois, o usuário escolheu contagem de sucessos
com `>>` e depois sua extensão `<<`, ambas implementadas para um grupo e alvo inteiro. As tabelas indicam o estado
atual dos demais recursos.
Depois disso, o usuário autorizou `!` com duas regras próprias: explosões em somas e críticos em
dobro, sem dados extras, nas contagens. Essa combinação do Caldronis não deve ser presumida idêntica
ao Rollem.

## Identificação e alcance

Os [termos oficiais](https://rollem.rocks/tos) identificam `rollem#7705` pelo ID
`240732567744151553`. A pesquisa cobre documentação pública e o changelog oficial; não houve
acesso às configurações autenticadas do seu servidor nem teste real desses recursos no Rollem.
A imagem fornecida mostra o formato que queremos reproduzir, mas não comprova opções de configuração.

Você informou que a instalação inicial do Caldronis funcionou no Discord. Esse relato confirma
o funcionamento observado por você; não equivale à execução de todos os casos do checklist.
O usuário também relatou que as novas expressões funcionaram. Ordenação por modo e repetição com
`#` foram confirmadas em relato posterior com imagem. O novo espaçamento e alinhamento dos totais
foi alterado depois desse relato e precisa de conferência visual após reiniciar o bot.

## Formato implementado

Entrada: `2d30+8`. Exemplo com resultados 30 e 20:

```text
`58` ← [**30**, 20] 2d30 + 8
```

No Discord, o total aparece em código e o 30 em negrito. A mensagem é uma resposta à mensagem
original, que identifica o jogador. O nome e avatar do bot dependem da configuração do Discord.
O total agora recebe margem dos dois lados dentro do código inline e seta longa `⟵`. Em repetições,
as caixas compartilham a largura do maior total e os números ficam centralizados, incluindo negativos.
No modo de contagem, essa caixa mostra quantos dados atenderam ao alvo: `>>` significa maior ou
igual e `<<` menor ou igual. A linha termina com operador e alvo, sem rótulo de sucesso/fracasso.

Entrada: `d30+FOR atacar o guarda`, com FOR=8 e dado 18:

```text
`26` ← [18] d30 + FOR
FOR=+8
> atacar o guarda
```

O formato mantém os sinais, valores de atributos e grupos de dados. O usuário escolheu destacar
em negrito os valores naturais 1 e máximo dentro dos colchetes. Total final, constantes e atributos
não recebem esse negrito; os destaques não alteram a matemática.
Exibe os valores de cada grupo do maior para o menor, conforme solicitação posterior do usuário.
`N#expressão` mostra uma linha por repetição, sem trocar a ordem das linhas e sem cabeçalho ou
soma geral. Dentro de cada linha, os dados também ficam em ordem decrescente.
A ordenação muda somente a apresentação; preserva os sorteios originais e o cálculo.
O texto da expressão conserva os tokens digitados, normalizando espaços em volta dos operadores.
Comentários são escapados e menções continuam bloqueadas. Respostas grandes são divididas por
termos em mensagens de até 1.900 unidades UTF-16, preservando todos os valores, sem novos sorteios.

## Rolagens e sintaxe

As linhas abaixo se baseiam na [sintaxe V1 oficial](https://rollem.rocks/docs/v1-syntax), com
detalhes de [explosão](https://rollem.rocks/docs/v1-syntax/exploding-dice),
[keep/drop](https://old.rollem.rocks/syntax/keep-drop) e
[faixa de crítico](https://rollem.rocks/docs/v1-syntax/crit-range).
O comportamento do Caldronis foi conferido no código local.

| Recurso | Rollem: exemplo | Caldronis atual |
| --- | --- | --- |
| Dados e soma/subtração | `2d30+8` | Implementado |
| Comentário | `d20 atacar` | Implementado |
| Manter maior; vantagem em d20 | `2d20kh1` | Removido por solicitação do usuário |
| Manter menor; desvantagem em d20 | `2d20kl1` | Removido por solicitação do usuário |
| Descartar menores | `4d6dl1` ou `4d6d1` | Removido por solicitação do usuário |
| Descartar maiores | `4d6dh1` | Removido por solicitação do usuário |
| Repetição | `2#d30`, `6#4d6` | Implementado; corpo precisa começar por dado |
| Explosão no máximo | `d6!` | Implementado em somas; com >>/<< dobra o crítico sem dados extras |
| Explosão por limiar | `d6!5` | Não implementado |
| Multiplicação/divisão | `d20*2`, `d20/2` | Não implementado |
| Parênteses | `d20+(2*3)` | Não implementado |
| Ajuste por dado | `4d6++2`, `4d6--2` | Não implementado |
| Contagem por limiar | `10d6>>4`, `10d6<<3` | Ambos implementados para um grupo e alvo inteiro, sem rótulos |
| Comparar total | `d20>=15` | Não implementado |
| Fate | `4dF` | Não implementado; altera dado inicial numérico |
| Burning Wheel | `B5`, `G5`, `W5`, com variantes abertas | Não implementado; altera regra de início |
| Explosão por dados iguais | `2d6daro`, `3d6taro`, `3d6aro` | Não implementado |
| Faixa de destaque | `d20c18` | Sem faixa configurável; destaca 1 e máximo naturais nos colchetes |
| Desabilitar ordenação | `4d6ns` | Não implementado; todos os grupos são exibidos em ordem decrescente |

Outros comportamentos aparecem no [README](https://github.com/rollem-discord/rollem-discord)
e no [changelog oficial](https://github.com/rollem-discord/rollem-discord/blob/main/packages/bot/CHANGELOG.md):

| Recurso | Rollem documentado | Caldronis atual |
| --- | --- | --- |
| Rolagem dentro de frase | `Eu [d20+5 atacar]` | Ignora; proibido pela regra atual |
| Cálculo sem dados | `r6+6` ou `&6+6` | Ignora; proibido pela regra atual |
| One Roll Engine / Fortune | `ore#10d10`, `fortune#10d10` | Não implementado |
| Agrupar valores/quantidades | `group`, `groupValue`, `groupSize` e aliases | Não implementado |
| Spoiler | `s#4d20` | Não implementado; fora do escopo atual |
| Ajuda/versão/estatísticas | Comandos por menção documentados no histórico | Não implementado |

Spoiler oculta visualmente o conteúdo, mas não constitui autorização de acesso: não é uma
implementação de rolagem privada. Não tratar esse recurso como segurança.

## Configurações

Fontes: [Rollem Next](https://rollem.rocks/docs/rollem-next),
[changelog](https://github.com/rollem-discord/rollem-discord/blob/main/packages/bot/CHANGELOG.md) e
[planejamento V2](https://rollem.rocks/docs/v2-syntax).

| Configuração | O que está documentado no Rollem | Caldronis |
| --- | --- | --- |
| Prefixo opcional | Cargo `rollem:prefix:<prefixo>` | Sem prefixo por decisão original |
| Versão de sintaxe no servidor | Cargos `rollem:beta` e `rollem:v2` no bot | Uma gramática estável própria |
| Sobrescrever sintaxe por usuário | Cargos `rollem:v1`, `rollem:beta`, `rollem:v2` | Não implementado |
| Escolha de canais | Acesso pode ser restringido nas permissões Discord | Mesma possibilidade pelas permissões Discord |
| Configurações detalhadas por usuário/canal/servidor | Listadas no planejamento V2 | Não assumir disponibilidade real |
| Ordenação padrão configurável | Listada no planejamento V2 | Ordem decrescente em todos os grupos, sem configuração |
| Variáveis, aliases e ficha ativa | Listadas no planejamento V2 | Atributos já persistentes; sem aliases ou múltiplas fichas |
| Cargo para editar outros jogadores | Não confirmado nas fontes consultadas | `/config mestre`, com ID do cargo e autorização no backend |

A página V2 é explicitamente **WIP**. Itens propostos nela não podem ser apresentados como
recursos já disponíveis no Rollem. A página pública de conta não permite auditar a configuração
efetiva do seu servidor. Também não foi confirmada uma API pública de importação de configurações.

## Limites e manutenção

O Rollem documenta [limites](https://rollem.rocks/docs/limitations), incluindo 100 dados e ausência
de dados de um lado. O Caldronis também limita a 100 dados, com lados entre 2 e 100.000, 30 termos,
1.000 caracteres e 40 atributos por perfil. Não foi confirmado um teto equivalente de lados do Rollem.

Nas repetições implementadas, o limite vale para o conjunto: `6#20d6` é rejeitado, pois seriam 120
sorteios. Há também limite de 100 termos para o conjunto e 30 por expressão. Explosões têm teto
compartilhado de 100 sorteios, incluindo iniciais, extras e repetições; se exceder, o conjunto falha
sem resultados parciais. Em contagens com `!`, não há sorteios extras: máximo vale 2 no `>>`,
1 vale 2 no `<<`, desde que atinja o alvo. Sem `!`, o peso de cada dado elegível permanece 1.

Substituir o Rollem para sua mesa exige cobrir os comandos que ela usa e a operação do bot.
Copiar toda a superfície de sintaxe inclui regras específicas de outros sistemas, mais combinações
e mais testes. Não é necessário para substituir o uso real da sua mesa.

## Proposta de sequência — aguardando escolha

1. O usuário escolheu contagem por alvo: `5d6>>4` conta 4 ou mais; `5d6<<3` conta 3 ou menos.
2. Conferir a contagem e os demais casos usando [QUICK_VALIDATION.md](QUICK_VALIDATION.md).
3. Registrar os cenários do checklist completo que ainda não foram executados.
4. Esta versão não aceita somas, subtrações, atributos ou múltiplos grupos com `>>` ou `<<`.
   Também não adiciona comparação de totais ou cancelamento por 1. O crítico em dobro é ativado
   somente pelo `!` junto do dado, conforme as escolhas do usuário.

Não copiar automaticamente mecanismos de configuração por nome de cargo. Os comandos slash e IDs
já usados no Caldronis são mais explícitos e mantêm autorização separada de nomes editáveis.
Prefixos, Fate e rolagens inline continuam exigindo decisão explícita sobre a regra inicial.
A exceção `N#expressão` foi autorizada pelo usuário e continua ancorada no início da mensagem;
o primeiro termo da expressão repetida deve ser dado numérico. A especificação original permanece
preservada no arquivo recebido, com as alterações posteriores registradas no README e nesta comparação.
