# Backup privado do Raspberry

Os navegadores conectados ao endereço privado sincronizam snapshots completos (incluindo fotos) a cada 5 segundos enquanto a página está visível. A consulta verifica a revisão; só transfere o JSON completo quando há alterações. Em Mais opções → Sincronização e backup, “Sincronizar agora” antecipa a sincronização e mostra a data do backup no Drive. Isso não antecipa o prazo de 15 dias.

O código só ativa esse recurso na origem privada configurada em `private-sync.js`. GitHub Pages não envia dados. `backup-server.py serve` atende o site e a API apenas em 127.0.0.1:8036; Tailscale Serve disponibiliza HTTPS privado em 8443. A API exige a origem privada e a revisão de origem de cada gravação. Uma gravação baseada em uma revisão antiga recebe 409, preservando os dados atuais. Páginas antigas de backup unidirecional precisam ser recarregadas e não podem mais enviar snapshots sem controle de versão.

Um navegador novo recebe os dados do Raspberry antes de iniciar a tela. Na migração, o antigo navegador principal conserva seu trabalho local ainda não enviado. Outros navegadores preservam uma cópia de seus dados anteriores no IndexedDB antes de adotar os dados centrais. As cópias podem ser baixadas pelo painel de sincronização.

O cliente mantém uma base por navegador e faz união de alterações independentes. Edições simultâneas no mesmo campo, ou exclusão versus alteração, interrompem o envio e mostram opções explícitas de qual versão usar. Ambas as versões são preservadas antes de resolver o conflito. Dados recebidos são aplicados com recarga da tela apenas quando não há campo em edição ou diálogo aberto. A página de avaliações também participa, exceto seus iframes internos que compartilham o armazenamento da página principal.

Snapshots e estado ficam fora do repositório, em `/home/caio/.local/share/treino36-backup`, com permissões restritas. Credenciais permanecem na configuração já existente do rclone, nunca no código. A conexão utilizada é `gdrive:`.

`backup-server.py upload` envia `latest.json` ao mesmo `treino36-backup.json` na pasta configurada, verifica tamanho e MD5 e guarda o ID do arquivo. Só faz outro envio após 15 dias desde o último sucesso. Falhas preservam a cópia local e o prazo anterior. O timer de usuário `treino36-backup.timer` consulta o prazo a cada hora, inclusive após reiniciar; logo o envio pode ocorrer até aproximadamente uma hora após completar 15 dias. A instalação usa linger para executar sem login.

Com o navegador fechado, o backup utiliza a última cópia recebida. Alterações ainda não enviadas não podem ser incluídas. O servidor deve permanecer ligado e conectado à internet para enviar ao Drive. O serviço mostra falhas no painel de backup e tenta novamente na hora seguinte.

Testes: `python3 tests/test_backup_server.py`, `node tests/test_sync_merge.js` e `python tests/test_private_sync_browser.py` (Playwright com Chromium instalado). O teste de navegador utiliza servidor e dados temporários, sem tocar nos dados reais.
