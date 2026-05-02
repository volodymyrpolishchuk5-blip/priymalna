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
                            <!-- <button class="price-tag" onclick="editService('${s.id}', '${s.name}', ${s.price}, ${s.duration})" style="border:none; cursor:pointer;">Edit</button> -->
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
                adminContainer.innerHTML += `
                    <div class="service-card master-card">
                        <div class="service-info" style="flex-grow: 1;">
                            <span class="name">${m.name}</span>
                            <span class="meta">${m.specialty} | TG: ${m.telegram_id || 'Немає'}</span>
                        </div>
                        <button class="price-tag delete-btn" onclick="deleteMaster('${m.id}', '${m.name}')" style="border:none; cursor:pointer;">Видалити</button>
                    </div>`;
            });
        }
    } catch(e) { console.error(e); }
}

async function fetchBookings() {
    const tenantId = localStorage.getItem('tenant_id');
    const container = document.getElementById('bookings-container');
    if (!container || !tenantId) return;
    
    container.innerHTML = '<p style="text-align:center; color:#777;">Завантаження...</p>';
    try {
        const response = await fetch(`/api/bookings?tenant=${tenantId}`);
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
                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 10px;">
                        <button class="action-btn" onclick="completeBooking('${b.id}')" style="padding: 8px; font-size: 12px; background: #e8f5e9; color: #2e7d32;">Виконано</button>
                        <button class="action-btn delete-btn" onclick="cancelBooking('${b.id}')" style="padding: 8px; font-size: 12px; margin-top: 0;">Скасувати</button>
                    </div>` : ''}
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
        const clients = await response.json();
        
        container.innerHTML = '';
        if (clients.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:#777;">Немає клієнтів</p>';
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
                        <button class="action-btn" onclick="updateClientStatus('${c.id}', null, ${!c.is_blacklisted})" style="padding: 8px; font-size: 12px; background: ${c.is_blacklisted ? '#f5f5f5' : '#ffebee'}; color: ${c.is_blacklisted ? '#333' : '#c62828'};">
                            ${c.is_blacklisted ? 'Відновити' : 'У Чорний список'}
                        </button>
                    </div>
                </div>`;
        });
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
    document.getElementById('modal-name').value = '';
    document.getElementById('modal-price').value = '';
    document.getElementById('modal-duration').value = '60';
    document.getElementById('service-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('service-modal').style.display = 'none';
}

async function saveModalService() {
    const name = document.getElementById('modal-name').value;
    const price = document.getElementById('modal-price').value;
    const duration = document.getElementById('modal-duration').value;
    const tenantId = localStorage.getItem('tenant_id');

    if (!name || !price) {
        alert("Заповніть назву та ціну!");
        return;
    }

    try {
        const res = await fetch('/api/services', {
            method: 'POST',
            body: JSON.stringify({
                action: "add_service",
                tenant_id: tenantId,
                name: name,
                price: price,
                duration: duration
            })
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
    document.getElementById('master-modal').style.display = 'flex';
}

function closeMasterModal() {
    document.getElementById('master-modal').style.display = 'none';
}

async function saveModalMaster() {
    const name = document.getElementById('master-name').value;
    const specialty = document.getElementById('master-specialty').value;
    const tgId = document.getElementById('master-tg-id').value;
    const tenantId = localStorage.getItem('tenant_id');

    if (!name || !specialty) {
        alert("Заповніть ім'я та спеціалізацію!");
        return;
    }

    try {
        const res = await fetch('/api/masters', {
            method: 'POST',
            body: JSON.stringify({
                action: "add_master",
                tenant_id: tenantId,
                name: name,
                specialty: specialty,
                telegram_id: tgId || null
            })
        });
        if (res.ok) {
            closeMasterModal();
            fetchMasters(tenantId);
        }
    } catch (e) { console.error(e); }
}

async function deleteMaster(id, name) {
    const tenantId = localStorage.getItem('tenant_id');
    if (confirm(`Видалити майстра "${name}"?`)) {
        try {
            const res = await fetch('/api/masters', {
                method: 'POST',
                body: JSON.stringify({ action: "delete_master", tenant_id: tenantId, master_id: id })
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