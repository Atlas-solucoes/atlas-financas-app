# Empresas e botões no celular — 29/10/2026

Na tela inicial, abra **Minhas empresas / dados para nota fiscal**. O mesmo cadastro
fica em **Documentos → Minhas empresas** e no formulário de natureza Corporativo.
Cadastre razão social, CNPJ e inscrição estadual (opcional; aceita ISENTO). CNPJ
numérico e alfanumérico são aceitos com conferência dos dígitos. A conferência não
consulta situação cadastral na Receita Federal nem valida IE em cada estado.

Ao escolher Corporativo, uma única empresa ativa é preenchida automaticamente.
Com várias, selecione na lista. Dados anteriores de empresa continuam disponíveis;
nenhum documento é reassociado em lote. Empresas arquivadas deixam de ser sugeridas
para novos documentos e continuam nos documentos já vinculados. Editar razão social
não reescreve o nome histórico dos comprovantes. Editar e salvar o próprio comprovante
atualiza sua classificação a partir da escolha feita no formulário.

Em Dados para nota fiscal, veja e copie todos os dados ou somente o CNPJ. Se o
navegador impedir a cópia, o texto pode ser selecionado manualmente. Não há envio
automático. Cadastro e consulta exigem conexão e login; dados fiscais não entram
no cache offline. O cadastro é privado por conta, não é um diretório público.

Botões de documentos/empresas têm altura mínima de 48 px, espaço de 12 px e,
em telas até 420 px, ocupam uma linha por botão. No cadastro durante um documento,
a foto selecionada e os demais campos permanecem no formulário.

## Verificação e proteção dos dados

48 testes locais: 19 investimentos, 14 carteira e 15 documentos/empresas.
CI de navegador cobre cadastro, CNPJ inválido, seleção única/múltipla, consulta em
segundo contexto, cópia simulada, foto preservada e botões em 320/360/390 px,
além das regressões financeiras, OCR/PDF e PWA existentes. Evidência final na PR
associada a esta entrega e no artefato homologacao-investimentos do GitHub Actions.
Navegador usa REST/Storage simulados; validação física segue na homologação.

Migração supabase/empresas.sql adiciona atlas_companies e vínculo company_id opcional;
não modifica app_state nem preenche ou apaga registros anteriores. RLS real testada
em transação revertida com usuários sintéticos: proprietário vê e edita; outro
usuário não lê; transferência, inserção alheia, duplicado e vínculo cruzado são
bloqueados. Atualização concorrente usa revision para recusar sobrescrita silenciosa.
Avisos preexistentes do Supabase continuam no registro de liberação anterior.

Publicação permanece em /nuvem/. Feche todas as abas/app antigos e reabra para
atualizar a PWA. Confira os arquivos públicos com Verificar publicação Atlas.
Em rollback, mantenha a tabela e a coluna novas, preservando empresas e vínculos;
reverta apenas o código. As versões anteriores ignoram o vínculo opcional.
