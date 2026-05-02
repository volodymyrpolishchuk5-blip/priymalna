let tg = window.Telegram.WebApp;
tg.expand(); 

document.addEventListener('DOMContentLoaded', () => {
    // 1. Get and store tenant_id
    const urlParams = new URLSearchParams(window.location.search);
    const tenantParam = urlParams.get('tenant');
    if (tenantParam) {
        localStorage.setItem('tenant_id', tenantParam);
    }
    const tenantId = localStorage.getItem('tenant_id');

    // Display user name
    if (document.getElementById('user-name')) {
        let user = tg.initDataUnsafe.user;
        if (user) {
            document.getElementById('user-name').innerText = (user.first_name || '') + ' ' + (user.last_name || '');
        }
    }

    // Render static pickers
    if (location.pathname.includes('calendar.html') || document.getElementById('date-picker')) {
        renderDates();
        renderTimes();
    }

    // Fetch and render dynamic content based on page
    if (tenantId) {
        if (document.getElementById('services') || document.getElementById('admin-services')) {
            fetchServices(tenantId);
            if (document.getElementById('admin-overview')) {
                fetchStats();
            }
        }
        if (document.getElementById('masters-list') || document.getElementById('admin-masters')) {
            fetchMasters(tenantId);
        }
        if (document.getElementById('admin-bookings')) {
            if (document.getElementById('admin-bookings').style.display === 'block') {
                fetchBookings();
            }
        }
        if (document.getElementById('admin-clients-tab')) {
            if (document.getElementById('admin-clients-tab').style.display === 'block') {
                fetchClients();
            }
        }
    }

    // Confirm page logic
    if (location.pathname.includes('confirm.html')) {
        let service = localStorage.getItem('selectedService') || "Послуга не обрана";
        let masterName = localStorage.getItem('selectedMasterName') || "Будь-який";
        let date = localStorage.getItem('selectedDate') || "";
        let time = localStorage.getItem('selectedTime') || "";
        
        let summaryItems = document.querySelectorAll('.summary-item strong');
        if (summaryItems.length >= 3) {
            summaryItems[0].innerText = service;
            summaryItems[1].innerText = date;
            summaryItems[2].innerText = time;
            if (summaryItems[3]) summaryItems[3].innerText = masterName;
        }
    }
});

// --- API FETCHERS ---

async function fetchServices(tenantId) {
    try {
        const res = await fetch(`/api/services?tenant=${tenantId}`);
        const services = await res.json();
        
        const clientContainer = document.getElementById('services');
        if (clientContainer) {
            clientContainer.innerHTML = '';
            services.forEach((s, i) => {
                clientContainer.innerHTML += `
                    <div class="service-card">
                        <img src="https://via.placeholder.com/60" class="service-img">
                        <div class="service-info">
                            <span class="service-name">${s.name}</span>
                            <span class="service-meta">${s.duration} хв</span>
                        </div>
                        <div class="service-price">${s.price} грн</div>
                        <input type="radio" name="service" value="${s.id}" data-name="${s.name}" ${i === 0 ? 'checked' : ''}>
                    </div>`;
            });
        }

        const adminContainer = document.getElementById('admin-services');
        if (adminContainer) {
            adminContainer.innerHTML = '';
            services.forEach(s => {
                adminContainer.innerHTML += `
                    <div class="service-card">
                        <div class="service-info">
                            <span class="name">${s.name}</span>
                            <span class="meta">${s.price} ₴ • ${s.duration} хв</span>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="price-tag" onclick="editService('${s.id}', '${s.name}', ${s.price}, ${s.duration})" style="border:none; cursor:pointer; background: #f5f5f5; color: #333;">Ред.</button>
                            <button class="price-tag delete-btn" onclick="deleteService('${s.id}', '${s.name}')" style="border:none; cursor:pointer;">Видалити</button>
                        </div>
                    </div>`;
            });
        }
    } catch (e) { console.error(e); }
}

async function fetchMasters(tenantId) {
    try {
        const res = await fetch(`/api/masters?tenant=${tenantId}`);
        const masters = await res.json();
        
        const clientContainer = document.getElementById('masters-list');
        if (clientContainer) {
            clientContainer.innerHTML = '';
            masters.forEach(m => {
                clientContainer.innerHTML += `
                    <div class="service-card master-card" onclick="selectMaster('${m.id}', '${m.name}')">
                        <img src="https://via.placeholder.com/60" style="border-radius: 50%; margin-right: 15px;">
                        <div class="service-info" style="flex-grow: 1;">
                            <span class="service-name">${m.name}</span>
                            <span class="service-meta">${m.specialty}</span>
                        </div>
                    </div>`;
            });
        }
        
        const adminContainer = document.getElementById('admin-masters');
        if (adminContainer) {
            adminContainer.innerHTML = '';
            masters.forEach(m => {
                const tgIdDisplay = m.telegram_id || 'Немає';
                adminContainer.innerHTML += `
                    <div class="service-card master-card" style="padding: 15px; display: block;">
                        <div style="display: flex; align-items: center; width: 100%; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 40px; height: 40px; background: #f0f0f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;">👤</div>
                            <div class="service-info" style="min-width: 0;">
                                <span class="name" style="font-size: 16px; font-weight: 800; white-space: normal;">${m.name}</span>
                                <span class="meta" style="color: #777; display: block;">${m.specialty} • ${m.commission_rate}%</span>
                            </div>
                        </div>
                        <div style="margin-bottom: 12px;">
                            <span class="copy-hint" onclick="copyToClipboard('${tgIdDisplay}')" style="font-size: 11px; background: #e3f2fd; color: #1565c0; padding: 4px 10px; border-radius: 6px; cursor: pointer; display: inline-block;">
                                🆔 ${tgIdDisplay}
                            </span>
                        </div>
                        <div style="display: flex; gap: 8px; width: 100%;">
                            <button class="action-btn" onclick="editMaster('${m.id}', '${m.name}', '${m.specialty}', '${m.telegram_id || ''}', ${m.commission_rate})" style="flex: 1; padding: 10px; background: #f5f5f5; color: #333; font-size: 12px; margin-top: 0;">Редагувати</button>
                            <button class="action-btn delete-btn" onclick="deleteMaster('${m.id}', '${m.name}')" style="flex: 1; padding: 10px; font-size: 12px; margin-top: 0;">Видалити</button>
                        </div>
                    </div>`;
            });
        }
    } catch(e) { console.error(e); }
}

async function fetchBookings() {
    const tenantId = localStorage.getItem('tenant_id');
    const user = tg.initDataUnsafe.user;
    const container = document.getElementById('bookings-container');
    if (!container || !tenantId) return;
    
    container.innerHTML = '<p style="text-align:center; color:#777;">Завантаження...</p>';
    try {
        const url = `/api/bookings?tenant=${tenantId}&user_id=${user ? user.id : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
             container.innerHTML = '<p style="text-align:center; color:red;">Доступ заборонено</p>';
             return;
        }
        const bookings = await response.json();
        
        container.innerHTML = '';
        if (bookings.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:#777;">Немає записів</p>';
            return;
        }
        
        bookings.forEach(b => {
            container.innerHTML += `
                <div class="booking-card service-card" style="flex-direction: column; align-items: flex-start; gap: 10px;">
                    <div style="display: flex; justify-content: space-between; width: 100%;">
                        <span style="font-weight: 800;">${b.name} (${b.phone})</span>
                        <span style="color: var(--text-secondary);">${b.date} ${b.time}</span>
                    </div>
                    <div style="font-size: 14px;">
                        Послуга: <strong>${b.service}</strong><br>
                        Майстер: <strong>${b.master || 'Будь-який'}</strong><br>
                        Статус: <strong>${b.status}</strong>
                    </div>
                    ${b.status === 'active' || b.status === 'waitlist' ? `
                    <div style="display: flex; gap: 5px; width: 100%; margin-top: 10px; flex-wrap: wrap;">
                        <button class="action-btn" onclick="completeBooking('${b.id}')" style="padding: 6px; font-size: 11px; background: #e8f5e9; color: #2e7d32; flex: 1;">Виконано</button>
                        <button class="action-btn" onclick="openRescheduleModal('${b.id}')" style="padding: 6px; font-size: 11px; background: #e3f2fd; color: #1565c0; flex: 1;">Перенести</button>
                        <button class="action-btn delete-btn" onclick="cancelBooking('${b.id}')" style="padding: 6px; font-size: 11px; margin-top: 0; flex: 1;">Скасувати</button>
                    </div>` : `
                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 10px;">
                        <button class="action-btn" onclick="repeatBooking('${b.id}')" style="padding: 8px; font-size: 12px; background: #f3e5f5; color: #7b1fa2; width: 100%;">🔁 Повторити запис</button>
                    </div>`}
                </div>`;
        });
    } catch (e) { console.error(e); }
}

async function fetchStats() {
    const tenantId = localStorage.getItem('tenant_id');
    if (!tenantId) return;
    try {
        const res = await fetch(`/api/stats?tenant=${tenantId}`);
        const stats = await res.json();
        
        document.getElementById('stats-today').innerText = `${stats.today_income} ₴`;
        document.getElementById('stats-week').innerText = `${stats.week_income} ₴`;
        document.getElementById('stats-month').innerText = `${stats.month_income} ₴`;
        document.getElementById('stats-total').innerText = stats.total_bookings;
    } catch (e) { console.error(e); }
}

async function fetchClients() {
    const tenantId = localStorage.getItem('tenant_id');
    const container = document.getElementById('admin-clients');
    if (!container || !tenantId) return;
    
    container.innerHTML = '<p style="text-align:center; color:#777;">Завантаження...</p>';
    try {
        const response = await fetch(`/api/clients?tenant=${tenantId}`);
        const data = await response.json();
        
        // Handle both old array format and new object format for safety
        const clients = Array.isArray(data) ? data : (data.clients || []);
        
        container.innerHTML = '';
        if (clients.length === 0) {
            container.innerHTML = `<p style="text-align:center; color:#777;">Немає клієнтів<br><small style="opacity:0.5">ID: ${data.tenant_id_searched || tenantId}</small></p>`;
            return;
        }
        
        clients.forEach(c => {
            container.innerHTML += `
                <div class="service-card" style="flex-direction: column; align-items: flex-start; gap: 10px;">
                    <div style="display: flex; justify-content: space-between; width: 100%;">
                        <span style="font-weight: 800; font-size: 16px;">
                            ${c.is_vip ? '👑 ' : ''}${c.name}
                        </span>
                        ${c.is_blacklisted ? '<span style="color: red; font-weight: bold;">ЧС</span>' : ''}
                    </div>
                    <div style="font-size: 14px; color: var(--text-secondary);">
                        📞 ${c.phone}<br>
                        📅 Доданий: ${new Date(c.created_at).toLocaleDateString()}
                    </div>
                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 10px;">
                        <button class="action-btn" onclick="updateClientStatus('${c.id}', ${!c.is_vip}, null)" style="padding: 8px; font-size: 12px; background: ${c.is_vip ? '#f5f5f5' : '#fff3e0'}; color: ${c.is_vip ? '#333' : '#e65100'};">
                            ${c.is_vip ? 'Прибрати VIP' : 'Зробити VIP'}
                        </button>
                        <button class="action-btn" onclick="updateClientStatus('${c.id}', null, ${!c.is_blacklisted})" style="padding: 8px; font-size: 12px; background: ${c.is_blacklisted ? '#f5f5f5' : '#ffebee'}; color: ${c.is_blacklisted ? '#333' : '#c62828'}; flex: 1;">
                            ${c.is_blacklisted ? 'Відновити' : 'У ЧС'}
                        </button>
                    </div>
                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 5px;">
                        <button class="action-btn" onclick="editClient('${c.id}', '${c.name}', '${c.phone}')" style="padding: 8px; font-size: 12px; background: #f5f5f5; color: #333; flex: 1;">Редагувати</button>
                        <button class="action-btn delete-btn" onclick="deleteClientRecord('${c.id}', '${c.name}')" style="padding: 8px; font-size: 12px; margin-top:0; flex: 1;">Видалити</button>
                    </div>
                </div>`;
            });
        }
    } catch (e) { console.error(e); }
}

// --- CLIENT ACTIONS ---

function selectMaster(id, name) {
    localStorage.setItem('selectedMasterId', id);
    localStorage.setItem('selectedMasterName', name);
    location.href = 'calendar.html';
}

function saveServiceAndNext() {
    let selected = document.querySelector('input[name="service"]:checked');
    if (selected) {
        localStorage.setItem('selectedServiceId', selected.value);
        localStorage.setItem('selectedService', selected.dataset.name);
        location.href = 'masters.html';
    } else {
        alert("Будь ласка, оберіть послугу");
    }
}

function finishBooking() {
    let name = document.querySelector('input[placeholder="Ваше ім\'я"]').value;
    let phone = document.querySelector('input[placeholder="+380"]').value;
    let tenantId = localStorage.getItem('tenant_id');
    
    if (!name || !phone) {
        alert("Будь ласка, заповніть всі поля");
        return;
    }
    let data = {
        action: "new_booking",
        tenant_id: tenantId,
        name: name, 
        phone: phone,
        service: localStorage.getItem('selectedService'),
        master_id: localStorage.getItem('selectedMasterId'),
        date: localStorage.getItem('selectedDate'),
        time: localStorage.getItem('selectedTime')
    };
    tg.sendData(JSON.stringify(data));
}

// --- ADMIN ACTIONS ---

function addNewService() {
    document.getElementById('modal-title').innerText = 'Додати послугу';
    document.getElementById('edit-service-id').value = '';
    document.getElementById('modal-name').value = '';
    document.getElementById('modal-price').value = '';
    document.getElementById('modal-duration').value = '60';
    document.getElementById('service-modal').style.display = 'flex';
}

function editService(id, name, price, duration) {
    document.getElementById('modal-title').innerText = 'Редагувати послугу';
    document.getElementById('edit-service-id').value = id;
    document.getElementById('modal-name').value = name;
    document.getElementById('modal-price').value = price;
    document.getElementById('modal-duration').value = duration;
    document.getElementById('service-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('service-modal').style.display = 'none';
}

async function saveModalService() {
    const id = document.getElementById('edit-service-id').value;
    const name = document.getElementById('modal-name').value;
    const price = document.getElementById('modal-price').value;
    const duration = document.getElementById('modal-duration').value;
    const tenantId = localStorage.getItem('tenant_id');
    const user = tg.initDataUnsafe.user;

    if (!name || !price) {
        alert("Заповніть назву та ціну!");
        return;
    }

    try {
        const payload = {
            action: id ? "update_service" : "add_service",
            tenant_id: tenantId,
            user_id: user ? user.id : null,
            name: name,
            price: price,
            duration: duration
        };
        if (id) payload.service_id = id;

        const res = await fetch('/api/services', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeModal();
            fetchServices(tenantId);
        }
    } catch (e) { console.error(e); }
}

async function deleteService(id, name) {
    const tenantId = localStorage.getItem('tenant_id');
    if (confirm(`Видалити послугу "${name}"?`)) {
        try {
            const res = await fetch('/api/services', {
                method: 'POST',
                body: JSON.stringify({ action: "delete_service", tenant_id: tenantId, service_id: id })
            });
            if (res.ok) fetchServices(tenantId);
        } catch (e) { console.error(e); }
    }
}

// Masters modal logic
function addNewMaster() {
    document.getElementById('master-modal-title').innerText = 'Додати майстра';
    document.getElementById('edit-master-id').value = '';
    document.getElementById('master-name').value = '';
    document.getElementById('master-specialty').value = '';
    document.getElementById('master-tg-id').value = '';
    document.getElementById('master-commission').value = '50';
    document.getElementById('master-modal').style.display = 'flex';
}

function editMaster(id, name, specialty, tgId, commission) {
    document.getElementById('master-modal-title').innerText = 'Редагувати майстра';
    document.getElementById('edit-master-id').value = id;
    document.getElementById('master-name').value = name;
    document.getElementById('master-specialty').value = specialty;
    document.getElementById('master-tg-id').value = tgId;
    document.getElementById('master-commission').value = commission;
    document.getElementById('master-modal').style.display = 'flex';
}

function closeMasterModal() {
    document.getElementById('master-modal').style.display = 'none';
}

async function saveModalMaster() {
    const id = document.getElementById('edit-master-id').value;
    const name = document.getElementById('master-name').value;
    const specialty = document.getElementById('master-specialty').value;
    const tgId = document.getElementById('master-tg-id').value;
    const commission = document.getElementById('master-commission').value;
    const tenantId = localStorage.getItem('tenant_id');
    const user = tg.initDataUnsafe.user;

    if (!name || !specialty) {
        alert("Заповніть ім'я та спеціалізацію!");
        return;
    }

    try {
        const payload = {
            action: id ? "update_master" : "add_master",
            tenant_id: tenantId,
            user_id: user ? user.id : null,
            name: name,
            specialty: specialty,
            telegram_id: tgId || null,
            commission_rate: commission
        };
        if (id) payload.master_id = id;

        const res = await fetch('/api/masters', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeMasterModal();
            fetchMasters(tenantId);
        } else {
            const err = await res.json();
            alert(err.error || "Помилка");
        }
    } catch (e) { console.error(e); }
}

async function deleteMaster(id, name) {
    const tenantId = localStorage.getItem('tenant_id');
    const user = tg.initDataUnsafe.user;
    if (confirm(`Видалити майстра "${name}"?`)) {
        try {
            const res = await fetch('/api/masters', {
                method: 'POST',
                body: JSON.stringify({ 
                    action: "delete_master", 
                    tenant_id: tenantId, 
                    user_id: user ? user.id : null,
                    master_id: id 
                })
            });
            if (res.ok) fetchMasters(tenantId);
        } catch (e) { console.error(e); }
    }
}

async function completeBooking(id) {
    const tenantId = localStorage.getItem('tenant_id');
    try {
        const res = await fetch('/api/bookings', {
            method: 'POST',
            body: JSON.stringify({ action: "complete_booking", tenant_id: tenantId, appt_id: id })
        });
        if (res.ok) fetchBookings();
    } catch (e) { console.error(e); }
}

async function cancelBooking(id) {
    const tenantId = localStorage.getItem('tenant_id');
    if (confirm(`Скасувати запис?`)) {
        try {
            const res = await fetch('/api/bookings', {
                method: 'POST',
                body: JSON.stringify({ action: "cancel_booking", tenant_id: tenantId, appt_id: id })
            });
            if (res.ok) fetchBookings();
        } catch (e) { console.error(e); }
    }
}

async function updateClientStatus(clientId, isVip, isBlacklisted) {
    const tenantId = localStorage.getItem('tenant_id');
    try {
        const payload = { action: "update_status", tenant_id: tenantId, client_id: clientId };
        if (isVip !== null) payload.is_vip = isVip;
        if (isBlacklisted !== null) payload.is_blacklisted = isBlacklisted;
        
        const res = await fetch('/api/clients', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (res.ok) fetchClients();
    } catch (e) { console.error(e); }
}

function editClient(id, name, phone) {
    if (id.startsWith('fb_')) {
        alert("Цей клієнт ще не збережений в базі. Створіть новий запис для нього, щоб він з'явився офіційно.");
        return;
    }
    document.getElementById('edit-client-id').value = id;
    document.getElementById('client-name-modal').value = name;
    document.getElementById('client-phone-modal').value = phone;
    document.getElementById('client-modal').style.display = 'flex';
}

function closeClientModal() {
    document.getElementById('client-modal').style.display = 'none';
}

async function saveModalClient() {
    const id = document.getElementById('edit-client-id').value;
    const name = document.getElementById('client-name-modal').value;
    const phone = document.getElementById('client-phone-modal').value;
    const tenantId = localStorage.getItem('tenant_id');

    try {
        const res = await fetch('/api/clients', {
            method: 'POST',
            body: JSON.stringify({ action: "update_client", tenant_id: tenantId, client_id: id, name: name, phone: phone })
        });
        if (res.ok) {
            closeClientModal();
            fetchClients();
            showToast("Дані клієнта оновлено!");
        }
    } catch (e) { console.error(e); }
}

async function deleteClientRecord(id, name) {
    if (id.startsWith('fb_')) {
        alert("Цей запис тимчасовий і не може бути видалений окремо.");
        return;
    }
    const tenantId = localStorage.getItem('tenant_id');
    if (confirm(`Видалити клієнта "${name}" з бази?`)) {
        try {
            const res = await fetch('/api/clients', {
                method: 'POST',
                body: JSON.stringify({ action: "delete_client", tenant_id: tenantId, client_id: id })
            });
            if (res.ok) {
                fetchClients();
                showToast("Клієнта видалено");
            }
        } catch (e) { console.error(e); }
    }
}

function openRescheduleModal(id) {
    const modal = document.getElementById('reschedule-modal');
    modal.querySelector('h3').innerText = "Перенести запис";
    modal.style.display = 'flex';
    document.getElementById('btn-save-reschedule').onclick = () => saveReschedule(id);
}

function closeRescheduleModal() {
    document.getElementById('reschedule-modal').style.display = 'none';
}

async function saveReschedule(id) {
    const dateInput = document.getElementById('reschedule-date');
    const timeInput = document.getElementById('reschedule-time');
    const date = dateInput.value;
    const time = timeInput.value;
    const tenantId = localStorage.getItem('tenant_id');

    if (!date || !time) {
        alert("Оберіть дату та час!");
        return;
    }

    try {
        const res = await fetch('/api/bookings', {
            method: 'POST',
            body: JSON.stringify({ action: "reschedule", tenant_id: tenantId, appt_id: id, date: date, time: time })
        });
        if (res.ok) {
            closeRescheduleModal();
            fetchBookings();
            showToast("Запис перенесено!");
        } else {
            alert("Помилка при перенесенні");
        }
    } catch (e) { console.error(e); }
}

async function repeatBooking(id) {
    // Open modal to select new date/time for the repeat
    const modal = document.getElementById('reschedule-modal');
    modal.querySelector('h3').innerText = "Повторити запис";
    modal.style.display = 'flex';
    
    document.getElementById('btn-save-reschedule').onclick = async () => {
        const date = document.getElementById('reschedule-date').value;
        const time = document.getElementById('reschedule-time').value;
        const tenantId = localStorage.getItem('tenant_id');

        if (!date || !time) {
            alert("Оберіть дату та час!");
            return;
        }

        try {
            const res = await fetch('/api/bookings', {
                method: 'POST',
                body: JSON.stringify({ action: "repeat_booking_with_time", tenant_id: tenantId, appt_id: id, date: date, time: time })
            });
            if (res.ok) {
                closeRescheduleModal();
                fetchBookings();
                showToast("Створено повторний запис!");
            } else {
                alert("Помилка при створенні запису");
            }
        } catch (e) { console.error(e); }
    };
}

function switchAdminTab(tab) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById('admin-overview').style.display = 'none';
    document.getElementById('admin-bookings').style.display = 'none';
    if(document.getElementById('admin-masters-tab')) document.getElementById('admin-masters-tab').style.display = 'none';
    if(document.getElementById('admin-clients-tab')) document.getElementById('admin-clients-tab').style.display = 'none';
    
    if (tab === 'overview') {
        document.getElementById('admin-overview').style.display = 'block';
        document.querySelectorAll('.nav-item')[0].classList.add('active');
        fetchStats();
    } else if (tab === 'bookings') {
        document.getElementById('admin-bookings').style.display = 'block';
        document.querySelectorAll('.nav-item')[1].classList.add('active');
        fetchBookings();
    } else if (tab === 'masters') {
        document.getElementById('admin-masters-tab').style.display = 'block';
        document.querySelectorAll('.nav-item')[2].classList.add('active');
    } else if (tab === 'clients') {
        document.getElementById('admin-clients-tab').style.display = 'block';
        document.querySelectorAll('.nav-item')[3].classList.add('active');
        fetchClients();
    }
}

function renderDates() {
    const container = document.getElementById('date-picker');
    if (!container) return;
    const days = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    const months = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'];
    
    for (let i = 0; i < 7; i++) {
        let d = new Date();
        d.setDate(d.getDate() + i);
        let item = document.createElement('div');
        item.className = 'date-item' + (i === 0 ? ' active' : '');
        let dateStr = `${d.getDate()} ${months[d.getMonth()]}`;
        item.onclick = () => {
            document.querySelectorAll('.date-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            localStorage.setItem('selectedDate', dateStr);
        };
        item.innerHTML = `<span class="day-name">${days[d.getDay()]}</span><span class="day-num">${d.getDate()}</span>`;
        container.appendChild(item);
        if (i === 0) localStorage.setItem('selectedDate', dateStr);
    }
}

function renderTimes() {
    const container = document.getElementById('time-picker');
    if (!container) return;
    const times = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'];
    times.forEach((t, i) => {
        let item = document.createElement('div');
        item.className = 'time-item' + (i === 5 ? ' active' : '');
        item.innerText = t;
        item.onclick = () => {
            document.querySelectorAll('.time-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            localStorage.setItem('selectedTime', t);
        };
        container.appendChild(item);
        if (i === 5) localStorage.setItem('selectedTime', t);
    });
}

function copyToClipboard(text) {
    if (text === 'Немає') return;
    navigator.clipboard.writeText(text).then(() => {
        showToast("Копійовано: " + text);
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.innerText = message;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 2000);
}