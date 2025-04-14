import os
import uuid
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from pdf2docx import Converter as PDFToDocxConverter
import subprocess
import time
import platform
from docx2pdf import convert

app = Flask(__name__)

# Configuración
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Asegurar que las carpetas existan
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Verificar extensión permitida
def allowed_file(filename, file_type):
    allowed_extensions = {
        'pdf': ['pdf'],
        'docx': ['docx', 'doc']
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions[file_type]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    # Verificar si hay archivo en la solicitud
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró ningún archivo'}), 400
    
    file = request.files['file']
    conversion_type = request.form.get('conversion_type', 'pdf_to_docx')
    
    # Verificar si se seleccionó un archivo
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    # Determinar tipo de conversión y verificar extensión
    if conversion_type == 'pdf_to_docx':
        if not allowed_file(file.filename, 'pdf'):
            return jsonify({'error': 'Solo se permiten archivos PDF para esta conversión'}), 400
        return convert_pdf_to_docx(file)
    elif conversion_type == 'docx_to_pdf':
        if not allowed_file(file.filename, 'docx'):
            return jsonify({'error': 'Solo se permiten archivos Word (.docx, .doc) para esta conversión'}), 400
        return convert_docx_to_pdf(file)
    else:
        return jsonify({'error': 'Tipo de conversión no válido'}), 400

def convert_pdf_to_docx(file):
    try:
        # Generar nombres de archivo únicos
        unique_id = str(uuid.uuid4())
        secure_name = secure_filename(file.filename)
        base_name = os.path.splitext(secure_name)[0]
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{secure_name}")
        docx_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"{unique_id}_{base_name}.docx")
        
        # Guardar el archivo PDF
        file.save(pdf_path)
        
        # Convertir PDF a DOCX
        cv = PDFToDocxConverter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        # Eliminar el archivo PDF subido para ahorrar espacio
        os.remove(pdf_path)
        
        # Devolver el nombre del archivo para descarga
        download_filename = f"{base_name}.docx"
        return jsonify({
            'success': True, 
            'message': 'Conversión exitosa', 
            'filename': os.path.basename(docx_path),
            'download_name': download_filename
        })
        
    except Exception as e:
        # En caso de error durante la conversión
        return jsonify({'error': f'Error en la conversión: {str(e)}'}), 500

def convert_docx_to_pdf(file):
    try:
        # Generar nombres de archivo únicos
        unique_id = str(uuid.uuid4())
        secure_name = secure_filename(file.filename)
        base_name = os.path.splitext(secure_name)[0]

        docx_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{secure_name}")
        pdf_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"{unique_id}_{base_name}.pdf")

        # Guardar el archivo DOCX
        file.save(docx_path)
        
        # Diagnóstico del entorno
        env_info = {}
        env_info["sistema"] = platform.system()
        env_info["path"] = os.environ.get("PATH", "No disponible")
        
        # Intentar encontrar LibreOffice
        try:
            which_result = subprocess.run(["which", "libreoffice"], capture_output=True, text=True, check=False)
            env_info["which_libreoffice"] = which_result.stdout if which_result.returncode == 0 else "No encontrado"
            
            which_soffice = subprocess.run(["which", "soffice"], capture_output=True, text=True, check=False)
            env_info["which_soffice"] = which_soffice.stdout if which_soffice.returncode == 0 else "No encontrado"
            
            find_result = subprocess.run(["find", "/usr", "-name", "soffice", "-o", "-name", "libreoffice"], 
                                        capture_output=True, text=True, check=False)
            env_info["find_result"] = find_result.stdout if find_result.returncode == 0 else "Error en búsqueda"
        except Exception as e:
            env_info["error_diagnostico"] = str(e)
        
        # Intentar usar unoconv (alternativa a LibreOffice)
        try:
            # Verificar si unoconv está instalado
            unoconv_check = subprocess.run(["which", "unoconv"], capture_output=True, text=True, check=False)
            if unoconv_check.returncode != 0:
                # Intentar instalar unoconv si no está disponible
                subprocess.run(["apt-get", "update"], check=False)
                subprocess.run(["apt-get", "install", "-y", "unoconv"], check=False)
            
            # Usar unoconv para la conversión
            subprocess.run(["unoconv", "-f", "pdf", "-o", pdf_path, docx_path], check=True)
            
            # Eliminar el archivo docx subido
            os.remove(docx_path)
            
            download_filename = f"{base_name}.pdf"
            return jsonify({
                'success': True,
                'message': 'Conversión exitosa con unoconv',
                'filename': os.path.basename(pdf_path),
                'download_name': download_filename,
                'env_info': env_info
            })
        except Exception as unoconv_error:
            env_info["error_unoconv"] = str(unoconv_error)
            
            # Si unoconv falla, intentar con pandoc como última opción
            try:
                # Verificar/instalar pandoc
                pandoc_check = subprocess.run(["which", "pandoc"], capture_output=True, text=True, check=False)
                if pandoc_check.returncode != 0:
                    subprocess.run(["apt-get", "install", "-y", "pandoc"], check=False)
                
                # Usar pandoc para la conversión
                subprocess.run([
                    "pandoc", docx_path, "-o", pdf_path
                ], check=True)
                
                # Eliminar el archivo docx subido
                os.remove(docx_path)
                
                download_filename = f"{base_name}.pdf"
                return jsonify({
                    'success': True,
                    'message': 'Conversión exitosa con pandoc',
                    'filename': os.path.basename(pdf_path),
                    'download_name': download_filename,
                    'env_info': env_info
                })
            except Exception as pandoc_error:
                env_info["error_pandoc"] = str(pandoc_error)
                raise Exception(f"Falló la conversión: {str(pandoc_error)}. Información del entorno: {env_info}")
    
    except Exception as e:
        return jsonify({'error': f'Error en la conversión: {str(e)}'}), 500


@app.route('/download/<filename>')
def download_file(filename):
    # Configurar el nombre de descarga para el usuario (eliminando el UUID)
    original_filename = "_".join(filename.split("_")[1:])
    
    return send_from_directory(
        app.config['DOWNLOAD_FOLDER'], 
        filename, 
        as_attachment=True,
        download_name=original_filename
    )

@app.route('/cleanup', methods=['POST'])
def cleanup_file():
    filename = request.json.get('filename')
    if filename:
        try:
            file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Nombre de archivo no proporcionado'}), 400

# Tarea de limpieza periódica (opcional)
def cleanup_old_files():
    """Eliminar archivos antiguos (más de 1 hora)"""
    current_time = time.time()
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            # Si el archivo tiene más de 1 hora
            if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > 3600:
                os.remove(file_path)

if __name__ == '__main__':
    # Limpiar archivos antiguos al iniciar
    cleanup_old_files()
    app.run(debug=True)
    

# Al final del archivo app.py, modifica:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)