let currentTemplates = [];
let currentRequesters = [];

// Initialize
window.addEventListener('pywebviewready', function() {
    loadData();
    setupNavigation();
    setupActions();
});

async function loadData() {
    currentTemplates = await pywebview.api.get_templates();
    currentRequesters = await pywebview.api.get_requesters();
    
    renderDropdowns();
    renderTemplatesList();
    renderRequestersList();
}

function renderDropdowns() {
    const tplSelect = document.getElementById('select-template');
    tplSelect.innerHTML = currentTemplates.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
    
    const reqSelect = document.getElementById('select-requester');
    reqSelect.innerHTML = currentRequesters.map(r => `<option value="${r.id}">${r.name}</option>`).join('');
}

function renderTemplatesList() {
    const container = document.getElementById('templates-list');
    container.innerHTML = currentTemplates.map(t => `
        <div class="item-card">
            <h3>${t.name}</h3>
            <p>${t.category} > ${t.action}</p>
            <div style="display: flex; gap: 10px;">
                <button class="btn-secondary" onclick="editTemplate('${t.id}')">Editar</button>
                <button class="btn-secondary" style="border-color: #ef4444; color: #ef4444;" onclick="deleteTemplate('${t.id}')">Eliminar</button>
            </div>
        </div>
    `).join('');
}

function renderRequestersList() {
    const container = document.getElementById('requesters-list');
    container.innerHTML = currentRequesters.map(r => `
        <div class="item-card">
            <h3>${r.name}</h3>
            <p>${r.email}</p>
        </div>
    `).join('');
}

function setupNavigation() {
    const menuItems = document.querySelectorAll('.menu-item');
    const tabs = document.querySelectorAll('.tab-content');
    
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-tab');
            
            menuItems.forEach(mi => mi.classList.remove('active'));
            item.classList.add('active');
            
            tabs.forEach(tab => tab.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');
        });
    });
}

function setupActions() {
    const launchBtn = document.getElementById('btn-launch');
    launchBtn.addEventListener('click', async () => {
        const tplId = document.getElementById('select-template').value;
        const reqId = document.getElementById('select-requester').value;
        const url = document.getElementById('url-input').value;
        const txtFile = document.getElementById('txt-upload').files[0];
        
        if (!tplId || !reqId) {
            alert("Por favor selecciona una plantilla y un solicitante.");
            return;
        }
        
        let customText = null;
        if (txtFile) {
            customText = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = e => resolve(e.target.result);
                reader.readAsText(txtFile);
            });
        }
        
        const statusContainer = document.getElementById('status-container');
        const statusText = document.getElementById('status-text');
        
        statusContainer.classList.remove('hidden');
        launchBtn.disabled = true;
        launchBtn.classList.remove('pulse');
        launchBtn.style.opacity = '0.5';
        
        const res = await pywebview.api.start_automation(tplId, reqId, url, customText);
        statusText.innerText = res.message || "Automatizando...";
    });
    
    const newTplBtn = document.getElementById('btn-new-template');
    if (newTplBtn) {
        newTplBtn.addEventListener('click', () => {
            document.getElementById('edit-tpl-name').value = '';
            document.getElementById('edit-tpl-cat').value = '';
            document.getElementById('edit-tpl-subcat').value = '';
            document.getElementById('edit-tpl-action').value = '';
            document.getElementById('edit-tpl-software').value = '';
            document.getElementById('edit-tpl-summary').value = '';
            document.getElementById('edit-tpl-details').value = '';
            
            document.getElementById('modal-template').classList.remove('hidden');
            
            document.getElementById('btn-save-template').onclick = async () => {
                const newTpl = {
                    id: 'tpl_' + Date.now(),
                    name: document.getElementById('edit-tpl-name').value || 'Nueva Plantilla',
                    category: document.getElementById('edit-tpl-cat').value,
                    category_sub: document.getElementById('edit-tpl-subcat').value,
                    action: document.getElementById('edit-tpl-action').value,
                    software_name: document.getElementById('edit-tpl-software').value,
                    summary: document.getElementById('edit-tpl-summary').value,
                    details: document.getElementById('edit-tpl-details').value
                };
                currentTemplates.push(newTpl);
                await pywebview.api.save_templates(currentTemplates);
                loadData();
                closeModal('modal-template');
            };
        });
    }
}

// Called by Python when automation is done
window.notifyAutomationComplete = function() {
    const statusText = document.getElementById('status-text');
    const statusContainer = document.getElementById('status-container');
    const launchBtn = document.getElementById('btn-launch');
    
    statusText.innerText = "¡Automatización completada!";
    statusContainer.querySelector('.spinner').style.display = 'none';
    
    setTimeout(() => {
        statusContainer.classList.add('hidden');
        statusContainer.querySelector('.spinner').style.display = 'block';
        launchBtn.disabled = false;
        launchBtn.classList.add('pulse');
        launchBtn.style.opacity = '1';
    }, 5000);
}

window.notifyAutomationError = function(error) {
    alert("Error en la automatización: " + error);
    document.getElementById('status-container').classList.add('hidden');
    document.getElementById('btn-launch').disabled = false;
    document.getElementById('btn-launch').style.opacity = '1';
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}

// Simple edit functionality for demonstration
function editTemplate(id) {
    const tpl = currentTemplates.find(t => t.id === id);
    if (!tpl) return;
    
    document.getElementById('edit-tpl-name').value = tpl.name;
    document.getElementById('edit-tpl-cat').value = tpl.category;
    document.getElementById('edit-tpl-subcat').value = tpl.category_sub || '';
    document.getElementById('edit-tpl-action').value = tpl.action;
    document.getElementById('edit-tpl-software').value = tpl.software_name;
    document.getElementById('edit-tpl-summary').value = tpl.summary;
    document.getElementById('edit-tpl-details').value = tpl.details;
    
    document.getElementById('modal-template').classList.remove('hidden');
    
    document.getElementById('btn-save-template').onclick = async () => {
        tpl.name = document.getElementById('edit-tpl-name').value;
        tpl.category = document.getElementById('edit-tpl-cat').value;
        tpl.category_sub = document.getElementById('edit-tpl-subcat').value;
        tpl.action = document.getElementById('edit-tpl-action').value;
        tpl.software_name = document.getElementById('edit-tpl-software').value;
        tpl.summary = document.getElementById('edit-tpl-summary').value;
        tpl.details = document.getElementById('edit-tpl-details').value;
        
        await pywebview.api.save_templates(currentTemplates);
        loadData();
        closeModal('modal-template');
    };
}

async function deleteTemplate(id) {
    if (confirm('¿Estás seguro de que deseas eliminar esta plantilla?')) {
        currentTemplates = currentTemplates.filter(t => t.id !== id);
        await pywebview.api.save_templates(currentTemplates);
        loadData();
    }
}
