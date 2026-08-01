from flask import Blueprint, request, jsonify
from app.services.requirement_service import save_requirement

requirement_bp = Blueprint('requirement', __name__)
@requirement_bp.route('/api/requirements/text', methods=['POST'])
def create_from_text():
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': 'Không có dữ liệu gửi lên'
        }), 400
    content = data.get('content', '')

    if not content.strip():
        return jsonify({
            'success': False,
            'message': 'Nội dung không được để trống'
        }), 400

    if len(content.strip()) < 50:
        return jsonify({
            'success': False,
            'message': 'Nội dung quá ngắn, cần ít nhất 50 ký tự!'
        }), 400

    title = data.get('title', 'Requirement nhập tay')
    req_id, create_at = save_requirement(
        filename = title,
        file_type='text',
        content = content
    )

    return jsonify({
        'success': True,
        'message': 'Lưu requirement thành công',
        'id': req_id,
        'title': title,
        'file_type': 'text',
        'text_length': len(content),
        'create_at': str(create_at)
    }), 201
