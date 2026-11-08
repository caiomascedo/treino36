# Cores e posição no painel de GIFs

Cada vídeo começa com **Cores originais**, inclusive vídeos pessoais e filmagens
de pessoas. Em **Vídeo / editar** (ou nas opções do exercício simples), o seletor
**Cor deste vídeo** oferece também **Adaptar ao tema** e **Inverter cores**.
A escolha vale para aquele arquivo, fica salva neste navegador e é aplicada
tanto à prévia quanto aos pixels do GIF gerado. O tema da ficha e as cores da
prescrição dos conjugados continuam independentes da imagem do vídeo.

O painel lembra neste navegador o aluno, o treino selecionado, o tema,
o exercício visível e os menus de edição abertos. Ao reabrir, relê a ficha para
mostrar as mudanças feitas no treino e restaura a posição pelo exercício. Capas
atuais e treinos anteriores possuem contextos separados. A última escolha
manual de demonstração também é respeitada quando o tema muda.
O treino escolhido é guardado imediatamente, mesmo se o painel for fechado
antes de terminar de desenhar os exercícios. A abertura foca o título, evitando
que o Safari abra sozinho o seletor de CM/modelo anatômico.

## Biblioteca e arquivos pessoais

Na **Lista de apagados**, cada item recuperável possui **Restaurar** e
**Apagar definitivamente**, com confirmação antes da exclusão. As exclusões
definitivas continuam registradas na lista para revisão; arquivos pessoais são
removidos também do IndexedDB. Os arquivos originais do catálogo/Drive não são
apagados pelo navegador.

O formulário mantém os mesmos botões **Salvar vídeo** e **Cancelar**, agora
maiores. Se o nome corresponder a um vídeo existente, informa que haverá
substituição. Nomes com mais de uma versão exigem selecionar a versão correta.
Ao trocar o arquivo, mantém ID, vínculos, favorito e rótulos personalizados;
arquivos inválidos e cancelamentos preservam o vídeo anterior. No seletor de
um exercício, Salvar também aplica o vídeo imediatamente, sem outra escolha.
Substituições do catálogo são cópias locais: links externos continuam abrindo o
arquivo original, conforme informado no formulário.

A prévia usa controles compactos de reproduzir/pausar, reiniciar, som, posição
e ampliar, com `playsinline` e sem o painel nativo de controles do iOS.

**Copiar Treino**, no início da ficha, copia somente as seções com exercícios.
D, E ou F vazios não geram títulos em branco. Uma seção volta a participar da
cópia assim que recebe um exercício. Os nomes, prescrições, links e rodapé
mantêm o formato existente.

Verificações de navegador com dados isolados e arquivos locais, incluindo GIFs
reais de 100 quadros e 5 segundos:

```sh
python tests/test_gif_view_and_copy.py
python tests/test_gif_theme_colors.py
python tests/test_personal_theme_layout.py
python tests/test_video_preview_context.py
python tests/test_video_replace_and_preview.py
```

Para WebKit, os testes aceitam `GIF_TEST_BROWSER=webkit` e
`PLAYWRIGHT_WEBKIT_EXECUTABLE` apontando para o executável do Playwright.
