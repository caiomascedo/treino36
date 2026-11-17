# Backup privado do Raspberry

O navegador principal envia um snapshot completo (incluindo fotos) a cada 30 segundos enquanto a página está visível e os dados mudaram. Em Mais opções, o botão “Enviar dados para backup” envia imediatamente ao Raspberry e mostra a data do último envio ao Drive. O envio ao Raspberry não força a antecipação do prazo de 15 dias.

O código só ativa esse recurso na origem privada configurada em `backup-sync.js`. GitHub Pages não envia dados. `backup-server.py serve` atende o site e a API apenas em 127.0.0.1:8036; Tailscale Serve disponibiliza HTTPS privado em 8443. A API aceita JSON com a origem privada e identifica o navegador principal. Outro navegador não pode substituir silenciosamente sua cópia. Uma primeira conexão precisa conter todos os alunos do backup inicial.

Snapshots e estado ficam fora do repositório, em `/home/caio/.local/share/treino36-backup`, com permissões restritas. Credenciais permanecem na configuração já existente do rclone, nunca no código. A conexão utilizada é `gdrive:`.

`backup-server.py upload` envia `latest.json` ao mesmo `treino36-backup.json` na pasta configurada, verifica tamanho e MD5 e guarda o ID do arquivo. Só faz outro envio após 15 dias desde o último sucesso. Falhas preservam a cópia local e o prazo anterior. O timer de usuário `treino36-backup.timer` consulta o prazo a cada hora, inclusive após reiniciar; logo o envio pode ocorrer até aproximadamente uma hora após completar 15 dias. A instalação usa linger para executar sem login.

Com o navegador fechado, o backup utiliza a última cópia recebida. Alterações ainda não enviadas não podem ser incluídas. O servidor deve permanecer ligado e conectado à internet para enviar ao Drive. O serviço mostra falhas no painel de backup e tenta novamente na hora seguinte.

Testes: `python3 tests/test_backup_server.py`.
