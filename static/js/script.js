document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const filePrompt = document.getElementById('file-prompt');
    const fileName = document.getElementById('file-name');
    const convertBtn = document.getElementById('convert-btn');
    const downloadBtn = document.getElementById('download-btn');
    const status = document.getElementById('status');
    const statusText = document.getElementById('status-text');
    const error = document.getElementById('error');
    const errorText = document.getElementById('error-text');
    const conversionTypeInput = document.getElementById('conversion-type');
    const pdfToDocxRadio = document.getElementById('pdf-to-docx');
    const docxToPdfRadio = document.getElementById('docx-to-pdf');
    
    // Variables globales
    let selectedFile = null;
    let convertedFileName = null;
    let originalFileName = null;
    
    // Manejar cambio en el tipo de conversión
    pdfToDocxRadio.addEventListener('change', updateFileInputAccept);
    docxToPdfRadio.addEventListener('change', updateFileInputAccept);
    
    function updateFileInputAccept() {
        // Actualizar el tipo de archivo aceptado según la conversión seleccionada
        if (pdfToDocxRadio.checked) {
            fileInput.accept = '.pdf';
            conversionTypeInput.value = 'pdf_to_docx';
            filePrompt.textContent = 'Arrastra un PDF aquí o haz clic para seleccionar';
        } else {
            fileInput.accept = '.docx,.doc';
            conversionTypeInput.value = 'docx_to_pdf';
            filePrompt.textContent = 'Arrastra un archivo Word aquí o haz clic para seleccionar';
        }
        
        // Resetear la selección de archivo
        resetFileSelection();
    }
    
    // Eventos para arrastrar y soltar archivos
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('dragover');
    }
    
    function unhighlight() {
        dropArea.classList.remove('dragover');
    }
    
    // Manejar archivos soltados
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    // Manejar selección de archivo mediante el input
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    // Procesar archivos seleccionados
    function handleFiles(files) {
        if (files.length === 0) return;
        
        const file = files[0];
        
        // Verificar tipo de archivo según conversión seleccionada
        if (pdfToDocxRadio.checked) {
            if (file.type !== 'application/pdf') {
                showError('El archivo debe ser un PDF');
                resetFileSelection();
                return;
            }
        } else {
            const validWordTypes = [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
                'application/msword' // .doc
            ];
            if (!validWordTypes.includes(file.type)) {
                showError('El archivo debe ser un documento Word (.docx o .doc)');
                resetFileSelection();
                return;
            }
        }
        
        // Verificar tamaño máximo (16MB)
        if (file.size > 16 * 1024 * 1024) {
            showError('El archivo no debe superar los 16MB');
            resetFileSelection();
            return;
        }
        
        // Archivo válido, actualizar UI
        selectedFile = file;
        filePrompt.classList.add('hidden');
        fileName.textContent = file.name;
        fileName.classList.remove('hidden');
        convertBtn.disabled = false;
        hideError();
    }
    
    // Botón para iniciar la conversión
    convertBtn.addEventListener('click', convertFile);
    
    // Función para convertir el archivo
    function convertFile() {
        if (!selectedFile) return;
        
        // Mostrar estado de carga
        const conversionText = pdfToDocxRadio.checked ? 
            'Convirtiendo PDF a Word...' : 
            'Convirtiendo Word a PDF...';
            
        showStatus(conversionText);
        convertBtn.disabled = true;
        
        // Crear formulario para enviar el archivo
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('conversion_type', conversionTypeInput.value);
        
        // Enviar petición AJAX
        fetch('/convert', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideStatus();
            
            if (data.success) {
                // Conversión exitosa
                convertedFileName = data.filename;
                originalFileName = data.download_name;
                downloadBtn.classList.remove('hidden');
                statusText.textContent = '¡Conversión completada!';
                status.classList.remove('hidden');
            } else {
                // Error en la conversión
                showError(data.error || 'Error al convertir el archivo');
                convertBtn.disabled = false;
            }
        })
        .catch(err => {
            hideStatus();
            showError('Error de conexión. Por favor, intenta de nuevo.');
            convertBtn.disabled = false;
            console.error('Error:', err);
        });
    }
    
    // Manejar botón de descarga
    downloadBtn.addEventListener('click', downloadFile);
    
    // Función para descargar el archivo convertido
    function downloadFile() {
        if (!convertedFileName) return;
        
        // Crear enlace de descarga
        const downloadUrl = `/download/${convertedFileName}`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = originalFileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Limpiar archivo del servidor después de un breve retraso
        setTimeout(() => {
            fetch('/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename: convertedFileName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Archivo limpiado del servidor');
                }
            })
            .catch(err => {
                console.error('Error al limpiar el archivo:', err);
            });
        }, 3000);
        
        // Resetear UI para una nueva conversión
        resetUI();
    }
    
    // Función para mostrar mensaje de error
    function showError(message) {
        errorText.textContent = message;
        error.classList.remove('hidden');
    }
    
    // Función para ocultar mensaje de error
    function hideError() {
        error.classList.add('hidden');
    }
    
    // Función para mostrar estado de carga
    function showStatus(message) {
        statusText.textContent = message;
        status.classList.remove('hidden');
    }
    
    // Función para ocultar estado de carga
    function hideStatus() {
        status.classList.add('hidden');
    }
    
    // Función para resetear la selección de archivo
    function resetFileSelection() {
        fileInput.value = '';
        selectedFile = null;
        fileName.classList.add('hidden');
        filePrompt.classList.remove('hidden');
        convertBtn.disabled = true;
    }
    
    // Función para resetear toda la UI
    function resetUI() {
        resetFileSelection();
        downloadBtn.classList.add('hidden');
        convertedFileName = null;
    }
    
    // Permitir hacer clic en todo el área de dropArea
    dropArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Inicializar con la configuración por defecto (PDF a DOCX)
    updateFileInputAccept();
});