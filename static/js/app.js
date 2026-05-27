/* ════════════════════════════════════════════
   APP.JS — Phòng Khám AI Client Logic
   ════════════════════════════════════════════ */

// ─── State ───
let currentUser = null;
let chatSessionId = null;
let chatFinished = false;

const API = '';  // Same origin

// ════════════════════════════════════════════
// INIT
// ════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadSpecialties();

    // Enter key for chat
    const chatInput = document.getElementById('chat-input');
    chatInput.addEventListener('keydown', (e) => {
        // Bỏ qua nếu đang gõ tiếng Việt có dấu (để tránh lỗi rơi rớt chữ)
        if (e.isComposing || e.keyCode === 229) return;
        
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Login type change
    document.getElementById('login-type').addEventListener('change', (e) => {
        const label = document.getElementById('login-user-label');
        const input = document.getElementById('login-username');
        if (e.target.value === 'patient') {
            label.textContent = 'Số điện thoại';
            input.placeholder = 'Nhập số điện thoại đã đăng ký';
        } else {
            label.textContent = 'Username / Email';
            input.placeholder = 'Nhập username hoặc email';
        }
    });
});

// ════════════════════════════════════════════
// AUTH
// ════════════════════════════════════════════

async function checkAuth() {
    try {
        const res = await fetch(API + '/api/auth/me', { credentials: 'include' });
        const data = await res.json();
        if (data.logged_in) {
            currentUser = data;
            updateNavForUser(data);
        }
    } catch (e) {
        console.log('Not logged in');
    }
}

function updateNavForUser(user) {
    document.getElementById('nav-guest').classList.add('hidden');
    document.getElementById('nav-user').classList.add('hidden');
    document.getElementById('nav-doctor').classList.add('hidden');
    document.getElementById('nav-admin').classList.add('hidden');

    const initial = (user.user_name || '?')[0].toUpperCase();

    if (user.user_type === 'patient') {
        document.getElementById('nav-user').classList.remove('hidden');
        document.getElementById('user-avatar').textContent = initial;
        document.getElementById('user-name-display').textContent = user.user_name;
    } else if (user.user_type === 'doctor') {
        document.getElementById('nav-doctor').classList.remove('hidden');
        document.getElementById('doc-avatar').textContent = initial;
        document.getElementById('doc-name-display').textContent = user.user_name;
    } else if (user.user_type === 'admin' || user.user_type === 'knowledge_admin') {
        document.getElementById('nav-admin').classList.remove('hidden');
        document.getElementById('admin-avatar').textContent = initial;
        document.getElementById('admin-name-display').textContent = user.user_name;
    }
}

function openAuthModal(tab = 'login') {
    document.getElementById('auth-modal').classList.add('active');
    switchAuthTab(tab);
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.remove('active');
}

function switchAuthTab(tab) {
    const tabs = document.querySelectorAll('#auth-tabs button');
    tabs.forEach((t, i) => {
        t.classList.toggle('active', (tab === 'login' && i === 0) || (tab === 'register' && i === 1));
    });
    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
    document.getElementById('auth-title').textContent = tab === 'login' ? 'Đăng nhập' : 'Đăng ký tài khoản';
}

async function doLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById('login-error');
    errEl.classList.remove('show');

    const body = {
        username: document.getElementById('login-username').value.trim(),
        password: document.getElementById('login-password').value,
        user_type: document.getElementById('login-type').value,
    };

    try {
        const res = await fetch(API + '/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.error || 'Đăng nhập thất bại';
            errEl.classList.add('show');
            return false;
        }
        currentUser = data;
        closeAuthModal();
        updateNavForUser(data);

        if (data.user_type === 'patient') showPage('dashboard');
        else if (data.user_type === 'doctor') showPage('doctor-queue');
        else showPage('admin-dashboard');
    } catch (err) {
        errEl.textContent = 'Lỗi kết nối server';
        errEl.classList.add('show');
    }
    return false;
}

async function doRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('register-error');
    errEl.classList.remove('show');

    const body = {
        full_name: document.getElementById('reg-name').value.trim(),
        phone: document.getElementById('reg-phone').value.trim(),
        gender: document.getElementById('reg-gender').value,
        password: document.getElementById('reg-password').value,
    };

    if (body.password.length < 6) {
        errEl.textContent = 'Mật khẩu phải có ít nhất 6 ký tự';
        errEl.classList.add('show');
        return false;
    }

    try {
        const res = await fetch(API + '/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.error || 'Đăng ký thất bại';
            errEl.classList.add('show');
            return false;
        }
        currentUser = { ...data, user_type: 'patient' };
        closeAuthModal();
        updateNavForUser(currentUser);
        showPage('dashboard');
    } catch (err) {
        errEl.textContent = 'Lỗi kết nối server';
        errEl.classList.add('show');
    }
    return false;
}

async function doLogout() {
    await fetch(API + '/api/auth/logout', { method: 'POST', credentials: 'include' });
    currentUser = null;
    chatSessionId = null;
    document.getElementById('nav-guest').classList.remove('hidden');
    document.getElementById('nav-user').classList.add('hidden');
    document.getElementById('nav-doctor').classList.add('hidden');
    document.getElementById('nav-admin').classList.add('hidden');
    showPage('landing');
}

// ════════════════════════════════════════════
// PAGE ROUTING
// ════════════════════════════════════════════

function showPage(page) {
    // Hide all pages
    document.querySelectorAll('[id^="page-"]').forEach(el => el.classList.add('hidden'));

    const target = document.getElementById('page-' + page);
    if (target) {
        target.classList.remove('hidden');
        // Re-trigger animation
        target.style.animation = 'none';
        target.offsetHeight; /* trigger reflow */
        target.style.animation = null; 
    } else {
        const landing = document.getElementById('page-landing');
        landing.classList.remove('hidden');
        landing.style.animation = 'none';
        landing.offsetHeight;
        landing.style.animation = null;
        return;
    }

    // Load data for specific pages
    if (page === 'dashboard') loadDashboard();
    else if (page === 'profile') loadProfile();
    else if (page === 'history') loadHistory();
    else if (page === 'doctor-queue') loadDoctorQueue();
    else if (page === 'admin-dashboard') loadAdminDashboard();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ════════════════════════════════════════════
// CHATBOT WIDGET
// ════════════════════════════════════════════

function openChatbot() {
    document.getElementById('chat-fab').classList.add('hidden');
    document.getElementById('chat-widget').classList.add('open');

    if (!chatSessionId) {
        startNewChat();
    }
}

function closeChatbot() {
    document.getElementById('chat-widget').classList.remove('open');
    document.getElementById('chat-fab').classList.remove('hidden');
}

async function startNewChat() {
    chatSessionId = null;
    chatFinished = false;
    const messagesEl = document.getElementById('chat-messages');
    messagesEl.innerHTML = '';

    const input = document.getElementById('chat-input');
    input.disabled = false;
    input.placeholder = 'Mô tả triệu chứng của bạn...';
    document.getElementById('chat-send').disabled = false;

    // Show loading
    showTypingIndicator();

    try {
        const res = await fetch(API + '/api/chat/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });
        const data = await res.json();
        removeTypingIndicator();

        if (data.error) {
            appendBotMessage('Lỗi: ' + data.error);
            return;
        }

        chatSessionId = data.session_id;
        data.messages.forEach(msg => appendBotMessage(msg.text));
    } catch (err) {
        removeTypingIndicator();
        appendBotMessage('Không thể kết nối server. Vui lòng thử lại.');
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || !chatSessionId || chatFinished) return;

    // Show user message
    appendUserMessage(text);
    input.value = '';
    input.focus();

    // Show typing
    showTypingIndicator();

    try {
        const res = await fetch(API + '/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ session_id: chatSessionId, message: text }),
        });
        const data = await res.json();
        removeTypingIndicator();

        if (data.error) {
            appendBotMessage('Lỗi: ' + data.error);
            return;
        }

        data.messages.forEach(msg => {
            appendBotMessage(msg.text, msg.type, msg.options);
        });

        if (data.status === 'finished') {
            chatFinished = true;
            input.disabled = true;
            input.placeholder = 'Phiên tư vấn đã kết thúc';
            document.getElementById('chat-send').disabled = true;
        }
    } catch (err) {
        removeTypingIndicator();
        appendBotMessage('Lỗi kết nối. Vui lòng thử lại.');
    }
}

function sendQuickReply(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    sendChatMessage();

    // Remove quick reply buttons after clicking
    document.querySelectorAll('.quick-replies').forEach(el => {
        el.style.opacity = '0.5';
        el.querySelectorAll('button').forEach(btn => btn.disabled = true);
    });
}

function appendUserMessage(text) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-msg patient';
    div.innerHTML = `
        <div class="msg-avatar">BN</div>
        <div class="msg-bubble">${escapeHtml(text)}</div>
    `;
    container.appendChild(div);
    scrollChat();
}

function appendBotMessage(text, type, options) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-msg bot';

    // Format markdown-like text
    let formatted = formatBotText(text);

    let html = `
        <div class="msg-avatar">AI</div>
        <div>
            <div class="msg-bubble${type === 'emergency' ? ' emergency-bubble' : ''}">${formatted}</div>
    `;

    // Add quick reply buttons for questions
    if (options && options.length > 0 && !chatFinished) {
        html += '<div class="quick-replies">';
        options.forEach(opt => {
            let cls = 'quick-reply-btn';
            if (opt.toLowerCase().includes('có')) cls += ' yes';
            else if (opt.toLowerCase().includes('không rõ')) cls += '';
            else if (opt.toLowerCase().includes('không')) cls += ' no';
            html += `<button class="${cls}" onclick="sendQuickReply('${escapeHtml(opt)}')">${escapeHtml(opt)}</button>`;
        });
        html += '</div>';
    }

    html += '</div>';
    div.innerHTML = html;

    // Style emergency messages
    if (type === 'emergency') {
        div.querySelector('.msg-bubble').style.background = '#fff5f5';
        div.querySelector('.msg-bubble').style.border = '2px solid #dc2626';
        div.querySelector('.msg-bubble').style.color = '#991b1b';
    }

    container.appendChild(div);
    scrollChat();
}

function formatBotText(text) {
    // Convert **bold** to <strong>
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/━+/g, '<hr style="border:none;border-top:1px solid #e2e8f0;margin:8px 0;">');
    html = html.replace(/\n/g, '<br>');
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="msg-avatar">AI</div>
        <div>
            <div class="msg-bubble typing-indicator-bubble" style="display:flex;gap:4px;align-items:center;padding:14px 16px;">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        </div>
    `;
    container.appendChild(div);
    scrollChat();
}

function removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

function scrollChat() {
    const container = document.getElementById('chat-messages');
    setTimeout(() => {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }, 50);
}

// ════════════════════════════════════════════
// PATIENT PAGES
// ════════════════════════════════════════════

async function loadDashboard() {
    if (!currentUser) return;
    document.getElementById('dash-name').textContent = currentUser.user_name || currentUser.name || '';

    try {
        const res = await fetch(API + '/api/patient/sessions', { credentials: 'include' });
        const data = await res.json();
        const sessions = data.sessions || [];

        document.getElementById('dash-total-sessions').textContent = sessions.length;
        document.getElementById('dash-completed').textContent = sessions.filter(s => s.status === 'completed').length;

        const listEl = document.getElementById('dash-sessions');
        if (sessions.length === 0) {
            listEl.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px;">Chưa có phiên tư vấn nào. Hãy bắt đầu ngay!</p>';
            return;
        }

        listEl.innerHTML = sessions.slice(0, 5).map(s => `
            <div class="session-item ${s.triage_urgency === 'emergency' ? 'emergency' : ''}"
                 onclick="viewSessionDetail(${s.id})">
                <div class="session-info">
                    <h4>Phiên #${s.id} — ${s.specialty_name || 'Chưa xác định'}</h4>
                    <span>${formatDate(s.start_time)} • ${s.status === 'completed' ? '✅ Hoàn thành' : '⏳ Đang xử lý'}</span>
                </div>
                <span class="badge ${urgencyBadge(s.triage_urgency)}">${urgencyLabel(s.triage_urgency)}</span>
            </div>
        `).join('');
    } catch (e) {
        console.error('Load dashboard error:', e);
    }
}

async function loadProfile() {
    try {
        const res = await fetch(API + '/api/patient/profile', { credentials: 'include' });
        const data = await res.json();

        document.getElementById('prof-name').value = data.full_name || '';
        document.getElementById('prof-phone').value = data.phone || '';
        document.getElementById('prof-gender').value = data.gender || '';
        document.getElementById('prof-height').value = data.height || '';
        document.getElementById('prof-weight').value = data.weight || '';
        document.getElementById('prof-blood').value = data.blood_type || '';
        document.getElementById('prof-allergies').value = data.allergies || '';
        document.getElementById('prof-conditions').value = data.underlying_conditions || '';
    } catch (e) {
        console.error('Load profile error:', e);
    }
}

async function saveProfile(e) {
    e.preventDefault();
    const body = {
        height: parseFloat(document.getElementById('prof-height').value) || null,
        weight: parseFloat(document.getElementById('prof-weight').value) || null,
        blood_type: document.getElementById('prof-blood').value,
        allergies: document.getElementById('prof-allergies').value,
        underlying_conditions: document.getElementById('prof-conditions').value,
    };
    try {
        const res = await fetch(API + '/api/patient/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (data.success) {
            alert('✅ Đã lưu hồ sơ y tế thành công!');
        }
    } catch (e) {
        alert('Lỗi khi lưu hồ sơ');
    }
    return false;
}

async function loadHistory() {
    try {
        const res = await fetch(API + '/api/patient/sessions', { credentials: 'include' });
        const data = await res.json();
        const sessions = data.sessions || [];

        const listEl = document.getElementById('history-list');
        if (sessions.length === 0) {
            listEl.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px;">Chưa có phiên tư vấn nào</p>';
            return;
        }

        listEl.innerHTML = sessions.map(s => `
            <div class="session-item ${s.triage_urgency === 'emergency' ? 'emergency' : ''}"
                 onclick="viewSessionDetail(${s.id})">
                <div class="session-info">
                    <h4>Phiên #${s.id} — ${s.specialty_name || 'Chưa xác định'}</h4>
                    <span>${formatDate(s.start_time)}</span>
                </div>
                <span class="badge ${urgencyBadge(s.triage_urgency)}">${urgencyLabel(s.triage_urgency)}</span>
            </div>
        `).join('');
    } catch (e) {
        console.error('Load history error:', e);
    }
}

async function viewSessionDetail(sessionId) {
    showPage('history-detail');
    document.getElementById('detail-session-id').textContent = sessionId;

    try {
        const res = await fetch(API + `/api/chat/history/${sessionId}`, { credentials: 'include' });
        const data = await res.json();
        const messages = data.messages || [];

        const messagesEl = document.getElementById('detail-messages');
        messagesEl.innerHTML = messages.map(m => `
            <div class="chat-msg ${m.role}">
                <div class="msg-avatar">${m.role === 'bot' ? 'AI' : 'BN'}</div>
                <div class="msg-bubble">${formatBotText(m.text)}</div>
            </div>
        `).join('');

        // Load recommendation
        const recEl = document.getElementById('detail-recommendation');
        // Find last bot message that looks like a result
        const resultMsg = messages.filter(m => m.role === 'bot').pop();
        recEl.innerHTML = resultMsg ? formatBotText(resultMsg.text) : '<p>Không có kết quả</p>';
    } catch (e) {
        console.error('Load detail error:', e);
    }
}

// ════════════════════════════════════════════
// DOCTOR PAGES
// ════════════════════════════════════════════

let currentDoctorSessionId = null;

async function loadDoctorQueue() {
    try {
        const res = await fetch(API + '/api/doctor/queue', { credentials: 'include' });
        const data = await res.json();
        const queue = data.queue || [];

        const tbody = document.getElementById('doctor-queue-body');
        if (queue.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:40px;">Không có ca chờ khám</td></tr>';
            return;
        }

        tbody.innerHTML = queue.map(q => `
            <tr class="${q.triage_urgency === 'emergency' ? 'emergency' : ''}" style="cursor:pointer;" onclick="viewDoctorSession(${q.id})">
                <td><strong>#${q.id}</strong></td>
                <td>${escapeHtml(q.patient_name || '')}</td>
                <td><span class="badge badge-info">${escapeHtml(q.specialty_name || 'N/A')}</span></td>
                <td><span class="badge ${urgencyBadge(q.triage_urgency)}">${urgencyLabel(q.triage_urgency)}</span></td>
                <td>${formatDate(q.end_time)}</td>
                <td><button class="btn btn-primary" style="padding:6px 16px;font-size:0.82rem;" onclick="event.stopPropagation();viewDoctorSession(${q.id})">Xem</button></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Load queue error:', e);
    }
}

async function viewDoctorSession(sessionId) {
    currentDoctorSessionId = sessionId;
    showPage('doctor-detail');
    document.getElementById('doc-detail-id').textContent = sessionId;
    document.getElementById('verify-correction').classList.add('hidden');

    try {
        const res = await fetch(API + `/api/doctor/session/${sessionId}`, { credentials: 'include' });
        const data = await res.json();

        // Patient info
        const infoEl = document.getElementById('doc-patient-info');
        const s = data.session;
        infoEl.innerHTML = `
            <div class="form-group"><label>Họ tên</label><p><strong>${escapeHtml(s.full_name || '')}</strong></p></div>
            <div class="form-group"><label>SĐT</label><p>${escapeHtml(s.phone || 'N/A')}</p></div>
            <div class="form-group"><label>Giới tính</label><p>${escapeHtml(s.gender || 'N/A')}</p></div>
            <div class="form-group"><label>Chiều cao / Cân nặng</label><p>${s.height || '-'} cm / ${s.weight || '-'} kg</p></div>
            <div class="form-group"><label>Dị ứng</label><p>${escapeHtml(s.allergies || 'Không')}</p></div>
            <div class="form-group"><label>Bệnh nền</label><p>${escapeHtml(s.underlying_conditions || 'Không')}</p></div>
        `;

        // Diseases
        const diseasesEl = document.getElementById('doc-diseases');
        if (data.diseases && data.diseases.length > 0) {
            diseasesEl.innerHTML = data.diseases.map((d, i) => `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);">
                    <span><strong>${i+1}.</strong> ${escapeHtml(d.disease_name)}</span>
                    <span class="badge badge-info">${(d.hybrid_score || 0).toFixed(1)} điểm</span>
                </div>
            `).join('');
        } else {
            diseasesEl.innerHTML = '<p style="color:var(--text-muted);">Không có dữ liệu</p>';
        }

        // Recommendation
        document.getElementById('doc-recommendation').innerHTML = formatBotText(data.recommendation || 'Không có');

        // Chat history
        const chatEl = document.getElementById('doc-chat-history');
        chatEl.innerHTML = (data.messages || []).map(m => `
            <div class="chat-msg ${m.role}">
                <div class="msg-avatar">${m.role === 'bot' ? 'AI' : 'BN'}</div>
                <div class="msg-bubble">${formatBotText(m.text)}</div>
            </div>
        `).join('');

        // Load diseases for correction dropdown
        const diseasesRes = await fetch(API + '/api/admin/diseases', { credentials: 'include' });
        const diseasesData = await diseasesRes.json();
        const select = document.getElementById('actual-disease');
        select.innerHTML = '<option value="">-- Chọn bệnh lý --</option>' +
            (diseasesData.diseases || []).map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    } catch (e) {
        console.error('Load doctor session error:', e);
    }
}

function verifyAI(isCorrect) {
    if (isCorrect) {
        fetch(API + `/api/doctor/verify/${currentDoctorSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ is_correct: true }),
        }).then(() => alert('✅ Đã xác nhận AI chẩn đoán đúng!'));
    } else {
        document.getElementById('verify-correction').classList.remove('hidden');
    }
}

function submitCorrection() {
    const diseaseId = document.getElementById('actual-disease').value;
    if (!diseaseId) {
        alert('Vui lòng chọn bệnh lý thực tế');
        return;
    }
    fetch(API + `/api/doctor/verify/${currentDoctorSessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ is_correct: false, actual_disease_id: parseInt(diseaseId) }),
    }).then(() => {
        alert('✅ Đã ghi nhận đánh giá. Cảm ơn bác sĩ!');
        document.getElementById('verify-correction').classList.add('hidden');
    });
}

// ════════════════════════════════════════════
// ADMIN PAGES
// ════════════════════════════════════════════

async function loadAdminDashboard() {
    try {
        const res = await fetch(API + '/api/admin/stats', { credentials: 'include' });
        const data = await res.json();

        document.getElementById('admin-stats-grid').innerHTML = `
            <div class="stat-card">
                <div class="stat-icon" style="background:rgba(26,86,219,0.1);">💬</div>
                <div class="stat-value">${data.total_sessions || 0}</div>
                <div class="stat-label">Tổng phiên chat</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background:rgba(5,150,105,0.1);">✅</div>
                <div class="stat-value">${data.completed_sessions || 0}</div>
                <div class="stat-label">Hoàn thành</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background:rgba(220,38,38,0.1);">🚨</div>
                <div class="stat-value">${data.emergency_count || 0}</div>
                <div class="stat-label">Ca khẩn cấp</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background:rgba(124,58,237,0.1);">👥</div>
                <div class="stat-value">${data.total_patients || 0}</div>
                <div class="stat-label">Bệnh nhân</div>
            </div>
        `;

        const chartEl = document.getElementById('admin-specialty-chart');
        const stats = data.specialty_distribution || [];
        if (stats.length === 0) {
            chartEl.innerHTML = '<p style="color:var(--text-muted);">Chưa có dữ liệu</p>';
        } else {
            const maxCount = Math.max(...stats.map(s => s.count));
            chartEl.innerHTML = stats.map(s => `
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <span style="width:150px;font-size:0.9rem;font-weight:500;">${escapeHtml(s.name)}</span>
                    <div style="flex:1;background:#f1f5f9;border-radius:6px;height:28px;overflow:hidden;">
                        <div style="width:${(s.count/maxCount*100)}%;height:100%;background:linear-gradient(90deg,var(--primary),var(--secondary));border-radius:6px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
                            <span style="color:white;font-size:0.78rem;font-weight:600;">${s.count}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Load admin dashboard error:', e);
    }
}

async function showAdminTab(tab) {
    const titleEl = document.getElementById('admin-tab-title');
    const headEl = document.getElementById('admin-table-head');
    const bodyEl = document.getElementById('admin-table-body');

    try {
        const btnAdd = document.getElementById('btn-add-new');
        const tableCard = document.getElementById('admin-table-card');
        const sandboxCard = document.getElementById('sandbox-card');
        
        if (tab === 'sandbox') {
            tableCard.classList.add('hidden');
            sandboxCard.classList.remove('hidden');
            if(document.getElementById('sandbox-messages').innerHTML === '') startSandbox();
            return;
        } else {
            tableCard.classList.remove('hidden');
            sandboxCard.classList.add('hidden');
            btnAdd.classList.remove('hidden');
            btnAdd.onclick = () => openCrudModal(tab);
        }

        if (tab === 'specialties') {
            titleEl.textContent = '🏥 Danh mục Chuyên khoa';
            const res = await fetch(API + '/api/admin/specialties', { credentials: 'include' });
            const data = await res.json();
            headEl.innerHTML = '<tr><th>ID</th><th>Mã</th><th>Tên chuyên khoa</th><th>Mô tả</th><th>Thao tác</th></tr>';
            bodyEl.innerHTML = (data.specialties || []).map(s => `
                <tr><td>${s.id}</td><td><code>${escapeHtml(s.code)}</code></td><td><strong>${escapeHtml(s.name)}</strong></td><td>${escapeHtml(s.description || '')}</td>
                <td><button class="btn btn-outline" style="padding:4px 8px;font-size:0.8rem;" onclick='openCrudModal("specialties", ${JSON.stringify(s)})'>Sửa</button>
                <button class="btn btn-danger" style="padding:4px 8px;font-size:0.8rem;" onclick="deleteRecord('specialties', ${s.id})">Xóa</button></td></tr>
            `).join('');
        } else if (tab === 'symptoms') {
            titleEl.textContent = '🩺 Danh mục Triệu chứng';
            const res = await fetch(API + '/api/admin/symptoms', { credentials: 'include' });
            const data = await res.json();
            headEl.innerHTML = '<tr><th>ID</th><th>Mã</th><th>Tên</th><th>Câu hỏi AI</th><th>Red Flag</th><th>Thao tác</th></tr>';
            bodyEl.innerHTML = (data.symptoms || []).map(s => `
                <tr>
                    <td>${s.id}</td>
                    <td><code>${escapeHtml(s.code)}</code></td>
                    <td>${escapeHtml(s.name)}</td>
                    <td style="max-width:200px;">${escapeHtml(s.question_text || '')}</td>
                    <td>${s.is_red_flag ? '<span class="badge badge-danger">🚩 Cờ đỏ</span>' : '<span class="badge badge-neutral">Bình thường</span>'}</td>
                    <td><button class="btn btn-outline" style="padding:4px 8px;font-size:0.8rem;" onclick='openCrudModal("symptoms", ${JSON.stringify(s)})'>Sửa</button>
                    <button class="btn btn-danger" style="padding:4px 8px;font-size:0.8rem;" onclick="deleteRecord('symptoms', ${s.id})">Xóa</button></td>
                </tr>
            `).join('');
        } else if (tab === 'diseases') {
            titleEl.textContent = '🦠 Danh mục Bệnh lý';
            const res = await fetch(API + '/api/admin/diseases', { credentials: 'include' });
            const data = await res.json();
            headEl.innerHTML = '<tr><th>ID</th><th>ICD</th><th>Tên bệnh</th><th>Chuyên khoa</th><th>Thao tác</th></tr>';
            bodyEl.innerHTML = (data.diseases || []).map(d => `
                <tr>
                    <td>${d.id}</td>
                    <td><code>${escapeHtml(d.icd_code || '')}</code></td>
                    <td><strong>${escapeHtml(d.name)}</strong></td>
                    <td><span class="badge badge-info">${escapeHtml(d.specialty_name)}</span></td>
                    <td style="white-space:nowrap;">
                        <button class="btn btn-primary" style="padding:4px 8px;font-size:0.8rem;" onclick="openRulesModal(${d.id}, '${escapeHtml(d.name)}')">Luật</button>
                        <button class="btn btn-outline" style="padding:4px 8px;font-size:0.8rem;" onclick='openCrudModal("diseases", ${JSON.stringify(d)})'>Sửa</button>
                        <button class="btn btn-danger" style="padding:4px 8px;font-size:0.8rem;" onclick="deleteRecord('diseases', ${d.id})">Xóa</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        bodyEl.innerHTML = `<tr><td colspan="5" style="color:var(--danger);">Lỗi: ${e.message}</td></tr>`;
    }
}

// ════════════════════════════════════════════
// ADMIN CRUD LOGIC
// ════════════════════════════════════════════
let currentCrudTab = '';
let currentCrudId = null;

async function openCrudModal(tab, data = null) {
    currentCrudTab = tab;
    currentCrudId = data ? data.id : null;
    const modal = document.getElementById('crud-modal');
    const title = document.getElementById('crud-modal-title');
    const body = document.getElementById('crud-modal-body');
    
    title.textContent = data ? "Cập nhật" : "Thêm mới";
    let html = '';
    
    if(tab === 'specialties') {
        html = `
            <div class="form-group"><label>Mã chuyên khoa (Code)</label><input type="text" id="crud-code" value="${data?escapeHtml(data.code):''}" ${data?'disabled':''}></div>
            <div class="form-group"><label>Tên chuyên khoa</label><input type="text" id="crud-name" value="${data?escapeHtml(data.name):''}"></div>
            <div class="form-group"><label>Mô tả</label><textarea id="crud-desc">${data?escapeHtml(data.description||''):''}</textarea></div>
        `;
    } else if(tab === 'symptoms') {
        html = `
            <div class="form-group"><label>Mã triệu chứng</label><input type="text" id="crud-code" value="${data?escapeHtml(data.code):''}" ${data?'disabled':''}></div>
            <div class="form-group"><label>Tên chuẩn y khoa</label><input type="text" id="crud-name" value="${data?escapeHtml(data.name):''}"></div>
            <div class="form-group"><label>Câu hỏi xác nhận AI</label><input type="text" id="crud-question" value="${data?escapeHtml(data.question_text||''):''}"></div>
            <div class="form-group"><label><input type="checkbox" id="crud-redflag" ${data&&data.is_red_flag?'checked':''}> Là dấu hiệu nguy kịch (Red Flag)</label></div>
        `;
    } else if(tab === 'diseases') {
        // fetch specialties for select
        const res = await fetch(API + '/api/admin/specialties', { credentials: 'include' });
        const resData = await res.json();
        const specOptions = (resData.specialties || []).map(s => `<option value="${s.id}" ${data&&data.specialty_id===s.id?'selected':''}>${escapeHtml(s.name)}</option>`).join('');
        
        html = `
            <div class="form-group"><label>Mã ICD</label><input type="text" id="crud-icd" value="${data?escapeHtml(data.icd_code||''):''}"></div>
            <div class="form-group"><label>Tên bệnh lý</label><input type="text" id="crud-name" value="${data?escapeHtml(data.name):''}"></div>
            <div class="form-group"><label>Chuyên khoa</label><select id="crud-spec">${specOptions}</select></div>
            <div class="form-group"><label>Mô tả</label><textarea id="crud-desc">${data?escapeHtml(data.description||''):''}</textarea></div>
        `;
    }
    
    body.innerHTML = html;
    modal.style.display = 'flex';
}

function closeCrudModal() { document.getElementById('crud-modal').style.display = 'none'; }

async function saveCrudData() {
    let payload = {};
    if(currentCrudTab === 'specialties') {
        payload = { code: document.getElementById('crud-code').value, name: document.getElementById('crud-name').value, description: document.getElementById('crud-desc').value };
    } else if(currentCrudTab === 'symptoms') {
        payload = { code: document.getElementById('crud-code').value, name: document.getElementById('crud-name').value, question_text: document.getElementById('crud-question').value, is_red_flag: document.getElementById('crud-redflag').checked };
    } else if(currentCrudTab === 'diseases') {
        payload = { icd_code: document.getElementById('crud-icd').value, name: document.getElementById('crud-name').value, description: document.getElementById('crud-desc').value, specialty_id: parseInt(document.getElementById('crud-spec').value) };
    }

    const url = API + '/api/admin/' + currentCrudTab + (currentCrudId ? '/' + currentCrudId : '');
    const method = currentCrudId ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, { method, headers: {'Content-Type':'application/json'}, credentials:'include', body: JSON.stringify(payload) });
        if(res.ok) {
            closeCrudModal();
            showAdminTab(currentCrudTab);
        } else {
            alert('Lỗi khi lưu dữ liệu');
        }
    } catch(e) { alert(e.message); }
}

async function deleteRecord(tab, id) {
    if(!confirm("Bạn có chắc chắn muốn xóa bản ghi này?")) return;
    try {
        const res = await fetch(API + '/api/admin/' + tab + '/' + id, { method: 'DELETE', credentials: 'include' });
        if(res.ok) showAdminTab(tab);
        else alert('Xóa thất bại (Có thể do ràng buộc dữ liệu)');
    } catch(e) { alert(e.message); }
}

// ════════════════════════════════════════════
// RULES ENGINE LOGIC
// ════════════════════════════════════════════
let currentRulesDiseaseId = null;

async function openRulesModal(diseaseId, diseaseName) {
    currentRulesDiseaseId = diseaseId;
    document.getElementById('rules-disease-name').textContent = diseaseName;
    document.getElementById('rules-modal').style.display = 'flex';
    document.getElementById('rules-table-body').innerHTML = '<tr><td colspan="5">Đang tải...</td></tr>';
    
    try {
        // Load symptoms for dropdown
        const symRes = await fetch(API + '/api/admin/symptoms', { credentials: 'include' });
        const symData = await symRes.json();
        document.getElementById('rule-symptom-select').innerHTML = '<option value="">-- Chọn triệu chứng --</option>' + (symData.symptoms||[]).map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
        
        // Load rules
        const res = await fetch(API + '/api/admin/rules/' + diseaseId, { credentials: 'include' });
        const data = await res.json();
        const rules = data.rules || [];
        document.getElementById('rules-table-body').innerHTML = '';
        rules.forEach(r => appendRuleRow(r.symptom_id, r.symptom_name, r.weight, r.is_mandatory, r.is_exclusion));
    } catch(e) {
        document.getElementById('rules-table-body').innerHTML = `<tr><td colspan="5" style="color:red">${e.message}</td></tr>`;
    }
}

function closeRulesModal() { document.getElementById('rules-modal').style.display = 'none'; }

function appendRuleRow(symptomId, symptomName, weight, isMandatory, isExclusion) {
    const tbody = document.getElementById('rules-table-body');
    const tr = document.createElement('tr');
    tr.dataset.symptomId = symptomId;
    tr.innerHTML = `
        <td>${escapeHtml(symptomName)}</td>
        <td><input type="number" min="0" max="10" step="0.1" value="${weight}" class="rule-weight" style="width:60px;"></td>
        <td><input type="checkbox" class="rule-mandatory" ${isMandatory?'checked':''}></td>
        <td><input type="checkbox" class="rule-exclusion" ${isExclusion?'checked':''}></td>
        <td><button class="btn btn-danger" style="padding:4px; font-size: 0.8rem;" onclick="this.closest('tr').remove()">Xóa</button></td>
    `;
    tbody.appendChild(tr);
}

function addRuleRow() {
    const sel = document.getElementById('rule-symptom-select');
    if(!sel.value) return;
    const symId = sel.value;
    const symName = sel.options[sel.selectedIndex].text;
    
    // Check if already exists
    const existing = Array.from(document.querySelectorAll('#rules-table-body tr')).find(tr => tr.dataset.symptomId === symId);
    if(existing) { alert("Triệu chứng này đã có trong luật."); return; }
    
    appendRuleRow(symId, symName, 5.0, false, false);
}

async function saveRulesData() {
    const rows = document.querySelectorAll('#rules-table-body tr');
    const rules = [];
    rows.forEach(tr => {
        rules.push({
            symptom_id: parseInt(tr.dataset.symptomId),
            weight: parseFloat(tr.querySelector('.rule-weight').value),
            is_mandatory: tr.querySelector('.rule-mandatory').checked,
            is_exclusion: tr.querySelector('.rule-exclusion').checked
        });
    });
    
    try {
        const res = await fetch(API + '/api/admin/rules/' + currentRulesDiseaseId, {
            method: 'POST', headers: {'Content-Type':'application/json'}, credentials:'include',
            body: JSON.stringify({rules})
        });
        if(res.ok) { alert("Lưu luật thành công!"); closeRulesModal(); }
        else alert("Lỗi khi lưu luật");
    } catch(e) { alert(e.message); }
}

// ════════════════════════════════════════════
// SANDBOX AI LOGIC
// ════════════════════════════════════════════
async function startSandbox() {
    document.getElementById('sandbox-messages').innerHTML = '';
    document.getElementById('sandbox-input').value = '';
    document.getElementById('sandbox-input').disabled = false;
    document.getElementById('sandbox-send').disabled = false;
    
    try {
        const res = await fetch(API + '/api/admin/sandbox/start', { method: 'POST', credentials: 'include' });
        const data = await res.json();
        if(data.messages) {
            data.messages.forEach(m => appendSandboxMsg(m.text, 'bot'));
        }
    } catch(e) { appendSandboxMsg("Lỗi khởi tạo Sandbox: " + e.message, 'bot'); }
}

async function sendSandboxMessage() {
    const input = document.getElementById('sandbox-input');
    const text = input.value.trim();
    if(!text) return;
    
    appendSandboxMsg(text, 'user');
    input.value = '';
    
    try {
        const res = await fetch(API + '/api/admin/sandbox/chat', {
            method: 'POST', headers: {'Content-Type':'application/json'}, credentials:'include',
            body: JSON.stringify({message: text})
        });
        const data = await res.json();
        if(data.messages) {
            data.messages.forEach(m => {
                if(m.options) {
                    appendSandboxMsg(m.text + "<br><br>Gợi ý: " + m.options.join(" / "), 'bot');
                } else {
                    appendSandboxMsg(m.text, 'bot', m.type === 'result');
                }
            });
        }
        if(data.status === 'finished') {
            document.getElementById('sandbox-input').disabled = true;
            document.getElementById('sandbox-send').disabled = true;
        }
    } catch(e) { appendSandboxMsg("Lỗi xử lý: " + e.message, 'bot'); }
}

function appendSandboxMsg(text, role, isResult=false) {
    const container = document.getElementById('sandbox-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.innerHTML = `
        ${role === 'bot' ? '<div class="msg-avatar">🤖</div>' : ''}
        <div class="msg-bubble" style="${isResult?'background:var(--success);color:white;':''}">${formatBotText(text)}</div>
        ${role === 'user' ? '<div class="msg-avatar">👨‍⚕️</div>' : ''}
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ════════════════════════════════════════════
// SPECIALTIES (Landing page)
// ════════════════════════════════════════════

const SPECIALTY_EMOJIS = {
    'noi': '🫀', 'ngoai': '🔪', 'nhi': '👶', 'san': '🤰', 'mat': '👁️',
    'tmh': '👂', 'rhm': '🦷', 'da_lieu': '🧴', 'than_kinh': '🧠',
    'co_xuong_khop': '🦴', 'tim_mach': '❤️', 'ho_hap': '🫁',
    'tieu_hoa': '🫃', 'noi_tiet': '🧬', 'than_tiet_nieu': '🫘',
};

async function loadSpecialties() {
    try {
        const res = await fetch(API + '/api/admin/specialties');
        const data = await res.json();
        const list = data.specialties || [];
        const container = document.getElementById('specialties-list');

        if (list.length === 0) {
            container.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Đang tải chuyên khoa...</p>';
            return;
        }

        container.innerHTML = list.map(s => {
            const emoji = SPECIALTY_EMOJIS[s.code] || '🏥';
            return `
                <div class="specialty-card">
                    <div class="emoji">${emoji}</div>
                    <h4>${escapeHtml(s.name)}</h4>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.log('Could not load specialties');
    }
}

// ════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════

function formatDate(isoStr) {
    if (!isoStr) return 'N/A';
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
        return isoStr;
    }
}

function urgencyBadge(urgency) {
    if (urgency === 'emergency') return 'badge-danger';
    if (urgency === 'high') return 'badge-warning';
    return 'badge-success';
}

function urgencyLabel(urgency) {
    if (urgency === 'emergency') return '🚨 Khẩn cấp';
    if (urgency === 'high') return '⚡ Ưu tiên';
    return '✅ Bình thường';
}
