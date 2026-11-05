# Painel de ligar e desligar — Windows

Abra **Caldronis Dice** pelo atalho na Área de Trabalho.

- **Ligar:** inicia o bot sem abrir o PowerShell.
- **Desligar:** encerra a conexão e o processo do bot.
- **Fechar a janela:** também desliga o bot.

O painel mostra “conectado” somente depois da confirmação do Discord. Enquanto tenta estabelecer
a conexão ou reconectar, mostra esse estado. Ligar novamente enquanto o bot está ativo não cria
outro processo. Também há travas por projeto para o painel e para as versões atualizadas do bot.

**Antes do primeiro uso:** se o bot já estiver rodando no PowerShell, encerre essa instância com
`Ctrl+C`. Um processo iniciado com código antigo, antes de existir a trava, não pode ser protegido
retroativamente. Depois, use o painel para ligar e desligar.

## Onde ficam os arquivos

- Executável: `dist/CaldronisDice.exe`, dentro da pasta do projeto.
- Atalho: `Caldronis Dice.lnk`, na Área de Trabalho.
- Token e configurações: `.env`, na pasta do projeto.
- Atributos: banco definido em `DATABASE_PATH`, normalmente `data/caldronis.sqlite3`.

Este executável é um **painel para a instalação local**, não uma distribuição independente do bot.
Ele usa os arquivos Python e o ambiente `.venv` existentes. Não apague nem mova essa pasta ou o
executável sem recriar o atalho. Atualizações nas rolagens entram ao desligar e ligar novamente;
não é necessário reconstruir o painel a cada alteração no motor de dados.

Token, banco e histórico do chat não são incluídos no executável. O painel recebe somente estados
conhecidos; não exibe respostas HTTP, conteúdo de mensagens nem credenciais. Não cria histórico
de rolagens ou novo arquivo de logs. O executável não foi assinado digitalmente.

## Encerramento

O painel pede ao processo que encerre a conexão normalmente. Se ele não terminar em 10 segundos,
o painel encerra somente o processo que criou. Não procura nem mata todos os processos Python.
Se o painel cair abruptamente, o fim do canal de controle pede ao bot que se desligue também.

## Reconstruir o painel

Somente necessário ao alterar o painel, seu controlador ou trocar a pasta do projeto. Na raiz:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[desktop]'
.\scripts\build_desktop.ps1
```

O script usa PyInstaller com janela gráfica, sem console e sem copiar `.env` ou banco.
Ele cria o executável em `dist/` e o atalho da Área de Trabalho; preserva um atalho homônimo que
aponte para outro aplicativo. `build/` e `dist/` ficam fora do Git.

Referência: [opções oficiais do PyInstaller](https://pyinstaller.org/en/stable/usage.html).

## Conferência manual

- [ ] Abrir o atalho: somente o painel aparece, sem PowerShell ou console.
- [ ] Ligar: aguardar “Ligado e conectado ao Discord” e conferir `d30` no canal de testes.
- [ ] Desligar: conferir que o bot para de responder.
- [ ] Ligar novamente: conferir `d30+FOR` e persistência dos atributos.
- [ ] Fechar a janela com o bot ligado: conferir encerramento.
- [ ] Abrir o atalho duas vezes: não abrir dois painéis/controladores para o mesmo projeto.
- [ ] Falha de rede/configuração: exibir estado de erro sem expor token ou detalhes internos.

Os testes automatizados do painel usam cliente e processo de demonstração, sem conectar um token
real ao Discord. Eles não substituem a conferência real acima.
