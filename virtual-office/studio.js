(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const urlParams = new URLSearchParams(window.location.search);
  const initialToken = urlParams.get('token') || localStorage.getItem('kantor_ai_token') || sessionStorage.getItem('kantor_ai_token') || '';
  if (urlParams.get('token')) {
    sessionStorage.setItem('kantor_ai_token', urlParams.get('token'));
  }
  const state = {token:initialToken, data:null, selected:'sales', view:'denah', agentSignature:'', epoch:0, loading:false};
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const number = value => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('id-ID').format(value) : '—';
  const modelLabel = value => value === 'deepseek-flash' ? 'DeepSeek Flash' : value;
  const date = (value, withTime=false) => {
    if(!value) return 'Tanggal belum tersedia';
    const parsed = new Date(value);
    if(Number.isNaN(parsed.getTime())) return 'Tanggal belum tersedia';
    return new Intl.DateTimeFormat('id-ID',{timeZone:'Asia/Jakarta',day:'numeric',month:'short',year:'numeric',...(withTime?{hour:'2-digit',minute:'2-digit'}:{})}).format(parsed)+(withTime?' WIB':'');
  };
  const runtime = agent => `<span class="runtime-label ${escape(agent.runtime)}"><span class="status-dot" aria-hidden="true"></span>${escape(agent.runtime_label)}</span>`;
  const showConnection = (label,status) => { $('connection-label').textContent=label; $('connection').dataset.state=status; };
  function showAccess(message='') {
    window.Office3D?.setVisible(false);
    $('office-app').hidden=true;
    $('access-screen').hidden=false;
    $('access-error').textContent=message;
  }
  function switchView(view, focusTab=false) {
    if(!['denah','tim','aktivitas'].includes(view)) return;
    state.view=view;
    window.Office3D?.setVisible(view==='denah');
    document.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-selected',String(button.dataset.view===view)));
    ['denah','tim','aktivitas'].forEach(name=>$('panel-'+name).hidden=name!==view);
    if(focusTab) $('tab-'+view).focus();
  }
  function chooseAgent(id, scroll=false, focus3d=true) {
    if(!state.data?.office.agents.some(agent=>agent.id===id)) return;
    state.selected=id;
    window.Office3D?.select(id,focus3d);
    $('scene-view').textContent=state.data.office.agents.find(agent=>agent.id===id).short_name;
    document.querySelectorAll('.room').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.id===id)));
    renderInspector();
    if(scroll) $('office-viewport').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth',block:'center'});
  }
  function renderAgents() {
    const agents=state.data.office.agents;
    if(!agents.some(agent=>agent.id===state.selected)) state.selected=agents[0]?.id;
    const focused=document.activeElement?.dataset?.id;
    $('floorplan').innerHTML=agents.map(agent=>`<button class="room" type="button" data-id="${escape(agent.id)}" data-wide="${['pm','researcher','sales','default'].includes(agent.id)}" aria-pressed="${agent.id===state.selected}" aria-controls="inspector"><span class="room-number" aria-hidden="true">${escape(agent.room)}</span><span class="room-topline"><span class="room-initials" aria-hidden="true">${escape(agent.initials)}</span><span class="room-name">${escape(agent.short_name)}</span></span><span class="room-role">${escape(agent.role)}</span><span class="room-bottom"><span class="room-stage">${escape(agent.stage)}</span>${runtime(agent)}</span></button>`).join('');
    $('team-body').innerHTML=agents.map(agent=>`<tr><td><div class="team-name"><span class="team-avatar" aria-hidden="true">${escape(agent.initials)}</span><span><strong>${escape(agent.name)}</strong><small>${escape(modelLabel(agent.model))}</small></span></div></td><td>${escape(agent.role)}</td><td>${runtime(agent)}</td><td>${escape(agent.stage)}</td><td><button class="text-button" type="button" data-open-agent="${escape(agent.id)}" aria-label="Buka ruang ${escape(agent.name)}">Lihat ruang ↗</button></td></tr>`).join('');
    $('floorplan').querySelectorAll('[data-id]').forEach(button=>button.addEventListener('click',()=>chooseAgent(button.dataset.id,true)));
    $('team-body').querySelectorAll('[data-open-agent]').forEach(button=>button.addEventListener('click',()=>{switchView('denah');chooseAgent(button.dataset.openAgent,true);}));
    if(focused) $('floorplan').querySelector(`[data-id="${CSS.escape(focused)}"]`)?.focus({preventScroll:true});
    window.Office3D?.update(agents);
    window.Office3D?.select(state.selected,false);
    renderInspector();
  }
  function renderInspector() {
    const agent=state.data.office.agents.find(agent=>agent.id===state.selected);
    if(!agent) {$('inspector').textContent='Belum ada data agen.';return;}
    $('inspector').innerHTML=`<div class="inspector-overview"><span class="eyebrow">RUANG ${escape(agent.room)} / ${escape(agent.group)}</span><h2 class="inspector-name">${escape(agent.name)}</h2><p class="inspector-role">${escape(agent.role)}</p>${runtime(agent)}<p class="inspector-description">${escape(agent.description)}</p><p class="agent-limit">${escape(agent.limitation)}</p><p class="model-label">${escape(modelLabel(agent.model))} · terkonfigurasi</p></div><section class="inspector-section" aria-label="Tanggung jawab"><h3>Fokus pekerjaan</h3><ul class="responsibilities">${agent.responsibilities.map(item=>`<li>${escape(item)}</li>`).join('')}</ul></section><section class="inspector-section" aria-label="Kesiapan agen"><h3>Catatan kesiapan</h3><dl class="check-list">${agent.checks.map(check=>`<div class="check-row"><dt>${escape(check.label)}</dt><dd>${escape(check.value)}</dd></div>`).join('')}</dl></section>`;
  }
  function renderActivity() {
    const data=state.data;
    const names=Object.fromEntries(data.office.agents.map(agent=>[agent.id,agent.short_name]));
    const jobStates={completed:'Generasi selesai',running:'Generasi sedang berjalan',submitted:'Generasi diajukan',awaiting_budget:'Generasi menunggu izin biaya',failed:'Generasi gagal'};
    const events=(data.recent_jobs || []).map(job=>({title:`${jobStates[job.state] || 'Catatan generasi'} · ${names[job.character_id] || job.character_id}`,detail:job.actual_credits==null?'Biaya aktual belum tercatat':`${number(job.actual_credits)} kredit terpakai · ${job.model || 'model belum tercatat'}`,time:job.created_at,mark:'G'}));
    (data.recent_approvals || []).forEach(approval=>events.push({title:approval.decision==='approved'?'Paket konten disetujui':'Keputusan review tersimpan',detail:'Keputusan tercatat melalui '+(approval.channel==='telegram'?'Telegram':approval.channel || 'kanal review')+'. Publikasi diperiksa terpisah.',time:approval.created_at,mark:'A'}));
    events.sort((a,b)=>(Date.parse(b.time)||0)-(Date.parse(a.time)||0));
    $('activity-list').innerHTML=events.length?events.slice(0,10).map(event=>`<li class="activity-item"><span class="event-mark" aria-hidden="true">${event.mark}</span><div><h3 class="event-title">${escape(event.title)}</h3><p class="event-detail">${escape(event.detail)}</p></div><time class="event-date">${escape(date(event.time,true))}</time></li>`).join(''):'<li class="empty-state">Belum ada aktivitas yang tercatat.</li>';
    const permissions=data.office.permissions;
    const details=[['Generasi baru',permissions.generation_enabled?'Diizinkan':'Nonaktif'],['Publikasi',permissions.publication_enabled?'Diizinkan':'Menunggu izin'],['Jadwal rutin',permissions.scheduler_enabled?'Aktif':'Nonaktif'],['Paket disetujui',number(data.stats?.total_approved)]];
    $('operation-details').innerHTML=details.map(([label,value])=>`<div class="check-row"><dt>${escape(label)}</dt><dd>${escape(value)}</dd></div>`).join('');
    $('evaluation-note').innerHTML='<strong>Evaluasi mingguan</strong>Laporan disusun terpisah. Tampilan kantor ini tidak memicu pengiriman atau pekerjaan baru.';
  }
  function render(data) {
    const office=data.office;
    if(!office || !Array.isArray(office.agents)) throw new Error('office_data_unavailable');
    $('access-screen').hidden=true;
    $('office-app').hidden=false;
    window.Office3D?.setVisible(state.view==='denah');
    state.data=data;
    const signature=JSON.stringify(office.agents);
    if(signature!==state.agentSignature){state.agentSignature=signature;renderAgents();}
    $('metric-agents').textContent=number(office.agents.length);
    $('metric-active').textContent=number(office.runtime.active_agents);
    $('metric-pending').textContent=number(Array.isArray(data.pending_accs)?data.pending_accs.length:null);
    $('operation-mode').textContent=office.permissions.scheduler_enabled?'Jadwal aktif':'Operasi manual';
    $('overview-note').textContent=office.runtime.active_agents===0?'Belum ada tugas berjalan.':typeof office.runtime.active_agents==='number'?'Pekerjaan sedang berlangsung.':'Status pekerjaan belum terkonfirmasi.';
    $('flow-balance').textContent=number(office.flow.balance);
    $('flow-as-of').textContent=office.flow.verified_at?`Diverifikasi ${date(office.flow.verified_at)} · ${office.flow.account}`:'Saldo belum diverifikasi';
    $('pilot-used').textContent=number(office.pilot.spent);
    $('pilot-cap').textContent=`dari ${number(office.pilot.cap)} kredit`;
    $('publication-state').textContent=office.permissions.publication_enabled?'Publikasi diizinkan':'Menunggu izin pemilik';
    $('today').textContent=date(office.checked_at);
    $('last-updated').textContent='Diperbarui '+new Intl.DateTimeFormat('id-ID',{timeZone:'Asia/Jakarta',hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date())+' WIB';
    $('data-notice').hidden=office.runtime.state==='running' && !data.error;
    $('data-notice').textContent=data.error?'Sebagian data produksi belum dapat dibaca. Data yang tersedia tetap ditampilkan.':office.runtime.state==='stale'?'Heartbeat gateway belum terbarui. Status pekerjaan tidak dianggap aktif.':'Gateway belum terkonfirmasi berjalan. Hasil pengujian tetap ditampilkan terpisah.';
    renderActivity();
    $('access-screen').hidden=true;
    $('office-app').hidden=false;
    showConnection('Sinkron','connected');
  }
  async function refresh(initial=false) {
    if(state.loading) return;
    const epoch=state.epoch;
    state.loading=true;
    $('refresh').disabled=true;
    try {
      const headers=state.token?{Authorization:`Bearer ${state.token}`} : {};
      const statusUrl = state.token ? `/api/status?token=${encodeURIComponent(state.token)}` : '/api/status';
      const response=await fetch(statusUrl,{headers,credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(8000)});
      if(epoch!==state.epoch) return;
      if(response.status===401){state.data=null;state.agentSignature='';showAccess();return;}
      if(!response.ok) throw new Error('status_unavailable');
      const data=await response.json();
      if(epoch!==state.epoch) return;
      render(data);
    } catch(error) {
      if(epoch!==state.epoch) return;
      showConnection('Terputus','error');
      if(initial || !state.data) showAccess('Kantor belum dapat dihubungi. Coba masuk kembali.');
      else{$('data-notice').hidden=false;$('data-notice').textContent='Koneksi data terputus. Tampilan ini memuat hasil sinkronisasi terakhir.';}
    } finally {state.loading=false;$('refresh').disabled=false;}
  }
  $('access-form').addEventListener('submit',async event=>{
    event.preventDefault();
    const button=$('access-submit');
    button.disabled=true;
    button.querySelector('span').textContent='Memeriksa akses';
    $('access-error').textContent='';
    try {
      const response=await fetch('/api/auth',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:$('access-password').value}),signal:AbortSignal.timeout(8000)});
      const data=await response.json();
      if(!response.ok || !data.authenticated || !data.token){$('access-error').textContent='PIN atau kata sandi belum sesuai.';return;}
      state.token=data.token;
      localStorage.removeItem('kantor_ai_token');sessionStorage.removeItem('kantor_ai_token');
      ($('remember-access').checked?localStorage:sessionStorage).setItem('kantor_ai_token',state.token);
      $('access-password').value='';
      await refresh(true);
    } catch(error) {$('access-error').textContent='Koneksi belum tersedia. Silakan coba lagi.';}
    finally {button.disabled=false;button.querySelector('span').textContent='Buka kantor';}
  });
  $('toggle-password').addEventListener('click',()=>{
    const input=$('access-password');const visible=input.type==='password';
    input.type=visible?'text':'password';$('toggle-password').textContent=visible?'Tutup':'Lihat';
    $('toggle-password').setAttribute('aria-label',visible?'Sembunyikan kata sandi':'Tampilkan kata sandi');
    $('toggle-password').setAttribute('aria-pressed',String(visible));
  });
  $('lock-office').addEventListener('click',async()=>{
    $('lock-office').disabled=true;
    try {
      const response=await fetch('/api/logout',{method:'POST',credentials:'same-origin',signal:AbortSignal.timeout(8000)});
      if(!response.ok) throw new Error('logout_failed');
      state.epoch++;state.token='';state.data=null;state.agentSignature='';
      localStorage.removeItem('kantor_ai_token');sessionStorage.removeItem('kantor_ai_token');
      $('floorplan').replaceChildren();$('inspector').replaceChildren();$('team-body').replaceChildren();$('activity-list').replaceChildren();
      showAccess();$('access-password').focus();
    } catch(error) {$('data-notice').hidden=false;$('data-notice').textContent='Belum bisa mengakhiri sesi. Periksa koneksi dan coba lagi.';}
    finally {$('lock-office').disabled=false;}
  });
  const tabs=[...document.querySelectorAll('[data-view]')];
  tabs.forEach((button,index)=>{
    button.addEventListener('click',()=>switchView(button.dataset.view));
    button.addEventListener('keydown',event=>{
      let target=null;
      if(event.key==='ArrowRight') target=(index+1)%tabs.length;
      if(event.key==='ArrowLeft') target=(index-1+tabs.length)%tabs.length;
      if(event.key==='Home') target=0;
      if(event.key==='End') target=tabs.length-1;
      if(target!==null){event.preventDefault();switchView(tabs[target].dataset.view,true);}
    });
  });
  document.querySelector('.brand').addEventListener('click',event=>{event.preventDefault();switchView('denah');});
  document.addEventListener('office:select-agent',event=>chooseAgent(event.detail.id,false,false));
  document.addEventListener('office:view-change',event=>$('scene-view').textContent=event.detail.label);
  $('scene-home').addEventListener('click',()=>window.Office3D?.home());
  $('scene-zoom-in').addEventListener('click',()=>window.Office3D?.zoom(1.25));
  $('scene-zoom-out').addEventListener('click',()=>window.Office3D?.zoom(.8));
  function setSceneFocus(active) {
    const frame=$('scene-frame');
    frame.classList.toggle('is-expanded',active);
    document.body.classList.toggle('scene-focus-open',active);
    if(active){frame.setAttribute('role','dialog');frame.setAttribute('aria-modal','true');frame.setAttribute('aria-label','Kantor 3D');}
    else{frame.removeAttribute('role');frame.removeAttribute('aria-modal');frame.removeAttribute('aria-label');}
    updateFullscreenControl();
  }
  function updateFullscreenControl() {
    const active=Boolean(document.fullscreenElement)||$('scene-frame').classList.contains('is-expanded');
    $('scene-fullscreen').setAttribute('aria-label',active?'Kembali ke tampilan kantor':'Tampilkan kantor dalam layar penuh');
    $('scene-fullscreen').textContent=active?'↙':'↗';
  }
  $('scene-fullscreen').addEventListener('click',async()=>{
    const button=$('scene-fullscreen');
    button.disabled=true;
    try {
      if(document.fullscreenElement) await document.exitFullscreen();
      else if($('scene-frame').classList.contains('is-expanded')) setSceneFocus(false);
      else {
        try{await $('scene-frame').requestFullscreen();}
        catch(error){setSceneFocus(true);}
      }
    } finally {button.disabled=false;updateFullscreenControl();}
  });
  document.addEventListener('fullscreenchange',updateFullscreenControl);
  document.addEventListener('keydown',event=>{
    if(!$('scene-frame').classList.contains('is-expanded'))return;
    if(event.key==='Escape'){setSceneFocus(false);$('scene-fullscreen').focus();}
    if(event.key==='Tab'){
      const buttons=[...$('scene-frame').querySelectorAll('button:not([hidden])')];
      if(!buttons.includes(document.activeElement)||(event.shiftKey&&document.activeElement===buttons[0])){event.preventDefault();buttons[buttons.length-1].focus();}
      else if(!event.shiftKey&&document.activeElement===buttons[buttons.length-1]){event.preventDefault();buttons[0].focus();}
    }
  });
  $('refresh').addEventListener('click',()=>refresh());
  document.addEventListener('visibilitychange',()=>{if(!document.hidden && state.data) refresh();});
  setInterval(()=>{if(!document.hidden && state.data) refresh();},10000);
  refresh(true);
})();
