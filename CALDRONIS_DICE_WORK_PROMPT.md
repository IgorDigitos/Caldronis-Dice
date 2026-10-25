# Caldronis Dice Bot — Instruções de implementação para ChatGPT Work

> **Missão:** implementar, testar e documentar a primeira versão funcional de um bot de rolagem de dados para Discord. **Não entregue apenas um planejamento:** crie os arquivos do projeto, escreva o código e execute os testes disponíveis. Trabalhe em etapas, com código simples e manutenção fácil.
>
> **Idioma:** documentação, mensagens do bot e explicações ao usuário em português do Brasil. Código e nomes técnicos podem usar inglês.

## 1. Contexto e objetivo

O bot será utilizado em mesas de RPG, sobretudo por jogadores que acessam o Discord pelo celular. Hoje eles precisam consultar a ficha para verificar atributos. O objetivo é permitir que escrevam diretamente `d30+FOR`, por exemplo, e recebam a rolagem com a FOR armazenada no perfil do autor.

**Escopo deliberadamente enxuto:** rolador universal com atributos personalizados, sem gerenciamento de combate, inventário, NPCs/inimigos, habilidades, IA, interface web ou integração com OpenRPG. Um jogador possui **um perfil por servidor**; não haverá troca entre múltiplos personagens nesta versão.

## 2. Decisões obrigatórias do MVP

- **Plataforma:** Discord; **linguagem:** Python 3.11+; **biblioteca:** `discord.py` estável; **persistência:** SQLite.
- **Dados permitidos:** qualquer quantidade de lados de **2 a 100.000**, inclusive `d2`, `d30` e `d100000`.
- **Quantidade de dados por expressão:** máximo de **100 dados no total**; limitar também o número de termos e tamanho da mensagem processada para evitar abuso. Nunca gerar uma lista gigantesca de dados.
- **Expressões:** dados, inteiros, atributos personalizados e operadores `+`/`-`: `d30`, `2d30+5`, `d30+FOR`, `d30+FOR+d4`, `d30+FOR-CON`, `3d6-2`.
- **Atributos:** nomes normalizados sem distinção de maiúsculas/minúsculas (`for` = `FOR`); sugerir `[A-Z][A-Z0-9_]*`, comprimento máximo razoável, e valores inteiros, inclusive negativos. O usuário pode criar nomes como `FOR`, `CON`, `AGI` ou outros. Não impor lista fixa.
- **Perfil:** vínculo por `(guild_id, discord_user_id)`, com atributos individuais e persistentes após reinício. Criar perfil automaticamente no primeiro cadastro, não exigir criação para rolagens sem atributo.
- **Edição:** o jogador altera apenas o próprio perfil; um mestre autorizado pode alterar o de outros jogadores.
- **Rolagens:** mensagens comuns no Discord, **sem `/r` e sem outro prefixo**. Comandos administrativos podem usar `/`.
- **Transparência:** mostrar autor, expressão original, resultados individuais dos dados, valores de atributos usados e total. Ao formatar, manter a resposta legível em celular.
- **Não armazenar histórico de rolagens** no banco no MVP; as mensagens do próprio Discord são suficientes por enquanto.

## 3. REGRA PRIORITÁRIA: só rolar quando o dado estiver no início da mensagem

A mensagem só é candidata a rolagem se **o primeiro conteúdo não vazio** começar com `dN` ou `XdN`, ignorando diferenças entre maiúsculas/minúsculas e espaços iniciais. `N` indica lados, `X` indica quantidade de dados. Assim, `2d30` também conta como começar com uma expressão de dados. A primeira parcela da expressão deve ser um dado.

**Deve rolar:**

| Mensagem recebida | Comportamento |
|---|---|
| `d30` | Rolar 1d30 |
| `d100000` | Rolar 1d100000 |
| `2d30+5` | Rolar 2d30+5 |
| `d30+FOR` | Consultar FOR do autor e rolar |
| `d30 + FOR + d4` | Aceitar espaços dentro da expressão |
| `d30+FOR atacar o guarda` | Rolar `d30+FOR`; tratar o restante como comentário |
| `  d20 teste de percepção` | Rolar `d20` (espaço inicial tolerado) |

**Não deve rolar:**

| Mensagem recebida | Comportamento |
|---|---|
| `Vou usar d30+FOR` | Ignorar: dado não está no início |
| `Ataque: d30+8` | Ignorar: dado não está no início |
| `!d30` | Ignorar: prefixo não permitido |
| `/r d30` | Não interpretar como mensagem de rolagem |
| `-d30` | Ignorar: primeiro elemento não é dado |
| `d30abc` | Não fazer rolagem parcial de `d30` |

**Expressões que começam corretamente, mas são inválidas:** `d1`, `d100001`, `101d20`, `d30+`, `d30+ATRIBUTO_INEXISTENTE`. Não executar rolagem parcial; informar o erro de forma discreta, com contexto suficiente para corrigir. Diferenciar mensagem que não é comando (ignorar) de tentativa inválida de rolagem (responder com erro).

**Comentários após a expressão:** aceitar texto livre **apenas depois de espaço separador**, por exemplo `d30+FOR atacar o guarda`. O motor deve extrair uma expressão válida a partir do começo sem tratar palavras soltas do comentário como atributos. Não engolir erros sintáticos: em `d30+` não é permitido rolar apenas `d30`; em `d30+FOR-CON` não ignorar o `-CON`. Projetar um tokenizador/parser bem definido e documentar a regra de separação entre expressão e comentário. Se houver caso ambíguo, priorizar não rolar incorretamente.

**Importante:** essa regra é intencional. Uma frase que comece literalmente com `d30` será interpretada como rolagem, mesmo que o autor estivesse falando sobre dados; não adicionar heurísticas de IA para adivinhar intenção.

## 4. Interface e comandos

### Rolagens de chat (sem barra)

O usuário digita `d30+FOR`, e o bot responde no mesmo canal, de preferência em resposta à mensagem original, por exemplo:

> **Rolagem de Thainan**  
> `d30 + FOR`  
> 🎲 d30: **18**  
> FOR: **+8**  
> **Total: 26**

Para `2d30+5`, exibir os valores individuais (ex.: `[12, 27] + 5 = 44`). Exibir comentários, quando existentes, como descrição opcional sem alterar o cálculo.

### Comandos slash de gestão

- `/perfil` — mostrar o próprio perfil; opcionalmente permitir visualizar o perfil de um usuário mencionado.
- `/atributo definir nome:<texto> valor:<inteiro>` — criar/atualizar atributo do próprio usuário.
- `/atributo remover nome:<texto>` — remover atributo do próprio usuário.
- `/mestre definir jogador:<membro> nome:<texto> valor:<inteiro>` — mestre configura atributo de outro jogador.
- `/mestre remover jogador:<membro> nome:<texto>` — mestre remove atributo de outro jogador.
- `/config mestre cargo:<cargo>` — servidor configura o cargo de mestre. **Apenas dono do servidor ou membro com permissão administrativa adequada** pode executar essa configuração.

Usar respostas privadas (*ephemeral*) para confirmação de edições e erros sensíveis; rolagens comuns devem ser públicas. Se o cargo de mestre não estiver configurado, orientar o administrador a configurá-lo; não conceder automaticamente privilégio a qualquer jogador. Validar autorização no **backend** de todo comando, nunca apenas na visibilidade da interface. Reconhecer mestre pelo ID do cargo, não pelo nome textual. O dono do servidor pode recuperar/ajustar a configuração.

**Não implementar rolagens secretas no MVP.**

## 5. Arquitetura sugerida

Criar uma estrutura semelhante a esta, podendo ajustar detalhes tecnicamente justificados:

```text
caldronis-dice/
├── README.md
├── .env.example
├── .gitignore
├── pyproject.toml              # ou requirements.txt
├── bot.py
├── config.py
├── dice/
│   ├── __init__.py
│   ├── parser.py              # interpretar e validar expressões
│   ├── roller.py              # sortear valores, calcular, retornar detalhes
│   └── models.py              # estruturas tipadas de resultado
├── profiles/
│   ├── __init__.py
│   ├── repository.py          # SQLite, queries parametrizadas
│   └── service.py             # regras de atributos e autorização
├── commands/
│   ├── __init__.py
│   ├── profiles.py
│   ├── attributes.py
│   └── administration.py
├── tests/
│   ├── test_parser.py
│   ├── test_roller.py
│   ├── test_profiles.py
│   └── test_message_detection.py
└── data/                      # banco local, ignorado pelo Git
```

Princípios:

1. **Separação clara:** parsing, rolagem, persistência, permissões e integração Discord independentes.
2. **Proibido `eval()` ou `exec()`** para calcular mensagens de usuários. Implementar parser restrito, com validação explícita de tokens, operadores e limites.
3. **Testabilidade:** poder injetar gerador de números aleatórios (*random source*) nos testes e obter resultados determinísticos. Em produção usar gerador apropriado para sorteios imparciais.
4. **SQLite seguro:** queries parametrizadas, constraints/índices adequados, chaves com `guild_id`, criação de tabelas no primeiro uso, contexto de transação, fechamento de conexões e sem bloquear event loop durante operações prolongadas. Não adicionar serviços externos.
5. **Segurança:** não registrar token ou conteúdo completo do chat nos logs. Ignorar bots, webhooks e mensagens privadas. Limitar tamanho de entrada, quantidade de operações e dados; lidar com erros sem derrubar o processo.
6. **Baixa complexidade:** não introduzir Docker, ORM, Redis, filas, serviços pagos ou arquitetura distribuída sem justificativa indispensável.

Modelo lógico sugerido de banco:

```text
profiles(guild_id, user_id, created_at, updated_at)
attributes(guild_id, user_id, name_normalized, value)
guild_settings(guild_id, master_role_id)
```

Definir chaves primárias/estrangeiras e garantir unicidade de `attributes` por `(guild_id, user_id, name_normalized)`.

## 6. Integração com Discord

- Criar o bot no [Discord Developer Portal](https://discord.com/developers/applications).
- As rolagens usam o evento de mensagens (`on_message`) e, por isso, exigem **Message Content Intent** ativado tanto no portal (Bot → Privileged Gateway Intents) quanto no código (`intents.message_content = True`). Não habilitar outros *privileged intents* sem necessidade.
- Solicitar permissões mínimas ao instalar no servidor: leitura de canal, envio de mensagens, histórico para responder, e escopo `applications.commands` para comandos slash; ajustar conforme a API/biblioteca.
- Os comandos `/perfil`, `/atributo`, `/mestre` e `/config` usam `discord.app_commands` e precisam de sincronização. Permitir `DEV_GUILD_ID` no `.env` para registrar e testar comandos em servidor de desenvolvimento com resposta rápida.
- Não assumir que o bot pode receber conteúdo de mensagens sem habilitar o intent.
- Isolar a lógica do parser da API do Discord.
- Se uma mensagem não começar com um dado, **não responder e não consultar o banco**.

Referências oficiais:

- [Discord — Gateway & Privileged Intents](https://discord.com/developers/docs/events/gateway)
- [discord.py — Gateway Intents](https://discordpy.readthedocs.io/en/stable/intents.html)
- [discord.py — Application Commands](https://discordpy.readthedocs.io/en/stable/interactions/api.html)

## 7. Plano obrigatório de execução no Work

Execute as etapas na ordem; avance após testes locais suficientes. Não se limite a explicar o procedimento.

### Etapa A — Preparar projeto

1. Criar pasta/repositório local `caldronis-dice` e estrutura organizada.
2. Configurar ambiente Python e dependências (`discord.py`, suporte a `.env` e `pytest`; evitar dependências excessivas).
3. Criar `.env.example` com `DISCORD_TOKEN=`, `DEV_GUILD_ID=` e configuração opcional de caminho do banco; criar `.gitignore` contendo `.env`, dados SQLite, ambientes virtuais e caches.
4. Criar `README.md` com instalação, execução e exemplos de comandos, em português.

### Etapa B — Motor universal de dados

1. Criar detector ancorado no início da mensagem, conforme a **seção 3**.
2. Criar parser de `dN`, `XdN`, números, atributos, `+` e `-`; espaços permitidos; comentário final opcional.
3. Validar dados de 2 a 100.000 lados e até 100 dados por expressão.
4. Implementar motor de rolagem que entrega cálculo e detalhamento por dado/atributo.
5. Cobrir os casos válidos, limites, entradas malformadas e detecção de prefixo com testes automatizados.

### Etapa C — Perfis SQLite

1. Criar esquema, inicialização automática e funções de leitura, gravação e remoção de atributos.
2. Implementar isolamento entre servidores e usuários.
3. Implementar validação/normalização de nomes e autorização (dono do perfil ou mestre).
4. Criar testes de persistência, atualização de FOR de 8 para 10, isolamento e permissões.

### Etapa D — Conectar ao Discord

1. Integrar `on_message` sem responder a bots, DMs ou mensagens cujo início não seja um dado.
2. Buscar o perfil do autor somente quando a expressão requerer atributos.
3. Responder com embed simples e legível, ou texto quando mais apropriado.
4. Implementar `/perfil`, `/atributo definir`, `/atributo remover`, `/mestre definir`, `/mestre remover` e `/config mestre`.
5. Tratar erros comuns: falta de atributo, falta de cargo, permissões insuficientes, mensagens longas e problemas de conexão.
6. Documentar o convite do bot, configuração de intents e sincronização dos comandos.

### Etapa E — Validar e entregar

1. Executar testes (`pytest`) e corrigir falhas encontradas.
2. Fazer verificação estática/lint simples se viável sem dependências excessivas.
3. Criar checklist de testes manuais no Discord, incluindo uso pelo celular.
4. Informar exatamente quais arquivos foram criados, quais testes passaram, o que depende de configuração manual e quais limitações restam.
5. **Não inventar execução com token real** e não solicitar que o usuário cole token no chat. Explicar como inserir o token localmente no `.env`.
6. Não fazer deploy público, publicar repositório ou expor credenciais sem autorização explícita.

## 8. Critérios objetivos de aceitação

O MVP está pronto somente se:

- [ ] `d30` funciona sem barra, respondendo no canal.
- [ ] `d2`, `d100000`, `2d30+5`, `d30+FOR` e `d30+FOR+d4` funcionam.
- [ ] `d30+FOR atacar o guarda` rola e mantém o comentário separado.
- [ ] `Vou usar d30`, `Ataque: d30` e `!d30` **não** acionam o bot.
- [ ] `d30+`, `d1`, `d100001`, `101d20` e atributo ausente são tratados sem rolagem parcial.
- [ ] `FOR=8` é salva por usuário; `d30+FOR` usa 8. Após alteração para 10, usa 10.
- [ ] Os atributos persistem após reiniciar o bot.
- [ ] Usuários não conseguem editar atributos alheios; mestre autorizado consegue.
- [ ] Perfis do mesmo jogador em servidores diferentes são independentes.
- [ ] O bot ignora mensagens de outros bots e conversas privadas.
- [ ] `pytest` passa e os passos de instalação estão documentados.

## 9. Restrições de escopo e forma de resposta

- **Não incluir:** IA, transcrição de áudio, NPCs/inimigos, sistema de combate/iniciativa, inventário, rolagens secretas, histórico persistente, painel web, integração com OpenRPG, hospedagem 24/7 ou autenticação própria.
- **Não mudar as decisões sem motivo técnico concreto.** Quando um detalhe não estiver especificado, escolher o padrão mais simples, seguro e adequado ao uso móvel, documentando a escolha.
- **Faça o trabalho agora, dentro do ambiente do Work.** Se não houver acesso ao Discord/token, implemente todo o código e os testes locais e entregue instruções claras para a conexão posterior.
- Ao finalizar, apresentar um resumo breve: **implementado / testado / pendente de configuração / comando para executar**.

**Primeira prioridade:** ter `d30` e `d30+FOR` confiáveis, com a regra de início da mensagem funcionando rigorosamente. Recursos adicionais só entram após isso.
