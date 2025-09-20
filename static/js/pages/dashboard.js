(function() {
    console.log('dashboard.js loaded')
    
    // Prevent double-binding if template reuses this
    if (window.__dashboardBound) return;
    window.__dashboardBound = true;

    // Elements
    const fileInput   = document.getElementById('file-input');
    const fileNameEl  = document.getElementById('file-name');
    const uploadForm  = document.getElementById('upload-form');
    const uploadBtn   = document.getElementById('upload-btn');
    const clearBtn    = document.getElementById('clear-file')
    const errorsDiv   = document.getElementById('upload-errors');
    const listBodyEl  = document.getElementById('files-list-body');
    const fileLabel   = document.querySelector('label[for="file-input"]');

    /* --------------- Upload button state --------------- */
    function setUploading(isUploading) {
        if (isUploading) {
            uploadBtn.dataset.originalText = uploadBtn.textContent;
            uploadBtn.textContent = 'Uploading...';
            uploadBtn.disabled = true;
        } else {
            uploadBtn.textContent = uploadBtn.dataset.originalText || 'Upload';
        }
    }

    /* ---------- File picker enable/disable helper ---------- */
    function setFilePickerEnabled(enabled) {
        if (!fileLabel) return;

        // Visual & interactive state
        fileLabel.classList.toggle('pointer-events-none', !enabled);
        fileLabel.classList.toggle('opacity-50', !enabled);
        fileLabel.classList.toggle('cursor-not-allowed', !enabled);

        // Accessibility
        fileLabel.setAttribute('aria-disabled', String(!enabled));

        // Key behavior: remove/restore the 'for' so clicks don't open the picker
        if (enabled) {
            fileLabel.setAttribute('for', 'file-input');
            fileLabel.removeAttribute('tabindex');
            fileLabel.removeAttribute('title');
        } else {
            fileLabel.removeAttribute('for');
            fileLabel.setAttribute('tabindex', '-1'); // keep it out of tab order
            fileLabel.setAttribute('title', 'Clear the file to select a different one');
        }
    }

    /* --------------- File selection UI --------------- */
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            fileNameEl.textContent = e.target.files[0].name;
            uploadBtn.disabled = false;
            clearBtn.classList.remove('hidden');
            setFilePickerEnabled(false); // disable label once a file is chosen
        } else {
            fileNameEl.textContent = 'No file selected';
            uploadBtn.disabled = true;
            clearBtn.classList.add('hidden')
            setFilePickerEnabled(true);
        }
    });

    /* ---------- Clear selection handler ---------- */
    clearBtn.addEventListener('click', () => {
        uploadForm.reset();
        fileNameEl.textContent = 'No file selected';
        uploadBtn.disabled = true;
        clearBtn.classList.add('hidden');
        setFilePickerEnabled(true);
    });

    /* --------------- Upload handler --------------- */
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorsDiv.textContent = '';

        // Guard: no file selected
        if (!fileInput.files || fileInput.files.length === 0) {
            errorsDiv.textContent = 'Please select a file to upload.';
            uploadBtn.disabled = true;
            return;
        }

        const formData = new FormData(uploadForm);

        try {
            setUploading(true);

            const res = await fetch(uploadForm.action, {
                method: 'POST',
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                body: formData,
                credentials: 'same-origin'
            });

            const data = await res.json().catch(() => ({}));

            if (res.ok && data.success) {
                // Swap in the fresh list HTML
                listBodyEl.innerHTML = data.html;

                // Reset form + UI state
                uploadForm.reset();
                fileNameEl.textContent = 'No file selected';
                clearBtn.classList.add('hidden')
                uploadBtn.disabled = true;
                setUploading(false);
                setFilePickerEnabled(true);
            } else {
                setUploading(false);
                if (data?.errors?.file) {
                    errorsDiv.textContent = data.errors.file.join(', ');
                } else if (data?.errors) {
                    errorsDiv.textContent = 'Upload failed. Please check the file and try again.';
                } else {
                    errorsDiv.textContent = 'Upload failed. Please try again.';
                }
                // Keep button enabled so user can retry without reselecting file
                uploadBtn.disabled = false;
            }
        } catch {
            setUploading(false);
            errorsDiv.textContent = 'An error occurred. Please try again.';
            // Keep button enabled so user can retry
            uploadBtn.disabled = false;
        }
    });

    /* ---------- Pagination (AJAX) ---------- */
    async function loadPage(url) {
        try {
            // Show a lightweight loading state
            const prevHTML = listBodyEl.innerHTML;
            listBodyEl.dataset.prevHTML = prevHTML;
            listBodyEl.innerHTML = '<div class="py-8 text-center text-gray-500">Loading…</div>';

            const res = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            });
            const data = await res.json();
            if (res.ok && data.success && data.html) {
                listBodyEl.innerHTML = data.html;
            } else {
                listBodyEl.innerHTML = prevHTML;
                alert('Could not load page.');
            }
        } catch {
            listBodyEl.innerHTML = listBodyEl.dataset.prevHTML || '';
            alert('Could not load page.');
        }
    }

    /* ---------- Pagination link click handler ---------- */
    listBodyEl.addEventListener('click', (e) => {
        const a = e.target.closest('a[data-page-link]');
        if (!a) return;
        e.preventDefault();
        const url = new URL(a.href, window.location.href);
        // Keep the browser URL in sync
        const params = new URLSearchParams(url.search);
        const page = params.get('page') || '1';
        const current = new URL(window.location.href);
        current.searchParams.set('page', page);
        history.replaceState(null, '', current.toString());
        loadPage(url.toString());
    });

    /* --------------- Delete handler --------------- */
    listBodyEl.addEventListener('submit', async (e) => {
        const form = e.target.closest('form.delete-form');
        if (!form) return; // ignore other forms

        e.preventDefault();

        const row = document.getElementById(`f-${form.dataset.itemId}`);
        const fileLabel = row?.querySelector('.font-medium')?.textContent?.trim();
        const confirmed = await window.confirmModal({
            title: 'Delete file',
            message: fileLabel 
            ? `Are you sure you want to delete “${fileLabel}”?` 
            : 'Are you sure you want to delete this file?',
            acceptText: 'Yes, delete',
            cancelText: 'Cancel'
        });
        if (!confirmed) return;

        const btn = form.querySelector('button[type=submit]');
        const originalText = btn?.textContent;
        if (btn) { btn.textContent = 'Deleting...'; btn.disabled = true; }

        try {
            const formData = new FormData(form);
            const res = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                body: formData,
                credentials: 'same-origin',
            });

            if (res.status === 204) {
                row?.remove();
                const remaining = listBodyEl.querySelectorAll('li[id^="f-"]').length;
                if (remaining === 0) {
                    // If page became empty, try loading previous page; else reload current
                    const url = new URL(window.location.href);
                    const currentPage = Number(url.searchParams.get('page') || '1');
                    const targetPage = Math.max(1, currentPage - 1);
                    url.searchParams.set('page', String(targetPage));
                    history.replaceState(null, '', url.toString());
                    loadPage(url.toString());
                }
                return;
            }

            // Try to surface server message if provided
            let msg = 'Could not delete file. Please try again.';
            try {
                const data = await res.json();
                if (data?.detail) msg = data.detail;
            } catch {}
            alert(msg);
        } catch {
            alert('Could not delete file. Please try again.');
        } finally {
            // Restore button if row wasn’t removed
            if (document.body.contains(row) && btn) {
                btn.textContent = originalText || 'Delete';
                btn.disabled = false;
            }
        }
    });
})();
