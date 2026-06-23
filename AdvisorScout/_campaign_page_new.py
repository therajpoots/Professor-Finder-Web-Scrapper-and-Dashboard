def _generate_campaign_page():
    """Generate a standalone campaign progress tracking page."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    campaign_page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campaign Pipeline — AdvisorScout</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#050508;--surface:#0d0d18;--card:#111120;--border:rgba(255,255,255,0.07);
  --text:#ffffff;--text2:#9090b0;--accent:#7d5fff;--accent2:#b3a4ff;
  --green:#00d2ad;--orange:#ff9f43;--red:#ff6b6b;--blue:#48dbfb;
}
body{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;
  background-image:radial-gradient(ellipse at top,rgba(125,95,255,0.08) 0%,transparent 60%),
                   radial-gradient(ellipse at bottom right,rgba(0,210,173,0.05) 0%,transparent 50%);}
.topnav{display:flex;align-items:center;justify-content:space-between;
  padding:1.2rem 2.5rem;border-bottom:1px solid var(--border);
  background:rgba(5,5,8,0.9);backdrop-filter:blur(20px);position:sticky;top:0;z-index:100;}
.nav-brand{display:flex;align-items:center;gap:12px;}
.nav-brand h1{font-size:1.3rem;font-weight:800;
  background:linear-gradient(135deg,var(--accent2),var(--blue));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.nav-links{display:flex;gap:1rem;}
.nav-link{color:var(--text2);text-decoration:none;font-size:.85rem;font-weight:600;
  padding:.5rem 1.2rem;border-radius:10px;transition:all .2s;border:1px solid transparent;}
.nav-link:hover,.nav-link.active{color:var(--text);background:rgba(255,255,255,0.06);border-color:var(--border);}
.nav-link.active{color:var(--accent2);border-color:rgba(125,95,255,0.3);}
.page{max-width:1400px;margin:0 auto;padding:2rem;}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem;}
@media(max-width:900px){.two-col{grid-template-columns:1fr;}}
.status-hero{background:linear-gradient(135deg,rgba(125,95,255,0.08),rgba(0,210,173,0.06));
  border:1px solid rgba(125,95,255,0.2);border-radius:24px;padding:2rem;margin-bottom:1.5rem;position:relative;overflow:hidden;}
.status-hero::before{content:'';position:absolute;top:0;right:0;width:300px;height:300px;
  background:radial-gradient(circle,rgba(125,95,255,0.15),transparent 70%);pointer-events:none;}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem;}
.hero-left h2{font-size:1.8rem;font-weight:800;margin-bottom:.3rem;}
.hero-left p{color:var(--text2);font-size:.88rem;}
.campaign-badge{display:inline-flex;align-items:center;gap:8px;
  padding:.6rem 1.4rem;border-radius:50px;font-weight:700;font-size:.85rem;}
.badge-running{background:rgba(0,210,173,0.12);color:var(--green);border:1px solid rgba(0,210,173,0.3);}
.badge-stopped{background:rgba(255,107,107,0.12);color:var(--red);border:1px solid rgba(255,107,107,0.3);}
.badge-completed{background:rgba(0,210,173,0.12);color:var(--green);border:1px solid rgba(0,210,173,0.3);}
.badge-idle{background:rgba(144,144,176,0.12);color:var(--text2);border:1px solid var(--border);}
.badge-error{background:rgba(255,107,107,0.12);color:var(--red);border:1px solid rgba(255,107,107,0.3);}
.badge-interrupted{background:rgba(255,159,67,0.12);color:var(--orange);border:1px solid rgba(255,159,67,0.3);}
.pulse{width:9px;height:9px;border-radius:50%;background:var(--green);animation:pulse 1.5s ease-in-out infinite;display:inline-block;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.5;transform:scale(1.4);}}
.prog-section{margin-bottom:.5rem;}
.prog-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem;}
.prog-header span{font-size:.85rem;font-weight:600;color:var(--text2);}
.prog-header strong{font-size:1rem;color:var(--accent2);}
.prog-track{height:12px;background:rgba(255,255,255,0.05);border-radius:10px;overflow:hidden;}
.prog-fill{height:100%;border-radius:10px;
  background:linear-gradient(90deg,var(--accent),var(--blue),var(--green));
  background-size:200% 100%;animation:shimmer 2s linear infinite;
  transition:width .6s ease;min-width:2px;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:0% 0}}
.metrics-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;margin-bottom:1.5rem;}
@media(max-width:900px){.metrics-grid{grid-template-columns:repeat(3,1fr);}}
.metric-card{background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:16px;
  padding:1.2rem;text-align:center;transition:border-color .2s;}
.metric-card:hover{border-color:rgba(125,95,255,0.3);}
.metric-num{font-size:2rem;font-weight:800;letter-spacing:-1px;display:block;margin-bottom:.25rem;}
.metric-num.green{color:var(--green);}.metric-num.orange{color:var(--orange);}
.metric-num.red{color:var(--red);}.metric-num.blue{color:var(--blue);}.metric-num.accent{color:var(--accent2);}
.metric-label{font-size:.68rem;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;font-weight:600;}
.controls-bar{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.5rem;}
.ctrl-btn{display:inline-flex;align-items:center;gap:.6rem;
  padding:.75rem 1.5rem;border-radius:12px;font-family:'Outfit',sans-serif;
  font-weight:700;font-size:.85rem;cursor:pointer;transition:all .25s;border:none;}
.btn-start{background:linear-gradient(135deg,var(--green),#00b894);color:#fff;box-shadow:0 6px 20px rgba(0,210,173,0.3);}
.btn-start:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(0,210,173,0.45);}
.btn-stop{background:linear-gradient(135deg,var(--red),#c0392b);color:#fff;box-shadow:0 6px 20px rgba(255,107,107,0.3);}
.btn-stop:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(255,107,107,0.4);}
.btn-reset{background:rgba(255,255,255,0.06);color:var(--text2);border:1px solid var(--border);}
.btn-reset:hover{background:rgba(255,255,255,0.1);color:var(--text);}
.btn-test{background:rgba(72,219,251,0.1);color:var(--blue);border:1px solid rgba(72,219,251,0.25);}
.btn-test:hover{background:rgba(72,219,251,0.18);}
.alert{padding:1rem 1.4rem;border-radius:14px;font-size:.88rem;margin-bottom:1.2rem;display:none;}
.alert.show{display:flex;align-items:center;gap:1rem;}
.alert-success{background:rgba(0,210,173,0.08);border:1px solid rgba(0,210,173,0.3);color:var(--green);}
.alert-error{background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.3);color:var(--red);}
/* PIPELINE */
.pipeline-card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:1.5rem;margin-bottom:1.5rem;}
.pipeline-card h3{font-size:.75rem;font-weight:700;margin-bottom:1.2rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;}
.pipeline{display:flex;gap:0;align-items:flex-start;}
.pipe-step{flex:1;display:flex;flex-direction:column;align-items:center;position:relative;}
.pipe-step:not(:last-child)::after{content:'';position:absolute;top:20px;left:calc(50% + 22px);
  right:calc(-50% + 22px);height:2px;background:var(--border);z-index:0;}
.pipe-step.done::after{background:var(--green);}
.pipe-step.active::after{background:linear-gradient(90deg,var(--accent),var(--border));}
.pipe-icon{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:1.1rem;border:2px solid var(--border);
  background:var(--surface);z-index:1;position:relative;transition:all .4s;}
.pipe-step.done .pipe-icon{background:rgba(0,210,173,0.15);border-color:var(--green);}
.pipe-step.active .pipe-icon{background:rgba(125,95,255,0.2);border-color:var(--accent2);
  box-shadow:0 0 18px rgba(125,95,255,0.5);animation:glow 1.5s ease-in-out infinite;}
@keyframes glow{0%,100%{box-shadow:0 0 10px rgba(125,95,255,0.3);}50%{box-shadow:0 0 24px rgba(125,95,255,0.7);}}
.pipe-label{font-size:.65rem;color:var(--text2);margin-top:.5rem;text-align:center;
  font-weight:600;text-transform:uppercase;letter-spacing:.5px;max-width:80px;line-height:1.3;}
.pipe-step.done .pipe-label{color:var(--green);}
.pipe-step.active .pipe-label{color:var(--accent2);}
/* CURRENT PROFESSOR */
.current-card{background:rgba(125,95,255,0.06);border:1px solid rgba(125,95,255,0.2);
  border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:1rem;}
.current-icon{font-size:1.5rem;}
.current-text{flex:1;}
.current-text .label{font-size:.68rem;color:var(--accent2);text-transform:uppercase;letter-spacing:1.5px;font-weight:700;}
.current-text .value{font-size:.95rem;font-weight:600;color:var(--text);margin-top:2px;}
.step-label{font-size:.8rem;color:var(--green);margin-top:.3rem;font-style:italic;}
/* PANELS */
.panel{background:var(--card);border:1px solid var(--border);border-radius:20px;overflow:hidden;}
.panel-header{padding:1rem 1.4rem;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;cursor:pointer;
  user-select:none;transition:background .2s;}
.panel-header:hover{background:rgba(255,255,255,0.02);}
.panel-header h3{font-size:.85rem;font-weight:700;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;}
.panel-tag{font-size:.63rem;padding:.2rem .6rem;border-radius:6px;font-weight:700;}
.tag-prompt{background:rgba(72,219,251,0.12);color:var(--blue);}
.tag-output{background:rgba(125,95,255,0.12);color:var(--accent2);}
.tag-email{background:rgba(0,210,173,0.12);color:var(--green);}
.tag-wc{background:rgba(255,159,67,0.12);color:var(--orange);}
.panel-toggle{font-size:.75rem;color:var(--text2);transition:transform .3s;flex-shrink:0;}
.panel-toggle.open{transform:rotate(180deg);}
.panel-body{padding:1.2rem 1.4rem;display:none;max-height:380px;overflow-y:auto;}
.panel-body.open{display:block;}
.panel-pre{font-family:'Courier New',monospace;font-size:.76rem;line-height:1.7;color:var(--text2);
  white-space:pre-wrap;word-break:break-word;}
.email-subject{font-size:.95rem;font-weight:700;color:var(--accent2);
  margin-bottom:.8rem;padding:.6rem 1rem;background:rgba(125,95,255,0.08);
  border-radius:10px;border-left:3px solid var(--accent);}
.email-body-text{font-size:.85rem;line-height:1.9;color:var(--text);white-space:pre-wrap;}
/* LOG */
.section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;}
.section-header h3{font-size:1rem;font-weight:700;color:var(--text);}
.section-header .sub{font-size:.8rem;color:var(--text2);}
.log-wrap{overflow-x:auto;border-radius:16px;border:1px solid var(--border);margin-bottom:2rem;}
.log-table{width:100%;border-collapse:collapse;}
.log-table th{background:rgba(255,255,255,0.03);padding:.8rem 1rem;
  text-align:left;font-size:.63rem;color:var(--text2);
  text-transform:uppercase;letter-spacing:1.5px;font-weight:700;
  border-bottom:1px solid var(--border);white-space:nowrap;}
.log-table td{padding:.75rem 1rem;border-bottom:1px solid rgba(255,255,255,0.04);
  font-size:.8rem;vertical-align:middle;}
.log-table tr:last-child td{border-bottom:none;}
.log-table tr:hover td{background:rgba(255,255,255,0.02);}
.status-sent{display:inline-flex;align-items:center;gap:4px;color:var(--green);font-weight:700;font-size:.75rem;}
.status-error{display:inline-flex;align-items:center;gap:4px;color:var(--red);font-weight:600;font-size:.72rem;
  max-width:200px;word-break:break-word;white-space:normal;}
.match-high{color:var(--orange);font-weight:700;font-size:.73rem;}
.match-good{color:var(--blue);font-weight:600;font-size:.73rem;}
.match-partial{color:var(--text2);font-size:.73rem;}
.email-cell{color:var(--text2);font-size:.75rem;font-family:monospace;}
.time-cell{color:var(--text2);font-size:.73rem;white-space:nowrap;}
.name-cell{font-weight:600;font-size:.83rem;}
.univ-cell{font-size:.73rem;color:var(--text2);}
.wc-cell{font-size:.73rem;color:var(--orange);font-weight:600;}
.subj-cell{font-size:.73rem;color:var(--accent2);max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.empty-log{text-align:center;padding:3rem;color:var(--text2);font-size:.9rem;}
.refresh-dot{width:8px;height:8px;border-radius:50%;background:var(--green);
  display:inline-block;margin-right:6px;animation:pulse 1.5s infinite;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:6px;}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.12);}
</style>
</head>
<body>

<nav class="topnav">
  <div class="nav-brand">
    <span style="font-size:1.5rem">📊</span>
    <h1>Campaign Pipeline</h1>
  </div>
  <div class="nav-links">
    <a href="/" class="nav-link">&#127968; Dashboard</a>
    <a href="/campaign" class="nav-link active">&#128202; Campaign</a>
  </div>
</nav>

<div class="page">

  <div class="alert alert-success" id="alert-success"><span>OK</span><span id="alert-text"></span></div>
  <div class="alert alert-error" id="alert-error"><span>!!</span><span id="alert-err-text"></span></div>

  <!-- HERO -->
  <div class="status-hero">
    <div class="hero-top">
      <div class="hero-left">
        <h2 id="hero-title">Email Campaign</h2>
        <p id="hero-sub">Checking status...</p>
      </div>
      <div id="campaign-badge" class="campaign-badge badge-idle">Loading...</div>
    </div>
    <div class="prog-section">
      <div class="prog-header">
        <span id="prog-label">Progress</span>
        <strong id="prog-pct">0%</strong>
      </div>
      <div class="prog-track"><div class="prog-fill" id="prog-fill" style="width:0%"></div></div>
    </div>
  </div>

  <!-- METRICS -->
  <div class="metrics-grid">
    <div class="metric-card"><span class="metric-num accent" id="m-total">--</span><span class="metric-label">Total</span></div>
    <div class="metric-card"><span class="metric-num green" id="m-sent">--</span><span class="metric-label">Sent</span></div>
    <div class="metric-card"><span class="metric-num red" id="m-failed">--</span><span class="metric-label">Failed</span></div>
    <div class="metric-card"><span class="metric-num orange" id="m-remaining">--</span><span class="metric-label">Remaining</span></div>
    <div class="metric-card"><span class="metric-num blue" id="m-rate">--</span><span class="metric-label">Success Rate</span></div>
  </div>

  <!-- CONTROLS -->
  <div class="controls-bar">
    <button class="ctrl-btn btn-start" id="btn-start" onclick="startCampaign()">&#9654; Start Campaign</button>
    <button class="ctrl-btn btn-stop" id="btn-stop" onclick="stopCampaign()" style="display:none">&#9632; Stop</button>
    <button class="ctrl-btn btn-reset" onclick="resetCampaign()">Reset Status</button>
    <button class="ctrl-btn btn-test" onclick="sendTestEmail()">Test Email</button>
    <button class="ctrl-btn btn-reset" onclick="window.location.href='/'">Back to Dashboard</button>
  </div>

  <!-- PIPELINE -->
  <div class="pipeline-card">
    <h3>Live Pipeline Steps</h3>
    <div class="pipeline">
      <div class="pipe-step idle" id="pipe-1">
        <div class="pipe-icon">&#128203;</div>
        <div class="pipe-label">Build Prompt</div>
      </div>
      <div class="pipe-step idle" id="pipe-2">
        <div class="pipe-icon">&#129302;</div>
        <div class="pipe-label">Call DeepSeek AI</div>
      </div>
      <div class="pipe-step idle" id="pipe-3">
        <div class="pipe-icon">&#9986;</div>
        <div class="pipe-label">Parse Email</div>
      </div>
      <div class="pipe-step idle" id="pipe-4">
        <div class="pipe-icon">&#128232;</div>
        <div class="pipe-label">Send via SMTP</div>
      </div>
      <div class="pipe-step idle" id="pipe-5">
        <div class="pipe-icon">&#8987;</div>
        <div class="pipe-label">Cooldown 15s</div>
      </div>
    </div>
  </div>

  <!-- CURRENT PROFESSOR -->
  <div class="current-card">
    <div class="current-icon">&#127919;</div>
    <div class="current-text">
      <div class="label">Currently Processing</div>
      <div class="value" id="current-prof-text">--</div>
      <div class="step-label" id="step-label">--</div>
    </div>
  </div>

  <!-- PROMPT + OUTPUT (2 col) -->
  <div class="two-col">
    <div class="panel">
      <div class="panel-header" onclick="togglePanel('prompt-body','prompt-toggle')">
        <h3>Prompt Sent to DeepSeek <span class="panel-tag tag-prompt">PROMPT</span></h3>
        <span class="panel-toggle" id="prompt-toggle">&#9660;</span>
      </div>
      <div class="panel-body" id="prompt-body">
        <div class="panel-pre" id="prompt-text">No prompt yet. Start the campaign to see live data.</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header" onclick="togglePanel('output-body','output-toggle')">
        <h3>DeepSeek Raw Output <span class="panel-tag tag-output">AI OUTPUT</span></h3>
        <span class="panel-toggle" id="output-toggle">&#9660;</span>
      </div>
      <div class="panel-body" id="output-body">
        <div class="panel-pre" id="output-text">Waiting for AI response...</div>
      </div>
    </div>
  </div>

  <!-- EMAIL PREVIEW (full width) -->
  <div class="panel" style="margin-bottom:1.5rem;">
    <div class="panel-header" onclick="togglePanel('email-panel-body','email-toggle')">
      <h3>Parsed Email Preview
        <span class="panel-tag tag-email">EMAIL</span>
        <span class="panel-tag tag-wc" id="wc-tag">-- words</span>
      </h3>
      <span class="panel-toggle" id="email-toggle">&#9660;</span>
    </div>
    <div class="panel-body" id="email-panel-body">
      <div class="email-subject" id="email-subject">Subject: --</div>
      <div class="email-body-text" id="email-body-text">No email generated yet.</div>
    </div>
  </div>

  <!-- LOG TABLE -->
  <div class="section-header">
    <h3><span class="refresh-dot"></span>Activity Log</h3>
    <span class="sub" id="log-count">Loading...</span>
  </div>
  <div class="log-wrap">
    <table class="log-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Professor</th>
          <th>University</th>
          <th>Email</th>
          <th>Subject</th>
          <th>Words</th>
          <th>Match</th>
          <th>Status</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody id="log-tbody">
        <tr><td colspan="9" class="empty-log">Waiting for campaign data...</td></tr>
      </tbody>
    </table>
  </div>

</div>

<script>
function escHtml(s){
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function togglePanel(bodyId, toggleId){
  const body=document.getElementById(bodyId);
  const tog=document.getElementById(toggleId);
  const isOpen=body.classList.contains('open');
  body.classList.toggle('open',!isOpen);
  tog.classList.toggle('open',!isOpen);
}

let panelsAutoOpened=false;

async function poll(){
  try{
    const res=await fetch('/mass_email_status.json?t='+Date.now());
    if(!res.ok) return;
    const s=await res.json();
    updateStatus(s);
  }catch(e){console.warn('Poll failed:',e);}
}

function updateStatus(s){
  const total=s.total||0, sent=s.sent||0, failed=s.failed||0;
  const remaining=Math.max(0,total-sent-failed);
  const pct=total>0?Math.min(100,Math.round((sent/total)*100)):0;
  const rate=(sent+failed)>0?Math.round((sent/(sent+failed))*100):0;

  document.getElementById('m-total').textContent=total||'--';
  document.getElementById('m-sent').textContent=sent;
  document.getElementById('m-failed').textContent=failed;
  document.getElementById('m-remaining').textContent=remaining>0?remaining:(total>0?'0':'--');
  document.getElementById('m-rate').textContent=(sent+failed)>0?rate+'%':'--';
  document.getElementById('prog-fill').style.width=pct+'%';
  document.getElementById('prog-pct').textContent=pct+'%';
  document.getElementById('prog-label').textContent=sent+' of '+total+' sent';
  document.getElementById('current-prof-text').textContent=s.current_prof||'--';
  document.getElementById('step-label').textContent=s.pipeline_label||'';

  // Pipeline steps
  const step=s.pipeline_step||0;
  for(let i=1;i<=5;i++){
    const el=document.getElementById('pipe-'+i);
    if(!el) continue;
    el.className='pipe-step '+(i<step?'done':i===step?'active':'idle');
  }

  // Prompt
  if(s.pipeline_prompt){
    document.getElementById('prompt-text').textContent=s.pipeline_prompt;
    if(!panelsAutoOpened){
      togglePanel('prompt-body','prompt-toggle');
      togglePanel('output-body','output-toggle');
      togglePanel('email-panel-body','email-toggle');
      panelsAutoOpened=true;
    }
  }
  // AI output
  if(s.pipeline_output) document.getElementById('output-text').textContent=s.pipeline_output;
  // Email preview
  if(s.pipeline_subject) document.getElementById('email-subject').textContent='Subject: '+s.pipeline_subject;
  if(s.pipeline_body) document.getElementById('email-body-text').textContent=s.pipeline_body;
  const wc=s.pipeline_word_count||0;
  document.getElementById('wc-tag').textContent=wc>0?wc+' words':'-- words';

  // Badge + hero
  const badge=document.getElementById('campaign-badge');
  const btnStart=document.getElementById('btn-start');
  const btnStop=document.getElementById('btn-stop');
  badge.className='campaign-badge';
  if(s.status==='running'){
    badge.classList.add('badge-running');
    badge.innerHTML='<span class="pulse"></span> Running';
    document.getElementById('hero-title').textContent='Email Campaign Active';
    document.getElementById('hero-sub').textContent='Sending via DeepSeek AI  |  '+sent+'/'+total+' complete';
    btnStart.style.display='none'; btnStop.style.display='flex';
  }else if(s.status==='completed'){
    badge.classList.add('badge-completed'); badge.textContent='Completed';
    document.getElementById('hero-title').textContent='Campaign Complete!';
    document.getElementById('hero-sub').textContent='All '+total+' professors processed  |  '+sent+' sent  |  '+failed+' failed';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else if(s.status==='stopped'){
    badge.classList.add('badge-stopped'); badge.textContent='Stopped';
    document.getElementById('hero-title').textContent='Campaign Stopped';
    document.getElementById('hero-sub').textContent='Manually stopped  |  '+sent+' sent so far';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else if(s.status==='error'){
    badge.classList.add('badge-error'); badge.textContent='Error';
    document.getElementById('hero-title').textContent='Campaign Error';
    document.getElementById('hero-sub').textContent=s.current_prof||'An error occurred';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else if(s.status==='interrupted'){
    badge.classList.add('badge-interrupted'); badge.textContent='Interrupted';
    document.getElementById('hero-title').textContent='Campaign Interrupted';
    document.getElementById('hero-sub').textContent='Server restarted. Click Start to resume.';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else{
    badge.classList.add('badge-idle'); badge.textContent='Idle';
    document.getElementById('hero-title').textContent='Email Campaign';
    document.getElementById('hero-sub').textContent='No active campaign. Click Start to begin.';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }

  // Log table
  const log=s.log||[];
  const tbody=document.getElementById('log-tbody');
  document.getElementById('log-count').textContent=log.length+' entries';
  if(log.length===0){
    tbody.innerHTML='<tr><td colspan="9" class="empty-log">No activity yet. Start the campaign.</td></tr>';
    return;
  }
  tbody.innerHTML=log.map((entry,i)=>{
    const isSent=entry.result==='Sent';
    const statusCell=isSent
      ?'<span class="status-sent">Sent</span>'
      :'<span class="status-error">'+escHtml(entry.result)+'</span>';
    const matchCell=(entry.match||'').includes('High')
      ?'<span class="match-high">'+escHtml(entry.match)+'</span>'
      :(entry.match||'').includes('Good')
        ?'<span class="match-good">'+escHtml(entry.match)+'</span>'
        :'<span class="match-partial">'+escHtml(entry.match||'--')+'</span>';
    return '<tr>'+
      '<td style="color:var(--text2);font-size:.72rem;">'+(log.length-i)+'</td>'+
      '<td class="name-cell">'+escHtml(entry.name||'--')+'</td>'+
      '<td class="univ-cell">'+escHtml(entry.university||'--')+'</td>'+
      '<td class="email-cell">'+escHtml(entry.email||'--')+'</td>'+
      '<td class="subj-cell" title="'+escHtml(entry.subject||'')+'">'+escHtml(entry.subject||'--')+'</td>'+
      '<td class="wc-cell">'+(entry.word_count?entry.word_count+'w':'--')+'</td>'+
      '<td>'+matchCell+'</td>'+
      '<td>'+statusCell+'</td>'+
      '<td class="time-cell">'+escHtml(entry.time||'--')+'</td>'+
      '</tr>';
  }).join('');
}

async function startCampaign(){
  if(!confirm('Start the email campaign? Emails will be sent to all matched professors via DeepSeek AI.')) return;
  panelsAutoOpened=false;
  try{ await fetch('/start_mass_email'); showAlert('success','Campaign started! Watching for updates...'); }
  catch(e){ showAlert('error','Failed to start: '+e.message); }
}
async function stopCampaign(){
  if(!confirm('Stop the campaign? Progress is saved.')) return;
  try{ await fetch('/stop_mass_email'); showAlert('success','Stop signal sent. Will halt after current email.'); }
  catch(e){ showAlert('error','Failed to stop: '+e.message); }
}
async function resetCampaign(){
  if(!confirm('Reset campaign status? This does NOT clear the sent log.')) return;
  try{ await fetch('/reset_campaign'); showAlert('success','Status reset.'); panelsAutoOpened=false; }
  catch(e){ showAlert('error','Failed to reset: '+e.message); }
}
async function sendTestEmail(){
  document.querySelectorAll('.ctrl-btn').forEach(b=>b.disabled=true);
  showAlert('success','Sending test email...');
  try{
    const res=await fetch('/send_test_email');
    const data=await res.json();
    if(data.status==='sent') showAlert('success','Test sent to '+data.sent_to+'! Subject: "'+data.subject+'"');
    else showAlert('error','Test failed: '+(data.message||'Unknown error'));
  }catch(e){ showAlert('error','Test email failed: '+e.message); }
  finally{ document.querySelectorAll('.ctrl-btn').forEach(b=>b.disabled=false); }
}
function showAlert(type,msg){
  document.getElementById('alert-success').classList.remove('show');
  document.getElementById('alert-error').classList.remove('show');
  if(type==='success'){
    document.getElementById('alert-text').textContent=msg;
    document.getElementById('alert-success').classList.add('show');
    setTimeout(()=>document.getElementById('alert-success').classList.remove('show'),6000);
  }else{
    document.getElementById('alert-err-text').textContent=msg;
    document.getElementById('alert-error').classList.add('show');
    setTimeout(()=>document.getElementById('alert-error').classList.remove('show'),8000);
  }
}
setInterval(poll,2000);
poll();
</script>
</body>
</html>"""
    campaign_path = os.path.join(RESULTS_DIR, "campaign_progress.html")
    with open(campaign_path, "w", encoding="utf-8") as f:
        f.write(campaign_page)

