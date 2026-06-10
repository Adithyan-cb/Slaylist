let data;
try {
    data = JSON.parse(localStorage.getItem('aura'));
} catch {
    data = null;
}

if (!data) {
    window.location.href = '/';
}

function populate() {
    document.getElementById('score').textContent = data.score?.toLocaleString() ?? '—';
    document.getElementById('max-score').textContent = '/ ' + (data.max_score?.toLocaleString() ?? '100');
    document.getElementById('tier-title').textContent = data.tier_title ?? 'UNKNOWN';
    document.getElementById('tagline').textContent = data.tagline ?? '';

    const breakdown = document.getElementById('breakdown');
    const items = [];

    if (data.breakdown) {
        data.breakdown.forEach(cat => {
            items.push({ label: cat.category, comment: cat.comment, score: cat.score });
        });
    }

    if (data.penalties) {
        data.penalties.forEach(p => {
            items.push({ label: p.reason, comment: p.comment, score: -p.deduction });
        });
    }

    if (items.length > 0) {
        breakdown.innerHTML = items.map((item, i) => `
            <div class="flex justify-between items-center py-2${i < items.length - 1 ? ' border-b border-outline-variant/20' : ''}">
                <div class="flex flex-col">
                    <span class="font-data-mono text-secondary text-sm">${item.label}</span>
                    <span class="font-data-mono text-text-muted text-xs">${item.comment}</span>
                </div>
                <span class="font-data-mono ${item.score >= 0 ? 'text-primary' : 'text-error'} font-bold">${item.score >= 0 ? '+' : ''}${item.score}</span>
            </div>
        `).join('');
    }

    const prescription = document.getElementById('prescription');
    if (data.prescription) {
        prescription.innerHTML = data.prescription.map((tip, i) => `
            <div class="flex items-start gap-md bg-input-bg p-md rounded-lg group hover:bg-input-bg/80 transition-colors border-l-4 border-primary">
                <span class="font-headline-hero text-primary/40 text-2xl leading-none">${String(i + 1).padStart(2, '0')}</span>
                <div class="space-y-1">
                    <p class="text-sm text-on-surface">${tip.tip}</p>
                    <p class="font-data-mono text-[10px] text-primary">${tip.gain}</p>
                </div>
            </div>
        `).join('');
    }

    const roastEl = document.getElementById('roast');
    if (roastEl) roastEl.textContent = data.specific_roast ?? '';
    const verdictEl = document.getElementById('verdict');
    if (verdictEl) verdictEl.textContent = data.verdict ?? '';
}

document.getElementById('try-another').addEventListener('click', () => {
    localStorage.removeItem('aura');
    window.location.href = '/';
});

populate();
