document.addEventListener('DOMContentLoaded', () => {
    // --- State & Constants ---
    window.currentUser = null;
    let mainChart = null;
    let systemOptions = [];
    window.systemOptions = systemOptions;
    const viewPanels = document.querySelectorAll('.view-panel');
    const navItems = document.querySelectorAll('.nav-item');

    // --- Initialization ---
    checkSession();
    loadSettings();
    loadSystemOptions();

    async function checkSession() {
        const saved = localStorage.getItem('ehsan_session');
        if (saved) {
            window.currentUser = JSON.parse(saved);
            showDashboard();
        }
    }

    async function loadSettings() {
        try {
            const res = await fetch('/api/settings');
            const s = await res.json();
            if (s.org_name) {
                document.getElementById('login-org-name').innerText = s.org_name;
                document.getElementById('side-org-name').innerText = s.org_name;
                document.getElementById('footer-org-name').innerText = s.org_name;
                document.title = s.org_name;
            }
            if (s.org_logo) { 
                document.getElementById('login-org-logo').src = s.org_logo; 
                document.getElementById('login-org-logo').style.display='block'; 
                document.getElementById('login-logo-placeholder').style.display='none';
                
                const sideLogo = document.getElementById('side-org-logo');
                if(sideLogo) { sideLogo.src = s.org_logo; sideLogo.style.display='block'; }
            }
            // Populate settings form if admin
            const sForm = document.getElementById('settings-form');
            if (sForm) {
                for (let key in s) {
                    if (sForm.elements[key]) sForm.elements[key].value = s[key];
                }
            }
            // Contacts
            const contactDiv = document.getElementById('login-contacts');
            if (contactDiv && (s.org_phone1 || s.org_phone2)) {
                contactDiv.innerHTML = `
                    ${s.org_phone1 ? `<span>📞 ${s.org_phone1}</span>` : ''} 
                    ${s.org_phone2 ? ` | <span>📞 ${s.org_phone2}</span>` : ''}
                `;
            }
        } catch (e) { console.error("Settings load failed", e); }
    }

    async function loadSystemOptions() {
        const res = await fetch('/api/options');
        systemOptions = await res.json();
        const fSelect = document.getElementById('f-status-select');
        if (fSelect) {
            const fOpts = systemOptions.filter(o => o.category === 'family_status');
            fSelect.innerHTML = fOpts.map(o => `<option value="${o.value}">${o.label}</option>`).join('') + '<option value="other">أخرى...</option>';
        }
    }

    // --- Notifications (Toasts) ---
    window.showToast = (message, type = 'success') => {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${message}</span><span class="toast-close" onclick="this.parentElement.remove()">×</span>`;
        container.appendChild(toast);
        setTimeout(() => { if(toast.parentElement) toast.remove(); }, 5000);
    };

    // --- Authentication ---
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = { username: e.target.username.value, password: e.target.password.value };
        const res = await fetch('/api/login', { method: 'POST', body: JSON.stringify(data), headers: {'Content-Type': 'application/json'} });
        const result = await res.json();
        if (res.ok) {
            window.currentUser = result;
            localStorage.setItem('ehsan_session', JSON.stringify(window.currentUser));
            showDashboard();
            showToast(`أهلاً بك، تم تسجيل الدخول بنجاح`);
        } else { showToast(result.error, 'error'); }
    });

    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('ehsan_session');
        location.reload();
    });

    function showDashboard() {
        document.getElementById('login-section').classList.add('hidden-section');
        document.getElementById('dashboard-section').classList.remove('hidden-section');
        document.getElementById('current-username').innerText = window.currentUser.name;
        document.getElementById('user-role-badge').innerText = window.currentUser.role.toUpperCase();
        
        navItems.forEach(nav => {
            const viewTarget = nav.getAttribute('data-target');
            const hasAccess = window.currentUser.role === 'admin' || (window.currentUser.permissions && window.currentUser.permissions.includes(viewTarget)) || viewTarget === 'overview-view';
            nav.style.display = hasAccess ? 'flex' : 'none';
        });

        initNotifications();
        initSearch();
        switchView('overview-view', navItems[0]);
    }

    // --- Navigation Controls ---
    navItems.forEach(item => { item.addEventListener('click', (e) => { e.preventDefault(); switchView(item.getAttribute('data-target'), item); }); });

    function switchView(targetId, activeNav = null) {
        viewPanels.forEach(p => p.classList.add('hidden-section'));
        const target = document.getElementById(targetId);
        if (target) { target.classList.remove('hidden-section'); target.classList.add('active-panel'); }
        
        navItems.forEach(n => n.classList.remove('active'));
        if (activeNav) activeNav.classList.add('active');

        if (targetId === 'overview-view') loadStats();
        if (targetId === 'entry-view') loadTableData('beneficiaries', 'entry-table-container');
        if (targetId === 'user-approvals-view') loadTeamView();
        if (targetId === 'settings-view') { renderOptionsList(); }
        if (targetId === 'research-view') loadResearchView();
        if (targetId === 'sharia-view') loadShariaView();
        if (targetId === 'finance-view') loadFinanceView();
    }

    // --- Dashboard Stats (v2.2.2 Square Cards) ---
    async function loadStats() {
        const res = await fetch('/api/stats');
        const d = await res.json();
        document.getElementById('s-total').innerText = d.total;
        document.getElementById('s-pending').innerText = d.pending;
        document.getElementById('s-sharia').innerText = d.sharia;
        document.getElementById('s-approved').innerText = d.approved;
        
        const ctx = document.getElementById('main-chart').getContext('2d');
        if (mainChart) mainChart.destroy();
        mainChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['الإجمالي', 'البحث', 'اللجنة', 'المعتمد'],
                datasets: [{ label: 'توزيع الحالات', data: [d.total, d.pending, d.sharia, d.approved], borderColor: '#0d9488', fill: true, backgroundColor: 'rgba(13, 148, 136, 0.1)' }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    }

    // --- Beneficiary Entry Logic ---
    window.openBenModal = () => {
        document.getElementById('add-beneficiary-form').reset();
        document.getElementById('f-other-wrap').style.display = 'none';
        document.getElementById('beneficiary-modal').classList.add('active');
    };

    document.getElementById('f-status-select')?.addEventListener('change', (e) => {
        document.getElementById('f-other-wrap').style.display = e.target.value === 'other' ? 'block' : 'none';
    });

    document.getElementById('add-beneficiary-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        payload = Object.fromEntries(new FormData(e.target).entries());
        payload.requester_id = window.currentUser ? window.currentUser.id : null;
        const res = await fetch('/api/beneficiaries', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type': 'application/json'} });
        const resData = await res.json();
        if (res.ok) {
            showToast(resData.message);
            document.getElementById('beneficiary-modal').classList.remove('active');
            loadTableData('beneficiaries', 'entry-table-container');
        } else { showToast(resData.error, 'error'); }
    });

    // --- Lifecycle Actions (Sharia / Finance Fixing) ---

    // 1. Research / Visit Logic
    async function loadResearchView() {
        const res = await fetch('/api/beneficiaries');
        const data = (await res.json()).filter(b => b.status === 'pending_research');
        renderActionTable('بحث ميداني وتدقيق الحالات', data, 'research-table-container', 'تدقيق البيانات', 'openResearchModal');
    }

    window.openResearchModal = (bid) => {
        const cats = systemOptions.filter(o => o.category === 'case_type');
        renderGenericModal('توثيق الزيارة وتصنيف الحالة', `
            <div class="input-group"><label>تصنيف الحالة الفني</label><select id="r-cat">${cats.map(c => `<option value="${c.label}">${c.label}</option>`).join('')}</select></div>
            <div class="input-group"><label>ملاحظات الباحث الاجتماعية</label><textarea id="r-notes" rows="4"></textarea></div>
            <button class="btn-primary" style="width:100%;" onclick="submitResearch(${bid})">إحالة للجنة الشرعية ⚖️</button>
        `);
    };

    window.submitResearch = async (bid) => {
        const payload = { beneficiaryId: bid, notes: document.getElementById('r-notes').value, case_type: document.getElementById('r-cat').value, userId: window.currentUser.id };
        const res = await fetch('/api/research/verify', { method:'POST', body: JSON.stringify(payload), headers:{'Content-Type':'application/json'} });
        if (res.ok) { showToast("تم التوثيق والإحالة حوزت اللجنة."); document.getElementById('generic-modal').classList.remove('active'); loadResearchView(); }
    };

    // 2. Sharia Logic (Fixing buttons)
    async function loadShariaView() {
        const res = await fetch('/api/beneficiaries');
        const data = (await res.json()).filter(b => b.status === 'pending_sharia');
        renderActionTable('دراسة اللجنة الشرعية والفتوى', data, 'sharia-table-container', 'إصدار القرار', 'openShariaModal');
    }

    window.openShariaModal = (bid) => {
        renderGenericModal('اتخاذ قرار اللجنة الشرعية', `
            <div class="input-group"><label>نص الفتوى أو القرار</label><textarea id="s-fatwa" rows="4" placeholder="اكتب مبررات القرار هنا..."></textarea></div>
            <div class="form-row">
                <button class="btn-primary" style="background:var(--success);" onclick="submitSharia(${bid}, 'approve')">اعتماد الملف ✅</button>
                <button class="btn-primary" style="background:var(--danger);" onclick="submitSharia(${bid}, 'reject')">رفض الملف ❌</button>
            </div>
        `);
    };

    window.submitSharia = async (bid, dec) => {
        const payload = { beneficiaryId: bid, decision: dec, fatwa: document.getElementById('s-fatwa').value, userId: window.currentUser.id };
        const res = await fetch('/api/sharia/approve', { method:'POST', body: JSON.stringify(payload), headers:{'Content-Type':'application/json'} });
        if (res.ok) { showToast("تم تسجيل قرار اللجنة."); document.getElementById('generic-modal').classList.remove('active'); loadShariaView(); }
    };

    // 3. Finance Logic (Fixing Disbursement)
    async function loadFinanceView() {
        const res = await fetch('/api/beneficiaries');
        const data = (await res.json()).filter(b => b.status === 'approved');
        renderActionTable('مالية المنظومة وصرف الإعانات', data, 'finance-table-container', 'صرف إعانة / واصل', 'openFinanceModal');
    }

    window.openFinanceModal = async (bid) => {
        const aidsRes = await fetch('/api/aid_types');
        const aids = await aidsRes.json();
        renderGenericModal('تأكيد صرف إعانة مالية', `
            <div class="input-group"><label>اختر نوع الإعانة</label><select id="f-aid">${aids.map(a => `<option value="${a.id}">${a.name} (${a.amount} ل.د)</option>`).join('')}</select></div>
            <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:15px;">سيتم إصدار وصل صرف مالي وتوثيقه في سجل المستفيد فور الضغط على تأكيد.</p>
            <button class="btn-primary" style="width:100%;" onclick="submitFinance(${bid})">تأكيد الصرف وإصدار الواصل 💰</button>
        `);
    };

    window.submitFinance = async (bid) => {
        const aidId = document.getElementById('f-aid').value;
        const res = await fetch('/api/distributions', { method:'POST', body: JSON.stringify({ beneficiaryId: bid, aidId: aidId, userId: window.currentUser.id }), headers:{'Content-Type':'application/json'} });
        if (res.ok) { showToast("تم الصرف بنجاح."); document.getElementById('generic-modal').classList.remove('active'); loadFinanceView(); }
    };

    // --- Admin Internal Operations v2.2.2 ---
    document.getElementById('internal-user-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target).entries());
        data.requester_id = window.currentUser ? window.currentUser.id : null;
        const res = await fetch('/api/users/add', { method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'} });
        const result = await res.json();
        if (res.ok) { 
            showToast(result.message); 
            document.getElementById('internal-user-modal').classList.remove('active'); 
            loadTeamView(); 
        } else { showToast(result.error, 'error'); }
    });

    document.getElementById('permissions-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const uid = document.getElementById('perm-user-id').value;
        const checkboxes = document.querySelectorAll('#permissions-form input[name="perms"]:checked');
        const perms = Array.from(checkboxes).map(cb => cb.value);
        
        const res = await fetch('/api/users/update_permissions', {
            method: 'POST',
            body: JSON.stringify({ id: uid, permissions: perms, requester_id: window.currentUser ? window.currentUser.id : null }),
            headers: {'Content-Type': 'application/json'}
        });
        if (res.ok) {
            showToast("تم تخصيص الصلاحيات وحفظ الجدار الناري بنجاح 🛡️");
            document.getElementById('permissions-modal').classList.remove('active');
            loadTeamView();
        } else {
            showToast("صلاحية مقيدة: هذا الإجراء مقصور على المدير العام.", "error");
        }
    });

    document.getElementById('forgot-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target).entries());
        const res = await fetch('/api/forgot_password', { method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'} });
        if (res.ok) {
            showToast("تم إرسال طلبك للإدارة، سيتم معالجته قريباً.");
            document.getElementById('forgot-modal').classList.remove('active');
        } else { showToast("فشل الإرسال", "error"); }
    });

    document.getElementById('settings-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target).entries());
        const res = await fetch('/api/settings', { method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'} });
        if (res.ok) { showToast("تم تحديث كافة بيانات المؤسسة والهوية."); loadSettings(); }
    });

    // --- Shared UI Helpers ---
    function renderActionTable(title, data, containerId, btnText, btnActionName) {
        const cont = document.getElementById(containerId);
        cont.innerHTML = `<h2>${title}</h2><div class="table-container">` +
            `<table class="data-table"><thead><tr><th>الاسم</th><th>الرقم الوطني</th><th>إجراء</th></tr></thead><tbody>` +
            data.map(b => `<tr><td>${b.name}</td><td><code>${b.national_id}</code></td><td><button class="btn-primary" style="padding:6px 12px; font-size:0.8rem;" onclick="${btnActionName}(${b.id})">${btnText}</button></td></tr>`).join('') +
            `</tbody></table></div>`;
    }

    function renderGenericModal(title, html) {
        const m = document.getElementById('generic-modal');
        const content = document.getElementById('generic-modal-content');
        content.innerHTML = `<h3>${title}</h3><hr style="margin:15px 0; opacity:0.1;">${html}`;
        m.classList.add('active');
    }

    window.openTimeline = async (bid) => {
        const res = await fetch(`/api/beneficiaries/${bid}/history`);
        const history = await res.json();
        const m = document.getElementById('timeline-modal');
        const cont = document.getElementById('timeline-content');
        cont.innerHTML = history.map(h => `
            <div class="timeline-item"> <div class="t-dot"></div> <div class="t-content">
                <div class="t-time">${new Date(h.date).toLocaleString('ar-LY')}</div>
                <div class="t-title">${h.action}</div> <div style="font-size:0.85rem;">${h.notes}</div>
            </div></div>`).join('') || 'لا سجلات لهذا الملف.';
        m.classList.add('active');
    };

    window.generateReportPreview = async () => {
        const type = document.getElementById('rep-type').value;
        const res = await fetch(`/api/${type}`);
        let data = await res.json();
        const from = document.getElementById('rep-from').value;
        const to = document.getElementById('rep-to').value;
        if (from) data = data.filter(d => new Date(d.created_at || d.date) >= new Date(from));
        if (to) data = data.filter(d => new Date(d.created_at || d.date) <= new Date(to));
        renderBeneficiaryTable(data, 'report-preview-container', true);
    };

    // --- Other Logic ---
    function initSearch() {
        const input = document.getElementById('global-search');
        input.addEventListener('input', debounce(async (e) => {
            const res = await fetch(`/api/search?q=${e.target.value}`);
            const data = await res.json();
            renderBeneficiaryTable(data, 'entry-table-container');
        }, 400));
    }

    function initNotifications() { setInterval(window.fetchNotifs, 20000); window.fetchNotifs(); }

    window.fetchNotifs = async function() {
        if (!window.currentUser) return;
        const role = window.currentUser.role;
        try {
            const res = await fetch(`/api/notifications?role=${encodeURIComponent(role)}`);
            if (!res.ok) return;
            const n = await res.json();

            // Badge: show count or hide
            const badge = document.getElementById('notif-count');
            if (n.length > 0) { badge.innerText = n.length; badge.style.display = 'inline-block'; }
            else { badge.innerText = ''; badge.style.display = 'none'; }

            const listEl = document.getElementById('notif-list');
            if (n.length === 0) {
                listEl.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:0.85rem;padding:15px;">لا توجد إشعارات جديدة ✅</div>';
                return;
            }

            // Role-to-view navigation map
            const roleViewMap = {
                researcher: 'research-view',
                sharia_committee: 'sharia-view',
                finance: 'finance-view',
                admin: 'user-approvals-view'
            };
            const roleLabels = {
                admin: '👤 مدير', researcher: '🏚️ باحث',
                sharia_committee: '⚖️ شرعية', finance: '💰 مالية'
            };

            listEl.innerHTML = n.map((x, i) => {
                const time = x.created_at ? new Date(x.created_at).toLocaleString('ar-LY') : '';
                const targetView = roleViewMap[x.target_role] || 'overview-view';
                // For admin: show which role this notification belongs to
                const roleTag = (role === 'admin' && x.target_role)
                    ? `<span style="background:#e2e8f0;border-radius:4px;font-size:0.66rem;padding:1px 5px;color:#475569;margin-right:3px;">${roleLabels[x.target_role] || x.target_role}</span>`
                    : '';
                const sep = i < n.length - 1
                    ? '<hr style="margin:7px 0;border:none;border-top:1px solid #e2e8f0;">'
                    : '';
                return `<div onclick="window.navigateFromNotif('${targetView}')"
                    style="padding:6px 4px;cursor:pointer;border-radius:5px;transition:background .15s;"
                    onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='transparent'">
                    <div style="font-size:0.82rem;line-height:1.4;">${roleTag}${x.message}</div>
                    <div style="display:flex;justify-content:space-between;margin-top:3px;">
                        <span style="font-size:0.68rem;color:#94a3b8;">${time}</span>
                        <span style="font-size:0.68rem;color:var(--primary);font-weight:700;">→ انتقال</span>
                    </div>
                </div>${sep}`;
            }).join('');
        } catch(e) { console.error('fetchNotifs error:', e); }
    };

    window.clearAllNotifs = async () => {
        if (!window.currentUser) return;
        const role = window.currentUser.role;
        const r = await fetch('/api/notifications/clear', {
            method: 'POST',
            body: JSON.stringify({ role }),
            headers: { 'Content-Type': 'application/json' }
        });
        if (r.ok) {
            await window.fetchNotifs();
            showToast('تم مسح إشعاراتك – باقي الفريق لم يتأثر ✅');
        }
    };

    window.navigateFromNotif = (targetView) => {
        document.getElementById('notif-dropdown')?.classList.remove('active');
        const navItem = document.querySelector(`.nav-item[data-target="${targetView}"]`);
        if (navItem && navItem.style.display !== 'none') {
            switchView(targetView, navItem);
        } else {
            showToast('لا تملك صلاحية الدخول لهذه الشاشة.', 'error');
        }
    };


    // --- Modals, Dropdowns & Logo Events v2.2.3 ---
    document.getElementById('register-user-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target).entries());
        const res = await fetch('/api/register', { method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'} });
        const result = await res.json();
        if (res.ok) { 
            showToast("تم إرسال طلب الانضمام، وهو الآن قيد مراجعة الإدارة."); 
            document.getElementById('register-modal').classList.remove('active'); 
        } else { showToast(result.error || "خطأ في الإرسال", 'error'); }
    });

    const logoUpload = document.getElementById('org-logo-upload');
    if(logoUpload) {
        logoUpload.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if(file) {
                const reader = new FileReader();
                reader.onloadend = () => {
                    document.getElementById('org-logo-hidden').value = reader.result;
                    showToast("تم قراءة صورة الشعار، لا تنسَ الضغط على 'حفظ'.");
                };
                reader.readAsDataURL(file);
            }
        });
    }

    window.toggleNotif = () => document.getElementById('notif-dropdown')?.classList.toggle('active');

    function debounce(f, w) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => f.apply(this,a), w); }; }
    window.togglePass = (id) => { const x = document.getElementById(id); x.type = x.type==='password'?'text':'password'; };
    
    window.addEventListener('click', (e) => { 
        if(!e.target.closest('.notif-wrapper') && !e.target.closest('#bell-btn')) {
            document.getElementById('notif-dropdown')?.classList.remove('active');
        }
        if(e.target.classList.contains('modal')) e.target.classList.remove('active'); 
    });
});

async function loadTableData(type, containerId) {
    const res = await fetch(`/api/${type}`);
    renderBeneficiaryTable(await res.json(), containerId);
}

function renderBeneficiaryTable(data, containerId, canDownload = false) {
    const cont = document.getElementById(containerId);
    if (!cont) return;
    cont.innerHTML = `<table class="data-table"><thead><tr><th>الرقم الوطني</th><th>الاسم</th><th>الحالة</th><th>إجراء</th></tr></thead><tbody>` +
        data.map(r => `<tr onclick="openTimeline(${r.id})"><td><code>${r.national_id}</code></td><td><strong>${r.name}</strong></td><td><span class="badge ${r.status}">${r.status}</span></td><td><button class="btn-primary" style="padding:4px 8px; font-size:0.75rem;">السجل 🛡️</button></td></tr>`).join('') +
        `</tbody></table>` + (canDownload ? `<button class="btn-primary" style="margin-top:15px;" onclick="window.print()">طباعة التقرير 📥</button>` : '');
}

async function loadTeamView() {
    const res = await fetch('/api/users/all');
    const users = await res.json();
    document.getElementById('user-approvals-body').innerHTML = users.map(u => {
        const actionBtn = u.status === 'pending' 
            ? `<button class="btn-primary" style="background:var(--success); padding:6px 12px; font-size:0.8rem;" onclick="approveUser(${u.id}, 'approve')">اعتماد ✌️</button>`
            : `<div style="display:flex; gap:5px;"><button class="btn-primary" style="padding:4px 8px; font-size:0.75rem;" onclick="openUserEdit(${u.id})">حالة/تعديل ⚙️</button><button class="btn-primary" style="padding:4px 8px; font-size:0.75rem; background:#334155;" onclick="openPermissionsEditor(${u.id})">واجهات 🛡️</button></div>`;
        return `<tr><td>${u.name}</td><td><code>${u.username}</code></td>
        <td style="cursor:pointer;" onclick="this.innerText='${u.password}'"><span style="background:var(--bg); border:1px solid var(--border); padding:2px 8px; border-radius:4px; color:var(--text-muted); font-size:0.8rem;">إظهار 👀</span></td>
        <td>${u.role}</td><td><span class="badge ${u.status}">${u.status}</span></td><td>${actionBtn}</td></tr>`;
    }).join('');
}

window.approveUser = async (uid, dec) => {
    const res = await fetch('/api/users/approve', {
        method: 'POST',
        body: JSON.stringify({ id: uid, decision: dec, requester_id: window.currentUser ? window.currentUser.id : null }),
        headers: {'Content-Type': 'application/json'}
    });
    if (res.ok) {
        showToast("تم الاعتماد بنجاح، يرجى تحديد صلاحيات الشاشات.");
        loadTeamView();
        openPermissionsEditor(uid);
    } else {
        const err = await res.json().catch(()=>({}));
        showToast(err.error || "مرفوض: للمدير فقط", "error");
    }
};

window.openPermissionsEditor = async (uid) => {
    const res = await fetch('/api/users/all');
    const user = (await res.json()).find(u => u.id === uid);
    document.getElementById('perm-user-name').innerText = user.name;
    document.getElementById('perm-user-id').value = uid;
    
    const checkboxes = document.querySelectorAll('#permissions-form input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = user.permissions && user.permissions.includes(cb.value);
    });
    
    document.getElementById('permissions-modal').classList.add('active');
};

window.openUserEdit = async (uid) => {
    const res = await fetch('/api/users/all');
    const user = (await res.json()).find(u => u.id === uid);
    const m = document.getElementById('generic-modal');
    const content = document.getElementById('generic-modal-content');
    content.innerHTML = `
        <h3>تعديل بيانات המوظف (${user.name})</h3>
        <form id="edit-user-form">
            <input type="hidden" name="id" value="${user.id}">
            <div class="form-row">
                <div class="input-group"><label>الاسم الإداري</label><input type="text" name="name" value="${user.name}"></div>
                <div class="input-group"><label>كلمة السر (يمكن التعديل)</label><input type="text" name="password" value="${user.password}"></div>
            </div>
            <div class="form-row">
                <div class="input-group"><label>الدور الوظيفي</label><select name="role"><option value="admin" ${user.role==='admin'?'selected':''}>مدير</option><option value="researcher" ${user.role==='researcher'?'selected':''}>باحث اجتماعي</option><option value="sharia_committee" ${user.role==='sharia_committee'?'selected':''}>لجنة شرعية</option><option value="finance" ${user.role==='finance'?'selected':''}>لجنة مالية</option></select></div>
                <div class="input-group"><label>حالة الاعتماد</label><select name="status"><option value="active" ${user.status==='active'?'selected':''}>نشط ومُعتمد</option><option value="pending" ${user.status==='pending'?'selected':''}>بالانتظار (Pending)</option><option value="inactive" ${user.status==='inactive'?'selected':''}>معطل ❌</option></select></div>
            </div>
            <button type="submit" class="btn-primary" style="width:100%; margin-top:15px;">حفظ واعتماد التعديلات 💾</button>
        </form>
    `;
    m.classList.add('active');
    document.getElementById('edit-user-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = Object.fromEntries(new FormData(e.target).entries());
        payload.requester_id = window.currentUser ? window.currentUser.id : null;
        const r = await fetch('/api/users/update', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type': 'application/json'} });
        if (r.ok) {
            showToast("تم تحديث واعتماد الموظف بنجاح.");
            m.classList.remove('active');
            loadTeamView();
        } else {
            const err = await r.json().catch(()=>({}));
            showToast(err.error || "فشل الحفظ، تحقق من صلاحيات المدير.", "error");
        }
    });
};

function renderOptionsList() {
    const cont = document.getElementById('options-list-table');
    cont.innerHTML = `<table class="data-table"><thead><tr><th>التصنيف</th><th>المسمى</th></tr></thead><tbody>` +
        window.systemOptions.map(o => `<tr><td>${o.category}</td><td>${o.label}</td></tr>`).join('') + `</tbody></table>`;
}
