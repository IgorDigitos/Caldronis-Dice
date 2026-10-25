# Validação real no Discord — pendente

O usuário relatou funcionamento inicial no Discord, sem detalhar cada cenário abaixo.
As caixas permanecem abertas até registro de execução individual. O usuário também relatou
funcionamento das expressões posteriores. Manter/descartar foi removido a pedido do usuário.
O usuário confirmou depois o funcionamento das repetições. O novo espaçamento e alinhamento dos
totais ainda precisam de conferência visual real. Para uma primeira passagem, use
[QUICK_VALIDATION.md](QUICK_VALIDATION.md).
Registre data, versão do código, servidor, sistema operacional e modelo do celular ao executar.
Não inclua token ou informações privadas nas evidências.

## Conexão e instalação

- [ ] Preencher `.env` local, habilitar Message Content Intent no portal e instalar com os escopos
  `bot` e `applications.commands`.
- [ ] Conceder View Channels, Send Messages e Read Message History no canal de teste.
- [ ] Usar DEV_GUILD_ID e iniciar `bot.py`; verificar bot online e comandos disponíveis.
- [ ] Conferir que Members/Presence intents continuam desligados.

## Rolagens e detecção

- [ ] `d30`, `d2` e `d100000`: resultado no intervalo e resposta à mensagem original.
- [ ] `2d30+5`: dois valores individuais e soma correta.
- [ ] Formato compacto: total em código, seta e dados junto da expressão, sem embed.
- [ ] Totais centralizados, com margem dos dois lados e largura uniforme nas repetições.
- [ ] Total isolado de um dígito tem margens iguais, sem deslocamento para a direita; seta longa `⟵`.
- [ ] Dado natural 1 ou máximo em negrito nos colchetes; total, atributos e constantes sem esse negrito.
- [ ] `d20+8`, ao sair 20: total 28 na caixa, apenas o 20 nos colchetes em negrito.
- [ ] `5d30+8`: valores exibidos do maior para o menor, incluindo empates, com total correto.
- [ ] `3d6-2d6`: cada grupo em ordem decrescente, preservando a subtração e a separação dos grupos.
- [ ] `2#d30`: duas linhas na mesma resposta, cada uma com seu total, sem cabeçalho ou soma geral.
- [ ] `3#d30+FOR`: FOR em cada cálculo, valor do atributo exibido uma única vez depois dos resultados.
- [ ] `2#3d6`: seis sorteios, dois totais; preservar ordem dentro dos grupos e entre repetições.
- [ ] Comparar `3d6` (decrescente) e `1#3d6` (ordem do sorteio).
- [ ] `2#d30 atacar`: comentário único ao final, sem alterar cálculos.
- [ ] `0#d30`, `101#d30`, `2#d30+`, `2#d1`, `2#2#d30`: erro sem resultado parcial.
- [ ] `51#2d6`: erro por mais de 100 dados; `100#d6+1`: erro por mais de 100 termos.
- [ ] `100#d30`: 100 resultados, divididos conforme necessário, sem omitir linhas.
- [ ] `Vou usar 2#d30` e `!2#d30`: ignorar.
- [ ] `2d20kh1`, `2d20kl1`, `4d6dh1`, `4d6dl1`: erro, sem aplicar manter/descartar.
- [ ] Resposta vinculada à mensagem original, identificando o jogador sem notificá-lo.
- [ ] `d30 + FOR + d4` e `d30+FOR-CON`: sinais, atributos e total corretos.
- [ ] `d30+FOR atacar o guarda`: comentário separado do cálculo.
- [ ] `  D20 teste de percepção`: aceitar espaços iniciais e maiúsculas.
- [ ] `Vou usar d30`, `Ataque: d30`, `!d30`, `/r d30` e `-d30`: nenhuma resposta.
- [ ] `d30abc`, `d30+`, `d1`, `d100001`, `101d20`, `99d20+2d4`, `d20 * 2`: erro, sem resultado parcial.
- [ ] Atributo inexistente: erro curto e compreensível, removido depois de aproximadamente 15 segundos.
- [ ] `100d100000`: todos os valores e total visíveis, sem ultrapassar limites do Discord.
- [ ] Mensagem candidata com mais de 1.000 caracteres: erro de tamanho.
- [ ] Bots e webhooks: nenhuma rolagem; mensagem privada: nenhuma rolagem.
- [ ] Editar uma mensagem existente não dispara uma nova rolagem.
- [ ] `@everyone` no comentário não gera notificação.

## Perfis e permissões

- [ ] `/perfil` antes do primeiro cadastro: orientação para cadastrar.
- [ ] `/atributo definir nome:for valor:8`; `d30+FOR` usa +8.
- [ ] Atualizar FOR para 10; próxima rolagem usa +10.
- [ ] Definir CON negativo; verificar subtração de atributo negativo.
- [ ] Parar e iniciar o bot; confirmar persistência de atributos e cargo configurado.
- [ ] Outro jogador possui atributos independentes.
- [ ] Mesmo jogador em outro servidor possui perfil independente.
- [ ] Usuário comum não consegue configurar o cargo nem editar/remover atributos alheios.
- [ ] Sem cargo de mestre configurado, `/mestre` orienta a configuração.
- [ ] Dono ou Gerenciar Servidor consegue executar `/config mestre`.
- [ ] Cargo @everyone e cargo de integração são rejeitados na configuração.
- [ ] Jogador com o cargo exato configura e remove atributo alheio.
- [ ] Cargo com mesmo nome e ID diferente não concede permissão.
- [ ] Remover cargo do mestre revoga sua capacidade de editar outros jogadores.
- [ ] Dono consegue configurar outro cargo após exclusão do cargo anterior.
- [ ] `/atributo remover` remove somente o próprio atributo.
- [ ] Confirmações e erros de gestão aparecem somente para quem usou o comando.
- [ ] Comandos de gestão não funcionam em DMs.

## Uso móvel e falhas

- [ ] No celular, cadastrar atributo, consultar perfil e rolar `d30+FOR` sem barra de rolagem.
- [ ] Conferir legibilidade de comentário, sinais, dados individuais e total em tela pequena.
- [ ] Retirar temporariamente Send Messages em canal de teste: sem derrubar o bot;
  restaurar permissões e confirmar próxima rolagem.
- [ ] Retirar Read Message History: conferir falha discreta e restaurar permissão.
- [ ] Interromper rede brevemente e restaurar: conferir reconexão; não esperar recuperação garantida
  de mensagens enviadas durante indisponibilidade.

## Registro do resultado

| Data | Cenário | Resultado | Evidência sem segredo | Pendência |
| --- | --- | --- | --- | --- |
| 25/10/2026 | Funcionamento inicial relatado pelo usuário | Relato positivo | Conversa | Registrar cenários |
| 25/10/2026 | Expressões da versão posterior relatadas pelo usuário | Relato positivo | Conversa | Registrar cenários |
| 25/10/2026 | Repetição com # confirmada pelo usuário | Relato positivo | Conversa e imagem | Registrar demais cenários |
| A preencher | Nova margem e alinhamento dos totais | Pendente | — | Conferir no computador e celular |
| A preencher | Centralização, seta longa e negrito nos dados 1/máximo | Pendente | — | Conferir após reiniciar |

Só registrar como validado no Discord após executar os casos relevantes e resolver falhas.
