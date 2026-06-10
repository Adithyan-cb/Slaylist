const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const calculateBtn = document.getElementById('calculate-btn');
const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const errorModal = document.getElementById('error-modal');
const errorTitle = document.getElementById('error-title');
const errorMessage = document.getElementById('error-message');
const errorCloseBtn = document.getElementById('error-close-btn');

let selectedFile = null;

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('bg-primary/10');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('bg-primary/10');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('bg-primary/10');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
});

errorCloseBtn.addEventListener('click', () => {
    hideError();
});

function handleFile(file) {
    selectedFile = file;
    dropZone.innerHTML = `
        <span class="material-symbols-outlined text-[48px] text-tertiary animate-bounce">check_circle</span>
        <p class="font-body-base font-bold text-text-primary">${file.name}</p>
        <p class="font-label-tiny text-label-tiny text-tertiary uppercase tracking-widest">READY TO CALCULATE</p>
    `;
    dropZone.style.backgroundImage = 'none';
    dropZone.style.border = '3px solid #c8cc6a';
}

calculateBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        showError('Upload a playlist screenshot first.');
        return;
    }

    uploadSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const res = await fetch('/api/analyze', { method: 'POST', body: formData });

        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            showError(body.detail || `Server error (${res.status})`);
            return;
        }

        const data = await res.json();

        localStorage.setItem('aura', JSON.stringify(data));
        window.location.href = '/result.html';
    } catch (err) {
        showError('Slaylist is experiencing technical difficulties. Try again.');
    }
});

function showError(msg) {
    loadingSection.classList.add('hidden');
    uploadSection.classList.remove('hidden');
    errorTitle.textContent = 'Upload failed';
    errorMessage.textContent = msg;
    errorModal.classList.remove('hidden');
    errorModal.classList.add('flex');
}

function hideError() {
    errorModal.classList.add('hidden');
    errorModal.classList.remove('flex');
}
