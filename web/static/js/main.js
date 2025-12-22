/**
 * Main Application Logic
 * Handles UI interactions and API calls
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const usernamesInput = document.getElementById('usernames');
    const btnConvert = document.getElementById('btn-convert-usernames');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const resultsSection = document.getElementById('results-section');
    const resultsGrid = document.getElementById('results-grid');
    const batchActions = document.getElementById('batch-actions');
    const btnDownloadAll = document.getElementById('btn-download-all');
    const previewModal = document.getElementById('preview-modal');
    const previewContainer = document.getElementById('preview-container');
    const modalClose = document.getElementById('modal-close');
    const modalTitle = document.getElementById('modal-title');
    const modalDownload = document.getElementById('modal-download');

    let currentResults = [];
    let currentViewer = null;
    let currentDownloadId = null;

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        });
    });

    // Convert by username
    btnConvert.addEventListener('click', async () => {
        const text = usernamesInput.value.trim();
        if (!text) {
            alert('Please enter at least one username');
            return;
        }

        const usernames = text.split('\n').map(u => u.trim()).filter(u => u);
        if (usernames.length === 0) {
            alert('Please enter valid usernames');
            return;
        }

        btnConvert.disabled = true;
        btnConvert.querySelector('.btn-text').style.display = 'none';
        btnConvert.querySelector('.btn-loading').style.display = 'inline';

        try {
            const response = await fetch('/api/convert/username', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ usernames })
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.results);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            alert('Failed to connect to server: ' + error.message);
        } finally {
            btnConvert.disabled = false;
            btnConvert.querySelector('.btn-text').style.display = 'inline';
            btnConvert.querySelector('.btn-loading').style.display = 'none';
        }
    });

    // File upload - dropzone click
    dropzone.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // Drag and drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    async function uploadFile(file) {
        if (!file.name.toLowerCase().endsWith('.png')) {
            alert('Please upload a PNG file');
            return;
        }

        dropzone.classList.add('loading');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/convert/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.results);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            alert('Failed to upload: ' + error.message);
        } finally {
            dropzone.classList.remove('loading');
        }
    }

    function displayResults(results) {
        currentResults = results.filter(r => r.success);

        resultsSection.style.display = 'block';
        resultsGrid.innerHTML = '';

        results.forEach(result => {
            const card = createResultCard(result);
            resultsGrid.appendChild(card);
        });

        // Show batch download if multiple successful results
        batchActions.style.display = currentResults.length > 1 ? 'block' : 'none';

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'result-card' + (result.success ? '' : ' error');

        if (result.success) {
            card.innerHTML = `
                <div class="result-preview" data-id="${result.id}">
                    <div class="preview-placeholder">Loading preview...</div>
                </div>
                <div class="result-info">
                    <div class="result-name">${result.name}</div>
                    <div class="result-dimensions">${result.dimensions.join(' × ')} blocks</div>
                    <div class="result-actions">
                        <button class="btn-preview" data-id="${result.id}" data-name="${result.name}">🔍 Preview</button>
                        <button class="btn-download" data-id="${result.id}">⬇ Download</button>
                    </div>
                </div>
            `;

            // Load mini preview
            setTimeout(() => loadMiniPreview(result), 100);

        } else {
            card.innerHTML = `
                <div class="result-info">
                    <div class="result-name">${result.username || result.name}</div>
                    <div class="result-error">❌ ${result.error}</div>
                </div>
            `;
        }

        return card;
    }

    async function loadMiniPreview(result) {
        try {
            const response = await fetch(result.preview_url);
            const data = await response.json();

            if (data.success) {
                const container = document.querySelector(`.result-preview[data-id="${result.id}"]`);
                if (container) {
                    container.innerHTML = '';
                    new MiniPreview(container, data.blocks, data.dimensions);
                }
            }
        } catch (error) {
            console.error('Failed to load preview:', error);
        }
    }

    // Result card actions (event delegation)
    resultsGrid.addEventListener('click', async (e) => {
        const previewBtn = e.target.closest('.btn-preview');
        const downloadBtn = e.target.closest('.btn-download');
        const previewArea = e.target.closest('.result-preview');

        if (previewBtn || previewArea) {
            const id = (previewBtn || previewArea).dataset.id;
            const name = previewBtn?.dataset.name || 'Sculpture';
            await openPreviewModal(id, name);
        }

        if (downloadBtn) {
            downloadFile(downloadBtn.dataset.id);
        }
    });

    async function openPreviewModal(id, name) {
        previewModal.classList.add('active');
        modalTitle.textContent = `${name} - 3D Preview`;
        currentDownloadId = id;

        // Clear previous viewer
        previewContainer.innerHTML = '<div style="color:#fff;padding:20px;">Loading 3D model...</div>';

        try {
            const response = await fetch(`/api/preview/${id}`);
            const data = await response.json();

            if (data.success) {
                previewContainer.innerHTML = '';
                currentViewer = new VoxelViewer(previewContainer);
                currentViewer.loadBlocks(data.blocks, data.dimensions);
            } else {
                previewContainer.innerHTML = '<div style="color:#f00;padding:20px;">Failed to load preview</div>';
            }
        } catch (error) {
            previewContainer.innerHTML = `<div style="color:#f00;padding:20px;">Error: ${error.message}</div>`;
        }
    }

    // Modal close
    modalClose.addEventListener('click', () => closeModal());
    previewModal.addEventListener('click', (e) => {
        if (e.target === previewModal) closeModal();
    });

    function closeModal() {
        previewModal.classList.remove('active');
        if (currentViewer) {
            currentViewer.dispose();
            currentViewer = null;
        }
    }

    modalDownload.addEventListener('click', () => {
        if (currentDownloadId) {
            downloadFile(currentDownloadId);
        }
    });

    function downloadFile(id) {
        window.location.href = `/api/download/${id}`;
    }

    // Batch download
    btnDownloadAll.addEventListener('click', async () => {
        const ids = currentResults.map(r => r.id);

        try {
            const response = await fetch('/api/download/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'sculptures.zip';
                a.click();
                URL.revokeObjectURL(url);
            } else {
                alert('Failed to create ZIP file');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });

    // Keyboard shortcut - Escape to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && previewModal.classList.contains('active')) {
            closeModal();
        }
    });
});
