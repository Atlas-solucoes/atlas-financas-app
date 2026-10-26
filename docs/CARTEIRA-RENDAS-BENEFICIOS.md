# Carteira, rendas e benefícios

Acesso após publicação: mesmo endereço /nuvem/, botão Carteira no cabeçalho,
atalho na tela inicial e Ajustes. Nenhum cartão/banco é conectado automaticamente:
os cadastros são manuais, sem número completo do cartão, senha bancária ou Open Finance.

1. Cadastre os bancos e informe o saldo atual de cada um. São saldos de partida,
   não novas receitas. Conferir o saldo novamente incorpora os registros anteriores.
2. Cadastre VA e VR separadamente com seus saldos atuais; em Salário e outras rendas,
   use Recarga de VA/VR, selecione o benefício, valor mensal e dia de crédito.
3. Em Salário dividido, informe cada quinzena/parte, valor, dia e banco de destino.
   Outras rendas podem ser mensais ou avulsas. Previstas não alteram saldo real:
   confirme o recebimento em Editar → Recebida. Uma recarga já incluída no saldo
   de partida não deve ser confirmada novamente: cadastre o próximo crédito.
4. Ative Usar a soma dos bancos no saldo geral somente após conferir todas as contas.
   Isso mantém o saldo geral anterior salvo e exige conta nos novos registros.
   Desativar retorna ao modelo anterior. VA, VR e limite não entram nessa soma.
5. Cadastre cartão com limite total, fechamento, vencimento e banco pagador.
   Registre a compra em Registrar, selecionando o cartão; o valor é o total da compra.
   Parcelas são distribuídas em centavos exatos e comprometem o limite total.
   Compra no dia do fechamento entra no próximo ciclo. Conferir com o emissor;
   feriados, prazo de processamento, juros e pagamentos parciais não são simulados.
6. Pague a fatura pela Carteira, escolhendo o banco de origem. Não cria outra despesa:
   liquida as compras e libera apenas o limite pago. Reabrir desfaz a liquidação.
   Se já havia uma fatura manual entre contas fixas, confira para não duplicar a previsão.
7. Ao registrar, selecione banco, cartão, VA (Mercado) ou VR (Comida fora). Um benefício
   não pode ser usado além do saldo ou parcelado. Crédito não é uma fonte de renda.
8. Planejar uso de um saldo reserva um gasto programado; só Registrar gasto altera
   saldo. Planos também permitem selecionar origem/categoria e reserva mensal.
   Reserva em benefício não reduz dinheiro bancário. No crédito, a reserva mensal
   do plano é dinheiro para a fatura, nunca renda de crédito. Valores já guardados
   em planos de dinheiro ficam fora do caixa livre ao somar bancos.

Cadastros são arquivados, sem apagar histórico. Bancos arquivados continuam na soma
até o usuário conferir/zerar seu saldo, evitando desaparecimento de valores.
Rendas, carteira, compras, faturas e fontes dos planos integram o documento app_state,
backup e restauração da conta atual. Versão v1 de backups antigos continua aceita.

## Proteção de clientes antigos

supabase/proteger_carteira_legado.sql adiciona um gatilho de compatibilidade, sem
reescrever documentos. Depois que uma carteira for cadastrada, gravações de uma aba
antiga que não conhece pgSchema=1 serão recusadas. Atualize e reabra o aplicativo.
O cliente novo detecta cadastros remotos ausentes numa cópia local da mesma revisão
antes de enviá-la e abre a escolha de conflito com backup. Não desative essa proteção
num rollback sem antes preservar e migrar os novos campos.

## Validação

Comandos locais: node tests/investimentos.test.cjs e node tests/pagamentos.test.cjs.
19 testes de regressão e 14 novos cenários de cálculos, quinzenas, recargas,
parcelamento, saldo, caixa, planos e roundtrip. O teste navegador inclui os mesmos
formulários reais e dois contextos isolados, com backend REST em memória.
Resultados de execução no GitHub Actions devem ser conferidos antes da publicação.
Homologação final no celular: conferir saldos de partida com o banco/emissor,
confirmar uma quinzena e uma recarga, registrar VA/VR, compra parcelada, fatura,
plano e comparar o saldo após sincronizar o segundo aparelho.

## Evidências adicionais

O primeiro navegador passou todos os formulários de carteira e a recarga no segundo contexto. Parou depois em timeout do BCB real; a interface manteve a taxa manual. O teste separa agora o contrato positivo (payload de teste) da disponibilidade externa: tenta o BCB real no máximo duas vezes e registra EXTERNAL UNAVAILABLE se não responder, exigindo que a taxa anterior permaneça. Esse registro não equivale a aprovação da consulta real naquele horário.

A proteção contra clientes antigos foi aplicada no Supabase e testada em tabela temporária: cliente antigo bloqueado, cliente novo aceito e conta legada sem carteira aceita. Nenhum documento financeiro de usuário foi modificado pelo teste.

## Resultado final e liberação para testes

Commit de código validado: 28955f865273170b4d9ecd4888407804122efbb1.
Execução aprovada: https://github.com/Atlas-solucoes/atlas-financas-app/actions/runs/40409646298
Foram aprovados 19 testes de regressão e 14 da carteira (33 no total). O navegador
passou os formulários, duas sessões com REST simulado, 320/360/390 px, recarga,
fatura sem duplicação, planos, consulta real do BCB (com CORS), fallback e PWA offline.
Capturas de tela e relatório ficam no artefato homologacao-investimentos.

Migração aplicada pelo Supabase: 20261026220050_proteger_carteira_clientes_legados.
Teste temporário também sob papel authenticated aprovou cliente novo e bloqueou
cliente antigo sem pgSchema. Os avisos do advisor permaneceram iguais aos anteriores.
Nenhum documento financeiro real foi escrito nos testes de migração.

Depois da publicação, feche as abas/app antigos e reabra o endereço habitual. Cadastre
os saldos atuais uma vez; só confirme renda/recarga ainda não incluída nesses saldos.
Para desfazer a escolha de soma bancária, desative-a na Carteira; o saldo geral anterior
continua salvo. Não reverta para cliente que desconheça os campos da carteira: o gatilho
impede a perda dos cadastros. Corrija o código mantendo o sanitizador atualizado.
A sincronização automatizada usou API simulada; a conferência final dos saldos reais
entre os celulares continua sendo parte da homologação pelo usuário.
