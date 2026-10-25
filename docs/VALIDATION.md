# Validação local — 25/10/2026

## Atualização atual: dados explosivos e críticos em dobro com !

O usuário autorizou `!` e esclareceu duas regras diferentes:

- Sem `>>`/`<<`, o máximo natural gera um dado extra, que também pode explodir. Somam-se todos
  os resultados, preservando modificadores, atributos, sinais e repetições.
- Com `>>`, o máximo natural elegível vale 2 e não gera outro dado.
- Com `<<`, o 1 natural elegível vale 2 e não gera outro dado.

Contagens sem `!` continuam com peso 1 por dado elegível. Valores que não atendem ao alvo não
pontuam. Dados em contagens não geram extras, inclusive se o valor for crítico. A formatação
mostra todos os valores em ordem decrescente e mantém uma linha por repetição e os destaques
naturais em negrito. Rótulos de sucesso/fracasso não foram reintroduzidos.

O limite de 100 sorteios é compartilhado por termos e repetições, incluindo dados extras.
O limite é verificado antes de cada chamada ao gerador; uma tentativa de sorteio 101 falha e o
handler exibe apenas o erro, sem resultados parciais. Os limites comuns foram centralizados
em `dice/limits.py`, compartilhado pelo parser e motor. Não foram adicionadas dependências.

**298 testes passaram em 4,43 s**, com 32 avisos internos de depreciação da biblioteca.
Ruff: análise e formatação aprovadas. `pip check`: nenhuma dependência incompatível.

Cobertura nova:

- Máximo, não máximo, cadeias de explosão, grupos mistos e apenas dados marcados explodindo.
- Soma/subtração e atributos com validação antes do primeiro sorteio.
- Repetições independentes, todas as faces visíveis, comentários e limites de tamanho.
- Sequência infinita de máximos interrompida após 100 sorteios; nenhuma chamada 101 ao gerador.
- Limite compartilhado entre grupos e repetições, sem reiniciar o orçamento em cada um.
- Rejeição de `!!`, `!5`, espaço antes de !, atributo com ! e sintaxe incompleta.
- Peso 2 no máximo em >> e no 1 em <<, sem qualquer sorteio extra; valores comuns valem 1.
- 100 dados críticos com contagem podem retornar 200, mas geram exatamente 100 sorteios.
- Contagens sem ! e demais recursos continuam cobertos pela suíte de regressão.

**O recurso ! ainda não foi validado no Discord real.** Banco, credenciais e configurações não
foram alterados. Não houve novo commit ou envio ao GitHub.

## Registro anterior: ordenar dados também nas repetições

O usuário enviou uma comparação com o Rollem e solicitou ordem decrescente dentro de cada linha,
inclusive com `#`, `>>` e `<<`. A formatação agora ordena todos os grupos do maior para o menor.
Cada repetição continua em sua própria linha, preservando a ordem das linhas e sua contagem/total.
Os valores originais permanecem intactos no resultado interno; só a apresentação é ordenada.

**250 testes passaram em 4,62 s.** Ruff (análise e formatação) passou. Permanecem os mesmos 27
avisos internos de depreciação da biblioteca. Os testes de repetição e contagem verificam a nova
ordenação, a separação das linhas, os destaques naturais e a preservação dos sorteios originais.

Sem mudança de cálculo, configuração ou banco. **A ordenação nova ainda precisa de conferência
visual no Discord após reiniciar o bot.** Alterações locais, sem novo commit ou envio ao GitHub.

## Registro anterior: contagem com << e remoção dos rótulos

O usuário aprovou a contagem `>>` e pediu o equivalente `<<`, removendo os rótulos de sucesso
e fracasso. `>>` conta valores maiores ou iguais ao alvo; `<<` conta menores ou iguais.
O número à esquerda é a contagem; depois dos dados aparecem somente a expressão, operador e alvo.
Comentários do jogador são preservados, inclusive quando usam as palavras sucesso/fracasso.

O modelo e os campos internos foram generalizados para contagem por alvo/direção, sem mudança
no banco. Permanecem os mesmos limites, restrição a um único grupo sem modificadores, suporte
a espaços, comentário e repetição com `#`. Negrito continua apenas nos dados naturais 1/máximo.

**250 testes passaram em 4,53 s**, com 27 avisos internos de depreciação da biblioteca.
Ruff (análise e formatação) passou; `pip check` não encontrou dependências incompatíveis.

Cobertura:

- Exemplo `5d6<<3` com `[6, 5, 3, 2, 1]` retorna 3, incluindo igualdade.
- Todas as 36 combinações de dois d6, com alvos de 0 a 7, em ambos os operadores.
- Zero, todos os dados, alvo acima dos lados e valores nos limites de entrada.
- Repetições independentes na ordem original; comentário único e respostas sem rótulos.
- Casos malformados, alvo inválido, operadores encadeados, atributos/modificadores e excesso
  de sorteios rejeitados antes de consultas ao banco ou rolagens.
- Regressão da contagem `>>`, parser normal, formatação, persistência e permissões.

**O modo << e a resposta sem rótulos ainda não foram validados no Discord real.**
Nenhuma dependência foi adicionada. Credenciais, banco e configurações não foram alterados;
não foi criado novo commit nem feito envio ao GitHub.

## Registro anterior: contagem de sucessos por alvo

Recurso escolhido pelo usuário: `5d6>>4` conta cada dado com resultado maior ou igual a 4.
O valor principal passa a ser a contagem, com o sufixo `sucesso`/`sucessos` para distinguir da soma.
Todos os dados permanecem visíveis, com 1/máximo em negrito somente nos colchetes. Um máximo
conta um sucesso e um 1 não cancela outros sucessos.

Nesta etapa, a gramática aceita um único grupo de dados e um alvo inteiro de 0 a 1.000.000.000,
com espaços, comentário e repetição opcional. Somas, subtrações, atributos e múltiplos grupos
junto de `>>` são rejeitados antes de sortear. Um alvo acima dos lados retorna zero sucessos.
Os limites de mensagem, repetições e 100 dados para o conjunto continuam valendo.

**214 testes passaram em 4,87 s**, com 25 avisos internos de depreciação da biblioteca.
Ruff: análise e formatação aprovadas. Cobertura nova:

- Exemplo escolhido `[6, 5, 4, 2, 1]` produz exatamente 3 sucessos.
- Todas as 36 combinações de dois d6, com alvos de 0 a 7, conferidas por valor individual.
- Limites inclusivos, zero sucessos, todos com sucesso e alvos fora do intervalo natural.
- Repetições independentes, ordem dos dados, comentário único e número de sorteios exato.
- Parser e handler rejeitam tentativas inválidas sem sorteio ou consulta ao banco.
- Contagens válidas também não consultam o banco, pois não precisam de atributos.
- 100 resultados e comentário com emojis divididos sem perda e dentro do limite do Discord.
- Menção em comentário não é confundida com comparação e permanece escapada.
- Regressão de perfis, permissões, rolagens normais, formatação e sintaxe já existente.

A primeira execução encontrou uma regressão no tratamento de comentários iniciados por menção
do Discord (`<@...>`); o detector foi corrigido e o caso entrou na suíte. A sintaxe `<<` e
comparações como `>=` continuam sem suporte e não são ignoradas como comentários de operador.

O README simplificado e sua declaração de uso de IA foram preservados. Banco, configuração e
credenciais não foram alterados. **Contagem de sucessos ainda não validada no Discord real.**

## Registro anterior: centralização, seta longa e críticos naturais

O usuário solicitou centralização dos totais, em especial números isolados de um dígito, e uma
seta mais longa. Foi substituído o alinhamento à direita por centralização e `←` por `⟵`.
Um total isolado de um dígito agora tem exatamente um espaço inseparável de cada lado, sem o
espaço extra anterior à esquerda. Em repetições, a largura continua compartilhada pelo maior
total; para comprimentos de paridade diferente a centralização usa a diferença mínima de um
caractere entre margens, conforme as possibilidades do texto monoespaçado.

O usuário confirmou a regra na caixa de pergunta e reforçou depois: **apenas o resultado natural
nos colchetes** recebe negrito quando igual a 1 ou ao máximo do dado. Exemplo: dado 20 em `d20+8`
destaca **20**, enquanto o total 28 permanece somente na caixa de código. Atributos e constantes
não recebem negrito de crítico. Nenhum efeito mecânico foi adicionado.

Verificações finais locais:

- **167 testes passaram em 3,51 s**, com os mesmos 20 avisos internos de depreciação da biblioteca.
- Ruff: análise e formatação aprovadas.
- Testes de mínimo/máximo em d2, d4, d30 e d100000, antes de modificadores.
- Grupo com máximo e mínimo juntos; apenas dados em negrito, sem destacar constantes ou atributos.
- Total isolado centralizado e margens equilibradas em lotes com negativos, zero e totais grandes.
- Regressão de ordenação, repetições, perfis, permissões e tamanho de mensagens.

O código de cálculo, o banco e a configuração não foram alterados. A aparência nova ainda precisa
de conferência real no Discord após reiniciar; não houve login pelo agente, commit ou push.

## Registro anterior: totais com margem e versão consolidada

O usuário confirmou que as repetições funcionaram e enviou uma imagem comparando o espaçamento
do Rollem e do Caldronis. O total agora tem espaço inseparável dos dois lados dentro do código
inline; em repetições, a largura é compartilhada pelo maior total e o alinhamento é à direita.
Isso inclui negativos, zero e totais de comprimentos diferentes. A formatação considera esses
espaços no limite de tamanho das mensagens.

O usuário escolheu consolidar a versão atual, sem adicionar comandos. Revisados parser, limites,
separação de comentário, rolagem, SQLite, autorização, configuração e tratamento de respostas.
O roteiro curto está em [QUICK_VALIDATION.md](QUICK_VALIDATION.md).

Resultado final:

| Verificação | Resultado |
| --- | --- |
| pytest | **156 testes passaram em 3,16 s** |
| Ruff, análise | Aprovado |
| Ruff, formatação | Aprovado após ajustar a formatação de uma asserção |
| pip check | Nenhuma dependência incompatível |
| git check-ignore | .env, banco local e ambiente virtual ignorados |

Permanecem 20 avisos de depreciação internos do discord.py no Python 3.14, sem falhas de teste.
Não foram adicionadas dependências nem alterados atributos, banco, credenciais ou configurações.
Não houve login pelo agente, commit ou push.

O teste novo verifica margem, alinhamento e preservação do valor para totais -1, 0 e 99998.
Os testes de referência e de 100 repetições foram atualizados, mantendo cobertura de ordem,
total, quantidade de resultados, limite de caracteres e ausência de sorteios adicionais.

O relato positivo do usuário se refere à versão anterior. **O novo espaçamento ainda precisa ser
conferido no Discord real**, inclusive no celular; testes de texto não certificam a aparência
de cada cliente. O checklist completo de permissões, persistência e falhas permanece aberto
até registro por cenário. Python 3.11–3.13 ainda não foi executado neste ambiente.

## Registro anterior: remoção de manter/descartar e repetição com #

O usuário esclareceu que não havia entendido a proposta anterior e solicitou a remoção de
manter/descartar. Foram removidos campos de seleção dos modelos, parsing dos modificadores,
filtros no cálculo, dados riscados e restrições de nomes associadas à seleção. Nenhum atributo,
configuração de servidor ou credencial foi apagado. A ordenação decrescente sem `#` foi mantida.

O usuário enviou uma segunda imagem: `2#d30` retorna duas linhas com totais separados, sem
cabeçalho, numeração ou soma geral. A implementação segue esse exemplo. Com `#`, mantém a ordem
dos dados e das repetições; atributos e comentário compartilhados aparecem uma única vez ao final.

**155 testes passaram em 3,96 s.** Ruff (análise) passou. Há 20 avisos de depreciação internos da
biblioteca, da mesma origem detalhada nas entregas anteriores. Os testes da funcionalidade removida
foram substituídos por testes de repetição e regressão da remoção.

Cobertura nova:

- Reprodução textual exata da imagem: `12 ← [12] 1d30` e `15 ← [15] 1d30` em duas linhas.
- Dados sem # continuam decrescentes; com # ficam na ordem original, inclusive `1#3d6`.
- Resultados independentes, sinais, atributos negativos e comentário compartilhado.
- Uma consulta de atributos por mensagem; todos os atributos validados antes do primeiro sorteio.
- Atualização de FOR de 8 para 10 no SQLite aplicada às repetições.
- 1 a 100 repetições, no máximo 100 dados e 100 termos no conjunto, 30 termos por expressão.
- Erros de prefixo, repetições aninhadas, expressão incompleta e limites: nenhuma rolagem parcial.
- 100 resultados divididos sem perder linhas, emojis ou gerar sorteios adicionais.
- Modificadores antigos são rejeitados como sintaxe de dado; nomes de atributos antes reservados
  exclusivamente para manter/descartar voltam a ser aceitos.

Verificações finais: `ruff format --check .` confirmou os 27 arquivos Python formatados;
`pip check` não encontrou dependências incompatíveis. Nenhuma dependência foi adicionada.
**A repetição com # ainda não foi validada no Discord real.**

## Registro anterior: ordenação decrescente e manter/descartar — revertido

**143 testes passaram em 4,66 s.** Ruff (análise e formatação) passou; `pip check` não encontrou
incompatibilidades. Há 17 avisos internos de depreciação do discord.py no Python 3.14, da mesma
origem já documentada abaixo. Nenhuma dependência foi adicionada.

Ordenação: primeiro foram executados 105 testes, todos aprovados. A apresentação ordena cada
grupo do maior para o menor sem modificar os resultados originais ou o total.
Depois, o usuário escolheu manter/descartar dados na caixa de pergunta; foram implementados
`kh`, `kl`, `dh`, `dl` e aliases `k` e `d`, com um modificador por grupo.

Verificações novas:

- Comparação de resultados esperados nos quatro modos e aliases, incluindo maiúsculas.
- Todas as 36 combinações de dois d6 para vantagem e desvantagem: total igual a máximo/mínimo.
- Empates selecionam exatamente N, sem remover todos os dados com o mesmo valor.
- Descartados riscados; soma/subtração considera somente os mantidos.
- Integração com atributo FOR salvo em SQLite e atualizado de 8 para 10.
- Rejeição de zero, quantidade excessiva, descarte de todos e modificadores incompletos/encadeados,
  antes de consultas ou sorteios.
- Limite global de 100 sorteios continua contando dados descartados.
- Resposta com 99 dados descartados entre 100 respeita o limite de tamanho.
- Nomes de atributos não podem coincidir com novas expressões de dado; nomes com `_MOD` continuam
  aceitos, sem migração ou exclusão de dados existentes.

O usuário relatou funcionamento das expressões da versão anterior. As mudanças desta seção foram
feitas depois desse relato e **ainda não foram validadas no Discord real**.
`#` continua sem suporte; a ordenação de futuras repetições não foi presumida.

## Registro anterior: formato compacto inspirado no Rollem

Resultado naquela etapa: **103 testes passaram**, em 4,23 s. Ruff (análise e formatação) passou.
Há 14 avisos de depreciação internos da biblioteca, da mesma origem descrita abaixo.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Os testes de apresentação foram atualizados para texto compacto e acrescentados casos de referência
exata (`58 ← [30, 20] 2d30 + 8` com máximo em negrito), grupos múltiplos, atributos negativos,
nome semelhante a dado, comentários com emojis, divisão sem novo sorteio e interrupção após falha
de envio. O teste de divisão inicialmente usava uma resposta curta demais para exceder o limite;
a entrada foi corrigida para exercitar de fato mensagens longas.

O usuário relatou que a instalação inicial funcionou no Discord. Não foi detalhada a execução de
todo o checklist. **O novo formato ainda não foi conferido no Discord real.**
Nenhum recurso extra do Rollem foi implementado; a comparação pública está em
[ROLLEM_COMPARISON.md](ROLLEM_COMPARISON.md).

## Registro histórico da entrega inicial

Na entrega inicial: **97 testes passaram**, sem teste real no Discord pelo agente.

## Ambiente efetivamente executado

- Windows, Python 3.14.6.
- discord.py 2.7.1, python-dotenv 1.2.4.
- pytest 9.1.1, Ruff 0.17.2.
- Instalação editável com `python -m pip install -e '.[dev]'` no ambiente `.venv`.
- Python 3.11+ é o requisito do projeto, mas 3.11–3.13 não estavam instalados e não foram executados.

## Etapas e evidências

1. Preparação: ambiente virtual, dependências, estrutura, configuração de exemplo e Git local.
2. Motor e perfis: primeira suíte com 62 testes passou antes da validação da integração Discord.
3. Integração: suíte ampliada para 97 testes, todos passaram.
4. Verificação estática: Ruff inicialmente encontrou linhas longas; a formatação foi corrigida.
5. Verificação final:

| Verificação | Resultado |
| --- | --- |
| pytest (97 casos) | 97 passaram; 8 avisos de depreciação da biblioteca |
| `ruff check --no-cache .` | Todos os checks passaram |
| `ruff format --check --no-cache .` | Todos os arquivos Python formatados |
| `pip check` | Nenhuma dependência incompatível |

Os oito avisos vêm de `discord/utils.py`, que usa um argumento posicional de `re.sub` depreciado
no Python 3.14. Não são falhas dos testes e não foram suprimidos nem corrigidos alterando terceiros.

Houve falha inicial de download de pacotes, resolvida com acesso de rede autorizado. Na última
verificação o executor restrito falhou antes de iniciar processos; ao executar fora dele, a pasta
temporária compartilhada do pytest tinha permissões de outro usuário do ambiente. Essa execução
intermediária terminou com 86 testes passando e 11 erros de preparação, sem falha de asserção.
A execução final usou uma pasta nova dentro do projeto e terminou com **97 passando em 2,40 s**:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .test-tmp-final
```

O comando habitual `python -m pytest -q` também passou anteriormente com os 97 testes. O comando
alternativo evita o cache e a pasta temporária compartilhada; não altera a lógica dos testes.

## O que os testes verificam

- Detector ancorado e mensagens que precisam ser ignoradas.
- Dados especiais, espaços, maiúsculas, comentários e extração da expressão original.
- Rejeição de sintaxe incorreta e limites antes de qualquer resultado parcial.
- Rolagem determinística com valores individuais, sinais e atributos negativos.
- Atributo inexistente rejeitado antes de sortear qualquer dado.
- Banco SQLite real temporário: atualização de FOR 8 → 10, reabertura, isolamento e foreign keys.
- Limite de 40 atributos, inclusive 45 gravações concorrentes sem exceder o limite.
- Autorização própria/mestre, revogação por mudança de cargo e configuração administrativa.
- Mensagens de bots, webhooks e DMs ignoradas.
- Zero consultas ao banco para conversas comuns, expressões inválidas e rolagens sem atributos.
- Handler completo de rolagem usando FOR salva e atualizada no banco.
- Limites de embeds, escape de texto livre e bloqueio de menções.
- Falhas de banco, rede e permissão de envio sem exposição de detalhes internos.
- Registro e callbacks dos comandos slash, respostas privadas e rejeição de operações indevidas.
- Sincronização global e de desenvolvimento com chamadas de rede simuladas.
- Configuração do token, ID do servidor e ausência de segredo na representação de configurações.

## Não verificado

Não houve login, conexão Gateway, sincronização remota, envio real, instalação no servidor,
validação de permissões reais ou teste pelo celular. Token não foi solicitado nem usado.
Não existe evidência de aprovação no Discord até executar [DISCORD_CHECKLIST.md](DISCORD_CHECKLIST.md).
Sem deploy, commit ou push automático.
