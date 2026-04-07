// EXPENSE AUDITOR — Single Page Application

const API = "http://127.0.0.1:8000";

// ── State ──
let currentUser = null;
let currentFilter = "all";
let notifPollInterval = null;

// ── Init ──
window.addEventListener("DOMContentLoaded", () => {
    const saved = localStorage.getItem("user");
    if (saved) {
        currentUser = JSON.parse(saved);
    }
    handleRoute();
});

window.addEventListener("hashchange", handleRoute);

// ═══════════════════════════════════════
// ROUTING
// ═══════════════════════════════════════

function navigate(page) {
    window.location.hash = page;
}

function handleRoute() {
    const hash = window.location.hash.replace("#", "") || "";
    const [page, param] = hash.split("/");

    // Protected routes
    if (!currentUser && page !== "login" && page !== "register") {
        window.location.hash = "login";
        return;
    }

    // Show/hide header
    const header = document.getElementById("appHeader");
    if (currentUser) {
        header.style.display = "flex";
        updateHeader();
        startNotifPolling();
    } else {
        header.style.display = "none";
        stopNotifPolling();
    }

    // Render page
    switch (page) {
        case "login":
        case "register":
            renderAuth(page);
            break;
        case "employee":
            renderEmployeePortal();
            break;
        case "dashboard":
            renderDashboard();
            break;
        case "claim":
            renderClaimDetail(parseInt(param));
            break;
        case "settings":
            renderSettings();
            break;
        default:
            if (currentUser) {
                navigate(currentUser.role === "company" ? "dashboard" : "employee");
            } else {
                navigate("login");
            }
    }
}

// ═══════════════════════════════════════
// HEADER
// ═══════════════════════════════════════

function updateHeader() {
    if (!currentUser) return;

    // Avatar
    document.getElementById("userAvatar").textContent =
        currentUser.username.charAt(0).toUpperCase();
    document.getElementById("userName").textContent = currentUser.username;
    document.getElementById("userRole").textContent =
        currentUser.role === "company" ? "Auditor" : "Employee";

    // Nav links
    const nav = document.getElementById("navLinks");
    if (currentUser.role === "company") {
        nav.innerHTML = `
            <li><a href="#dashboard" class="${location.hash.includes('dashboard') ? 'active' : ''}">Dashboard</a></li>
            <li><a href="#settings" class="${location.hash.includes('settings') ? 'active' : ''}">Settings</a></li>
        `;
    } else {
        nav.innerHTML = `
            <li><a href="#employee" class="${location.hash.includes('employee') ? 'active' : ''}">Submit Claim</a></li>
        `;
    }

    fetchUnreadCount();
}

function logout() {
    currentUser = null;
    localStorage.removeItem("user");
    stopNotifPolling();
    navigate("login");
}


// ═══════════════════════════════════════
// AUTH PAGE
// ═══════════════════════════════════════

function renderAuth(mode) {
    document.getElementById("appHeader").style.display = "none";
    const main = document.getElementById("mainContent");

    main.innerHTML = `
    <div class="auth-container">
        <div class="auth-card">
            <div style="display:flex; justify-content:center; margin-bottom:12px;">
                <img src="logo/TrueClaim_logo_1.png" alt="TrueClaim Logo" style="height: 110px;">
            </div>
            <h2>TrueClaim</h2>
            <p class="subtitle">Policy-First Intelligence Platform</p>

            <div class="auth-tabs">
                <button id="tabLogin" class="${mode === 'login' ? 'active' : ''}" onclick="navigate('login')">Sign In</button>
                <button id="tabRegister" class="${mode === 'register' ? 'active' : ''}" onclick="navigate('register')">Register</button>
            </div>

            <form id="authForm" onsubmit="handleAuth(event)">
                <div class="form-group">
                    <label for="auth-username">Username</label>
                    <input class="form-input" type="text" id="auth-username" name="username" placeholder="Enter username" required>
                </div>
                <div class="form-group">
                    <label for="auth-password">Password</label>
                    <input class="form-input" type="password" id="auth-password" name="password" placeholder="Enter password" required>
                </div>

                ${mode === "register" ? `
                <div class="form-group">
                    <label for="auth-role">Role</label>
                    <select class="form-select" id="auth-role" name="role">
                        <option value="employee">Employee</option>
                        <option value="company">Finance Auditor</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="auth-company">Company ID</label>
                    <input class="form-input" type="text" id="auth-company" name="company_id" placeholder="e.g., C101" required>
                </div>
                ` : ""}

                <button type="submit" class="btn btn-primary btn-full" id="authSubmitBtn">
                    ${mode === "login" ? "Sign In" : "Create Account"}
                </button>
            </form>

            <p class="text-center text-muted text-sm mt-4">
                ${mode === "login"
            ? `Don't have an account? <span class="link-text" onclick="navigate('register')">Register</span>`
            : `Already have an account? <span class="link-text" onclick="navigate('login')">Sign In</span>`
        }
            </p>
        </div>
    </div>`;
}

async function handleAuth(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const isLogin = !document.getElementById("auth-role");

    const btn = document.getElementById("authSubmitBtn");
    btn.disabled = true;
    btn.textContent = isLogin ? "Signing in..." : "Creating account...";

    try {
        if (isLogin) {
            const res = await fetch(`${API}/login`, { method: "POST", body: formData });
            const data = await res.json();
            if (data.error) {
                showToast(data.error, "error");
                btn.disabled = false;
                btn.textContent = "Sign In";
                return;
            }
            currentUser = data;
            localStorage.setItem("user", JSON.stringify(data));
            showToast(`Welcome back, ${data.username}!`, "success");
            navigate(data.role === "company" ? "dashboard" : "employee");
        } else {
            await fetch(`${API}/register`, { method: "POST", body: formData });
            showToast("Account created! Please sign in.", "success");
            navigate("login");
        }
    } catch (err) {
        showToast("Server error. Is the backend running?", "error");
        btn.disabled = false;
        btn.textContent = isLogin ? "Sign In" : "Create Account";
    }
}


// ═══════════════════════════════════════
// EMPLOYEE PORTAL
// ═══════════════════════════════════════

function renderEmployeePortal() {
    const main = document.getElementById("mainContent");
    main.innerHTML = `
    <h1 class="page-title animate-in">Submit Expense Claim</h1>
    <p class="page-subtitle animate-in stagger-1">Upload your receipt and provide business context for automated policy verification.</p>

    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 24px;" class="animate-in stagger-2" id="portalGrid">
        <!-- Upload Form -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">New Claim</h3>
            </div>

            <form id="uploadForm" onsubmit="submitClaim(event)">
                <div class="form-group">
                    <label>Receipt Image / PDF</label>
                    <div class="upload-dropzone" id="dropzone">
                        <div class="icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg></div>
                        <div class="text-main">Drop your receipt here or click to browse</div>
                        <div class="text-sub">Supports JPG, PNG, PDF • Max 10MB</div>
                        <input type="file" id="fileInput" name="file" accept="image/jpeg,image/png,application/pdf" required onchange="handleFileSelect(this)">
                    </div>
                    <div id="filePreview"></div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label for="claimed_date">Expense Date</label>
                        <input class="form-input" type="date" id="claimed_date" name="claimed_date" required>
                    </div>
                    <div class="form-group">
                        <label for="company_id">Company ID</label>
                        <input class="form-input" type="text" id="company_id" name="company_id" value="${currentUser?.company_id || ''}" readonly>
                    </div>
                </div>

                <div class="form-group">
                    <label for="purpose">Business Purpose</label>
                    <textarea class="form-textarea" id="purpose" name="purpose" placeholder="Describe the business reason for this expense (e.g., Client meeting lunch, Project travel)" required></textarea>
                </div>

                <input type="hidden" name="username" value="${currentUser?.username || ''}">

                <button type="submit" class="btn btn-primary btn-full" id="submitBtn">
                    Submit for Audit
                </button>
            </form>

            <div id="ocrResult"></div>
        </div>

        <!-- My Claims -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">My Claims</h3>
            </div>
            <div id="myClaims">
                <div class="loading-skeleton" style="height:40px;margin-bottom:8px;"></div>
                <div class="loading-skeleton" style="height:40px;margin-bottom:8px;"></div>
                <div class="loading-skeleton" style="height:40px;"></div>
            </div>
        </div>
    </div>`;

    // Setup drag-and-drop
    const dz = document.getElementById("dropzone");
    dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("dragover"); });
    dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
    dz.addEventListener("drop", (e) => {
        e.preventDefault();
        dz.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
            document.getElementById("fileInput").files = e.dataTransfer.files;
            handleFileSelect(document.getElementById("fileInput"));
        }
    });

    loadMyClaims();
}

function handleFileSelect(input) {
    const preview = document.getElementById("filePreview");
    if (!input.files || !input.files[0]) {
        preview.innerHTML = "";
        return;
    }

    const file = input.files[0];
    const isImage = file.type.startsWith("image/");
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);

    let thumbHtml = isImage
        ? `<img src="${URL.createObjectURL(file)}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;">`
        : `<div style="width:48px;height:48px;background:var(--bg-input);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg></div>`;

    preview.innerHTML = `
    <div class="file-preview">
        ${thumbHtml}
        <div class="file-info">
            <div class="file-name">${file.name}</div>
            <div class="file-size">${sizeMB} MB</div>
        </div>
        <button type="button" class="remove-file" onclick="clearFile()">✕</button>
    </div>`;
}

function clearFile() {
    document.getElementById("fileInput").value = "";
    document.getElementById("filePreview").innerHTML = "";
}

async function submitClaim(e) {
    e.preventDefault();
    const btn = document.getElementById("submitBtn");
    btn.disabled = true;
    btn.textContent = "Processing...";

    const formData = new FormData(e.target);

    try {
        const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
        const data = await res.json();

        // Show OCR result
        const statusClass = data.status.toLowerCase();
        let warningHtml = "";
        if (data.confidence_warning) {
            warningHtml = `<div class="ocr-warning"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg> ${data.confidence_warning}</div>`;
        }

        document.getElementById("ocrResult").innerHTML = `
        <div class="ocr-result">
            <h3>Audit Result</h3>
            ${warningHtml}
            <div class="result-grid">
                <div class="result-item">
                    <div class="label">Merchant</div>
                    <div class="value">${data.merchant || 'N/A'}</div>
                </div>
                <div class="result-item">
                    <div class="label">Date</div>
                    <div class="value">${data.date || 'N/A'}</div>
                </div>
                <div class="result-item">
                    <div class="label">Amount</div>
                    <div class="value">${data.currency} ${Number(data.amount).toLocaleString()}</div>
                </div>
                <div class="result-item">
                    <div class="label">Confidence</div>
                    <div class="value">${data.confidence}%</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width:${data.confidence}%; background:${data.confidence > 60 ? 'var(--success)' : data.confidence > 40 ? 'var(--warning)' : 'var(--danger)'}"></div>
                    </div>
                </div>
            </div>
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <span class="status-pill status-${statusClass}">${data.status}</span>
                <span class="text-sm text-muted">Claim #${data.id}</span>
            </div>
            <p style="margin-top:12px; font-size:0.85rem; color:var(--text-secondary);">${data.explanation}</p>
        </div>`;

        showToast(`Claim #${data.id} submitted — ${data.status}`, data.status === "Approved" ? "success" : data.status === "Flagged" ? "warning" : "error");

        // Reset form
        e.target.reset();
        document.getElementById("filePreview").innerHTML = "";
        document.getElementById("company_id").value = currentUser?.company_id || "";

        // Reload claims
        loadMyClaims();
    } catch (err) {
        showToast("Failed to submit claim. Check backend connection.", "error");
    }

    btn.disabled = false;
    btn.textContent = "Submit for Audit";
}

async function loadMyClaims() {
    const container = document.getElementById("myClaims");
    try {
        const res = await fetch(`${API}/claims?role=employee&username=${currentUser.username}&company_id=${currentUser.company_id}`);
        const claims = await res.json();

        if (!claims.length) {
            container.innerHTML = `
            <div class="table-empty">
                <div class="icon"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="12" x2="2" y2="12"></line><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path><line x1="6" y1="16" x2="6.01" y2="16"></line><line x1="10" y1="16" x2="10.01" y2="16"></line></svg></div>
                <p>No claims yet. Submit your first expense!</p>
            </div>`;
            return;
        }

        container.innerHTML = `<div class="claim-cards">${claims.map(c => `
            <div class="claim-card" onclick="navigate('claim/${c.id}')">
                <div class="claim-amount">${c.currency || '₹'}${Number(c.amount).toLocaleString()}</div>
                <div class="claim-info">
                    <div class="claim-merchant">${c.merchant}</div>
                    <div class="claim-meta">${c.date || 'N/A'} • ${c.purpose?.substring(0, 40) || ''}${(c.purpose?.length || 0) > 40 ? '...' : ''}</div>
                </div>
                <span class="status-pill status-${c.status.toLowerCase()}">${c.status}</span>
            </div>
        `).join("")}</div>`;
    } catch {
        container.innerHTML = `<p class="text-muted text-sm">Could not load claims.</p>`;
    }
}


// ═══════════════════════════════════════
// FINANCE DASHBOARD
// ═══════════════════════════════════════

async function renderDashboard() {
    const main = document.getElementById("mainContent");
    main.innerHTML = `
    <h1 class="page-title animate-in">Finance Audit Dashboard</h1>
    <p class="page-subtitle animate-in stagger-1">Review, audit, and manage expense claims across your organization.</p>

    <div class="stats-row animate-in stagger-2" id="statsRow">
        <div class="stat-card"><div class="loading-skeleton" style="height:60px;"></div></div>
        <div class="stat-card"><div class="loading-skeleton" style="height:60px;"></div></div>
        <div class="stat-card"><div class="loading-skeleton" style="height:60px;"></div></div>
        <div class="stat-card"><div class="loading-skeleton" style="height:60px;"></div></div>
    </div>

    <div class="table-filters animate-in stagger-3">
        <button class="filter-btn active" data-filter="all" onclick="filterClaims('all', this)">All</button>
        <button class="filter-btn" data-filter="Rejected" onclick="filterClaims('Rejected', this)">Rejected</button>
        <button class="filter-btn" data-filter="Flagged" onclick="filterClaims('Flagged', this)">Flagged</button>
        <button class="filter-btn" data-filter="Approved" onclick="filterClaims('Approved', this)">Approved</button>
    </div>

    <div class="table-wrapper animate-in stagger-4">
        <table class="claims-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Merchant</th>
                    <th>Amount</th>
                    <th>Date</th>
                    <th>Risk</th>
                    <th>Status</th>
                    <th>Explanation</th>
                </tr>
            </thead>
            <tbody id="claimsTableBody">
                <tr><td colspan="8"><div class="loading-skeleton" style="height:30px;margin:8px 0;"></div><div class="loading-skeleton" style="height:30px;margin:8px 0;"></div></td></tr>
            </tbody>
        </table>
    </div>`;

    try {
        const res = await fetch(`${API}/claims?role=company&company_id=${currentUser.company_id}`);
        window._allClaims = await res.json();
        renderStats(window._allClaims);
        renderClaimsTable(window._allClaims);
    } catch {
        document.getElementById("claimsTableBody").innerHTML =
            `<tr><td colspan="8" class="text-center text-muted" style="padding:40px;">Could not load claims. Is the backend running?</td></tr>`;
    }
}

function renderStats(claims) {
    const total = claims.length;
    const approved = claims.filter(c => c.status === "Approved").length;
    const flagged = claims.filter(c => c.status === "Flagged").length;
    const rejected = claims.filter(c => c.status === "Rejected").length;

    document.getElementById("statsRow").innerHTML = `
    <div class="stat-card">
        <div class="stat-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg></div>
        <div class="stat-label">Total Claims</div>
        <div class="stat-value">${total}</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>
        <div class="stat-label">Approved</div>
        <div class="stat-value" style="color:var(--success)">${approved}</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg></div>
        <div class="stat-label">Flagged</div>
        <div class="stat-value" style="color:var(--warning)">${flagged}</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg></div>
        <div class="stat-label">Rejected</div>
        <div class="stat-value" style="color:var(--danger)">${rejected}</div>
    </div>`;
}

function renderClaimsTable(claims) {
    const tbody = document.getElementById("claimsTableBody");

    if (!claims.length) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="table-empty"><div class="icon"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="12" x2="2" y2="12"></line><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path><line x1="6" y1="16" x2="6.01" y2="16"></line><line x1="10" y1="16" x2="10.01" y2="16"></line></svg></div><p>No claims found.</p></div></td></tr>`;
        return;
    }

    tbody.innerHTML = claims.map(c => {
        return `
        <tr onclick="navigate('claim/${c.id}')">
            <td>#${c.id}</td>
            <td>${c.username}</td>
            <td class="merchant-name">${c.merchant}</td>
            <td class="amount">${c.currency || '₹'}${Number(c.amount).toLocaleString()}</td>
            <td>${c.date || 'N/A'}</td>
            <td><span class="risk-${c.risk_level}">${c.risk_level.toUpperCase()}</span></td>
            <td><span class="status-pill status-${c.status.toLowerCase()}">${c.status}</span></td>
            <td class="text-sm">${truncate(c.explanation, 50)}</td>
        </tr>`;
    }).join("");
}

function filterClaims(status, btn) {
    currentFilter = status;
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    const filtered = status === "all"
        ? window._allClaims
        : window._allClaims.filter(c => c.status === status);
    renderClaimsTable(filtered);
}


// ═══════════════════════════════════════
// CLAIM DETAIL VIEW
// ═══════════════════════════════════════

async function renderClaimDetail(id) {
    const main = document.getElementById("mainContent");
    main.innerHTML = `
    <div class="back-nav" onclick="history.back()">← Back</div>
    <h1 class="page-title">Claim #${id}</h1>
    <div class="detail-grid" id="detailGrid">
        <div class="receipt-panel"><div class="loading-skeleton" style="height:300px;width:100%;"></div></div>
        <div class="detail-panel"><div class="loading-skeleton" style="height:300px;"></div></div>
    </div>`;

    try {
        const res = await fetch(`${API}/claims/${id}`);
        if (!res.ok) throw new Error("Not found");
        const c = await res.json();

        const isAuditor = currentUser?.role === "company";
        const confColor = c.ocr_confidence > 60 ? "var(--success)" : c.ocr_confidence > 40 ? "var(--warning)" : "var(--danger)";

        // Receipt panel
        let receiptHtml;
        if (c.receipt_path) {
            const ext = c.receipt_path.split('.').pop().toLowerCase();
            if (["jpg", "jpeg", "png", "gif", "webp"].includes(ext)) {
                receiptHtml = `<img src="${API}/receipt/${c.receipt_path}" alt="Receipt Image" style="max-width:100%;border-radius:8px;">`;
            } else {
                receiptHtml = `<div class="no-image"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:8px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg><br>PDF Receipt<br><a href="${API}/receipt/${c.receipt_path}" target="_blank" class="btn btn-secondary btn-sm mt-4">Open PDF</a></div>`;
            }
        } else {
            receiptHtml = `<div class="no-image"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:8px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg><br>No receipt image available</div>`;
        }

        // Policy snippet rendering
        const snippets = (c.policy_snippet || "").split(" | ").filter(s => s.trim());
        const snippetHtml = snippets.length
            ? snippets.map(s => `<div class="policy-snippet-box">"${s}"</div>`).join('<div style="height:8px;"></div>')
            : `<div class="policy-snippet-box">No specific policy snippet matched.</div>`;

        // Override section (for auditors)
        let overrideHtml = "";
        if (isAuditor) {
            if (c.override_status) {
                overrideHtml = `
                <div class="override-info">
                    <strong>Overridden</strong> to <span class="status-pill status-${c.override_status.toLowerCase()}">${c.override_status}</span>
                    by <strong>${c.override_by}</strong><br>
                    <em style="color:var(--text-muted); font-size:0.8rem;">"${c.override_comment}"</em>
                </div>`;
            }
            overrideHtml += `
            <div class="override-box mt-4">
                <h3>Override Decision</h3>
                <div class="override-actions">
                    <button class="btn btn-success btn-sm" onclick="selectOverride('Approved', this)">Approve</button>
                    <button class="btn btn-warning btn-sm" onclick="selectOverride('Flagged', this)">Flag</button>
                    <button class="btn btn-danger btn-sm" onclick="selectOverride('Rejected', this)">Reject</button>
                </div>
                <div class="form-group">
                    <label>Comment</label>
                    <textarea class="form-textarea" id="overrideComment" placeholder="Reason for override..."></textarea>
                </div>
                <input type="hidden" id="overrideStatus" value="">
                <button class="btn btn-primary btn-full" onclick="submitOverride(${c.id})" id="overrideSubmitBtn" disabled>
                    Submit Override
                </button>
            </div>`;
        }

        document.getElementById("detailGrid").innerHTML = `
        <!-- Left: Receipt Image -->
        <div class="receipt-panel animate-in">
            <h3 class="card-title mb-4">Receipt</h3>
            ${receiptHtml}
        </div>

        <!-- Right: Details -->
        <div class="detail-panel">
            <!-- Extracted Data -->
            <div class="detail-section animate-in stagger-1">
                <h3>Extracted Data</h3>
                <div class="detail-row">
                    <span class="label">Merchant</span>
                    <span class="value">${c.merchant}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Receipt Date</span>
                    <span class="value">${c.date || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Claimed Date</span>
                    <span class="value">${c.claimed_date || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Amount</span>
                    <span class="value amount">${c.currency || '₹'}${Number(c.amount).toLocaleString()}</span>
                </div>
                <div class="detail-row">
                    <span class="label">OCR Confidence</span>
                    <span class="value" style="color:${confColor}">${c.ocr_confidence}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width:${c.ocr_confidence}%; background:${confColor}"></div>
                </div>
            </div>

            <!-- Status & Purpose -->
            <div class="detail-section animate-in stagger-2">
                <h3>Audit Decision</h3>
                <div class="detail-row">
                    <span class="label">Status</span>
                    <span class="status-pill status-${c.status.toLowerCase()}">${c.status}${c.override_status ? ' (overridden)' : ''}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Risk Level</span>
                    <span class="value risk-${c.risk_level}">${c.risk_level.toUpperCase()}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Business Purpose</span>
                    <span class="value">${c.purpose}</span>
                </div>
                <div style="margin-top:10px;">
                    <p class="text-sm" style="color:var(--text-secondary)">${c.explanation}</p>
                </div>
            </div>

            <!-- Policy Snippet -->
            <div class="detail-section animate-in stagger-3">
                <h3>Policy Reference</h3>
                ${snippetHtml}
            </div>

            <!-- Override (Auditor only) -->
            ${overrideHtml ? `<div class="animate-in stagger-4">${overrideHtml}</div>` : ""}
        </div>`;

    } catch (err) {
        main.innerHTML = `
        <div class="back-nav" onclick="history.back()">← Back</div>
        <div class="card text-center" style="padding:60px;">
            <p style="font-size:1.2rem; margin-bottom:8px;">Claim not found</p>
            <p class="text-muted">This claim may have been deleted or the ID is invalid.</p>
        </div>`;
    }
}

function selectOverride(status, btn) {
    document.getElementById("overrideStatus").value = status;
    document.querySelectorAll(".override-actions .btn").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    document.getElementById("overrideSubmitBtn").disabled = false;
}

async function submitOverride(claimId) {
    const status = document.getElementById("overrideStatus").value;
    const comment = document.getElementById("overrideComment").value;

    if (!status) {
        showToast("Please select a status", "warning");
        return;
    }
    if (!comment.trim()) {
        showToast("Please provide a comment for the override", "warning");
        return;
    }

    const btn = document.getElementById("overrideSubmitBtn");
    btn.disabled = true;
    btn.textContent = "Submitting...";

    const formData = new FormData();
    formData.append("new_status", status);
    formData.append("comment", comment);
    formData.append("auditor", currentUser.username);

    try {
        const res = await fetch(`${API}/claims/${claimId}/override`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        showToast(data.message, "success");
        renderClaimDetail(claimId); // refresh
    } catch {
        showToast("Failed to submit override", "error");
        btn.disabled = false;
        btn.textContent = "Submit Override";
    }
}


// ═══════════════════════════════════════
// NOTIFICATIONS
// ═══════════════════════════════════════

function toggleNotifPanel() {
    const panel = document.getElementById("notifPanel");
    const overlay = document.getElementById("notifOverlay");
    const isOpen = panel.classList.contains("open");

    if (isOpen) {
        panel.classList.remove("open");
        overlay.classList.remove("open");
    } else {
        panel.classList.add("open");
        overlay.classList.add("open");
        loadNotifications();
    }
}

async function loadNotifications() {
    if (!currentUser) return;
    const list = document.getElementById("notifList");

    try {
        const res = await fetch(`${API}/notifications?username=${currentUser.username}`);
        const notifs = await res.json();

        if (!notifs.length) {
            list.innerHTML = `<div class="notif-empty">No notifications yet</div>`;
            return;
        }

        list.innerHTML = notifs.map(n => `
        <div class="notif-item ${n.is_read ? '' : 'unread'} type-${n.type}" onclick="handleNotifClick(${n.id}, ${n.claim_id})">
            <div class="notif-message">${n.message}</div>
            <div class="notif-time">${formatTime(n.created_at)}</div>
        </div>`).join("");
    } catch {
        list.innerHTML = `<div class="notif-empty">Could not load notifications</div>`;
    }
}

async function handleNotifClick(notifId, claimId) {
    // Mark as read
    try {
        await fetch(`${API}/notifications/${notifId}/read`, { method: "POST" });
    } catch { }

    toggleNotifPanel();
    if (claimId) navigate(`claim/${claimId}`);
    fetchUnreadCount();
}

async function markAllRead() {
    if (!currentUser) return;
    const fd = new FormData();
    fd.append("username", currentUser.username);
    try {
        await fetch(`${API}/notifications/read_all`, { method: "POST", body: fd });
        loadNotifications();
        fetchUnreadCount();
        showToast("All notifications marked as read", "info");
    } catch { }
}

async function fetchUnreadCount() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API}/notifications/unread_count?username=${currentUser.username}`);
        const data = await res.json();
        const badge = document.getElementById("notifBadge");
        badge.textContent = data.count > 0 ? data.count : "";
        badge.setAttribute("data-count", data.count);
    } catch { }
}

function startNotifPolling() {
    stopNotifPolling();
    fetchUnreadCount();
    notifPollInterval = setInterval(fetchUnreadCount, 15000);
}

function stopNotifPolling() {
    if (notifPollInterval) {
        clearInterval(notifPollInterval);
        notifPollInterval = null;
    }
}


// ═══════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const iconMap = {
        "success": `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`,
        "error": `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
        "warning": `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
        "info": `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
    };
    const icon = iconMap[type] || iconMap["info"];
    toast.innerHTML = `<span style="display:flex;align-items:center;opacity:0.9;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function truncate(str, len) {
    if (!str) return "";
    return str.length > len ? str.substring(0, len) + "..." : str;
}

function formatTime(dateStr) {
    if (!dateStr) return "";
    try {
        const d = new Date(dateStr + "Z");
        const now = new Date();
        const diff = Math.floor((now - d) / 1000);
        if (diff < 60) return "Just now";
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return d.toLocaleDateString();
    } catch {
        return dateStr;
    }
}

// ═══════════════════════════════════════
// COMPANY SETTINGS (Auditor)
// ═══════════════════════════════════════

async function renderSettings() {
    const main = document.getElementById("mainContent");
    main.innerHTML = `
    <h1 class="page-title animate-in">Company Settings</h1>
    <p class="page-subtitle animate-in stagger-1">Manage employees and organization expense policies.</p>

    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 24px;" class="animate-in stagger-2">
        <!-- Employees Table -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Registered Employees</h3>
            </div>
            <div class="table-wrapper">
                <table class="claims-table">
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Username</th>
                            <th>Role</th>
                        </tr>
                    </thead>
                    <tbody id="employeesTableBody">
                        <tr><td colspan="3"><div class="loading-skeleton" style="height:30px;margin:8px 0;"></div></td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Policy Upload Form -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Policy Document</h3>
            </div>
            <form id="policyForm" onsubmit="uploadPolicy(event)">
                <div class="form-group">
                    <label>Upload Company Policy (PDF)</label>
                    <input type="file" id="policyFile" class="form-input" accept="application/pdf" required>
                    <p class="text-sm text-muted mt-2">Uploading a new policy immediately updates AI verification rules.</p>
                </div>
                <button type="submit" class="btn btn-primary" id="policySubmitBtn">Upload Policy</button>
            </form>
        </div>
    </div>`;

    loadEmployees();
}

async function loadEmployees() {
    const tbody = document.getElementById("employeesTableBody");
    try {
        const res = await fetch(`${API}/employees?company_id=${currentUser.company_id}`);
        const employees = await res.json();

        if (!employees.length) {
            tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted">No employees registered yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = employees.map(e => `
            <tr>
                <td>#${e.id}</td>
                <td>${e.username}</td>
                <td><span class="status-pill status-approved">${e.role.toUpperCase()}</span></td>
            </tr>
        `).join("");
    } catch {
        tbody.innerHTML = `<tr><td colspan="3" class="text-center" style="color:var(--danger)">Failed to load employees.</td></tr>`;
    }
}

async function uploadPolicy(e) {
    e.preventDefault();
    const btn = document.getElementById("policySubmitBtn");
    const fileInput = document.getElementById("policyFile");

    if (!fileInput.files.length) return;

    btn.disabled = true;
    btn.textContent = "Uploading...";

    const formData = new FormData();
    formData.append("company_id", currentUser.company_id);
    formData.append("file", fileInput.files[0]);

    try {
        const res = await fetch(`${API}/upload_policy`, { method: "POST", body: formData });
        const data = await res.json();
        if (res.ok) {
            showToast("Policy uploaded and processed successfully", "success");
            fileInput.value = "";
        } else {
            showToast(data.error || "Failed to upload policy", "error");
        }
    } catch {
        showToast("Error connecting to server", "error");
    }

    btn.disabled = false;
    btn.textContent = "Upload Policy";
}