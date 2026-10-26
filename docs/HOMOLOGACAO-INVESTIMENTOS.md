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
Resultado: 10 testes aprovados, zero falhas; saída em TESTES-INVESTIMENTOS.txt.
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
