# Documentos e reembolsos

Endereço de homologação: o mesmo /nuvem/ em uso. Não cria outro site, conta de IA
ou conexão com WhatsApp Business. Entrada: botão Documentos, atalho na página inicial,
Anexos/reembolso no gasto, anexos na conta, orçamento no plano e documento na fatura.

## O que esta entrega faz

- Captura pela câmera ou seleção de PDF/JPG/PNG/WEBP. Foto permite girar e recortar
  margens; a imagem é redimensionada, convertida em JPEG e perde os metadados EXIF.
- Bucket privado da conta, limite de 10 MB por arquivo; assinatura do conteúdo,
  MIME, nome e tamanho verificados, SHA-256 para evitar repetir arquivo no mesmo
  registro. Arquivo já existente em outro registro exige confirmação explícita.
- Registro pessoal/corporativo, empresa, quem pagou, valor, data, observação e
  situação de reembolso. Só corporativo pago pelo próprio usuário com empresa
  informada permite A solicitar/Solicitado/Recebido.
- Filtros por empresa, natureza, datas e situação; até 50 registros por página.
  Total a receber é dos registros da página, não de todos os arquivos individualmente.
- Seleção limpa ao mudar página/filtros. Preparar envio baixa somente anexos dos
  registros selecionados. Até 10 arquivos/20 MB. O compartilhamento usa o menu do
  dispositivo; WhatsApp/e-mail dependem dos apps e suporte do navegador. Há ZIP e
  mensagem para envio manual. Compartilhar não confirma entrega nem marca solicitação.
- Registrar crédito de reembolso abre o formulário de entrada para confirmação
  de valor, data e banco. Um identificador estável por documento impede duplicar
  o crédito. Marcar somente a situação como recebido não muda saldo automaticamente.

## Leitura e atualização com revisão

Tesseract.js 7.0.0/core 7.0.0, idioma português, e PDF.js 5.4.149, carregados por
versões fixas sob demanda. Não há chave paga de IA nem envio do arquivo a um LLM.
As bibliotecas/dados de idioma precisam de internet na primeira leitura. A análise
ocorre no dispositivo; anexar ao Atlas é uma ação separada, explícita.

Fotos: OCR local. PDFs: texto das primeiras cinco páginas; primeira página escaneada
pode receber OCR. Demais páginas escaneadas precisam de conferência manual. O
arquivo completo é preservado como anexo. PDFs grandes/ilegíveis/protegidos podem
ser anexados e preenchidos manualmente; não há interpretação integral de qualquer PDF.

Sugere descrição, data, vencimento, categoria e valor. Mais de um total diferente
não vira um palpite: o usuário escolhe. Agendamento é identificado e exige confirmar
execução antes de propor um registro financeiro. A leitura nunca baixa conta, paga
fatura, confirma crédito ou cria lançamento sozinha.

Conferir lançamento abre os formulários já existentes. Confirmar Salvar é o ato que
altera os dados financeiros. Novas despesas e reembolsos guardam origem/IDs estáveis;
repetir o mesmo documento não deve criar outra transação.

Fatura: Anexar fatura atual/futura está disponível mesmo sem compra anterior. Ao
conferir o total e vencimento, o usuário vê compras já cadastradas e a diferença
que será saldo anterior. Só essa diferença é incluída, preservando compras detalhadas.
Não importa automaticamente item a item toda fatura ou parcelas de várias compras.
Se o total for menor que as compras existentes, exige revisar os lançamentos.

## Dados e segurança

SQL: supabase/documentos_reembolsos.sql. Duas tabelas novas, RLS por auth.uid(),
revisão otimista para metadados, vínculo de documento exige mesmo proprietário,
path uid/case_id/document_id.ext. Bucket privado; sem UPDATE/upsert de arquivos.
Reembolso não é incluído como salário recorrente; é uma entrada avulsa confirmada.
Não reescreve documentos app_state existentes. Anexos e metadados ficam separados
para que um cliente antigo não apague os novos registros ao sincronizar JSON legado.

A sincronização dos anexos exige login e internet. O conteúdo dos arquivos privados
não vai ao cache da PWA. Download/compartilhamento deixa uma cópia no aparelho ou no
aplicativo escolhido pelo usuário. Logout encerra OCR e descarta arquivos em memória.
Vínculos a planos são privados do proprietário; não concedem acesso automático aos
participantes de um projeto compartilhado. Não há envio automático por WhatsApp/e-mail.

JSON de backup anterior preserva dados financeiros; não contém o conteúdo dos anexos.
Documentos permanecem na conta Supabase e podem ser baixados/compartilhados separadamente.
O relatório corporativo com formulário/modelo da empresa continua para próxima etapa.

## Verificação

Unitários: testes financeiros existentes + tests/documentos.test.cjs.
Navegador: testes existentes + tests/browser_documentos.py com Storage/REST em memória,
foto sintética, OCR real e PDF de teste, duplicação, classificação, filtros, ZIP,
compartilhamento simulado, revisão de lançamento e segunda sessão.
Teste de RLS deve usar dados sintéticos em subtransação revertida; não toca gastos
reais nem envia mensagens. Resultado de rede OCR/CDI e limites da execução devem ser
registrados no relatório do Actions antes da publicação no endereço de testes.
