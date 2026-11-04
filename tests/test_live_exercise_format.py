from pathlib import Path
import os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page();page.set_content('<div class="section"><ol contenteditable="true"><li></li></ol></div>');page.add_script_tag(content=(Path(__file__).resolve().parents[1]/'live-exercise-format.js').read_text());row=page.locator('li')
 for ending in ['3x','4x','1x','—']:
  row.evaluate("e=>e.replaceChildren()");row.click();page.keyboard.insert_text('Agachamento taça '+ending);assert row.locator('.bold').inner_text()=='Agachamento taça';assert row.text_content().replace('\u00a0',' ')=='Agachamento taça — '+('' if ending=='—' else ending);page.keyboard.insert_text('12');assert row.text_content().replace('\u00a0',' ').endswith(('— ' if ending=='—' else ending)+'12');assert row.locator('.bold').inner_text()=='Agachamento taça'
 row.evaluate("e=>{const a=document.createElement('a');a.className='exercise-video';a.href='https://youtu.be/Keep';a.textContent='(Vídeo)';e.append(a)}");page.keyboard.insert_text(' + 15');assert row.locator('a').get_attribute('href')=='https://youtu.be/Keep';assert '12 + 15' in row.text_content().replace('\u00a0',' ');b.close();print('PASS: 1x/3x/4x/dash add bold/separator; continued typing and media preserved')
