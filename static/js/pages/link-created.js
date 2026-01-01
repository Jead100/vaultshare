(function() {
    // ---------- Copy Button ----------
    const shareInput = document.getElementById('share-link');
    const copyBtn = document.getElementById('copy-btn')

    let copyResetTimer;

    async function doCopy() {
        if (!shareInput || !copyBtn) return;

        try {
            await navigator.clipboard.writeText(shareInput.value);
            flashCopied();
        } catch {
            // Fallback for old browsers: select text for manual copy
            shareInput.select();
        }
    }

    function flashCopied() {
        const original = copyBtn.textContent;
        copyBtn.dataset.state = 'copied';
        copyBtn.textContent = 'Copied!';
        clearTimeout(copyResetTimer);
        copyResetTimer = setTimeout(() => {
            copyBtn.dataset.state = 'ready';
            copyBtn.textContent = original;
        }, 2000);
    }

    copyBtn?.addEventListener('click', doCopy);

    // ---------- Expiry Countdown ----------
    const cdEl = document.getElementById('countdown');
    const meta = document.getElementById('link-meta');
    if (!cdEl || !meta) return;

    // Convert to ms
    const expiryMs = Number(meta.dataset.expires) * 1000;
    const serverNowMs = Number(meta.dataset.serverNow) * 1000;
    if (!Number.isFinite(expiryMs) || !Number.isFinite(serverNowMs)) return;

    // Estimate server<->client clock offset (and include network delay)
    const offset = Date.now() - serverNowMs; // positive if client clock is ahead

    const baseTitle = document.title.replace(/\s*\(.*\)$/, ''); // strip any previous "(...)" suffix

    function formatMMSS(ms) {
        const total = Math.max(0, Math.round(ms / 1000));
        const m = Math.floor(total / 60);
        const s = total % 60;
        return `${m}:${String(s).padStart(2, '0')}`;
    }

    function onExpired() {
        // Freeze UI when expired
        cdEl.textContent = 'Expired';
        document.title = `${baseTitle} (Expired)`;
        const p = cdEl.closest('p');
        p?.classList.remove('text-red-500');
        p?.classList.add('text-gray-500');
        const btn = document.getElementById('copy-btn');
        if (copyBtn) {
            copyBtn.disabled = true;
            const status = document.getElementById('copy-status');
            if (status) status.textContent = 'This link has expired.';

            // Dim the input so the whole "share" row looks inactive
            const row = shareInput?.closest('.flex.items-center');
            row?.classList.add('opacity-60');

            // Move focus back to the link field for accessibility
            shareInput?.focus();
        }
    }

    function tick() {
        const serverNowApprox = Date.now() - offset;
        const remaining = expiryMs - serverNowApprox;
        if (remaining <= 0) {
            clearInterval(timer);
            onExpired();
        } else {
            const timeStr = formatMMSS(remaining);
            cdEl.textContent = timeStr;
            // Also reflect in the tab title:
            document.title = `${baseTitle} (${timeStr})`;
        }
    }

    // Kick off immediately, then every second
    tick();
    const timer = setInterval(tick, 1000);
})();
