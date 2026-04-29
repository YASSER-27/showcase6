/**
 * Showcase Studio Mini - Core Logic
 * Handles drag-drop, element creation, and editor interactions.
 */

const state = {
    images: [],
    elements: [],
    selectedId: null,
    clipboard: null,
    styleClipboard: null,
    isDragging: false,
    draggedElem: null,
    startPos: { x: 0, y: 0 },
    startRect: { x: 0, y: 0, w: 0, h: 0 }
};

// ── DOM Elements ──
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('previewGrid');
const uploadSection = document.getElementById('uploadSection');
const editorSection = document.getElementById('editorSection');
const canvas = document.getElementById('canvas');
const progressBar = document.getElementById('progressBar');
const propsContent = document.getElementById('propsContent');
const noSelectionMsg = document.querySelector('.no-selection-msg');

// ── Initialization ──
function init() {
    setupDragAndDrop();
    setupEventListeners();
}

// ── Drag & Drop Logic ──
function setupDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        handleFiles(dt.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

async function handleFiles(files) {
    const validFiles = Array.from(files).filter(f => f.type.startsWith('image/')).slice(0, 4 - state.images.length);
    
    for (const file of validFiles) {
        const reader = new FileReader();
        reader.onload = (e) => {
            state.images.push(e.target.result);
            updatePreviewGrid();
            if (state.images.length >= 1) {
                // Short delay to show preview then transition
                setTimeout(startEditor, 800);
            }
        };
        reader.readAsDataURL(file);
    }
}

function updatePreviewGrid() {
    previewGrid.innerHTML = '';
    state.images.forEach(src => {
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `<img src="${src}">`;
        previewGrid.appendChild(div);
    });
}

function startEditor() {
    progressBar.style.width = '100%';
    uploadSection.classList.remove('active');
    editorSection.classList.add('active');
    
    // Add first image to canvas automatically
    state.images.forEach((src, idx) => {
        const offset = idx * 40;
        addElement('image', { src, x: 100 + offset, y: 100 + offset, w: 400 });
    });
}

// ── Element Management ──
function addElement(type, options = {}) {
    const id = 'elem-' + Date.now() + Math.floor(Math.random() * 1000);
    const elem = document.createElement('div');
    elem.id = id;
    elem.className = 'canvas-element';
    elem.style.left = (options.x || 50) + 'px';
    elem.style.top = (options.y || 50) + 'px';
    elem.style.zIndex = state.elements.length + 1;
    
    const data = {
        id,
        type,
        x: options.x || 50,
        y: options.y || 50,
        w: options.w || (type === 'text' ? 300 : 200),
        h: options.h || (type === 'text' ? 'auto' : 150),
        rotX: options.rotX || 0,
        rotY: options.rotY || 0,
        rotZ: options.rotZ || 0,
        shadow: options.shadow !== undefined ? options.shadow : 20,
        opacity: options.opacity !== undefined ? options.opacity : 100,
        color: options.color || '#ffffff',
        text: options.text || 'Double click to edit',
        fontSize: options.fontSize || (type === 'badge' ? 14 : 40),
        bg: options.bg || '#7c5cfc'
    };

    if (type === 'image') {
        const img = document.createElement('img');
        img.src = options.src;
        elem.appendChild(img);
        elem.style.width = data.w + 'px';
    } else if (type === 'text' || type === 'badge') {
        const textDiv = document.createElement('div');
        textDiv.className = 'text-content';
        textDiv.innerText = data.text;
        textDiv.style.color = data.color;
        textDiv.style.fontSize = data.fontSize + 'px';
        
        if (type === 'badge') {
            if (options.subType === 'split') {
                const [left, right] = data.text.split('|');
                elem.innerHTML = `
                    <div class="split-badge">
                        <div class="left-part">${left || 'build'}</div>
                        <div class="right-part" style="background:${data.bg}">${right || 'passing'}</div>
                    </div>
                `;
                elem.style.background = 'transparent';
                elem.style.padding = '0';
            } else {
                elem.style.background = data.bg;
                elem.style.borderRadius = options.subType === 'square' ? '4px' : (options.subType === 'rect' ? '4px' : '50px');
                elem.style.padding = '2px 16px';
                textDiv.style.fontWeight = 'bold';
                elem.appendChild(textDiv);
            }
        } else {
            elem.appendChild(textDiv);
        }
    }

    // Add Resizer & Rotation Handle
    const resizer = document.createElement('div');
    resizer.className = 'resizer br';
    elem.appendChild(resizer);

    const rotHandle = document.createElement('div');
    rotHandle.className = 'rotation-handle';
    elem.appendChild(rotHandle);

    // Interaction Events
    elem.addEventListener('mousedown', (e) => selectElement(id, e));
    
    canvas.appendChild(elem);
    state.elements.push(data);
    selectElement(id);
    
    updateTransform(id);
}

function selectElement(id, e = null) {
    if (state.selectedId) {
        document.getElementById(state.selectedId)?.classList.remove('selected');
    }
    
    state.selectedId = id;
    const elem = document.getElementById(id);
    if (elem) {
        elem.classList.add('selected');
        showProperties(id);
        
        if (e && !e.target.classList.contains('resizer')) {
            startDrag(e, id);
        }
    }
}

function showProperties(id) {
    const data = state.elements.find(el => el.id === id);
    if (!data) return;

    noSelectionMsg.classList.add('hidden');
    propsContent.classList.remove('hidden');
    
    document.getElementById('propTitle').innerText = `Edit ${data.type.toUpperCase()}`;
    
    // Text props visibility
    const textProps = document.getElementById('textProps');
    const badgeColors = document.getElementById('badgeColors');
    
    if (data.type === 'text' || data.type === 'badge') {
        textProps.classList.remove('hidden');
        document.getElementById('textInput').value = data.text;
        document.getElementById('textSize').value = data.fontSize;
        document.getElementById('textColor').value = data.color;
        
        if (data.type === 'badge') {
            badgeColors.classList.remove('hidden');
            document.getElementById('badgeBg').value = data.bg;
        } else {
            badgeColors.classList.add('hidden');
        }
    } else {
        textProps.classList.add('hidden');
    }

    // Sliders
    document.getElementById('rotX').value = data.rotX;
    document.getElementById('rotY').value = data.rotY;
    document.getElementById('rotZ').value = data.rotZ;
    document.getElementById('shadowStr').value = data.shadow;
    document.getElementById('opacity').value = data.opacity;
}

// ── Interactions ──
function startDrag(e, id) {
    state.isDragging = true;
    state.draggedElem = id;
    const data = state.elements.find(el => el.id === id);
    state.startPos = { x: e.clientX, y: e.clientY };
    state.startRect = { x: data.x, y: data.y };
    
    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', stopDrag);
}

function onDrag(e) {
    if (!state.isDragging) return;
    
    const dx = e.clientX - state.startPos.x;
    const dy = e.clientY - state.startPos.y;
    
    const data = state.elements.find(el => el.id === state.draggedElem);
    data.x = state.startRect.x + dx;
    data.y = state.startRect.y + dy;
    
    const elem = document.getElementById(state.draggedElem);
    elem.style.left = data.x + 'px';
    elem.style.top = data.y + 'px';
}

function stopDrag() {
    state.isDragging = false;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', stopDrag);
}

function updateTransform(id) {
    const data = state.elements.find(el => el.id === id);
    const elem = document.getElementById(id);
    if (!data || !elem) return;

    const transform = `rotateX(${data.rotX}deg) rotateY(${data.rotY}deg) rotateZ(${data.rotZ}deg)`;
    elem.style.transform = transform;
    elem.style.opacity = data.opacity / 100;
    
    const shadowVal = data.shadow / 2;
    elem.style.boxShadow = `0 ${shadowVal}px ${shadowVal * 2}px rgba(0,0,0,0.5)`;
}

// ── Event Listeners ──
function setupEventListeners() {
    // Toolbar Actions
    document.getElementById('addTextBtn').addEventListener('click', () => {
        addElement('text', { text: 'New Text Block', x: 100, y: 100 });
    });

    document.getElementById('addImageBtn').addEventListener('click', () => {
        fileInput.click();
    });

    // Property Inputs
    document.getElementById('textInput').addEventListener('input', (e) => {
        if (!state.selectedId) return;
        const data = state.elements.find(el => el.id === state.selectedId);
        data.text = e.target.value;
        const target = document.getElementById(state.selectedId).querySelector('.text-content');
        if (target) target.innerText = data.text;
    });

    document.getElementById('textSize').addEventListener('input', (e) => {
        if (!state.selectedId) return;
        const data = state.elements.find(el => el.id === state.selectedId);
        data.fontSize = e.target.value;
        const target = document.getElementById(state.selectedId).querySelector('.text-content');
        if (target) target.style.fontSize = data.fontSize + 'px';
    });

    document.getElementById('textColor').addEventListener('input', (e) => {
        if (!state.selectedId) return;
        const data = state.elements.find(el => el.id === state.selectedId);
        data.color = e.target.value;
        const target = document.getElementById(state.selectedId).querySelector('.text-content');
        if (target) target.style.color = data.color;
    });

    document.getElementById('badgeBg').addEventListener('input', (e) => {
        if (!state.selectedId) return;
        const data = state.elements.find(el => el.id === state.selectedId);
        data.bg = e.target.value;
        const elem = document.getElementById(state.selectedId);
        if (elem) elem.style.background = data.bg;
    });

    ['rotX', 'rotY', 'rotZ', 'shadowStr', 'opacity'].forEach(id => {
        document.getElementById(id).addEventListener('input', (e) => {
            if (!state.selectedId) return;
            const data = state.elements.find(el => el.id === state.selectedId);
            const key = id === 'shadowStr' ? 'shadow' : id;
            data[key] = e.target.value;
            updateTransform(state.selectedId);
        });
    });

    document.getElementById('deleteElem').addEventListener('click', () => {
        deleteSelected();
    });

    document.querySelectorAll('.badge-preset').forEach(btn => {
        btn.addEventListener('click', () => {
            addElement('badge', {
                text: btn.dataset.text,
                bg: btn.dataset.bg,
                color: btn.dataset.fg,
                subType: btn.dataset.type || 'pill',
                x: 150,
                y: 150
            });
        });
    });

    document.getElementById('bringFront').addEventListener('click', () => {
        if (!state.selectedId) return;
        const elem = document.getElementById(state.selectedId);
        const maxZ = Math.max(...state.elements.map(el => parseInt(document.getElementById(el.id).style.zIndex || 0)));
        elem.style.zIndex = maxZ + 1;
    });

    document.getElementById('sendBack').addEventListener('click', () => {
        if (!state.selectedId) return;
        const elem = document.getElementById(state.selectedId);
        const minZ = Math.min(...state.elements.map(el => parseInt(document.getElementById(el.id).style.zIndex || 0)));
        elem.style.zIndex = Math.max(0, minZ - 1);
    });

    document.getElementById('resetBtn').addEventListener('click', () => {
        location.reload();
    });

    // Export Action
    document.getElementById('exportBtn').addEventListener('click', () => {
        exportCanvas();
    });

    // Background Color
    document.getElementById('canvasBg').addEventListener('input', (e) => {
        canvas.style.background = e.target.value;
    });

    document.getElementById('copyElem').addEventListener('click', () => {
        copySelected();
    });

    document.getElementById('copyStyle').addEventListener('click', () => {
        if (!state.selectedId) return;
        const data = state.elements.find(el => el.id === state.selectedId);
        state.styleClipboard = { ...data };
    });

    document.getElementById('pasteStyle').addEventListener('click', () => {
        if (!state.selectedId || !state.styleClipboard) return;
        const data = state.elements.find(el => el.id === state.selectedId);
        const style = state.styleClipboard;
        
        data.rotX = style.rotX;
        data.rotY = style.rotY;
        data.rotZ = style.rotZ;
        data.shadow = style.shadow;
        data.opacity = style.opacity;
        data.color = style.color;
        data.bg = style.bg;
        
        const elem = document.getElementById(state.selectedId);
        if (data.type === 'badge') elem.style.background = data.bg;
        const target = elem.querySelector('.text-content');
        if (target) {
            target.style.color = data.color;
        }
        
        updateTransform(state.selectedId);
        showProperties(state.selectedId);
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Delete or Backspace
        if (e.key === 'Delete' || (e.key === 'Backspace' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
            deleteSelected();
        }

        // Ctrl+C (Copy)
        if (e.ctrlKey && e.key === 'c') {
            copySelected();
        }

        // Ctrl+V (Paste)
        if (e.ctrlKey && e.key === 'v') {
            pasteSelected();
        }
    });
}

function deleteSelected() {
    if (!state.selectedId) return;
    const elem = document.getElementById(state.selectedId);
    if (elem) {
        elem.remove();
        state.elements = state.elements.filter(el => el.id !== state.selectedId);
        state.selectedId = null;
        propsContent.classList.add('hidden');
        noSelectionMsg.classList.remove('hidden');
    }
}

function copySelected() {
    if (!state.selectedId) return;
    const data = state.elements.find(el => el.id === state.selectedId);
    if (data) {
        state.clipboard = JSON.parse(JSON.stringify(data)); // Deep copy
    }
}

function pasteSelected() {
    if (!state.clipboard) return;
    const options = { ...state.clipboard };
    options.x += 40; // Offset pasted element
    options.y += 40;
    
    // For images, we need the src from the DOM element because it's not in the data object
    if (options.type === 'image') {
        const origElem = document.getElementById(state.clipboard.id);
        if (origElem) {
            options.src = origElem.querySelector('img').src;
        }
    }
    
    addElement(options.type, options);
}

function exportCanvas() {
    document.getElementById('ratioModal').classList.remove('hidden');
}

document.getElementById('closeRatioModal').addEventListener('click', () => {
    document.getElementById('ratioModal').classList.add('hidden');
});

document.querySelectorAll('.ratio-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const ratioStr = btn.dataset.ratio; // e.g., "1/1"
        const [wRatio, hRatio] = ratioStr.split('/').map(Number);
        document.getElementById('ratioModal').classList.add('hidden');
        await performExport(wRatio / hRatio);
    });
});

async function performExport(aspectRatio) {
    if (typeof htmlToImage === 'undefined') {
        alert("Export library still loading...");
        return;
    }

    const exportBtn = document.getElementById('exportBtn');
    exportBtn.innerText = "Exporting...";
    exportBtn.disabled = true;

    // Hide selection
    const prevSelected = state.selectedId;
    if (prevSelected) document.getElementById(prevSelected).classList.remove('selected');

    // Store original height
    const origHeight = canvas.offsetHeight;
    const targetHeight = canvas.offsetWidth / aspectRatio;
    
    // Temporarily resize canvas
    canvas.style.height = targetHeight + 'px';
    canvas.style.display = 'flex'; // Ensure centering if needed
    canvas.style.alignItems = 'center';
    canvas.style.justifyContent = 'center';

    try {
        const dataUrl = await htmlToImage.toPng(canvas, {
            quality: 1,
            pixelRatio: 3,
            backgroundColor: document.getElementById('canvasBg').value,
            style: {
                background: document.getElementById('canvasBg').value,
                display: 'block'
            }
        });
        
        const link = document.createElement('a');
        link.download = `showcase-${Date.now()}.png`;
        link.href = dataUrl;
        link.click();
    } catch (error) {
        console.error('Export failed:', error);
    } finally {
        // Restore
        canvas.style.height = '';
        canvas.style.display = '';
        if (prevSelected) document.getElementById(prevSelected).classList.add('selected');
        exportBtn.innerText = "Export Image";
        exportBtn.disabled = false;
    }
}

// Resizing logic (simplified)
canvas.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('resizer')) {
        const id = e.target.parentElement.id;
        const data = state.elements.find(el => el.id === id);
        state.isResizing = true;
        state.resizingId = id;
        state.startPos = { x: e.clientX, y: e.clientY };
        state.startRect = { w: data.w, h: data.h };
        
        const onResize = (moveE) => {
            const dx = moveE.clientX - state.startPos.x;
            const dy = moveE.clientY - state.startPos.y;
            data.w = state.startRect.w + dx;
            const elem = document.getElementById(id);
            elem.style.width = data.w + 'px';
        };
        
        const stopResize = () => {
            state.isResizing = false;
            document.removeEventListener('mousemove', onResize);
            document.removeEventListener('mouseup', stopResize);
        };
        
        document.addEventListener('mousemove', onResize);
        document.addEventListener('mouseup', stopResize);
        e.stopPropagation();
    }
});

// Rotation Handle Logic
canvas.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('rotation-handle')) {
        const id = e.target.parentElement.id;
        const data = state.elements.find(el => el.id === id);
        const elem = document.getElementById(id);
        const rect = elem.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const onRotate = (moveE) => {
            const dx = moveE.clientX - centerX;
            const dy = moveE.clientY - centerY;
            const angle = Math.atan2(dy, dx) * (180 / Math.PI) + 90;
            data.rotZ = angle;
            updateTransform(id);
            // Update slider if visible
            if (state.selectedId === id) {
                document.getElementById('rotZ').value = angle;
            }
        };

        const stopRotate = () => {
            document.removeEventListener('mousemove', onRotate);
            document.removeEventListener('mouseup', stopRotate);
        };

        document.addEventListener('mousemove', onRotate);
        document.addEventListener('mouseup', stopRotate);
        e.stopPropagation();
    }
});

init();
