import os, socket, time
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
POD = os.environ.get("HOSTNAME", socket.gethostname())

def burn(ms):
    end = time.perf_counter() + ms / 1000
    x = 0
    while time.perf_counter() < end:
        x += 1  # busy loop = real CPU usage

PAGE = """
<!doctype html><title>HPA Practice</title>
<body style="font-family:sans-serif;max-width:640px;margin:30px auto">
<h2>HPA Practice App</h2>
<p>Each request burns CPU on whichever pod receives it.</p>
<label>Parallel users: <b id=uv>5</b></label><br>
<input id=users type=range min=0 max=100 value=5 style="width:100%"><br><br>
<label>CPU per request (ms): <b id=mv>200</b></label><br>
<input id=ms type=range min=10 max=1000 value=200 style="width:100%"><br><br>
<button id=toggle>Start load</button>
<h3>Pods that answered (last 50 requests)</h3>
<div id=pods>-</div>
<p>Total sent: <span id=sent>0</span> | Errors: <span id=err>0</span></p>
<script>
let running=false, sent=0, err=0, recent=[];
const $=id=>document.getElementById(id);
$('users').oninput=()=>$('uv').textContent=$('users').value;
$('ms').oninput=()=>$('mv').textContent=$('ms').value;
$('toggle').onclick=()=>{running=!running;$('toggle').textContent=running?'Stop load':'Start load'};
async function worker(i){
  while(true){
    if(running && i < +$('users').value){
      try{
        const r=await fetch('/burn?ms='+$('ms').value);
        const j=await r.json(); recent.push(j.pod); if(recent.length>50) recent.shift();
        sent++;
      }catch(e){err++}
    } else { await new Promise(r=>setTimeout(r,300)); }
  }
}
for(let i=0;i<100;i++) worker(i);
setInterval(()=>{
  const c={}; recent.forEach(p=>c[p]=(c[p]||0)+1);
  $('pods').innerHTML=Object.entries(c).map(([p,n])=>p+' : '+n).join('<br>')||'-';
  $('sent').textContent=sent; $('err').textContent=err;
},500);
</script></body>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/burn")
def do_burn():
    ms = min(int(request.args.get("ms", 200)), 5000)
    burn(ms)
    return jsonify(pod=POD, burned_ms=ms)

@app.route("/healthz")
def health():
    return "ok"