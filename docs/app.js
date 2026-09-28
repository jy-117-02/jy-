const VALUE_COLUMNS = [
  ["Revenue","매출액"],["GrossProfit","매출총이익"],["OperatingIncome","영업이익"],["NetIncome","당기순이익"],["EBITDA","EBITDA"],
  ["Assets","자산"],["Cash","현금성자산"],["Receivables","매출채권"],["Inventory","재고자산"],["PPE","유형자산"],
  ["Liabilities","부채"],["InterestBearingDebt","이자부채"],["Equity","자본"],["CFO","영업CF"],["CFI","투자CF"],["CFF","재무CF"],["CAPEX","CAPEX"],["FCF","FCF"]
];
const RATIO_COLUMNS = [
  ["operatingMargin","영업이익률","%"],["netMargin","순이익률","%"],["roe","ROE","%"],["roa","ROA","%"],["roic","ROIC","%"],
  ["currentRatio","유동비율","%"],["quickRatio","당좌비율","%"],["debtRatio","부채비율","%"],["interestCoverage","이자보상배율","x"],
  ["assetTurnover","자산회전율","x"],["dso","DSO","d"],["dio","DIO","d"],["dpo","DPO","d"],["ccc","CCC","d"],["revenueGrowth","매출성장률","%"],["cfoToNetIncome","CFO/순이익","x"]
];
let financialData = null;
const wonTn = value => value == null ? "–" : `${(value/1e12).toLocaleString("ko-KR",{maximumFractionDigits:2})}`;
const percent = value => value == null ? "–" : `${Number(value).toLocaleString("ko-KR",{maximumFractionDigits:2})}%`;
const ratioValue = (value, unit) => value == null ? "–" : `${Number(value).toLocaleString("ko-KR",{maximumFractionDigits:2})}${unit}`;
const fullWon = value => value == null ? "데이터 없음" : `${Number(value).toLocaleString("ko-KR")}원`;

function chartDefaults(){
  Chart.defaults.font.family='Inter, "Noto Sans KR", sans-serif'; Chart.defaults.color="#7a8495";
  return {responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{position:"bottom",labels:{usePointStyle:true,boxWidth:7,padding:18,font:{size:10}}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.dataset.yAxisID==="pct"?percent(c.raw):fullWon(c.raw)}`}}},scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{grid:{color:"#edf0f5"},ticks:{font:{size:10},callback:v=>`${(v/1e12).toFixed(0)}조`}}}};
}
function createCharts(annual){
  const labels=annual.map(p=>String(p.year)); const val=k=>annual.map(p=>p.values[k]); const rat=k=>annual.map(p=>p.ratios[k]);
  new Chart(document.querySelector("#incomeChart"),{type:"line",data:{labels,datasets:[{label:"매출액",data:val("Revenue"),borderColor:"#0968f0",backgroundColor:"rgba(9,104,240,.12)",fill:true,tension:.35,pointRadius:2},{label:"영업이익",data:val("OperatingIncome"),borderColor:"#16b8a6",backgroundColor:"transparent",tension:.35,pointRadius:2}]},options:chartDefaults()});
  const marginOpt=chartDefaults(); marginOpt.scales.y={grid:{color:"#edf0f5"},ticks:{callback:v=>`${v}%`}}; marginOpt.plugins.tooltip.callbacks.label=c=>`${c.dataset.label}: ${percent(c.raw)}`;
  new Chart(document.querySelector("#marginChart"),{type:"line",data:{labels,datasets:[{label:"영업이익률",data:rat("operatingMargin"),borderColor:"#0968f0",tension:.35,pointRadius:2},{label:"ROE",data:rat("roe"),borderColor:"#f79009",tension:.35,pointRadius:2}]},options:marginOpt});
  new Chart(document.querySelector("#balanceChart"),{type:"bar",data:{labels,datasets:[{label:"자산",data:val("Assets"),backgroundColor:"#0968f0"},{label:"부채",data:val("Liabilities"),backgroundColor:"#9cbff6"},{label:"자본",data:val("Equity"),backgroundColor:"#1cc8a0"}]},options:chartDefaults()});
  new Chart(document.querySelector("#cashflowChart"),{type:"bar",data:{labels,datasets:[{label:"영업CF",data:val("CFO"),backgroundColor:"#0968f0"},{label:"CAPEX",data:val("CAPEX"),backgroundColor:"#91b9f6"},{label:"FCF",data:val("FCF"),backgroundColor:"#13b58c"}]},options:chartDefaults()});
}
function renderKpis(latest, previous){
  const growth=(key,ratio=false)=>ratio?(latest.ratios[key]!=null&&previous?.ratios[key]!=null?latest.ratios[key]-previous.ratios[key]:null):(latest.values[key]!=null&&previous?.values[key]?((latest.values[key]-previous.values[key])/Math.abs(previous.values[key])*100):null);
  const items=[["매출액",wonTn(latest.values.Revenue)+"조원",growth("Revenue"),false],["영업이익",wonTn(latest.values.OperatingIncome)+"조원",growth("OperatingIncome"),false],["영업이익률",percent(latest.ratios.operatingMargin),growth("operatingMargin",true),true],["ROE",percent(latest.ratios.roe),growth("roe",true),true]];
  document.querySelector("#heroKpis").innerHTML=items.map(x=>`<div class="hero-kpi"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join("");
  document.querySelector("#kpiGrid").innerHTML=items.map(x=>`<article class="kpi-card"><p>${x[0]} · ${latest.year}</p><strong>${x[1]}</strong><small>${x[2]==null?"전년 비교 없음":`${x[2]>=0?"▲":"▼"} ${Math.abs(x[2]).toFixed(2)}${x[3]?"%p":"% YoY"}`}</small></article>`).join("");
}
function renderTable(id, periods){
  const table=document.querySelector(id); const head=[["period","기간"],...VALUE_COLUMNS,...RATIO_COLUMNS.map(x=>[x[0],x[1]])];
  table.innerHTML=`<thead><tr>${head.map(x=>`<th>${x[1]}</th>`).join("")}</tr></thead><tbody>${[...periods].reverse().map(p=>`<tr><td>${p.period}<br><small>${p.fsDiv||"–"}</small></td>${VALUE_COLUMNS.map(x=>`<td>${wonTn(p.values[x[0]])}</td>`).join("")}${RATIO_COLUMNS.map(x=>`<td>${ratioValue(p.ratios[x[0]],x[2])}</td>`).join("")}</tr>`).join("")}</tbody>`;
}
function renderPeers(peers){document.querySelector("#peerGrid").innerHTML=peers.map(p=>`<article class="peer-card"><span class="code">KRX · ${p.stockCode}</span><h3>${p.company}</h3><strong>${p.segment}</strong><p>${p.reason}</p></article>`).join("");}
function downloadCategory(category){
  const rows=financialData.periods.filter(p=>p.category===category); const headers=["기간",...VALUE_COLUMNS.map(x=>x[1]),...RATIO_COLUMNS.map(x=>x[1])];
  const csv=[headers,...rows.map(p=>[p.period,...VALUE_COLUMNS.map(x=>p.values[x[0]]??""),...RATIO_COLUMNS.map(x=>p.ratios[x[0]]??"")])].map(r=>r.map(v=>`"${String(v).replaceAll('"','""')}"`).join(",")).join("\n");
  const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob(["\ufeff"+csv],{type:"text/csv"})); a.download=`samsung_${category}.csv`; a.click(); URL.revokeObjectURL(a.href);
}
async function init(){
  try{
    const [financial,peers]=await Promise.all([fetch("data/financials.json").then(r=>{if(!r.ok)throw Error(r.status);return r.json()}),fetch("data/peers.json").then(r=>r.json())]); financialData=financial; renderPeers(peers);
    document.querySelector("#updatedAt").textContent=`업데이트 ${new Date(financial.generatedAt).toLocaleDateString("ko-KR")}`;
    const annual=financial.periods.filter(p=>p.category==="annual"); const half=financial.periods.filter(p=>p.category==="halfYear"); const quarterly=financial.periods.filter(p=>p.category==="quarterly");
    renderTable("#annualTable",annual); renderTable("#halfTable",half); renderTable("#quarterlyTable",quarterly);
    if(annual.length){renderKpis(annual.at(-1),annual.at(-2));createCharts(annual);}else{document.querySelector("#heroKpis").innerHTML="<p>DART_API_KEY 설정 후 워크플로를 실행해 주세요.</p>";document.querySelector("#dataNotice").hidden=false;document.querySelector("#dataNotice").textContent="아직 수집된 데이터가 없습니다. GitHub Secret 등록 후 Monthly DART Update를 수동 실행하면 자동으로 채워집니다.";}
    if(financial.warnings?.length){const box=document.querySelector("#dataNotice");box.hidden=false;box.textContent=`일부 기간은 데이터가 없거나 파싱되지 않았습니다 (${financial.warnings.length}건). data/financials.json의 warnings를 확인하세요.`;}
    document.querySelectorAll("[data-download]").forEach(b=>b.addEventListener("click",()=>downloadCategory(b.dataset.download)));
  }catch(e){document.querySelector("#updatedAt").textContent="데이터 로드 실패";const box=document.querySelector("#dataNotice");box.hidden=false;box.textContent="데이터 파일을 불러오지 못했습니다. GitHub Pages 설정과 docs/data/financials.json을 확인해 주세요.";}
}
window.addEventListener("DOMContentLoaded",init);
