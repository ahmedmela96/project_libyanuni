CSS = """
/* Toggle Switch UI for Permissions */
.toggle-switch {
    position: relative; display: inline-block; width: 50px; height: 26px;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
    position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
    background-color: #cbd5e1; transition: .3s; border-radius: 34px;
}
.toggle-slider:before {
    position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px;
    background-color: white; transition: .3s; border-radius: 50%;
}
.toggle-switch input:checked + .toggle-slider { background-color: var(--primary); }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(24px); }

.perm-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 15px; border-bottom: 1px solid var(--border);
}
.perm-row:last-child { border-bottom: none; }
.perm-label { font-weight: 600; color: var(--navy); }
"""

with open('style.css', 'a', encoding='utf-8') as f:
    f.write(CSS)
