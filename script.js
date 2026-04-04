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
    const avatarInitial = document.getElementById('avatar-initial');
    const currentDateTxt = document.getElementById('current-date');

    // --- Modals ---
    const closeBtns = document.querySelectorAll('.close-btn');
    const addBeneficiaryForm = document.getElementById('add-beneficiary-form');
    const addUserForm = document.getElementById('add-user-form');
    const newDistributionForm = document.getElementById('new-distribution-form');

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
        const data = {
            username: loginForm.username.value,
            password: loginForm.password.value
        };

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();

            if (res.ok) {
                currentUser = result;
                localStorage.setItem('ehsan_session', JSON.stringify(currentUser));
                showDashboard();
            } else {
                alert(result.error || 'اسم المستخدم أو كلمة المرور غير صحيحة');
            }
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
        avatarInitial.innerText = currentUser.name.charAt(0);
        userRoleBadge.innerText = currentUser.role.toUpperCase();
        
        userRoleBadge.className = `badge role-${currentUser.role}`;

        // Permissions Handling
        if (currentUser.role === 'clerk') {
            document.querySelectorAll('.clerk-hidden').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
        } else if (currentUser.role === 'manager') {
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
        } else {
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'flex');
        }

        loadStats();
        switchView('overview-view');
    }

    // --- Navigation ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.getAttribute('data-target');
            switchView(target, item);
        });
    });

    async function switchView(targetId, activeItem = null) {
        viewPanels.forEach(p => p.classList.add('hidden-section'));
        viewPanels.forEach(p => p.classList.remove('active-panel'));
        
        const panel = document.getElementById(targetId);
        if (panel) {
            panel.classList.remove('hidden-section');
            panel.classList.add('active-panel');
        }
        
        navItems.forEach(i => i.classList.remove('active'));
        if (activeItem) {
            activeItem.classList.add('active');
        } else {
            const defaultNav = Array.from(navItems).find(n => n.getAttribute('data-target') === targetId);
            if (defaultNav) defaultNav.classList.add('active');
        }

        if (targetId === 'beneficiaries-view') loadBeneficiaries();
        if (targetId === 'users-view') loadUsers();
        if (targetId === 'aid-types-view') loadAidTypes();
        if (targetId === 'distributions-view') loadDistributions();
        if (targetId === 'overview-view') loadStats();
    }

    // --- Data Loaders ---

    async function loadStats() {
        try {
            const res = await fetch('/api/stats');
            const d = await res.json();
            document.getElementById('stat-total-beneficiaries').innerText = d.totalBeneficiaries.toLocaleString('ar-LY');
            document.getElementById('stat-total-distributions').innerText = d.totalDistributions.toLocaleString('ar-LY');
            document.getElementById('stat-total-staff').innerText = d.totalStaff.toLocaleString('ar-LY');
        } catch (e) {}
    }

    async function loadBeneficiaries() {
        const tbody = document.getElementById('beneficiaries-table-body');
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">جاري تحميل البيانات...</td></tr>';
        try {
            const res = await fetch('/api/beneficiaries');
            const data = await res.json();
            tbody.innerHTML = data.map(b => `
                <tr>
                    <td><strong>${b.name}</strong></td>
                    <td><code>${b.national_id}</code></td>
                    <td>${b.family_size} أشخاص</td>
                    <td>
                        <span class="score-badge">${b.need_score.toFixed(1)}</span>
                        <div class="need-score-container"><div class="need-score-bar" style="width: ${(b.need_score/3.4)*100}%"></div></div>
                    </td>
                    <td><button class="btn-text">👁️ معاينة</button></td>
                </tr>
            `).join('');
        } catch (err) { tbody.innerHTML = '<tr><td colspan="5">خطأ في جلب البيانات</td></tr>'; }
    }

    async function loadUsers() {
        const tbody = document.getElementById('users-table-body');
        try {
            const res = await fetch('/api/users');
            const data = await res.json();
            tbody.innerHTML = data.map(u => `
                <tr>
                    <td>${u.name}</td>
                    <td><code>${u.username}</code></td>
                    <td><span class="badge role-${u.role}">${u.role.toUpperCase()}</span></td>
                    <td style="font-size:0.8rem; color:var(--text-muted);">${new Date(u.created_at).toLocaleDateString('ar-LY')}</td>
                </tr>
            `).join('');
        } catch (err) {}
    }

    async function loadAidTypes() {
        const tbody = document.getElementById('aid-types-table-body');
        try {
            const res = await fetch('/api/aid_types');
            const data = await res.json();
            tbody.innerHTML = data.map(a => `
                <tr>
                    <td>${a.name}</td>
                    <td><span class="badge" style="background:#f1f5f9; color:#475569;">${a.category}</span></td>
                    <td><strong>${a.amount} د.ل</strong></td>
                    <td>${a.sponsor || 'جهة عامة'}</td>
                </tr>
            `).join('');
        } catch (e) {}
    }

    async function loadDistributions() {
        const tbody = document.getElementById('distributions-table-body');
        try {
            const res = await fetch('/api/distributions_full');
            const data = await res.json();
            tbody.innerHTML = data.map(d => `
                <tr>
                    <td><strong>${d.b_name}</strong></td>
                    <td><span class="badge" style="background:var(--primary-light); color:var(--primary-dark);">${d.a_name}</span></td>
                    <td style="font-size:0.85rem;">${new Date(d.date).toLocaleDateString('ar-LY')}</td>
                    <td><span style="font-weight:700;">${d.u_name}</span></td>
                </tr>
            `).join('') || '<tr><td colspan="4" style="text-align:center;">لا توجد سجلات توزيع</td></tr>';
        } catch (err) {}
    }

    // --- Search ---
    const searchInput = document.getElementById('global-search-input');
    searchInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const q = searchInput.value.trim();
            if (!q) return;
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            const container = document.getElementById('search-result-container');
            container.innerHTML = data.map(b => `
                <div style="background:var(--primary-light); padding:20px; border-radius:12px; margin-bottom:12px; border:1px solid var(--primary-dark);">
                    <h3>${b.name}</h3>
                    <p style="margin:8px 0;">الرقم الوطني: <code>${b.national_id}</code></p>
                    <div style="display:flex; align-items:center;">
                        <span class="score-badge">${b.need_score.toFixed(1)}</span>
                        <div class="need-score-container" style="flex-grow:1;"><div class="need-score-bar" style="width: ${(b.need_score/3.4)*100}%"></div></div>
                    </div>
                </div>
            `).join('') || '<p style="text-align:center; padding:20px; color:var(--danger);">لا توجد نتائج مطابقة</p>';
            document.getElementById('search-modal').classList.add('active');
        }
    });

    // --- Form Handlers ---
    document.getElementById('btn-add-user')?.addEventListener('click', () => document.getElementById('user-modal').classList.add('active'));
    document.getElementById('btn-add-beneficiary')?.addEventListener('click', () => document.getElementById('beneficiary-modal').classList.add('active'));
    document.getElementById('btn-new-distribution')?.addEventListener('click', async () => {
        const bRes = await fetch('/api/beneficiaries');
        const beneficiaries = await bRes.json();
        const aRes = await fetch('/api/aid_types');
        const aidTypes = await aRes.json();

        document.getElementById('select-beneficiary').innerHTML = beneficiaries.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
        document.getElementById('select-aid').innerHTML = aidTypes.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
        document.getElementById('distribution-modal').classList.add('active');
    });

    addUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(addUserForm).entries());
        const res = await fetch('/api/users', { method: 'POST', body: JSON.stringify(data), headers: {'Content-Type':'application/json'} });
        if (res.ok) { 
            alert('تم إضافة المستخدم بنجاح'); 
            document.getElementById('user-modal').classList.remove('active'); 
            loadUsers(); loadStats(); addUserForm.reset();
        } else { alert('خطأ: ربما اسم المستخدم مسجل مسبقاً'); }
    });

    addBeneficiaryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(addBeneficiaryForm).entries());
        const res = await fetch('/api/beneficiaries', { method: 'POST', body: JSON.stringify(data), headers: {'Content-Type':'application/json'} });
        const result = await res.json();
        if (res.ok) { 
            alert(`تم الحفظ. درجة الاحتياج المقدرة: ${result.needScore}`); 
            document.getElementById('beneficiary-modal').classList.remove('active'); 
            loadBeneficiaries(); loadStats(); addBeneficiaryForm.reset();
        } else { alert(result.error); }
    });

    newDistributionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            beneficiaryId: newDistributionForm.beneficiaryId.value,
            aidId: newDistributionForm.aidId.value,
            userId: currentUser.id
        };
        const res = await fetch('/api/distributions', { method: 'POST', body: JSON.stringify(data), headers: {'Content-Type':'application/json'} });
        const result = await res.json();
        if (res.ok) { 
            alert(result.message); 
            document.getElementById('distribution-modal').classList.remove('active'); 
            loadStats(); loadDistributions(); newDistributionForm.reset();
        } else { alert(result.error); }
    });

    // --- Modal Closing Logic ---
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mId = btn.getAttribute('data-close');
            document.getElementById(mId).classList.remove('active');
        });
    });

    window.addEventListener('click', (e) => { 
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('active'); 
        }
    });
});
