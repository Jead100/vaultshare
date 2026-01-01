(function () {
    function confirmModal({
        title = 'Confirm action',
        message = 'Are you sure?',
        acceptText = 'Confirm',
        cancelText = 'Cancel'
    } = {}) {
        const modal = document.getElementById('confirm-modal');
        if (!modal) {
            // graceful fallback if the partial wasn't included
            return Promise.resolve(window.confirm(message));
        }

        const backdrop = modal.firstElementChild;
        const dialog = modal.querySelector('[role="dialog"]');
        const titleEl = document.getElementById('confirm-modal-title');
        const descEl = document.getElementById('confirm-modal-desc');
        const btnCancel = document.getElementById('confirm-cancel');
        const btnAccept = document.getElementById('confirm-accept');

        titleEl.textContent = title;
        descEl.textContent = message;
        btnAccept.textContent = acceptText;
        btnCancel.textContent = cancelText;

        modal.classList.remove('hidden');

        const prevActive = document.activeElement;
        const prevOverflow = document.documentElement.style.overflow;
        document.documentElement.style.overflow = 'hidden';
        btnAccept.focus();

        return new Promise((resolve) => {
        let done = false;

        const cleanup = (value) => {
                if (done) return;
                done = true;

                modal.classList.add('hidden');
                document.documentElement.style.overflow = prevOverflow;
                if (prevActive && typeof prevActive.focus === 'function') prevActive.focus();

                btnAccept.removeEventListener('click', onAccept);
                btnCancel.removeEventListener('click', onCancel);
                backdrop.removeEventListener('click', onCancel);
                document.removeEventListener('keydown', onKey);

                resolve(value);
            };

            const onAccept = () => cleanup(true);
            const onCancel = () => cleanup(false);
            const onKey = (e) => {
                if (e.key === 'Escape') onCancel();
                if (e.key === 'Enter') onAccept();
            };

            btnAccept.addEventListener('click', onAccept);
            btnCancel.addEventListener('click', onCancel);
            backdrop.addEventListener('click', onCancel);
            document.addEventListener('keydown', onKey);
        });
    }

    // expose globally
    window.confirmModal = confirmModal;
})();
