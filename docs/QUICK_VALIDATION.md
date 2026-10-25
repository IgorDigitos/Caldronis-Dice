# Conferência da versão atual no Discord

O usuário relatou que as rolagens e repetições funcionaram. A versão atual também conta dados
por alvo: `>>` conta iguais ou superiores, `<<` conta iguais ou inferiores. O valor à esquerda
representa a contagem, sem rótulos de sucesso/fracasso. O negrito fica no 1/máximo naturais.
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
| [ ] | `2#5d6>>4` e `2#5d6<<3` | Duas linhas independentes em cada mensagem; dados do maior para o menor dentro de cada linha |
| [ ] | `2d30` e depois `2#d30` | O primeiro soma dois dados num total; o segundo mostra dois totais independentes |
| [ ] | `5d6>>4` | O número à esquerda conta apenas dados 4, 5 e 6; todos os valores continuam visíveis |
| [ ] | `5d6<<3` | O número à esquerda conta apenas dados 1, 2 e 3; o alvo 3 também entra |
| [ ] | `3#5d6 << 3 atacar` | Três contagens independentes, sem rótulos automáticos, com comentário único |
| [ ] | `5d6<<0` e `5d6<<6` | O primeiro retorna zero; o segundo retorna cinco |
| [ ] | `5d6<<`, `5d6<<3+1` e `5d6+FOR<<3` | Erro sem executar parcialmente a expressão |
| [ ] | `d6!` | Cada 6 gera outro d6; somar todos os valores, mostrando inclusive os extras |
| [ ] | `2#d6!` | Duas linhas independentes; orçamento de 100 sorteios compartilhado |
| [ ] | `5d6!>>4` | 4 e 5 valem 1; 6 vale 2; exatamente cinco sorteios, sem extras |
| [ ] | `5d6!<<3` | 2 e 3 valem 1; 1 vale 2; exatamente cinco sorteios, sem extras |
| [ ] | `d6 !`, `d6!!` e `d6!5` | Erro, sem rolagem parcial |
| [ ] | `3#5d6 >> 4 atacar` | Três contagens independentes, na ordem do sorteio, com um comentário ao final |
| [ ] | `5d6>>7` e `5d6>>1` | Zero sucessos no primeiro; cinco no segundo, sem cancelamento por resultado 1 |
| [ ] | `5d6>>`, `5d6>>4+1` e `5d6+FOR>>4` | Erro sem executar parcialmente a expressão |
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
