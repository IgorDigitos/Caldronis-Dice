# Caldronis Dice

Bot de dados para Discord, pensado como uma alternativa modular para quem quer adaptar o rolador
às necessidades da própria mesa de RPG. Usa Python, discord.py e SQLite, com módulos separados
para interpretar expressões, sortear dados, salvar atributos e gerenciar comandos.

**Desenvolvido com auxílio de IA (ChatGPT/Codex) na criação do código, dos testes e da documentação.**
As rolagens são processadas por um parser restrito e um gerador aleatório; não dependem de IA.

## O que faz

- Rola dados diretamente no chat, sem prefixo ou comando de barra.
- Salva atributos personalizados de cada jogador, separados por servidor.
- Repete expressões com `#`, mostrando um resultado por linha.
- Conta dados por alvo: `>>` para iguais ou maiores e `<<` para iguais ou menores.
- Aceita `!`: explosões em somas e críticos em dobro nas contagens.
- Permite ao jogador editar seus atributos e ao mestre autorizado editar os de outros jogadores.

## Exemplos

| Mensagem | Resultado |
| --- | --- |
| `d30` | Rola um dado de 30 lados |
| `2d30+8` | Soma dois dados de 30 lados e adiciona 8 |
| `d30+FOR` | Soma ao dado a FOR cadastrada do jogador |
| `d30+FOR atacar o guarda` | Faz a rolagem e mantém o texto como comentário |
| `2#d30` | Faz duas rolagens independentes |
| `3#d30+FOR` | Repete três vezes a rolagem com FOR |
| `5d6>>4` | Conta quantos dos cinco dados saíram com 4 ou mais |
| `5d6<<3` | Conta quantos dos cinco dados saíram com 3 ou menos |
| `3#5d6>>4` | Faz três contagens independentes de sucessos |
| `d6!` | Ao sair 6, sorteia novamente e soma todos os resultados |
| `5d6!>>4` | Conta 4 ou mais; cada 6 vale 2, sem dados extras |
| `5d6!<<3` | Conta 3 ou menos; cada 1 vale 2, sem dados extras |

A expressão precisa estar no início da mensagem. Frases como `Vou usar d30` são ignoradas.
Os dados sempre aparecem do maior para o menor, inclusive com `#`, `>>` e `<<`.
Cada repetição permanece em sua própria linha, sem mudar a ordem das rolagens.
O 1 e o máximo natural de cada dado aparecem em negrito, sem alterar o cálculo.

Na contagem, o número à esquerda mostra quantos dados atenderam ao alvo, sem rótulos de
sucesso ou fracasso. Exemplo: `5d6>>4` com `[6, 5, 4, 2, 1]` retorna **3**;
`5d6<<3` com `[6, 5, 3, 2, 1]` também retorna **3**. Sem `!`, cada dado conta no máximo uma vez,
sem cancelamentos por resultado 1. Espaços, comentário e repetição são aceitos: `3#5d6 << 3 atacar`.
Por enquanto, use um único grupo de dados e alvo inteiro de 0 a 1.000.000.000;
atributos, somas e subtrações não podem ser combinados com esses operadores.
Em `>>`, um alvo acima dos lados retorna zero; em `<<`, conta todos os dados.
Rolagens comuns com atributos continuam funcionando normalmente.

### Como funciona o !

- **Sem contagem:** o máximo natural gera outro dado do mesmo tipo; máximos consecutivos continuam
  explodindo. `d6!` com 6 e depois 4 soma **10**. Funciona com atributos, subtrações e repetição:
  `3d6!+FOR`, `d30-d6!` e `2#d6!`.
- **Com `>>`:** o máximo natural vale **2**, sem sortear outro dado. Em `5d6!>>4`,
  `[6, 5, 4, 2, 1]` retorna **4**.
- **Com `<<`:** o 1 natural vale **2**, sem sortear outro dado. Em `5d6!<<3`,
  `[6, 5, 3, 2, 1]` retorna **4**.

O dobro só se aplica a dados que atendem ao alvo. O `!` deve ficar junto do dado: `d6!`, não `d6 !`.
Todos os resultados ficam visíveis, inclusive os extras das explosões, em ordem decrescente.
São aceitos até **100 sorteios por mensagem**, somando dados iniciais, extras e todas as repetições.
Se for necessário ultrapassar esse limite, o bot retorna erro sem mostrar resultado parcial.
Não há suporte a `!!` ou a um alvo de explosão como `d6!5`.

## Comandos

| Comando | Função |
| --- | --- |
| `/perfil` | Consulta seus atributos |
| `/atributo definir nome:FOR valor:8` | Cria ou atualiza um atributo seu |
| `/atributo remover nome:FOR` | Remove um atributo seu |
| `/mestre definir jogador:@jogador nome:FOR valor:10` | Define um atributo de outro jogador |
| `/mestre remover jogador:@jogador nome:FOR` | Remove um atributo de outro jogador |
| `/config mestre cargo:@Mestre` | Configura o cargo autorizado a editar outros jogadores |

Somente o dono ou quem tem **Gerenciar Servidor** pode configurar o cargo de mestre.
As confirmações e os erros dos comandos de gestão são privados.

## Instalação

Requer **Python 3.11 ou superior**. No PowerShell:

```powershell
git clone https://github.com/IgorDigitos/Caldronis-Dice.git
cd Caldronis-Dice
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
Copy-Item .env.example .env
notepad .env
```

Se já tem o projeto, use a pasta existente e preserve seu `.env`.
Preencha esse arquivo localmente:

```dotenv
DISCORD_TOKEN=seu_token
DEV_GUILD_ID=id_do_servidor_de_testes
DATABASE_PATH=data/caldronis.sqlite3
```

**Não publique nem compartilhe o token ou o arquivo `.env`.** O banco é criado automaticamente.

## Configuração do Discord

1. Crie uma aplicação no [Discord Developer Portal](https://discord.com/developers/applications)
   e obtenha o token na seção **Bot**.
2. Habilite **Message Content Intent**. Members e Presence Intents não são necessários.
3. Convide o bot com os escopos `bot` e `applications.commands` e as permissões **View Channels**,
   **Send Messages** e **Read Message History**. Para threads, inclua **Send Messages in Threads**.
4. Ative o modo desenvolvedor no Discord, copie o ID do servidor e preencha `DEV_GUILD_ID`.
5. Inicie o bot e, se precisar de mestres, configure o cargo usando `/config mestre`.

`DEV_GUILD_ID` registra os comandos no servidor de testes. Deixe vazio para registro global.

## Executar e testar

Inicie o bot na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe bot.py
```

Mantenha o processo aberto para o bot responder. Use `Ctrl+C` para encerrar.

Para executar os testes locais:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Limites e estado atual

- Dados de 2 a 100.000 lados, até 100 sorteios por mensagem, incluindo explosões e repetições.
- Até 30 termos por expressão, 100 termos no conjunto de repetições e 1.000 caracteres por mensagem.
- Até 40 atributos por perfil; nomes de até 32 caracteres e valores inteiros.
- Não inclui combate, inventário, painel web ou modificadores de manter/descartar.
- Hospedagem e execução ficam por conta de quem instala o bot.

Há testes automatizados e relatos de funcionamento no Discord. Isso não substitui a validação
de cada mudança e configuração no servidor, incluindo a aparência pelo celular.

## Documentação

- [Conferência rápida no Discord](docs/QUICK_VALIDATION.md)
- [Checklist completo](docs/DISCORD_CHECKLIST.md)
- [Resultados dos testes locais](docs/VALIDATION.md)
- [Comparação de recursos com o Rollem](docs/ROLLEM_COMPARISON.md)
- [Especificação inicial](CALDRONIS_DICE_WORK_PROMPT.md)
