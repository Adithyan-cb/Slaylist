const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const calculateBtn = document.getElementById('calculate-btn');
const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const errorSection = document.getElementById('error-section');

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
    errorSection.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const res = await fetch('/api/analyze', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        localStorage.setItem('aura', JSON.stringify(data));
        window.location.href = '/result.html';
    } catch (err) {
        showError('The Vibe Bureau is experiencing technical difficulties. Try again.');
    }
});

function showError(msg) {
    uploadSection.classList.remove('hidden');
    loadingSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    errorSection.querySelector('p').textContent = msg;
}
