# Caldronis Dice

Bot de Discord em Python com rolagens sem prefixo e atributos personalizados por jogador e
servidor. A especificação principal está em [CALDRONIS_DICE_WORK_PROMPT.md](CALDRONIS_DICE_WORK_PROMPT.md).

**Estado: funcionamento das rolagens e repetições relatado pelo usuário no Discord; versão
consolidada com totais centralizados, seta longa e destaques de dados naturais, aguardando
conferência visual real.**
O checklist completo ainda precisa ser registrado.
O agente não realizou login com token do Discord. Repositório público:
[IgorDigitos/Caldronis-Dice](https://github.com/IgorDigitos/Caldronis-Dice).
Para conferir a versão atual, siga o [roteiro curto de validação](docs/QUICK_VALIDATION.md).

O formato foi alterado a pedido do usuário, tomando a imagem do Rollem como referência.
Veja a [comparação de recursos e configurações](docs/ROLLEM_COMPARISON.md) antes de escolher extras.
Por solicitação posterior do usuário, manter/descartar foi removido. A sintaxe `N#expressão` foi
autorizada como exceção à regra original de iniciar diretamente por um dado; o corpo ainda precisa
começar por dado e tudo continua ancorado no início da mensagem.

## Iniciar localmente no Windows

Requer Python 3.11 ou superior e acesso à internet para baixar dependências e conectar ao Discord.
No PowerShell:

```powershell
cd 'C:\Caldronis Dice'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
Copy-Item .env.example .env
notepad .env
```

Se `.env` já existir, edite-o e pule a cópia para preservar a configuração existente.
Não é necessário ativar o ambiente nem alterar políticas do PowerShell.

Preencha no arquivo local:

```dotenv
DISCORD_TOKEN=seu_token_local
DEV_GUILD_ID=id_do_servidor_de_testes
DATABASE_PATH=data/caldronis.sqlite3
```

O token é segredo: não envie no chat, não tire capturas dele e não publique `.env`.
Em caso de vazamento, redefina o token no portal. As variáveis do ambiente têm precedência sobre `.env`.
O caminho relativo do banco é resolvido a partir da pasta do projeto.

Execute:

```powershell
.\.venv\Scripts\python.exe bot.py
```

O bot sincroniza os comandos ao iniciar. `Ctrl+C` encerra o processo; precisa permanecer rodando para
responder. O banco e suas tabelas são criados automaticamente no primeiro início.
Para instalar somente dependências de execução, use `pip install -e .` com o Python do ambiente.

## Configurar o Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications), crie uma aplicação
   e configure seu bot na seção **Bot**. Copie o token somente para o `.env` local.
2. Em **Bot → Privileged Gateway Intents**, habilite **Message Content Intent**. O código também o
   habilita. Não precisa habilitar **Server Members Intent** nem **Presence Intent**.
3. No gerador de convite em **OAuth2 → URL Generator**, selecione os escopos `bot` e
   `applications.commands`. Instale no servidor de testes usando uma conta autorizada a instalar bots.
4. Permissões do bot: **View Channels**, **Send Messages** e **Read Message History**.
   O formato compacto atual usa texto e não precisa de **Embed Links**.
   Para usar threads, conceda **Send Messages in Threads** e acesso à thread. Não precisa de
   Administrator, Manage Roles ou Manage Messages. Verifique também as substituições de cada canal.
5. Ative o modo desenvolvedor no Discord, copie o ID do servidor de testes e coloque-o em
   `DEV_GUILD_ID`. Reinicie o processo. O bot deve aparecer online e registrar quatro grupos/comandos
   de nível superior: `/perfil`, `/atributo`, `/mestre` e `/config`.
6. Crie um cargo comum para mestres, atribua-o às pessoas corretas e execute
   `/config mestre cargo:<cargo>`. Somente o dono ou quem possui **Gerenciar Servidor** pode configurar.
   `@everyone`, cargos de integrações e cargos de outro servidor são rejeitados.
7. Teste seguindo [docs/DISCORD_CHECKLIST.md](docs/DISCORD_CHECKLIST.md), inclusive pelo celular.

Com `DEV_GUILD_ID` preenchido, a sincronização é específica do servidor de desenvolvimento. Com ele
vazio, os comandos são sincronizados globalmente e a disponibilidade pode demorar. Ao mudar para
registro global, comandos antigos específicos do servidor podem continuar aparecendo nesse servidor;
não se faz exclusão automática de registros remotos neste MVP. Não misture os modos durante a primeira
validação.

Referências oficiais: [intents](https://discordpy.readthedocs.io/en/stable/intents.html) e
[comandos de aplicação](https://discordpy.readthedocs.io/en/stable/interactions/api.html).

## Uso

Mensagens comuns no canal, sem `/r`, `!` ou outro prefixo:

```text
d30
d2
d100000
2d30+5
d30+FOR
d30 + FOR + d4
d30+FOR-CON atacar o guarda
2#d30
3#d30+FOR
2#3d6
```

### Repetir rolagens com #

| Mensagem | Efeito |
| --- | --- |
| `2#d30` | Rola um d30 duas vezes, com dois totais separados |
| `3#d30+FOR` | Rola d30 e soma FOR em cada uma das três repetições |
| `2#3d6` | Rola três d6 duas vezes, com um total por grupo de três |

O número antes de `#` indica quantas vezes repetir a expressão inteira. Use `2#d30`, com o número
junto do `#`; espaços após `#` e dentro da expressão são aceitos, como `2# d30 + FOR`.
`2d30` continua sendo dois dados somados em um único resultado; `2#d30` gera dois resultados separados.

Exemplo de `2#d30`, com resultados 12 e 15, seguindo a imagem enviada pelo usuário:

`12` ← [12] 1d30  
`15` ← [15] 1d30

Uma linha por repetição na mesma resposta, sem cabeçalho, numeração ou soma geral. Com `#`, os
valores e repetições ficam na ordem do sorteio; sem `#`, cada grupo aparece do maior para o menor.
Isso também vale para `1#3d6`. Em repetições, `d30` é mostrado como `1d30`.
Atributos e comentário compartilhados aparecem uma única vez, depois das linhas de resultados.
Rolagens grandes são divididas em mensagens quando necessário, preservando todas as linhas.

São permitidas de 1 a 100 repetições, até 100 dados e 100 termos no conjunto, com 30 termos por
expressão. Exemplo: `50#2d6` é aceito; `51#2d6` excede 100 dados; `100#d6+1` excede 100 termos.
Zero, repetição aninhada, dados inválidos e expressões incompletas são rejeitados antes de sortear.
Os modificadores `kh`, `kl`, `dh`, `dl`, `k` e `d` de manter/descartar não são aceitos.

`Vou usar d30`, `Ataque: d30`, `!d30`, `/r d30` e `-d30` são ignoradas sem consultar o banco.
Espaços iniciais e diferenças entre maiúsculas/minúsculas são aceitos. Bots, webhooks e DMs são
ignorados. Apenas novas mensagens são processadas; editar uma mensagem não faz outra rolagem.

Comandos de gestão, com confirmações e erros privados:

| Comando | Efeito |
| --- | --- |
| `/perfil` | Consulta seus próprios atributos neste servidor |
| `/atributo definir nome:FOR valor:8` | Cria ou atualiza seu atributo |
| `/atributo remover nome:FOR` | Remove seu atributo |
| `/mestre definir jogador:@jogador nome:FOR valor:10` | Edita atributo de outro jogador |
| `/mestre remover jogador:@jogador nome:FOR` | Remove atributo de outro jogador |
| `/config mestre cargo:@Mestre` | Define o cargo de mestre por ID |

Um jogador tem um perfil por servidor; o primeiro cadastro cria o perfil. Ler um perfil vazio ou
rolar sem atributos não cria registros. Não existe histórico de rolagens no banco.
Um administrador ou dono **configura** o cargo, mas editar outro jogador exige possuir o cargo de
mestre configurado. Não existe privilégio implícito de edição alheia. O dono consegue recuperar a
configuração caso o cargo seja excluído ou perca acesso ao comando por configuração do Discord.
As permissões são verificadas no backend; visibilidade na interface não substitui autorização.

## Parser e limites

Gramática restrita, sem avaliação dinâmica de código:

```text
expressão := dado (('+' | '-') (dado | inteiro | atributo))*
dado      := [quantidade] ('d' | 'D') lados
mensagem  := espaços_iniciais [repetições '#'] espaços expressão [espaço comentário]
```

Após cada termo, os espaços são consumidos. Se o próximo caractere for `+` ou `-`, ele pertence à
expressão e exige outro termo. Caso exista outro texto após um espaço, ele inicia o comentário.
Depois disso, o comentário inteiro é texto livre e não participa do cálculo. Sem espaço, qualquer
sufixo inesperado é erro: `d30abc` e `d30+FORabc!` não causam rolagem parcial.

Por cautela, um comentário não pode começar por `* / % = ^ ( ) #`: `d20 * 2` é erro de operador, não
uma rolagem de `d20`. Comentários que começam por `+` ou `-` são interpretados como continuação da
expressão; escreva uma palavra antes desses símbolos se quiser incluí-los no comentário.
`d20 FOR` rola apenas `d20` com comentário `FOR`; para somar FOR, escreva `d20+FOR`.
`d20+`, `d20+FOR-CON` com CON ausente e qualquer expressão inválida falham por inteiro, antes
do sorteio. Uma frase que comece literalmente por `d30` aciona o bot por decisão da especificação.

| Limite | Valor |
| --- | --- |
| Lados por dado | 2 a 100.000 |
| Dados somados na expressão | 1 a 100 |
| Termos na expressão | 30 |
| Repetições com # | 1 a 100 |
| Dados no conjunto de repetições | 100 |
| Termos no conjunto de repetições | 100 |
| Mensagem candidata, incluindo comentário | 1.000 caracteres |
| Inteiro literal | 0 a 1.000.000.000; sinal pelo operador |
| Nome de atributo | 1 a 32 caracteres; `[A-Z][A-Z0-9_]*` |
| Valor de atributo | -1.000.000.000 a +1.000.000.000 |
| Atributos por perfil | 40 |

Nomes são normalizados para maiúsculas. Nomes como `D20`, compostos por D seguido somente de dígitos,
são reservados. `D20_MOD` e `D20KH1` são nomes válidos, pois manter/descartar foi removido.
Nenhum atributo ou configuração existente foi apagado. Não há multiplicação,
divisão, parênteses, números decimais ou operadores unários em sequência: use `d20-2`, não `d20+-2`.
Uma mensagem cujo começo não seja candidato é ignorada mesmo que longa.

Os resultados são respostas à mensagem original, que identifica o autor. Exemplo visual:

`58` ← [**30**, 20] 2d30 + 8

O total aparece primeiro, dentro da caixa de código, sem negrito adicional.
Conforme a regra escolhida pelo usuário, somente resultados naturais iguais a 1 (erro crítico)
ou ao número de lados (crítico) ficam em negrito dentro dos colchetes. Constantes, atributos e
total final não recebem esse negrito; os destaques não alteram o cálculo nem aplicam bônus/penalidades.
Exemplo: `d20+8` com dado 20 mostra `28` ⟵ [**20**] d20 + 8; com dado 1 mostra
`9` ⟵ [**1**] d20 + 8.
O total tem espaços inseparáveis dos dois lados dentro do código inline. Nas repetições, todos
os totais usam a largura do maior número e são centralizados, incluindo o sinal de negativos.
Um total isolado de um dígito tem a mesma margem dos dois lados, sem espaço extra à esquerda.
A seta `⟵` tem haste mais longa que a anterior `←`. A aparência final deve ser conferida no Discord.
Grupos de dados ficam junto de seus termos; atributos usados e seus valores aparecem na linha
seguinte, seguidos pelo comentário, quando existir. Os tokens da expressão são preservados,
normalizando espaços em volta dos operadores. Sem `#`, cada grupo é exibido do maior para o menor.
Com `#`, a ordem original dos sorteios é mantida na exibição e cada repetição tem seu próprio total.
Respostas longas são divididas em até 1.900 unidades UTF-16 por mensagem, sem omitir valores ou
sortear novamente. A divisão considera também emojis. Se um envio falhar, as continuações param.
Menções são desabilitadas e o texto livre é escapado. Erros de rolagem no canal são públicos e
apagados após 15 segundos quando possível; mensagens comuns não suportam respostas ephemeral.

## Estrutura

```text
Caldronis Dice/
├── CALDRONIS_DICE_WORK_PROMPT.md  especificação recebida
├── README.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── bot.py                       cliente, eventos e sincronização
├── config.py                    variáveis locais e validação
├── message_handler.py           integração de mensagens e formatação
├── dice/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   └── roller.py
├── profiles/
│   ├── __init__.py
│   ├── repository.py            SQLite, transações e trabalho fora do event loop
│   └── service.py               atributos e autorização
├── commands/
│   ├── __init__.py
│   ├── common.py
│   ├── profiles.py
│   ├── attributes.py
│   └── administration.py
├── tests/
│   ├── test_parser.py
│   ├── test_roller.py
│   ├── test_profiles.py
│   ├── test_message_detection.py
│   ├── test_commands.py
│   ├── test_config.py
│   └── test_repetitions.py
├── docs/
│   ├── DISCORD_CHECKLIST.md
│   ├── QUICK_VALIDATION.md        roteiro curto da versão consolidada
│   ├── ROLLEM_COMPARISON.md       pesquisa, recursos atuais e propostas
│   └── VALIDATION.md
└── data/                        gerada no início; ignorada pelo Git
```

O projeto usa Git, com branch principal `main` e repositório remoto `IgorDigitos/Caldronis-Dice`.
`.venv`, `.env`, bancos, caches e metadados de instalação são ignorados. A pasta atual é a raiz,
sem outra pasta aninhada. Confira os commits com `git log --oneline` e alterações com `git status`.

## Verificações locais

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check
```

Os testes não precisam de rede, token ou servidor Discord. Os testes de integração usam banco real
temporário e objetos Discord simulados. O gerador é injetável e determinístico nos testes; em produção
é usado `secrets.randbelow`, com sorteios independentes e sem operação de módulo sobre bytes aleatórios.
Os resultados registrados estão em [docs/VALIDATION.md](docs/VALIDATION.md).

## Operação, falhas e limites do MVP

- SQLite usa parâmetros, chaves compostas por servidor/usuário, foreign keys, unicidade e transações.
  Cada operação abre e fecha sua conexão numa thread; espera de bloqueio é limitada a 5 segundos.
  O limite de atributos é verificado na mesma transação da gravação, inclusive sob concorrência.
- Token e conteúdo completo do chat não são registrados nos logs da aplicação. Não habilite logs de
  depuração HTTP/Gateway em ambientes reais sem revisar seus efeitos sobre privacidade.
- Falhas de envio e permissões são registradas sem repetir a rolagem. Não há resposta alternativa se o
  bot não consegue enviar no canal. Falhas do banco retornam erro sem expor detalhes internos.
- O cliente usa a reconexão padrão da biblioteca para desconexões recuperáveis; não promete entrega
  de mensagens perdidas enquanto estiver offline ou idempotência entre múltiplas instâncias.
- Execute uma única instância por token/banco. Não há hospedagem 24/7, fila, limitação de frequência
  própria por usuário ou proteção contra ataques distribuídos; existem limites por entrada e os
  controles de taxa da API. O escopo é um bot simples de mesa de RPG.
- Para backup, pare o bot e copie o arquivo configurado em `DATABASE_PATH`. Preserve-o ao atualizar
  o código. Não existe interface de exclusão completa de perfil, migração avançada ou exportação.
- Sem IA, áudio, combate, iniciativa, NPCs, inventário, rolagens secretas, histórico persistente,
  painel web, múltiplos personagens ou integração com OpenRPG.
- Pendências: conferir o espaçamento e o alinhamento após reiniciar o bot e registrar o checklist real;
  confirmar configuração do cargo de mestre e testes de permissões, se ainda não feitos.
  Python 3.11–3.13 ainda não foi executado neste ambiente. Manter/descartar foi removido;
  explosões e outros extras não foram implementados.

Para futuras alterações, valide os testes, revise `git status` e faça um commit local. O envio ao
GitHub é uma etapa separada. A publicação inicial deste projeto foi solicitada pelo usuário;
isso não substitui a conferência de cada mudança no Discord.
