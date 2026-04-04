document.addEventListener('DOMContentLoaded', () => {
    
    // --- Elements ---
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const loginForm = document.getElementById('login-form');
    const roleSelect = document.getElementById('role-select');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const logoutBtn = document.getElementById('logout-btn');

    // --- Toggle Password Visibility ---
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            if (type === 'password') {
                togglePasswordBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 20px; height: 20px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
            } else {
                togglePasswordBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 20px; height: 20px;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';
            }
        });
    }

    // Dashboard Elements
    const navItems = document.querySelectorAll('.nav-item');
    const viewPanels = document.querySelectorAll('.view-panel');
    const userRoleBadge = document.getElementById('user-role-badge');
    const adminOnlyElements = document.querySelectorAll('.admin-only');
    const managerAdminElements = document.querySelectorAll('.manager-admin-only');

    // --- State ---
    let currentUserRole = null; // 'admin', 'manager', 'clerk'
    let familiesDatabase = []; // قاعدة بيانات لتخزين العائلات المدخلة مؤقتاً

    // --- Authentication Simulation ---
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Mock Login
        const role = roleSelect.value;
        const name = usernameInput.value || (role === 'admin' ? 'مدير النظام' : role === 'manager' ? 'مدير الجمعية' : 'موظف بيانات');
        
        login(role, name);
    });

    logoutBtn.addEventListener('click', () => {
        logout();
    });

    function login(role, name) {
        currentUserRole = role;
        
        // Update UI info
        document.getElementById('current-username').innerText = name;
        
        let roleDisplay = '';
        let badgeColor = '';
        let badgeBg = '';

        if (role === 'admin') {
            roleDisplay = 'Admin';
            badgeColor = '#ef4444'; // danger
            badgeBg = '#fee2e2';
        } else if (role === 'manager') {
            roleDisplay = 'Manager';
            badgeColor = '#1d4ed8'; // blue
            badgeBg = '#dbeafe';
        } else {
            roleDisplay = 'Clerk';
            badgeColor = '#7e22ce'; // purple
            badgeBg = '#f3e8ff';
        }
        
        userRoleBadge.innerText = roleDisplay;
        userRoleBadge.style.color = badgeColor;
        userRoleBadge.style.backgroundColor = badgeBg;

        // Apply Permissions (Authorization)
        applyPermissions();

        // Switch Screen
        loginSection.classList.remove('active-section');
        loginSection.classList.add('hidden-section');
        dashboardSection.classList.remove('hidden-section');
        dashboardSection.classList.add('active-section');

        // Reset to overview View
        switchView('overview-view');
    }

    function logout() {
        currentUserRole = null;
        
        // Reset inputs
        loginForm.reset();

        // Switch Screen
        dashboardSection.classList.remove('active-section');
        dashboardSection.classList.add('hidden-section');
        loginSection.classList.remove('hidden-section');
        loginSection.classList.add('active-section');
    }

    // --- Authorization / Permission Logic ---
    function applyPermissions() {
        // Reset all displays first
        adminOnlyElements.forEach(el => el.style.display = 'none');
        managerAdminElements.forEach(el => el.style.display = 'none');

        // Apply based on role
        if (currentUserRole === 'admin') {
            adminOnlyElements.forEach(el => el.style.display = 'block');
            managerAdminElements.forEach(el => el.style.display = 'block');
        } else if (currentUserRole === 'manager') {
            managerAdminElements.forEach(el => el.style.display = 'block');
        } else if (currentUserRole === 'clerk') {
            // Clerk sees neither admin-only nor manager-admin-only specific sections
            // They only see overview and Data entry usually, maybe restrict overview stats too
        }

        // Specifically for menu items (li), they use block, inline, or whatever they default to.
        // For our design, we just use display: block for list items.
    }

    // --- Navigation (SPA Logic) ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            switchView(targetId, item);
        });
    });

    function switchView(targetId, activeNavItem = null) {
        // 1. Hide all panels
        viewPanels.forEach(panel => {
            panel.classList.remove('active-panel');
            panel.classList.add('hidden-panel');
        });

        // 2. Remove active class from all nav items
        navItems.forEach(item => item.classList.remove('active'));

        // 3. Show target panel
        const targetPanel = document.getElementById(targetId);
        if (targetPanel) {
            targetPanel.classList.remove('hidden-panel');
            targetPanel.classList.add('active-panel');
        }

        // 4. Set active nav item
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        } else {
            // Find the nav item matching the default panel (overview)
            const defaultNav = Array.from(navItems).find(n => n.getAttribute('data-target') === targetId);
            if (defaultNav) defaultNav.classList.add('active');
        }
    }

    // --- Data Entry Form Logic ---
    let familyIdCounter = 1; // العداد يبدأ من رقم 1
    const dataEntryForm = document.getElementById('data-entry-form');
    if (dataEntryForm) {
        dataEntryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // استخدام الرقم التسلسلي ومن ثم زيادته للعائلة القادمة
            const familyId = familyIdCounter++;
            
            // تخزين البيانات للبحث لاحقاً
            const inputs = dataEntryForm.querySelectorAll('input, select');
            const familyData = {
                id: familyId,
                name: inputs[0].value,
                nationalId: inputs[1].value,
                aidType: inputs[2].value,
                size: inputs[3].value,
                phone: inputs[4].value
            };
            familiesDatabase.push(familyData);
            
            // Show Success Alert with the Family ID
            alert(`تم حفظ الملف العائلي بنجاح!\n\n📌 الرقم التعريفي الخاص بالعائلة هو: ${familyId}\n\nيُرجى الاحتفاظ بهذا الرقم لتسهيل البحث والمراجعة لاحقاً.`);
            
            // Reset the form after submission
            dataEntryForm.reset();
        });
    }

    // --- Global Search Logic ---
    const searchInput = document.getElementById('global-search-input');
    const searchModal = document.getElementById('search-modal');
    const closeSearchModal = document.getElementById('close-search-modal');
    const searchResultContainer = document.getElementById('search-result-container');

    if (searchInput && searchModal) {
        // استمع للضغط على زر Enter
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim().toLowerCase();
                if (!query) return;

                // البحث الشامل: فحص جميع بيانات العائلة ومطابقتها مع كلمة البحث
                const results = familiesDatabase.filter(family => 
                    Object.values(family).some(val => val.toString().toLowerCase().includes(query))
                );

                searchResultContainer.innerHTML = ''; // مسح النتائج السابقة

                if (results.length > 0) {
                    results.forEach(family => {
                        const card = document.createElement('div');
                        card.style.marginBottom = '20px';
                        card.style.paddingBottom = '20px';
                        card.style.borderBottom = '1px dashed var(--border)';
                        
                        card.innerHTML = `
                            <div class="family-details-grid">
                                <div class="detail-item">
                                    <span class="detail-label">رقم الملف (ID)</span>
                                    <span class="detail-value">${family.id}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">اسم المستفيد</span>
                                    <span class="detail-value">${family.name}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">الرقم الوطني</span>
                                    <span class="detail-value">${family.nationalId}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">رقم الهاتف</span>
                                    <span class="detail-value">${family.phone}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">نوع المساعدة</span>
                                    <span class="detail-value">${family.aidType}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">أفراد الأسرة</span>
                                    <span class="detail-value">${family.size} شخص</span>
                                </div>
                            </div>
                        `;
                        searchResultContainer.appendChild(card);
                    });
                } else {
                    searchResultContainer.innerHTML = '<div class="not-found-msg">لم يتم العثور على أية نتائج مطابقة لهذا البحث.</div>';
                }

                // Show modal
                searchModal.classList.remove('hidden-modal');
            }
        });
    }

    if (closeSearchModal && searchModal) {
        // إغلاق النافذة من زر X
        closeSearchModal.addEventListener('click', () => {
            searchModal.classList.add('hidden-modal');
        });
        
        // إغلاق النافذة عند النقر خارجها
        window.addEventListener('click', (e) => {
            if (e.target === searchModal) {
                searchModal.classList.add('hidden-modal');
            }
        });
    }
});
