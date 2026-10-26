# Investimentos — homologação pendente

Data: 2026-10-26. Branch: feature/investimentos-cdi-comparador.
Base revisada: 46caaa092ad4850703855f730bac9954c8513aea.

## Status de liberação

NÃO promover para main. As correções abaixo são candidatas a homologação;
a validação externa e em dispositivos ainda não foi concluída. Nenhuma migração
ou escrita no banco de produção foi executada.

## Correções

- Cadastro integrado agora gera UUID, exigido pelo sanitizador do documento.
- Falha de armazenamento retorna erro ao módulo e reverte a alteração em memória.
- Documento que contém apenas investimentos não é tratado como vazio na primeira sincronização.
- Edições feitas enquanto um POST/PATCH está em andamento mantêm dirty e são reagendadas.
- Service worker armazena somente arquivos públicos da pasta, ignora API/autorização,
  remove apenas versões do próprio cache e espera a próxima ativação normal.
- Consulta opt-in ao BCB/SGS 4389, com timeout, validação básica e data de referência.
  Em falha mantém a taxa manual, explicitamente identificada. A integração ainda
  precisa ser confirmada contra a API real, incluindo CORS e unidade da série.
- Prazo exige meses inteiros. IR regressivo por aporte; IOF sobre ganho antes do IR.

O simulador usa taxa anual efetiva, capitalização diária de 252 dias úteis/ano,
21 dias úteis/mês, aportes ao fim de cada mês e idade aproximada de cada aporte
(meses × 365/12). Não calcula rentabilidade efetiva de extratos ou resgates por
calendário. Não considera taxas do emissor, feriados ou mudanças de lei. LCI/LCA
representam a hipótese de isenção para PF: confirmar legislação vigente antes da
liberação. Nenhuma afirmação de conformidade fiscal foi validada externamente.

## Evidências executadas

Comando: `node tests/investimentos.test.cjs` (Node v24.19.0).
Resultado: 19 testes aprovados, zero falhas; saída em TESTES-INVESTIMENTOS.txt.
Inclui compilação dos scripts HTML, cálculo anual, isenção, aporte no último mês,
taxa zero, limites de IR/IOF, documento com investimentos, edição durante PATCH,
rollback da bridge e isolamento de caches do service worker.
São testes locais com simulações de rede/armazenamento; não equivalem a E2E.

Consulta somente leitura das políticas Supabase de public.app_state confirmou:
SELECT/DELETE limitam auth.uid()=user_id; INSERT usa WITH CHECK; UPDATE usa
USING e WITH CHECK para o mesmo proprietário. Isso não substitui teste com JWTs.
Advisors reportaram projeto_convites com RLS sem políticas e sete funções públicas
SECURITY DEFINER executáveis por authenticated. Revisar os corpos/autorizações
antes de alterar permissões, para preservar projetos compartilhados.
Referências:
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy
- https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable

O clone e a consulta BCB falharam no ambiente: conexão ao proxy:8080 indisponível.
Os arquivos foram lidos pela integração GitHub. O changelog Supabase e as fontes
fiscais não puderam ser consultados pelo executor. Não foi possível executar
navegador/celular nem autenticar duas contas de teste pela aplicação.

## Roteiro obrigatório antes de liberar

1. Criar preview HTTPS isolado desta branch, sem alterar main/produção. Fazer backup
   exportado do app e backup do banco antes de qualquer ação de liberação.
2. Usar conta de homologação com lançamentos, planos e investimentos: abrir em dois
   dispositivos, editar alternadamente, sincronizar, recarregar e conferir os dados.
3. Testar alterações simultâneas, edição durante rede lenta, modo offline, reconexão,
   expiração de sessão, logout/login e troca de conta durante requisição pendente.
   Confirmar que nenhum dado de uma conta chega à outra. Há risco preexistente de
   estado global durante troca de sessão; esse fluxo ainda precisa de revisão/E2E.
4. Confirmar bloqueio por RLS com JWT de outra conta e acesso anônimo. Verificar
   relrowsecurity, privilégios e funções privilegiadas, sem inserir dados reais.
5. Consultar CDI no Android/iOS: confirmar série/unidade e data com o BCB; testar
   timeout, CORS, resposta inválida, indisponibilidade e taxa manual posterior.
6. Validar legislação atual de IR, IOF e isenção de LCI/LCA. Comparar exemplos com
   calculadora independente, especialmente aportes e limites 180/360/720 dias.
7. Android Chrome e iPhone Safari: instalar PWA, reabrir standalone, abrir Investir,
   navegar, usar teclado, testar 320/360/390 px, zoom, leitura por tecnologia assistiva,
   voltar do background e iniciar offline depois de atualizar o cache.
8. Testar atualização de PWA com aba antiga aberta. Não limpar armazenamento local
   como procedimento de atualização. Confirmar manutenção de extrato, contas,
   planos, assistente, projetos compartilhados, exportação e restauração de backup.
9. Registrar dispositivo, navegador, horário, versão e evidência de cada cenário.
   Só aprovar o merge após resolver falhas críticas e todos os riscos de perda de dados.

Rollback: reverter o commit de código na branch/preview e incrementar a versão do
cache em uma entrega corretiva. Não restaurar documento antigo sobre dados recentes
sem comparar/exportar primeiro. Este conjunto de mudanças não altera schema.


## Continuação após informar o endereço de testes

Endereço em uso pela família: https://atlas-solucoes.github.io/atlas-financas-app/nuvem/.
Não é um ambiente novo: o trabalho preserva essa instalação. A última execução
Pages observada foi 40260005179, concluída com sucesso a partir da main,
commit 29943ee734bc9ad9da4d4cefb2e15f5c5a3fafa9. Portanto, a branch de investimentos
não está publicada nesse endereço. Não alterar a fonte de publicação sem validar
os bloqueios e preservar o armazenamento usado nos testes existentes.

Acesso público alternativo confirmou resposta do BCB em 26/10/2026:
SGS 4389 retornou [{"data":"23/10/2026","valor":"13.65"}]. Isso valida o endpoint e
a interpretação do payload; não comprova CORS no celular. Não há taxa fixa de
13,65% no código: a aplicação consulta a última observação disponível.
Fonte: https://api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados/ultimos/1?formato=json

Referências oficiais consultadas para a revisão tributária:
- https://www.tesourodireto.com.br/sobre-o-tesouro/regras-e-regulamento
- https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/preenchimento/manual-mir/rendimentos/rendimentos-do-capital

O modelo conserva a tabela regressiva e a hipótese PF indicada na interface.
Continua sendo uma projeção mensal aproximada, e não cálculo fiscal de resgate.
A consulta adicional de pg_class confirmou RLS habilitada em app_state; a chave
primária user_id e as restrições de objeto JSON/tamanho/revisão positiva estão presentes.

Correções adicionais: requisições REST e refresh rejeitam respostas de sessão antiga;
logout cancela agendamento; download da nuvem exige backup local e persistência
bem-sucedidos antes de confirmar revisão; saldo zero não é considerado vazio;
bridge sanitiza somente investimentos, preservando os demais registros sem mutação.

A suíte local agora cobre 19 cenários, incluindo dois dispositivos simulados,
conflito simultâneo, troca de conta/refresh, falha de quota e sanitizador real.
Não utiliza contas nem tokens reais. A execução local de Chromium falhou por
restrição do sandbox (setsockopt: Operation not permitted), não por erro do app.
Foi preparado tests/browser_investimentos.py e um workflow somente de testes,
sem deploy ou acesso a segredos: abre dois contextos Chromium móveis, intercepta
todas as chamadas Supabase com servidor em memória, verifica reload, preservação
de lançamentos, 320/360/390 px, consulta BCB real e falha, e PWA offline.
Resultados desse workflow devem ser conferidos no GitHub Actions; não considerar
as verificações de navegador aprovadas antes da conclusão da execução.

O teste em celulares físicos e a sincronização autenticada real com duas sessões
continuam pendentes. As contas existentes não foram acessadas nem modificadas.

## Resultado de navegador confirmado

Execução de push 40381209049 concluiu com sucesso no commit 7b916fbbc5b0e838c09e2d327f2b524aac69ca31:
https://github.com/Atlas-solucoes/atlas-financas-app/actions/runs/40381209049

Evidências extraídas dos logs em RESULTADO-BROWSER-INVESTIMENTOS.json:
- fluxo UI/iframe/bridge/REST simulado/segundo navegador/recarga preservou lançamento;
- ausência de rolagem horizontal em 320, 360 e 390 px;
- consulta real ao BCB pelo Chromium passou, incluindo CORS e data de referência;
- resposta de erro da API preservou a taxa existente;
- app e tela de investimentos abriram offline com service worker;
- nenhuma exceção JavaScript não tratada nos cenários executados.

O artefato homologacao-investimentos contém relatório e captura da tela.
A instalação em celular físico, Safari/iOS e sincronização autenticada real seguem
pendentes: a simulação não comprova esses cenários. Foi adicionado ao workflow um
smoke test separado do endereço público informado, em perfil novo sem login e com
Supabase bloqueado, para verificar a página em uso sem acessar dados existentes.
Não confundir esse smoke test da main publicada com os testes da feature local no runner.

A revisão somente leitura das sete funções privilegiadas confirmou search_path
vazio e predicados de autenticação/propriedade ou destinatário nos corpos analisados.
Os avisos do advisor são motivo de revisão, não evidência isolada de vazamento.
Nenhuma política ou função foi alterada nesta entrega.
