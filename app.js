const COLORS=['#4f9cff','#4be1c3','#ffb454'];
const fmt=v=>v==null?'—':new Intl.NumberFormat('ko-KR',{notation:'compact',maximumFractionDigits:1}).format(v);
const pct=v=>v==null?'—':`${v.toFixed(2)}%`;
const chart=(id,labels,datasets)=>new Chart(document.getElementById(id),{type:'line',data:{labels,datasets},options:{responsive:true,plugins:{legend:{labels:{color:'#cfe0f5'}}},scales:{x:{ticks:{color:'#8fa5bf'},grid:{color:'#20324a'}},y:{ticks:{color:'#8fa5bf'},grid:{color:'#20324a'}}}}});
fetch('./data/financials.json').then(r=>{if(!r.ok)throw Error('financials.json이 없습니다. 먼저 수집 스크립트를 실행하세요.');return r.json()}).then(d=>{
 const p=d.periods, last=p.at(-1), years=p.map(x=>x.year); document.getElementById('meta').textContent=`${d.basis} · 최근 갱신 ${new Date(d.updatedAt).toLocaleString('ko-KR')}`;
 const cards=[['매출액',fmt(last.values.Revenue)],['영업이익',fmt(last.values.OperatingIncome)],['영업이익률',pct(last.ratios.operatingMargin)],['부채비율',pct(last.ratios.debtRatio)]];
 document.getElementById('cards').innerHTML=cards.map(([a,b])=>`<article class="card"><span>${last.year} ${a}</span><strong>${b}</strong></article>`).join('');
 chart('incomeChart',years,[['매출액','Revenue'],['영업이익','OperatingIncome'],['당기순이익','NetIncome']].map((x,i)=>({label:x[0],data:p.map(y=>y.values[x[1]]),borderColor:COLORS[i],backgroundColor:COLORS[i],tension:.3})));
 chart('profitChart',years,[['영업이익률','operatingMargin'],['순이익률','netMargin'],['ROE','roe']].map((x,i)=>({label:x[0],data:p.map(y=>y.ratios[x[1]]),borderColor:COLORS[i],backgroundColor:COLORS[i],tension:.3})));
 chart('stabilityChart',years,[['부채비율','debtRatio'],['유동비율','currentRatio']].map((x,i)=>({label:x[0],data:p.map(y=>y.ratios[x[1]]),borderColor:COLORS[i],backgroundColor:COLORS[i],tension:.3})));
 const cols=[['연도','year'],['매출액','Revenue'],['영업이익','OperatingIncome'],['당기순이익','NetIncome'],['자산','Assets'],['부채','Liabilities'],['자본','Equity']];
 document.getElementById('table').innerHTML=`<thead><tr>${cols.map(c=>`<th>${c[0]}</th>`).join('')}</tr></thead><tbody>${[...p].reverse().map(y=>`<tr>${cols.map((c,i)=>`<td>${i?fmt(y.values[c[1]]):y.year}</td>`).join('')}</tr>`).join('')}</tbody>`;
}).catch(e=>document.querySelector('main').innerHTML=`<div class="error"><h2>대시보드를 표시할 수 없습니다.</h2><p>${e.message}</p></div>`);

