from flask import Blueprint, request, jsonify
from app.services.file_service import allowed_file, save_uploaded_file, extract_text
from app.services.requirement_service import save_requirement
from app.database import test_connection

upload_bp = Blueprint('upload',__name__)
@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Không tìm thấy trong file request'}), 400
    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'message': "Chưa chọn file!"}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Chỉ chấp nhận file PDF, DOCX, TXT, CSV'}), 400

    filename, file_path = save_uploaded_file(file)
    extracted_text = extract_text(file_path)

    if not extracted_text.strip():
        return jsonify({'success': False, 'message': 'Không đọc được nội dung file'}), 400

    file_type = filename.rsplit('.', 1)[1].lower()
    req_id, create_at = save_requirement(filename, file_type, extracted_text)

    return jsonify({
        'success': True,
        'message': 'Upload thành công',
        'id': req_id,
        'filename': filename,
        'file_path': file_path,
        'file_type': file_type,
        'text_length': len(extracted_text),
        'create_at': str(create_at),
        'preview': extracted_text[:500]
    }), 200

@upload_bp.route('/api/test-db', methods=['GET'])
def test_db():
    success, message = test_connection()
    return jsonify({
        'success': success,
        'message': message
    })