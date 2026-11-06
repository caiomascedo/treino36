# Cores e posição no painel de GIFs

Cada vídeo começa com **Cores originais**, inclusive vídeos pessoais e filmagens
de pessoas. Em **Vídeo / editar** (ou nas opções do exercício simples), o seletor
**Cor deste vídeo** oferece também **Adaptar ao tema** e **Inverter cores**.
A escolha vale para aquele arquivo, fica salva neste navegador e é aplicada
tanto à prévia quanto aos pixels do GIF gerado. O tema da ficha e as cores da
prescrição dos conjugados continuam independentes da imagem do vídeo.

O painel lembra, durante a sessão da aba, o aluno, o treino selecionado, o tema,
o exercício visível e os menus de edição abertos. Ao reabrir, relê a ficha para
mostrar as mudanças feitas no treino e restaura a posição pelo exercício. Capas
atuais e treinos anteriores possuem contextos separados. A última escolha
manual de demonstração também é respeitada quando o tema muda.

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
```

Para WebKit, os testes aceitam `GIF_TEST_BROWSER=webkit` e
`PLAYWRIGHT_WEBKIT_EXECUTABLE` apontando para o executável do Playwright.
