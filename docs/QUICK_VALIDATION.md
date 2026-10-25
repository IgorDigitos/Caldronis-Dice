# Conferência da versão atual no Discord

O usuário relatou que as rolagens e repetições funcionaram. O ajuste mais recente é visual:
margens simétricas no total isolado, centralização, seta `⟵` e negrito no 1/máximo naturais.
O total final permanece na caixa de código, sem negrito adicional.
Esta conferência verifica a versão consolidada; o checklist completo continua em
[DISCORD_CHECKLIST.md](DISCORD_CHECKLIST.md).

Não é necessário reinstalar dependências nem alterar `.env`. Reinicie o processo existente
com `Ctrl+C` e execute no PowerShell:

```powershell
cd 'C:\Caldronis Dice'
.\.venv\Scripts\python.exe bot.py
```

Use um servidor/canal de testes. Marque cada caso somente depois de conferir o resultado real.

| Feito | Digite ou execute | O que deve acontecer |
| --- | --- | --- |
| [ ] | `2#d30` | Duas linhas na mesma resposta, cada total em caixa com espaço dos dois lados; sem soma geral |
| [ ] | `5#d30-10` | Cinco totais separados; caixas com a mesma largura e números centralizados, inclusive se houver negativos |
| [ ] | `d4` | Quando sair um único dígito, conferir margens iguais dos dois lados e seta longa `⟵` |
| [ ] | `10#d4+8` | Quando sair 1 ou 4, apenas esse dado fica em negrito nos colchetes; os totais 9 e 12 não recebem negrito adicional |
| [ ] | `5d6` | Cinco valores do maior para o menor, todos incluídos no total |
| [ ] | `2d30` e depois `2#d30` | O primeiro soma dois dados num total; o segundo mostra dois totais independentes |
| [ ] | `/atributo definir nome:TESTE valor:8` e `2#d30+TESTE` | Cada linha soma 8; TESTE=+8 aparece uma vez abaixo dos resultados |
| [ ] | Reiniciar e executar `/perfil` | TESTE continua salvo; depois remova com `/atributo remover nome:TESTE` |
| [ ] | `Vou usar d30` e `Vou usar 2#d30` | Nenhuma resposta |
| [ ] | `d30+`, `2#d30+`, `51#2d6` | Erro breve, sem executar parte da rolagem |
| [ ] | Usuário sem cargo usa `/mestre definir` em outro jogador | Edição negada; atributo do alvo permanece intacto |
| [ ] | Mestre configurado repete a edição em um jogador de teste | Edição aceita; confirmação privada |
| [ ] | Repetir os três primeiros casos pelo celular | Caixas e resultados legíveis, sem corte ou linha perdida |

O nome TESTE pode existir no seu perfil: nesse caso escolha outro nome temporário para não
sobrescrever um atributo que já usa. Teste permissões apenas com jogadores de teste e valores
temporários. A margem deve ser conferida no Discord: testes de texto não comprovam a aparência
em todos os temas, fontes e celulares.

## Registro

Data: a preencher. Servidor/canal: a preencher. Dispositivo: a preencher.

- Resultado: a preencher.
- Cenários com falha: a preencher.
- Evidência: a preencher, sem token ou dados privados.

Depois da conferência, revise `git status` antes de criar o commit local. Publicar no GitHub
é um passo separado; não foi feito automaticamente.
