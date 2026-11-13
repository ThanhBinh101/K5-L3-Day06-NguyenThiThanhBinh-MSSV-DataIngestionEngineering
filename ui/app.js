'use strict';
const $ = (selector) => document.querySelector(selector);
const cells = Array.from({length:1},()=>({strokes:[],candidates:[],selected:null,revision:0,busy:false,error:'',uncertain:false}));
let active=0, ready=false, drawing=null, querySequence=0;
const timers=Array(1).fill(null);
const canvases=[];
const lessonValue=()=>$('#lesson').value ? Number($('#lesson').value) : null;
for(let i=1;i<=16;i++){
 const option=document.createElement('option');option.value=i;option.textContent=`Bài ${String(i).padStart(2,'0')}`;$('#lesson').append(option);
}
function element(tag,className,text){const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=text;return el;}
async function api(path,data){
 const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 const result=await response.json();if(!response.ok)throw new Error(result.error||'Chưa thể xử lý yêu cầu.');return result;
}
function drawCell(index){
 const canvas=canvases[index],ctx=canvas.getContext('2d');
 ctx.clearRect(0,0,256,256);ctx.strokeStyle='#254b38';ctx.fillStyle='#254b38';ctx.lineWidth=4;ctx.lineCap='round';ctx.lineJoin='round';
 for(const stroke of cells[index].strokes){
  if(stroke.length===1){ctx.beginPath();ctx.arc(stroke[0][0],stroke[0][1],2,0,Math.PI*2);ctx.fill();continue;}
  ctx.beginPath();ctx.moveTo(...stroke[0]);for(const point of stroke.slice(1))ctx.lineTo(...point);ctx.stroke();
 }
}
function pointAt(event,canvas){const rect=canvas.getBoundingClientRect();return [Math.max(0,Math.min(256,(event.clientX-rect.left)*256/rect.width)),Math.max(0,Math.min(256,(event.clientY-rect.top)*256/rect.height))];}
function invalidate(index){const cell=cells[index];cell.revision++;cell.candidates=[];cell.selected=null;cell.error='';cell.busy=false;clearTimeout(timers[index]);}
function setActive(index){active=index;renderState();}
for(let index=0;index<1;index++){
 const wrap=element('div','write-cell');
 wrap.append(element('span','cell-index',String(index+1).padStart(2,'0')));
 const canvas=element('canvas');canvas.width=256;canvas.height=256;canvas.tabIndex=0;
 canvas.setAttribute('aria-label',`Ô chữ mễ ${index+1}, viết một chữ Kanji bằng chuột hoặc cảm ứng`);
 canvases.push(canvas);wrap.append(canvas,element('span','cell-chosen',''));$('#writing-grid').append(wrap);
 canvas.addEventListener('focus',()=>setActive(index));
 canvas.addEventListener('pointerdown',(event)=>{
  if(event.button!==0||drawing)return;event.preventDefault();canvas.focus();setActive(index);
  if(cells[index].strokes.length>=64){cells[index].error='Tối đa 64 nét mỗi ô. Xóa bớt nét để viết tiếp.';renderState();return;}
  invalidate(index);drawing={index,pointer:event.pointerId};canvas.setPointerCapture(event.pointerId);
  cells[index].strokes.push([pointAt(event,canvas)]);drawCell(index);renderState();
 });
 canvas.addEventListener('pointermove',(event)=>{
  if(!drawing||drawing.index!==index||drawing.pointer!==event.pointerId)return;
  const stroke=cells[index].strokes.at(-1);
  for(const sample of (event.getCoalescedEvents?.()||[event])){
   const p=pointAt(sample,canvas),last=stroke.at(-1);
   if(Math.hypot(p[0]-last[0],p[1]-last[1])>.6&&stroke.length<1024)stroke.push(p);
  }
  drawCell(index);
 });
 const finish=(event)=>{
  if(!drawing||drawing.index!==index||drawing.pointer!==event.pointerId)return;
  drawing=null;if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
  timers[index]=setTimeout(()=>recognizeCell(index),500);renderState();
 };
 canvas.addEventListener('pointerup',finish);canvas.addEventListener('pointercancel',finish);canvas.addEventListener('lostpointercapture',finish);
 const phraseButton=element('button');phraseButton.type='button';phraseButton.setAttribute('aria-label',`Chọn ô viết ${index+1}`);
 phraseButton.append(element('small','',String(index+1).padStart(2,'0')),element('span','','·'));
 phraseButton.addEventListener('click',()=>{setActive(index);canvases[index].focus();});$('#phrase').append(phraseButton);
}
function renderState(){
 document.querySelectorAll('.write-cell').forEach((wrap,i)=>{
  wrap.classList.toggle('active',i===active);wrap.querySelector('.cell-chosen').textContent=cells[i].selected||'';
 });
 [...$('#phrase').children].forEach((button,i)=>{
  button.classList.toggle('filled',Boolean(cells[i].selected));button.classList.toggle('active',i===active);
  button.querySelector('span').textContent=cells[i].selected||(cells[i].strokes.length?'?':'·');
 });
 const written=cells.filter(c=>c.strokes.length),selected=written.filter(c=>c.selected);
 $('#search-handwriting').disabled=!ready||!written.length||selected.length!==written.length;
 $('#text-search').disabled=!ready;
 $('#clear-all').disabled=!written.length;
 $('#undo').disabled=!cells[active].strokes.length;$('#clear-cell').disabled=!cells[active].strokes.length;
 $('#recognize-all').disabled=!written.length||cells.some(c=>c.busy);
 $('#stroke-info').textContent=`Ô ${String(active+1).padStart(2,'0')} · ${cells[active].strokes.length} nét`;
 $('#active-label').textContent=`· Ô ${String(active+1).padStart(2,'0')}`;
 $('#selection-note').textContent=!written.length?'Viết một chữ ở ô bên trái để bắt đầu.':selected.length<written.length?'Chọn một gợi ý cho các ô có dấu “?” trước khi tra cứu.':`Đã ghép ${selected.length} chữ gợi ý. Kiểm tra và chọn lại nếu cần.`;
 const cell=cells[active];
 $('#recognition-status').textContent=cell.busy?'Đang so nét…':cell.error|| (cell.candidates.length?(cell.uncertain?'Chưa rõ nét · bạn chọn lại nhé':'Chọn chữ phù hợp với ý bạn'):'Gợi ý hiện sau khi bạn viết');
 const candidates=$('#candidates');candidates.replaceChildren();
 if(!cell.candidates.length){
  const empty=element('div','suggestion-empty');empty.append(element('span','','✧'));
  empty.append(element('p','',cell.busy?'Đang tìm các chữ có hình dạng gần nhất…':cell.error?'Bạn có thể viết thêm nét hoặc hoàn tác để thử lại.':'Không cần viết thật hoàn hảo.\nMình sẽ tìm những chữ có nét gần giống.'));
  candidates.append(empty);return;
 }
 cell.candidates.forEach((candidate)=>{
  const button=element('button','candidate');button.type='button';button.classList.toggle('selected',cell.selected===candidate.kanji);
  button.setAttribute('aria-label',`Chọn chữ ${candidate.kanji}, ${candidate.han_viet}`);button.setAttribute('aria-pressed',String(cell.selected===candidate.kanji));
  button.title=`${candidate.han_viet} · Bài ${candidate.lesson} · ${candidate.reference_strokes} nét mẫu`;
  button.append(element('strong','',candidate.kanji),element('small','',candidate.han_viet));
  button.addEventListener('click',()=>{cell.selected=candidate.kanji;renderState();});candidates.append(button);
 });
}
async function recognizeCell(index){
 const cell=cells[index];if(!cell.strokes.length)return;
 clearTimeout(timers[index]);const revision=cell.revision;
 cell.busy=true;cell.error='';renderState();
 try{
  const result=await api('/api/recognize',{cells:[{index,strokes:cell.strokes}]});
  if(cell.revision!==revision)return;
  const r=result.cells[0];cell.candidates=r.candidates;cell.uncertain=r.uncertain;
  cell.selected=r.uncertain?null:(r.candidates[0]?.kanji||null);
 }catch(error){if(cell.revision===revision)cell.error=error.message;}
 finally{if(cell.revision===revision)cell.busy=false;renderState();}
}
$('#undo').addEventListener('click',()=>{invalidate(active);cells[active].strokes.pop();drawCell(active);renderState();if(cells[active].strokes.length)recognizeCell(active);});
$('#clear-cell').addEventListener('click',()=>{invalidate(active);cells[active].strokes=[];drawCell(active);renderState();});
$('#clear-all').addEventListener('click',()=>{if(drawing)return;for(let i=0;i<1;i++){invalidate(i);cells[i].strokes=[];drawCell(i);}setActive(0);});
$('#recognize-all').addEventListener('click',()=>Promise.all(cells.map((cell,i)=>cell.strokes.length?recognizeCell(i):Promise.resolve())));
$('#search-handwriting').addEventListener('click',()=>{
 const query=cells.map(c=>c.selected||'').join('');$('#query').value=query;doSearch(query);
});
$('#search-form').addEventListener('submit',(event)=>{event.preventDefault();doSearch($('#query').value);});
for(const button of document.querySelectorAll('[data-query]'))button.addEventListener('click',()=>{$('#query').value=button.dataset.query;doSearch(button.dataset.query);});
function resultCard(result){
 const e=result.entry;const card=$('#result-template').content.firstElementChild.cloneNode(true);
 card.querySelector('.entry-kanji').textContent=e.kanji;card.querySelector('h3').textContent=e.han_viet;
 card.querySelector('.entry-kind').textContent=({exact:'KHỚP CHỮ / TỪ',han_viet:'ĐỒNG ÂM HÁN VIỆT',mnemonic:'THEO CÁCH GỢI NHỚ',semantic:'GỢI Ý GẦN NGHĨA'})[result.match];
 card.querySelector('.entry-badges').textContent=`Bài ${String(e.lesson).padStart(2,'0')} · Trang ${e.page}${result.score!==null?` · cosine ${result.score.toFixed(3)}`:''}`;
 card.querySelector('.source-link').href=`/source.pdf#page=${e.page}`;
 card.querySelector('.source-link').setAttribute('aria-label',`Mở PDF nguồn ở trang ${e.page}`);
 card.querySelector('.on').textContent=e.onyomi==='-'?'—':e.onyomi;card.querySelector('.kun').textContent=e.kunyomi==='-'?'—':e.kunyomi;
 card.querySelector('.mnemonic').textContent=`Cách nhớ · ${e.mnemonic}`;
 for(const v of e.vocabulary){const row=element('tr');row.append(element('td','',v.word),element('td','',v.reading),element('td','',v.meaning_vi));card.querySelector('tbody').append(row);}
 return card;
}
function renderQuerySuggestions(selector,title,items){
 const container=$(selector);container.replaceChildren();container.hidden=!items.length;
 if(!items.length)return;
 container.append(element('h3','',title));
 const list=element('div','query-chips');
 for(const item of items){
  const button=element('button');button.type='button';button.append(element('strong','',item.text),element('span','',item.label));
  button.addEventListener('click',()=>{$('#query').value=item.text;doSearch(item.text);});list.append(button);
 }
 container.append(list);
}
async function doSearch(query){
 query=query.trim();if(!query){$('#query').focus();$('#search-message').textContent='Nhập chữ hoặc câu hỏi để bắt đầu.';return;}
 const sequence=++querySequence;
 $('#search-message').textContent='Đang tìm trong tài liệu…';$('#result-count').textContent='Đang tra cứu';$('#results').replaceChildren();$('#correction-suggestions').hidden=true;$('#similar-suggestions').hidden=true;
 try{
  const result=await api('/api/search',{query,lesson:lessonValue()});if(sequence!==querySequence)return;
  const nodes=[];
  if(result.kind==='han_viet'&&result.results.some(r=>r.tone_match)){
   const exact=result.results.filter(r=>r.tone_match),similar=result.results.filter(r=>!r.tone_match);
   nodes.push(element('h3','result-group-heading','Khớp âm Hán Việt đã nhập'),...exact.map(resultCard));
   if(similar.length)nodes.push(element('h3','result-group-heading','Các âm Hán Việt tương tự'),...similar.map(resultCard));
  }else nodes.push(...result.results.map(resultCard));
  $('#results').replaceChildren(...nodes);
  $('#result-count').textContent=`${result.total} mục · ${result.vocabulary_count} từ · ${result.elapsed_ms} ms`;
  $('#search-message').textContent=result.note;
  renderQuerySuggestions('#correction-suggestions','Có phải bạn muốn tìm?',result.suggestions||[]);
  renderQuerySuggestions('#similar-suggestions','Lưu ý: từ tương tự',result.similar||[]);
  if(!result.results.length&&!result.suggestions?.length)$('#search-message').textContent='Không tìm thấy mục phù hợp trong phạm vi này. Thử chọn tất cả bài hoặc miêu tả thêm.';
  $('#results-section').scrollIntoView({behavior:'smooth',block:'start'});
 }catch(error){if(sequence!==querySequence)return;$('#search-message').textContent=error.message;$('#result-count').textContent='Chưa có kết quả';}
}
async function pollStatus(){
 try{
  const response=await fetch('/api/status'),status=await response.json();
  ready=status.ready;$('#model-status').textContent=ready?'● Sẵn sàng · xử lý local':status.error?'Tra cứu chưa sẵn sàng · xem log server':'Đang nạp model · bạn có thể viết tay';
  $('#model-status').classList.toggle('ready',ready);renderState();
  if(!ready&&!status.error)setTimeout(pollStatus,2000);
 }catch(error){$('#model-status').textContent='Mất kết nối server · mở lại UI';ready=false;renderState();}
}
renderState();pollStatus();
