# Registro de conclusão — Documentos e reembolsos

Entrega de 29/10/2026. Repositório Atlas-solucoes/atlas-financas-app, PR #4.
URL mantida: https://atlas-solucoes.github.io/atlas-financas-app/nuvem/.

## Entregue nesta etapa

Documentos privados vinculados a gasto, conta, cartão/fatura ou plano; foto,
rotação/recorte e PDF; leitura local com campos revisáveis; classificação pessoal
ou corporativa, empresa e responsável pelo pagamento; situações de reembolso;
filtros; seleção para compartilhamento nativo ou ZIP; crédito de reembolso revisado
e protegido contra duplicação; reconciliação do saldo anterior da fatura sem
repetir compras já registradas. Nenhum envio automático a empresa, WhatsApp ou e-mail.

O relatório corporativo no formato da empresa permanece na etapa seguinte,
conforme pedido do usuário. Não foi criado outro site, plugin ou serviço de IA pago.

## Evidências

Commit de código c185050c69d8d14eadd5cf72ab92b777684d3fd4:
https://github.com/Atlas-solucoes/atlas-financas-app/actions/runs/40864136653

46 testes: 19 investimentos, 14 carteira, 13 documentos, todos aprovados.
Navegador com 320/360/390 px: fluxo financeiro anterior, foto sintética, OCR real
em português, PDF sintético, recusa de arquivo falso/duplicado, pessoal/corporativo,
filtros, ZIP validado, compartilhamento simulado, revisão de despesa/crédito de
reembolso e segundo contexto. PWA offline e consulta BCB também passaram.
Os dados de Storage/REST dos testes de navegador são simulados: não usaram fotos,
senhas, tokens ou transações financeiras reais dos usuários.

O bucket real foi configurado privado, com limite de 10 MB e MIME restrito.
RLS testada no banco com dados sintéticos em subtransação revertida: proprietário
vê seu caso/documento, outro usuário não vê; transferência de proprietário,
inserção em nome de outro usuário, vínculo cruzado e duplicado foram bloqueados.
Teste de prefixo do Storage confirmou o predicado de proprietário. Isso não é
um teste de upload real com duas sessões de autenticação: continua uma verificação
de homologação a executar sem usar documentos financeiros reais de terceiros.

A etapa Verificar publicação Atlas compara hashes dos arquivos no endereço público
com o commit implantado, sem autenticação ou acesso ao banco. Resultado de publicação
fica no GitHub Actions e no artefato verificacao-publicacao.

## Uso no celular

Feche abas e o aplicativo antigos e reabra o endereço. Entre na conta e vá a
Documentos ou Anexos/reembolso no gasto. Tire uma foto ou escolha PDF. Confira
valor/data e use o formulário financeiro apenas quando quiser registrar/alterar.
Defina Corporativo, empresa, Pago por você e A solicitar quando aplicável.
Filtre, selecione e prepare arquivos; escolha WhatsApp/e-mail no menu do aparelho
ou baixe o ZIP. Marque Solicitado somente depois de confirmar o envio.

## Critérios para anunciar como produto vendável

Esta entrega conclui o recurso solicitado no ambiente de testes. Não equivale à
certificação de prontidão comercial. Antes de oferecer a clientes, registrar:

1. Homologação física em Android e iPhone/Safari: câmera, arquivo/PDF, compartilhamento,
   atualização da PWA e logout; e duas contas reais de teste provando isolamento no
   upload/download, sem documentos reais de clientes nos testes.
2. Política de privacidade/termos e canal de suporte para documentos financeiros;
   definir retenção, exclusão de conta/arquivos e acesso aos dados da empresa.
3. Procedimento testado de backup/restauração incluindo anexos (o JSON financeiro
   sozinho não contém os arquivos), monitoramento e limites de uso/custo do Storage.
4. Revisar avisos preexistentes do Supabase, inclusive proteção contra senhas vazadas,
   e registrar a decisão de segurança para a abertura pública.
5. Definir oferta, preço, cobrança e permissões de acesso se houver venda por assinatura.
   Não foram implementados cobrança, contrato ou integração comercial não solicitados.

Esses itens são uma lista finita de liberação comercial, não funcionalidades que
foram anunciadas como prontas. O relatório corporativo completo é melhoria posterior.

## Limites e recuperação

Até 10 MB por arquivo e 10 arquivos/20 MB por compartilhamento. Reconhecimento de
foto depende da nitidez. PDF usa texto de até 5 páginas e OCR da primeira página
escaneada; páginas não lidas exigem conferência manual. Não importa automaticamente
todas as compras/parcelas de qualquer fatura. Agendamento não comprova pagamento.
O compartilhamento no sistema operacional não comprova entrega ao destinatário.

A leitura é local; anexar à nuvem é uma ação explícita. Arquivos privados não entram
no cache da PWA. No rollback, preservar bucket/tabelas e o JSON financeiro; reverter
somente código para uma versão compatível. A proteção de clientes legados da Carteira
continua ativa e não deve ser removida para forçar uma gravação antiga.

Antes de acessar documentos privados, o cliente exige confirmação da política de cache
do service worker ativo. Uma versão antiga exige fechar abas/app e reabrir, impedindo
que um worker legado intercepte e guarde as novas respostas privadas.

Migração registrada pelo Supabase: 20261029110109_documentos_privados_e_reembolsos.

A fatura também permite digitar o total manualmente e escolher Conferir total/saldo
anterior, sem anexar ou reconhecer arquivo. Só a confirmação inclui a diferença
em relação às compras existentes; o fluxo de navegador cobre repetição sem duplicar.

A leitura possui limites de tempo para baixar o leitor, iniciá-lo e reconhecer texto;
fechar o formulário cancela a leitura e libera o uso dos documentos. Respostas JSON
e arquivos são novamente verificados após o corpo ser recebido, evitando aplicar
uma resposta da conta anterior se houver logout/troca de sessão durante a transferência.
O navegador inclui teste de resposta atrasada após logout e de início de OCR cancelado.
