const data = JSON.parse(localStorage.getItem('aura'));

if (!data) {
    window.location.href = '/';
}

function populate() {
    document.getElementById('score').textContent = data.score?.toLocaleString() ?? '—';
    document.getElementById('tier-title').textContent = data.tier_title ?? 'UNKNOWN';
    document.getElementById('tagline').textContent = data.tagline ?? '';

    const breakdown = document.getElementById('breakdown');
    if (data.breakdown) {
        breakdown.innerHTML = data.breakdown.map(cat => `
            <div class="flex justify-between items-center py-2 border-b border-outline-variant/20">
                <div class="flex flex-col">
                    <span class="font-data-mono text-secondary text-sm">${cat.category}</span>
                    <span class="font-data-mono text-text-muted text-xs">${cat.comment}</span>
                </div>
                <span class="font-data-mono ${cat.score >= 0 ? 'text-primary' : 'text-error'} font-bold">${cat.score >= 0 ? '+' : ''}${cat.score}</span>
            </div>
        `).join('');
    }

    const penalties = document.getElementById('penalties');
    if (data.penalties) {
        penalties.innerHTML = data.penalties.map(p => `
            <div class="flex justify-between items-center py-2 border-b border-outline-variant/20">
                <div class="flex flex-col">
                    <span class="font-data-mono text-text-muted text-xs">${p.reason}</span>
                    <span class="font-data-mono text-text-muted text-[10px]">${p.comment}</span>
                </div>
                <span class="font-data-mono text-error font-bold">-${p.deduction}</span>
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
                    <p class="font-data-mono text-[10px] text-primary">+${tip.gain} AURA</p>
                </div>
            </div>
        `).join('');
    }

    document.getElementById('roast').textContent = data.specific_roast ?? '';
    document.getElementById('verdict').textContent = data.verdict ?? '';
}

document.getElementById('try-another').addEventListener('click', () => {
    localStorage.removeItem('aura');
    window.location.href = '/';
});

populate();
