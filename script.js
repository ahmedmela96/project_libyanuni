document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const navItems = document.querySelectorAll('.nav-item');
    const viewPanels = document.querySelectorAll('.view-panel');
    const userRoleBadge = document.getElementById('user-role-badge');
    const currentUsernameTxt = document.getElementById('current-username');
    const currentDateTxt = document.getElementById('current-date');

    // --- State ---
    let currentUser = null;

    // --- Date Init ---
    if (currentDateTxt) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        currentDateTxt.innerText = new Date().toLocaleDateString('ar-LY', options);
    }

    // --- Authentication ---
    checkSession();

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = { username: loginForm.username.value, password: loginForm.password.value };
        try {
            const res = await fetch('/api/login', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } });
            const result = await res.json();
            if (res.ok) {
                currentUser = result;
                localStorage.setItem('ehsan_session', JSON.stringify(currentUser));
                showDashboard();
            } else { alert(result.error || 'فشل الدخول'); }
        } catch (err) { alert('خطأ في الاتصال بالخادم'); }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('ehsan_session');
        location.reload();
    });

    function checkSession() {
        const saved = localStorage.getItem('ehsan_session');
        if (saved) {
            currentUser = JSON.parse(saved);
            showDashboard();
        }
    }

    function showDashboard() {
        loginSection.classList.add('hidden-section');
        dashboardSection.classList.remove('hidden-section');
        currentUsernameTxt.innerText = currentUser.name;
        userRoleBadge.innerText = currentUser.role.toUpperCase();
        userRoleBadge.className = `badge role-${currentUser.role}`;

        // Role-based visibility
        document.querySelectorAll('.nav-item').forEach(el => {
            if (!el.classList.contains(`role-${currentUser.role}`) && !el.classList.contains('role-admin')) {
                el.style.display = 'none';
            } else {
                el.style.display = 'flex';
            }
        });

        loadStats();
        switchView('overview-view');
    }

    // --- Navigation ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(item.getAttribute('data-target'), item);
        });
    });

    async function switchView(targetId, activeItem = null) {
        viewPanels.forEach(p => p.classList.add('hidden-section'));
        viewPanels.forEach(p => p.classList.remove('active-panel'));
        
        const panel = document.getElementById(targetId);
        if (panel) { panel.classList.remove('hidden-section'); panel.classList.add('active-panel'); }
        
        navItems.forEach(i => i.classList.remove('active'));
        if (activeItem) activeItem.classList.add('active');

        // Data Loading per View
        if (targetId === 'overview-view') loadStats();
        if (targetId === 'entry-view') loadEntryTable();
        if (targetId === 'research-view') loadResearchTable();
        if (targetId === 'sharia-view') loadShariaTable();
        if (targetId === 'finance-view') loadFinanceTable();
        if (targetId === 'users-view') loadUsersTable();
    }

    // --- Data Loaders ---

    async function loadStats() {
        try {
            const res = await fetch('/api/stats');
            const d = await res.json();
            document.getElementById('s-total').innerText = d.total;
            document.getElementById('s-pending').innerText = d.pending;
            document.getElementById('s-sharia').innerText = d.sharia;
            document.getElementById('s-approved').innerText = d.approved;
        } catch (e) {}
    }

    async function loadEntryTable() {
        const tbody = document.getElementById('entry-table-body');
        const res = await fetch('/api/beneficiaries');
        const data = await res.json();
        tbody.innerHTML = data.map(b => `
            <tr>
                <td><strong>${b.name}</strong></td>
                <td><code>${b.national_id}</code></td>
                <td><span class="badge" style="background:#f1f5f9;">${translateStatus(b.status)}</span></td>
                <td style="font-size:0.8rem;">${new Date(b.created_at).toLocaleDateString('ar-LY')}</td>
            </tr>
        `).join('');
    }

    async function loadResearchTable() {
        const tbody = document.getElementById('research-table-body');
        const res = await fetch('/api/beneficiaries');
        const data = await res.json();
        const pending = data.filter(b => b.status === 'pending_research');
        tbody.innerHTML = pending.map(b => `
            <tr>
                <td><strong>${b.name}</strong></td>
                <td>${b.address}</td>
                <td><span class="score-badge">${b.need_score.toFixed(1)}</span></td>
                <td><button class="btn-primary" style="padding:6px 12px; font-size:0.8rem;" onclick="openResearchModal(${b.id})">توثيق الزيارة</button></td>
            </tr>
        `).join('') || '<tr><td colspan="4" style="text-align:center;">لا توجد مهام ميدانية حالياً</td></tr>';
    }

    async function loadShariaTable() {
        const tbody = document.getElementById('sharia-table-body');
        const res = await fetch('/api/beneficiaries');
        const data = await res.json();
        const pending = data.filter(b => b.status === 'pending_sharia');
        tbody.innerHTML = pending.map(b => `
            <tr>
                <td><strong>${b.name}</strong></td>
                <td style="font-size:0.85rem; max-width:300px;">${b.researcher_notes}</td>
                <td><span class="score-badge">${b.need_score.toFixed(1)}</span></td>
                <td><button class="btn-primary" style="padding:6px 12px; font-size:0.8rem;" onclick="openShariaModal(${b.id}, '${b.researcher_notes}')">إصدار فتوى</button></td>
            </tr>
        `).join('') || '<tr><td colspan="4" style="text-align:center;">لا توجد طلبات بانتظار الفتوى</td></tr>';
    }

    async function loadFinanceTable() {
        const tbody = document.getElementById('finance-table-body');
        const res = await fetch('/api/distributions_full');
        const data = await res.json();
        tbody.innerHTML = data.map(d => `
            <tr>
                <td><strong>${d.b_name}</strong></td>
                <td><span class="badge role-clerk">${d.a_name}</span></td>
                <td>${new Date(d.date).toLocaleDateString('ar-LY')}</td>
                <td>${d.u_name}</td>
            </tr>
        `).join('') || '<tr><td colspan="4" style="text-align:center;">لا توجد عمليات صرف مسجلة</td></tr>';
    }

    async function loadUsersTable() {
        const tbody = document.getElementById('users-table-body');
        const res = await fetch('/api/users');
        const data = await res.json();
        tbody.innerHTML = data.map(u => `
            <tr>
                <td>${u.name}</td>
                <td><code>${u.username}</code></td>
                <td><span class="badge role-${u.role}">${u.role.toUpperCase()}</span></td>
                <td>${new Date(u.created_at).toLocaleDateString('ar-LY')}</td>
            </tr>
        `).join('');
    }

    // --- Helper Functions ---

    window.openResearchModal = (bid) => {
        const modal = document.getElementById('research-modal');
        modal.querySelector('input[name="bid"]').value = bid;
        modal.classList.add('active');
    };

    window.openShariaModal = (bid, notes) => {
        const modal = document.getElementById('sharia-modal');
        modal.querySelector('input[name="bid"]').value = bid;
        document.getElementById('research-summary-text').innerText = `تقرير الباحث: ${notes}`;
        modal.classList.add('active');
    };

    window.submitSharia = async (decision) => {
        const form = document.getElementById('approve-sharia-form');
        const bid = form.bid.value;
        const fatwa = form.fatwa.value;
        const res = await fetch('/api/sharia/approve', {
            method: 'POST',
            body: JSON.stringify({ beneficiaryId: bid, decision, fatwa }),
            headers: { 'Content-Type': 'application/json' }
        });
        if (res.ok) { 
            alert('تم تسجيل القرار الشرعي بنجاح'); 
            document.getElementById('sharia-modal').classList.remove('active');
            loadShariaTable(); loadStats(); 
        }
    };

    function translateStatus(s) {
        const map = { 'pending_research': 'قيد البحث الميداني', 'pending_sharia': 'قيد الفتوى', 'approved': 'معتمد ✅', 'rejected': 'مرفوض ❌' };
        return map[s] || s;
    }

    // --- Form Handlers ---

    document.getElementById('verify-research-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = { beneficiaryId: e.target.bid.value, notes: e.target.notes.value };
        const res = await fetch('/api/research/verify', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } });
        if (res.ok) { alert('تم التوثيق والمتابعة'); document.getElementById('research-modal').classList.remove('active'); loadResearchTable(); loadStats(); }
    });

    document.getElementById('add-beneficiary-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target).entries());
        const res = await fetch('/api/beneficiaries', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } });
        const result = await res.json();
        if (res.ok) { alert(result.message); document.getElementById('beneficiary-modal').classList.remove('active'); loadEntryTable(); loadStats(); e.target.reset(); }
        else { alert(result.error); }
    });

    document.getElementById('btn-distribute')?.addEventListener('click', async () => {
        const bRes = await fetch('/api/beneficiaries');
        const beneficiaries = await bRes.json();
        const aRes = await fetch('/api/aid_types');
        const aidTypes = await aRes.json();

        // Financial aids ONLY for approved families, unless immediate
        document.getElementById('select-beneficiary').innerHTML = beneficiaries.map(b => `<option value="${b.id}">${b.name} (${translateStatus(b.status)})</option>`).join('');
        document.getElementById('select-aid').innerHTML = aidTypes.map(a => `<option value="${a.id}">${a.name} ${a.requires_approval ? '🕒 مشروطة' : '🚀 فورية'}</option>`).join('');
        document.getElementById('distribution-modal').classList.add('active');
    });

    document.getElementById('new-distribution-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = { beneficiaryId: e.target.beneficiaryId.value, aidId: e.target.aidId.value, userId: currentUser.id };
        const res = await fetch('/api/distributions', { method: 'POST', body: JSON.stringify(data), headers: {'Content-Type':'application/json'} });
        const result = await res.json();
        if (res.ok) { alert(result.message); document.getElementById('distribution-modal').classList.remove('active'); loadFinanceTable(); loadStats(); }
        else { alert(result.error); }
    });

    document.getElementById('add-user-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target).entries());
        const res = await fetch('/api/users', { method: 'POST', body: JSON.stringify(data), headers: {'Content-Type':'application/json'} });
        if (res.ok) { alert('تم منح الصلاحية بنجاح'); document.getElementById('user-modal').classList.remove('active'); loadUsersTable(); e.target.reset(); }
    });

    // --- Global Search ---
    const searchInp = document.getElementById('global-search');
    searchInp.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const res = await fetch(`/api/search?q=${encodeURIComponent(searchInp.value)}`);
            const data = await res.json();
            const cont = document.getElementById('search-result-container');
            cont.innerHTML = data.map(b => `
                <div style="background:#f8fafc; padding:20px; border-radius:12px; margin-bottom:12px; border:1px solid #e2e8f0;">
                    <h3>${b.name}</h3>
                    <p>الرقم الوطني: <code>${b.national_id}</code></p>
                    <p>الحالة: <strong>${translateStatus(b.status)}</strong></p>
                    <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;">${b.sharia_fatwa || ''}</div>
                </div>
            `).join('') || '<p>لا توجد نتائج</p>';
            document.getElementById('search-modal').classList.add('active');
        }
    });

    // Closing modals
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mId = btn.getAttribute('data-close');
            document.getElementById(mId).classList.remove('active');
        });
    });

    window.addEventListener('click', (e) => { if (e.target.classList.contains('modal')) e.target.classList.remove('active'); });
});
