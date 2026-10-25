# Validação local — 25/10/2026

## Atualização atual: centralização, seta longa e críticos naturais

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
