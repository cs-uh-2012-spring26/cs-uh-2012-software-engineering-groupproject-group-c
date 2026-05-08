/* ============================================================
   Fitness Class Manager — Vanilla JS Front-End  (v3)
   ============================================================ */

// ── Configuration ────────────────────────────────────────────
const API_BASE = window.location.origin;

// ── State ────────────────────────────────────────────────────
let token = localStorage.getItem('token') || null;
let userRole = localStorage.getItem('role') || null;
let userEmail = localStorage.getItem('email') || null;

// ── DOM helpers ──────────────────────────────────────────────
const $ = sel => document.querySelector(sel);
const show = el => el.classList.remove('hidden');
const hide = el => el.classList.add('hidden');
const showMsg = (el, msg) => { el.textContent = msg; show(el); };
const hideMsg = (...els) => els.forEach(e => { e.textContent = ''; hide(e); });

// ── DOM refs ─────────────────────────────────────────────────
const navUser = $('#nav-user');
const navGreeting = $('#nav-greeting');
const navAuth = $('#nav-auth');
const navCreate = $('#nav-create');
const navPrefs = $('#nav-prefs');
const navLinks = document.querySelectorAll('.nav-link');
const btnLogout = $('#btn-logout');
const loginForm = $('#login-form');
const registerForm = $('#register-form');
const loginError = $('#login-error');
const registerError = $('#register-error');
const registerSuccess = $('#register-success');
const createClassForm = $('#create-class-form');
const createClassError = $('#create-class-error');
const createClassSuccess = $('#create-class-success');
const classList = $('#class-list');
const btnRefresh = $('#btn-refresh');
const tabs = document.querySelectorAll('.tab');
const regNotif = $('#reg-notif');
const telegramField = $('#telegram-field');

// Recurrence toggle in create form
const ccRecToggle = $('#cc-recurrence-toggle');
const ccRecFields = $('#cc-recurrence-fields');

// Preferences form
const prefsForm = $('#prefs-form');
const prefsError = $('#prefs-error');
const prefsSuccess = $('#prefs-success');
const prefsTelegramField = $('#prefs-telegram-field');

// Modal refs
const modalOverlay = $('#modal-overlay');
const modalTitle = $('#modal-title');
const modalMessage = $('#modal-message');
const modalConfirm = $('#modal-confirm');
const modalCancel = $('#modal-cancel');

const detailsOverlay = $('#details-overlay');
const detailsTitle = $('#details-title');
const detailsBody = $('#details-body');
const detailsClose = $('#details-close');

const recurrenceOverlay = $('#recurrence-overlay');
const recurrenceForm = $('#recurrence-form');
const recurrenceClose = $('#recurrence-close');

// Reminder Prompt refs
const reminderPromptOverlay = $('#reminder-prompt-overlay');
const reminderPromptThis = $('#reminder-prompt-this');
const reminderPromptAll = $('#reminder-prompt-all');
const reminderPromptCancel = $('#reminder-prompt-cancel');

// ── Toast ────────────────────────────────────────────────────
function toast(msg, type = 'success') {
    const el = $('#toast');
    el.textContent = msg;
    el.className = `toast toast-${type}`;
    show(el);
    clearTimeout(el._t);
    el._t = setTimeout(() => hide(el), 3500);
}

// ── API wrapper ──────────────────────────────────────────────
async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
}

// ── Confirmation modal ───────────────────────────────────────
function confirmAction(title, message) {
    return new Promise(resolve => {
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        show(modalOverlay);
        const cleanup = (val) => {
            hide(modalOverlay);
            modalConfirm.removeEventListener('click', onYes);
            modalCancel.removeEventListener('click', onNo);
            resolve(val);
        };
        const onYes = () => cleanup(true);
        const onNo = () => cleanup(false);
        modalConfirm.addEventListener('click', onYes);
        modalCancel.addEventListener('click', onNo);
    });
}

// ── Details modal ────────────────────────────────────────────
function showDetails(title, html) {
    detailsTitle.textContent = title;
    detailsBody.innerHTML = html;
    show(detailsOverlay);
}
detailsClose.addEventListener('click', () => hide(detailsOverlay));
detailsOverlay.addEventListener('click', e => { if (e.target === detailsOverlay) hide(detailsOverlay); });

// ── Recurrence modal ─────────────────────────────────────────
recurrenceClose.addEventListener('click', () => hide(recurrenceOverlay));
recurrenceOverlay.addEventListener('click', e => { if (e.target === recurrenceOverlay) hide(recurrenceOverlay); });

// ── Reminder Prompt modal ─────────────────────────────────────────
function promptForReminderTarget() {
    return new Promise(resolve => {
        show(reminderPromptOverlay);
        const cleanup = (val) => {
            hide(reminderPromptOverlay);
            reminderPromptThis.removeEventListener('click', onThis);
            reminderPromptAll.removeEventListener('click', onAll);
            reminderPromptCancel.removeEventListener('click', onCancel);
            resolve(val);
        };
        const onThis = () => cleanup('this');
        const onAll = () => cleanup('all');
        const onCancel = () => cleanup(null);
        reminderPromptThis.addEventListener('click', onThis);
        reminderPromptAll.addEventListener('click', onAll);
        reminderPromptCancel.addEventListener('click', onCancel);
    });
}

// ══════════════════════════════════════════════════════════════
//  NAVIGATION — classes page is the default / landing page
// ══════════════════════════════════════════════════════════════

function navigateTo(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = $(`#page-${page}`);
    if (target) target.classList.add('active');

    // Highlight the nav link (skip hidden ones gracefully)
    navLinks.forEach(l => l.classList.remove('active'));
    const link = $(`[data-page="${page}"]`);
    if (link && !link.classList.contains('hidden')) link.classList.add('active');

    if (page === 'classes') loadClasses();
}

navLinks.forEach(link => {
    link.addEventListener('click', () => navigateTo(link.dataset.page));
});
$('#nav-brand').addEventListener('click', () => navigateTo('classes'));

// ══════════════════════════════════════════════════════════════
//  AUTH STATE
// ══════════════════════════════════════════════════════════════

function setLoggedIn(email, role, accessToken) {
    token = accessToken; userRole = role; userEmail = email;
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    localStorage.setItem('email', email);
    renderUI();
    navigateTo('classes');
}

function logout() {
    token = null; userRole = null; userEmail = null;
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('email');
    renderUI();
    navigateTo('classes');   // always go back to classes list
    toast('Logged out');
}

function renderUI() {
    if (token) {
        show(navUser); hide(navAuth); show(navPrefs);
        navGreeting.textContent = `${userEmail} (${userRole})`;
        if (userRole === 'trainer' || userRole === 'admin') {
            show(navCreate);
        } else {
            hide(navCreate);
        }
    } else {
        hide(navUser); show(navAuth); hide(navCreate); hide(navPrefs);
    }
}

// ── Tab switching ────────────────────────────────────────────
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        if (tab.dataset.tab === 'login') { show(loginForm); hide(registerForm); }
        else { hide(loginForm); show(registerForm); }
        hideMsg(loginError, registerError, registerSuccess);
    });
});

// ── Telegram toggle (registration) ───────────────────────────
regNotif.addEventListener('change', () => {
    regNotif.value === 'telegram' ? show(telegramField) : hide(telegramField);
});

// ── Recurrence toggle (create class form) ────────────────────
ccRecToggle.addEventListener('change', () => {
    ccRecToggle.checked ? show(ccRecFields) : hide(ccRecFields);
});

// ── Telegram toggle (preferences) ────────────────────────────
$('#prefs-channels').addEventListener('change', () => {
    const telegramChecked = $('#prefs-channels input[value="telegram"]').checked;
    telegramChecked ? show(prefsTelegramField) : hide(prefsTelegramField);
});

// ══════════════════════════════════════════════════════════════
//  LOGIN
// ══════════════════════════════════════════════════════════════

loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    hideMsg(loginError);
    const email = $('#login-email').value.trim();
    const password = $('#login-password').value;
    const { ok, data } = await api('/Authentication/login', {
        method: 'POST', body: JSON.stringify({ email, password }),
    });
    if (ok) {
        setLoggedIn(email, data.role, data.token);
        toast('Logged in!');
    } else {
        showMsg(loginError, data.message || 'Login failed');
    }
});

// ══════════════════════════════════════════════════════════════
//  REGISTER
// ══════════════════════════════════════════════════════════════

registerForm.addEventListener('submit', async e => {
    e.preventDefault();
    hideMsg(registerError, registerSuccess);
    const body = {
        username: $('#reg-username').value.trim(),
        email: $('#reg-email').value.trim(),
        password: $('#reg-password').value,
        phone: $('#reg-phone').value.trim(),
        role: $('#reg-role').value,
        notification_preferences: [regNotif.value],
    };
    if (regNotif.value === 'telegram') body.telegram_chat_id = $('#reg-telegram').value.trim();
    const { ok, data } = await api('/Authentication/register', {
        method: 'POST', body: JSON.stringify(body),
    });
    if (ok) {
        showMsg(registerSuccess, 'Account created! You can now log in.');
        registerForm.reset();
    } else {
        showMsg(registerError, data.message || 'Registration failed');
    }
});

// ── Logout ───────────────────────────────────────────────────
btnLogout.addEventListener('click', logout);

// ══════════════════════════════════════════════════════════════
//  PREFERENCES
// ══════════════════════════════════════════════════════════════

prefsForm.addEventListener('submit', async e => {
    e.preventDefault();
    hideMsg(prefsError, prefsSuccess);

    const channels = [...$('#prefs-channels').querySelectorAll('input:checked')].map(cb => cb.value);
    if (channels.length === 0) {
        showMsg(prefsError, 'Select at least one notification channel.');
        return;
    }

    const body = { notification_preferences: channels };
    const telegramChecked = channels.includes('telegram');
    if (telegramChecked) {
        const chatId = $('#prefs-telegram-id').value.trim();
        if (!chatId) {
            showMsg(prefsError, 'Telegram Chat ID is required when telegram is selected.');
            return;
        }
        body.telegram_chat_id = chatId;
    }

    const yes = await confirmAction('Update Preferences', 'Save your notification preferences?');
    if (!yes) return;

    const { ok, data } = await api('/Authentication/preferences', {
        method: 'PATCH', body: JSON.stringify(body),
    });
    if (ok) {
        showMsg(prefsSuccess, 'Preferences updated!');
        toast('Preferences saved');
    } else {
        showMsg(prefsError, data.message || 'Failed to update preferences');
    }
});

// ── HTML escape helper ───────────────────────────────────────
function esc(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ── Filter toggle ────────────────────────────────────────────
const filterPast = $('#filter-past');
filterPast.addEventListener('change', () => loadClasses());

// ── Date helpers ─────────────────────────────────────────────
function parseDate(str) {
    if (!str) return null;
    const d = new Date(str);
    return isNaN(d) ? null : d;
}

function formatDateGroup(date) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1);
    const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (target.getTime() === today.getTime()) return '📅 Today';
    if (target.getTime() === tomorrow.getTime()) return '📅 Tomorrow';

    const diff = Math.round((target - today) / 86400000);
    const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
    const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    if (diff > 0 && diff <= 6) return `📅 ${dayName}, ${monthDay}`;
    if (diff < 0) return `📅 ${monthDay} (Past)`;
    return `📅 ${dayName}, ${monthDay}`;
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function friendlyDate(date) {
    const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `${monthDay} · ${formatTime(date)}`;
}

async function loadClasses() {
    classList.innerHTML = '<p class="placeholder-text">Loading classes…</p>';
    const { ok, data } = await api('/classes/');
    if (!ok) { classList.innerHTML = '<p class="placeholder-text">Could not load classes.</p>'; return; }

    let classes = data.classes || [];
    if (!classes.length) { classList.innerHTML = '<p class="placeholder-text">No classes available yet.</p>'; return; }

    const now = new Date();
    const hidePast = filterPast.checked;

    // Parse dates and sort
    classes = classes.map(c => {
        const raw = c.occurrence_date || c.schedule || '';
        const dt = parseDate(raw);
        return { ...c, _date: dt, _raw: raw, _isPast: dt ? dt < now : false };
    });

    // Filter if needed
    if (hidePast) {
        classes = classes.filter(c => !c._isPast);
    }

    // Sort by date (upcoming first, past at the end)
    classes.sort((a, b) => {
        if (!a._date && !b._date) return 0;
        if (!a._date) return 1;
        if (!b._date) return -1;
        return a._date - b._date;
    });

    if (!classes.length) {
        classList.innerHTML = '<p class="placeholder-text">No upcoming classes. Uncheck "Upcoming only" to see past classes.</p>';
        return;
    }

    classList.innerHTML = '';
    let lastDateGroup = '';

    classes.forEach(c => {
        const enrolled = c.enrolled || 0;
        const capacity = c.capacity || '?';
        const full = typeof capacity === 'number' && enrolled >= capacity;
        const classId = c.class_id || c._id || c.id || '';
        const isPast = c._isPast;

        // Date group separator
        if (c._date) {
            const group = formatDateGroup(c._date);
            if (group !== lastDateGroup) {
                lastDateGroup = group;
                const sep = document.createElement('div');
                sep.className = 'date-separator';
                sep.textContent = group;
                classList.appendChild(sep);
            }
        }

        const div = document.createElement('div');
        div.className = 'class-item' + (isPast ? ' past-class' : '');

        const dateBadge = c._date ? `<span class="date-badge">🕐 ${friendlyDate(c._date)}</span>` : '';
        const pastBadge = isPast ? `<span class="past-badge">Past</span>` : '';

        div.innerHTML = `
            <div class="class-item-top">
                <div class="class-info">
                    <h3>${esc(c.name)} ${pastBadge}</h3>
                    <div class="class-meta">
                        ${dateBadge}
                        <span>📍 ${esc(c.location || '')}</span>
                        <span>👤 ${esc(c.instructor || '')}</span>
                    </div>
                    ${c.description ? `<div class="class-desc">${esc(c.description)}</div>` : ''}
                </div>
                <span class="capacity-badge ${full ? 'cap-full' : 'cap-ok'}">${enrolled}/${capacity} spots</span>
            </div>
            <div class="class-actions" id="actions-${classId}"></div>
        `;

        const actions = div.querySelector(`#actions-${classId}`);

        // ── Member: Book / RSVP (only for upcoming) ──
        if (userRole === 'member' && !isPast) {
            const btn = document.createElement('button');
            btn.className = 'btn-action btn-book';
            btn.textContent = '🎟 Book / RSVP';
            btn.disabled = full;
            btn.addEventListener('click', () => bookClass(classId, c.occurrence_date, btn));
            actions.appendChild(btn);
        }

        // ── Trainer / Admin actions ──
        if (userRole === 'trainer' || userRole === 'admin') {
            // View Members
            const btnMembers = document.createElement('button');
            btnMembers.className = 'btn-action';
            btnMembers.textContent = '👥 Members';
            btnMembers.addEventListener('click', () => viewMembers(classId, c.name, c.occurrence_date));
            actions.appendChild(btnMembers);

            // Send Reminder (only for upcoming)
            if (!isPast) {
                const btnRemind = document.createElement('button');
                btnRemind.className = 'btn-action btn-remind';
                btnRemind.textContent = '📧 Send Reminder';
                btnRemind.addEventListener('click', () => sendReminder(classId, c.name, c.occurrence_date));
                actions.appendChild(btnRemind);
            }

            // Recurrence (show on ALL classes)
            const btnRec = document.createElement('button');
            btnRec.className = 'btn-action';
            btnRec.textContent = c.recurrence ? '🔄 Edit Recurrence' : '🔄 Add Recurrence';
            btnRec.addEventListener('click', () => openRecurrenceModal(classId));
            actions.appendChild(btnRec);
        }

        classList.appendChild(div);
    });
}

btnRefresh.addEventListener('click', () => { loadClasses(); toast('Refreshed'); });

// ── Book / RSVP ──────────────────────────────────────────────
async function bookClass(classId, occurrenceDate, btn) {
    if (!occurrenceDate) {
        toast('Occurrence date is missing', 'error');
        return;
    }

    const yes = await confirmAction('Book Class', `Are you sure you want to book this class for ${occurrenceDate}?`);
    if (!yes) return;

    btn.disabled = true; btn.textContent = 'Booking…';
    const body = { occurrence_date: occurrenceDate };
    const { ok, data } = await api(`/classes/${classId}/book`, {
        method: 'POST', body: JSON.stringify(body),
    });
    if (ok) {
        toast(`Booked! (${data.enrolled}/${data.capacity})`);
        btn.textContent = '✓ Booked';
        loadClasses();
    } else {
        toast(data.message || 'Booking failed', 'error');
        btn.disabled = false; btn.textContent = '🎟 Book / RSVP';
    }
}

// ── View Members ─────────────────────────────────────────────
async function viewMembers(classId, className, occurrenceDate) {
    if (!occurrenceDate) {
        toast('Occurrence date is missing', 'error');
        return;
    }

    const body = { occurrence_date: occurrenceDate };
    const { ok, data } = await api(`/classes/${classId}/members`, {
        method: 'POST', body: JSON.stringify(body),
    });
    if (!ok) { toast(data.message || 'Could not load members', 'error'); return; }

    const members = data.booked_members || [];
    let html;
    if (members.length === 0) {
        html = '<p class="placeholder-text" style="padding:1rem 0">No members booked yet.</p>';
    } else {
        html = '<ul>' + members.map(m => `<li>📧 ${esc(m)}</li>`).join('') + '</ul>';
    }
    showDetails(`Members — ${className} (${occurrenceDate})`, html);
}

// ── Send Reminder ────────────────────────────────────────────
async function sendReminder(classId, className, occurrenceDate) {
    const target = await promptForReminderTarget();
    if (!target) return; // cancelled

    const isAll = target === 'all';

    const body = (!isAll && occurrenceDate) ? { occurrence_date: occurrenceDate } : {};
    const { ok, data } = await api(`/classes/${classId}/send-reminder`, {
        method: 'POST',
        body: JSON.stringify(body)
    });
    if (ok) {
        const r = data.results || {};
        toast(`Reminders sent! (${r.total_sent || 0} sent, ${r.total_failed || 0} failed)`);
    } else {
        toast(data.message || 'Failed to send reminders', 'error');
    }
}

// ── Update Recurrence ────────────────────────────────────────
function openRecurrenceModal(classId) {
    $('#rec-class-id').value = classId;
    recurrenceForm.reset();
    show(recurrenceOverlay);
}

recurrenceForm.addEventListener('submit', async e => {
    e.preventDefault();
    const classId = $('#rec-class-id').value;
    const frequency = $('#rec-frequency').value;
    const endDate = $('#rec-end-date').value;
    const occurrences = $('#rec-occurrences').value;

    const days = [...recurrenceForm.querySelectorAll('.checkbox-row input:checked')].map(cb => cb.value);

    const body = { frequency };
    if (frequency === 'weekly' && days.length) body.days_of_week = days;
    if (endDate) body.end_date = endDate;
    if (occurrences) body.total_occurrences = parseInt(occurrences, 10);

    const yes = await confirmAction('Update Recurrence', 'Update the recurrence rule for this class?');
    if (!yes) return;

    const { ok, data } = await api(`/classes/${classId}/recurrence`, {
        method: 'PATCH', body: JSON.stringify(body),
    });
    if (ok) {
        toast('Recurrence updated!');
        hide(recurrenceOverlay);
        loadClasses();
    } else {
        toast(data.message || 'Failed to update recurrence', 'error');
    }
});

// ══════════════════════════════════════════════════════════════
//  CREATE CLASS (with optional recurrence)
// ══════════════════════════════════════════════════════════════

createClassForm.addEventListener('submit', async e => {
    e.preventDefault();
    hideMsg(createClassError, createClassSuccess);

    const body = {
        name: $('#cc-name').value.trim(),
        instructor: $('#cc-instructor').value.trim(),
        schedule: $('#cc-schedule').value,
        capacity: parseInt($('#cc-capacity').value, 10),
        location: $('#cc-location').value.trim(),
        description: $('#cc-description').value.trim(),
    };

    // Attach optional recurrence
    if (ccRecToggle.checked) {
        const freq = $('#cc-rec-freq').value;
        const recurrence = { frequency: freq };
        const days = [...$('#cc-rec-days').querySelectorAll('input:checked')].map(cb => cb.value);
        if (freq === 'weekly' && days.length) recurrence.days_of_week = days;
        const endDate = $('#cc-rec-end').value;
        if (endDate) recurrence.end_date = endDate;
        const occ = $('#cc-rec-occ').value;
        if (occ) recurrence.total_occurrences = parseInt(occ, 10);
        body.recurrence = recurrence;
    }

    const yes = await confirmAction('Create Class', `Create the class "${body.name}"?`);
    if (!yes) return;

    const { ok, data } = await api('/classes/', {
        method: 'POST', body: JSON.stringify(body),
    });
    if (ok) {
        showMsg(createClassSuccess, 'Class created!');
        createClassForm.reset();
        hide(ccRecFields);
        toast('Class created');
    } else {
        showMsg(createClassError, data.message || 'Failed to create class');
    }
});

// ══════════════════════════════════════════════════════════════
//  INIT — always land on the classes page
// ══════════════════════════════════════════════════════════════

renderUI();
navigateTo('classes');
