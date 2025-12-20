// State
const state = {
    file: null,
    rules: [],
    worker: null
};

// UI Elements
const els = {
    navs: document.querySelectorAll('.dock-item'),
    views: document.querySelectorAll('.view'),
    fileInput: document.getElementById('file-input'),
    dropZone: document.getElementById('drop-zone'),
    portalContainer: document.querySelector('.portal-container'), // NEW
    fileInfo: document.getElementById('file-info-panel'),
    fileName: document.getElementById('file-name'),
    fileSize: document.getElementById('file-size'),
    pipelineList: document.getElementById('pipeline-list'),
    statusDot: document.querySelector('.status-dot'),
    statusText: document.querySelector('.status-text'),
    btnRun: document.getElementById('btn-run'),
    restartContainer: document.getElementById('restart-container'),
    logBody: document.getElementById('log-body'),
    downloadSection: document.getElementById('download-section'),
    btnDownload: document.getElementById('btn-download'),
    previewTable: document.getElementById('preview-table')
};

function init() {
    setupNavigation();
    setupFileUpload();
    setupWorker();
    if (els.btnRun) els.btnRun.addEventListener('click', runPipeline);
}

function setupNavigation() {
    els.navs.forEach(nav => {
        nav.addEventListener('click', () => {
            switchTab(nav.getAttribute('data-tab'));
        });
    });
}

function switchTab(tab) {
    els.navs.forEach(n => n.classList.remove('active'));
    els.views.forEach(v => v.classList.remove('active'));

    document.querySelector(`.dock-item[data-tab="${tab}"]`)?.classList.add('active');
    document.getElementById(`view-${tab}`)?.classList.add('active');
}

// Expose for HTML buttons
window.switchTab = switchTab;

function setupWorker() {
    state.worker = new Worker('worker.js');
    state.worker.onmessage = function (e) {
        const { type, data, error } = e.data;
        if (type === 'READY') {
            if (els.statusDot) els.statusDot.className = 'status-dot green';
            if (els.statusText) els.statusText.innerText = 'ONLINE';
            log('SYSTEM::ENGINE_READY [PYODIDE_LOADED]');
        }
        else if (type === 'LOG') log(`ENGINE::${data.toUpperCase()}`);
        else if (type === 'RESULT') {
            log('SYSTEM::PROCESS_COMPLETE');
            els.btnRun.innerHTML = '<ion-icon name="checkmark-done"></ion-icon> SUCCESS';
            els.restartContainer.classList.remove('hidden');
            els.downloadSection.classList.remove('hidden');
            const url = URL.createObjectURL(new Blob([data], { type: 'text/csv' }));
            els.btnDownload.onclick = () => {
                const a = document.createElement('a');
                a.href = url;
                a.download = 'cleaned_data.csv';
                a.click();
            };
        }
        else if (type === 'ERROR') {
            log(`ERROR::${error}`);
            els.statusDot.className = 'status-dot red';
            els.btnRun.innerText = 'FATAL_ERROR';
            els.restartContainer.classList.remove('hidden');
        }
    };
}

function setupFileUpload() {
    els.dropZone.addEventListener('click', () => { els.fileInput.value = ''; els.fileInput.click(); });
    els.fileInput.addEventListener('change', (e) => {
        if (e.target.files?.length > 0) handleFile(e.target.files[0]);
    });
    els.dropZone.addEventListener('dragover', (e) => { e.preventDefault(); });
    els.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files?.length > 0) handleFile(e.dataTransfer.files[0]);
    });
}

function handleFile(file) {
    state.file = file;
    els.fileName.innerText = file.name.toUpperCase();
    els.fileSize.innerText = (file.size / 1024 / 1024).toFixed(2) + ' MB';

    // UI Transition: Hide Portal, Show Info Button
    els.portalContainer.classList.add('hidden');
    els.fileInfo.classList.remove('hidden');

    const reader = new FileReader();
    reader.onload = function (e) {
        const rows = e.target.result.split('\n').filter(r => r.trim()).slice(0, 5);
        renderPreview(rows);

        // Auto-Advance to Operations
        setTimeout(() => {
            switchTab('transform');
        }, 1200);
    };
    reader.readAsText(file.slice(0, 5000));
}

function renderPreview(rows) {
    if (!rows.length) { els.previewTable.innerHTML = '<div>NO_DATA</div>'; return; }
    let html = '<table>';
    rows.forEach((row, i) => {
        const cols = row.split(',');
        html += '<tr>';
        cols.forEach(col => {
            let clean = col.replace(/"/g, '').trim();
            html += i === 0 ? `<th>${clean}</th>` : `<td>${clean}</td>`;
        });
        html += '</tr>';
    });
    html += '</table>';
    els.previewTable.innerHTML = html;
}

window.addRule = function (type, params = {}) {
    if (type === 'sort_values') {
        const col = prompt("TARGET_COLUMN_ID:");
        if (!col) return;
        params.column = col;
    }
    state.rules.push({ id: Date.now(), type, params });
    renderRules();
};

window.removeRule = function (id) {
    state.rules = state.rules.filter(r => r.id !== id);
    renderRules();
};

function renderRules() {
    els.pipelineList.innerHTML = '';
    if (!state.rules.length) {
        els.pipelineList.innerHTML = '<li style="background:transparent; border:none; text-align:center; color:#555;">// NULL_PIPELINE</li>';
        return;
    }
    const labels = {
        'drop_duplicates': 'DEDUP_ROWS',
        'drop_na': 'PRUNE_NULL',
        'fill_na': 'FILL_ZERO',
        'fill_na_mean': 'FILL_MEAN',
        'standard_columns': 'SNAKE_CASE',
        'capitalize_strings': 'TITLE_CASE',
        'trim_strings': 'TRIM_WS',
        'sort_values': (p) => `SORT_BY[${p.column}]`
    };
    state.rules.forEach(rule => {
        const txt = typeof labels[rule.type] === 'function' ? labels[rule.type](rule.params) : labels[rule.type];
        const li = document.createElement('li');
        li.innerHTML = `<span>${txt}</span><ion-icon name="close" style="cursor:pointer; color:var(--neon-red);" onclick="removeRule(${rule.id})"></ion-icon>`;
        els.pipelineList.appendChild(li);
    });
}

function runPipeline() {
    if (!state.file) { alert('ERR: SOURCE_MISSING'); switchTab('source'); return; }
    switchTab('run');
    els.btnRun.innerHTML = '<ion-icon name="sync"></ion-icon> EXECUTING...';
    els.btnRun.disabled = true;
    els.logBody.innerHTML = '';
    log('INIT_SEQUENCE_START...');
    const reader = new FileReader();
    reader.onload = (e) => state.worker.postMessage({ type: 'CLEAN', file: e.target.result, rules: state.rules });
    reader.readAsArrayBuffer(state.file);
}

window.resetPipeline = function () {
    state.file = null; state.rules = [];
    els.fileInput.value = '';

    // UI Reset
    els.fileInfo.classList.add('hidden');
    els.portalContainer.classList.remove('hidden'); // Show Portal

    els.previewTable.innerHTML = '';
    renderRules();
    els.btnRun.innerHTML = '<ion-icon name="flash"></ion-icon> INITIALIZE SEQUENCE';
    els.btnRun.disabled = false;
    els.downloadSection.classList.add('hidden');
    els.restartContainer.classList.add('hidden');
    switchTab('source');
};

function log(msg) {
    if (!els.logBody) return;
    const div = document.createElement('div');
    div.innerText = `> ${msg}`;
    els.logBody.appendChild(div);
    els.logBody.scrollTop = els.logBody.scrollHeight;
}

init();
