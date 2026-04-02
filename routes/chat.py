import os
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_socketio import emit, join_room
from extensions import db, socketio
from models import Message, User
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

chat_bp = Blueprint('chat', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'py',
                      'js', 'html', 'css', 'zip', 'docx', 'md'}
MAX_FILE_SIZE_MB = 10

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image(filename):
    return filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# ─── INBOX ───────────────────────────────────────────────────────────────────

@chat_bp.route('/inbox')
@login_required
def inbox():
    sent = Message.query.filter_by(
        sender_id=current_user.id, is_deleted=False
    ).with_entities(Message.receiver_id).distinct()
    received = Message.query.filter_by(
        receiver_id=current_user.id, is_deleted=False
    ).with_entities(Message.sender_id).distinct()
    partner_ids = set([r.receiver_id for r in sent] + [r.sender_id for r in received])

    inbox = []
    for pid in partner_ids:
        other = User.query.get(pid)
        if not other:
            continue
        last_msg = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == pid)) |
            ((Message.sender_id == pid) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()

        unread_count = Message.query.filter_by(
            sender_id=pid,
            receiver_id=current_user.id,
            is_read=False,
            is_deleted=False
        ).count()

        inbox.append({
            'other_user':   other,
            'last_message': last_msg.content if last_msg else 'No messages yet',
            'last_type':    last_msg.msg_type if last_msg else 'text',
            'timestamp':    last_msg.created_at if last_msg else None,
            'unread_count': unread_count,
        })

    inbox.sort(key=lambda x: x['timestamp'] or datetime.min, reverse=True)
    return render_template('chat/inbox.html', inbox=inbox)


# ─── CONVERSATION ─────────────────────────────────────────────────────────────

@chat_bp.route('/conversation/<int:user_id>')
@login_required
def conversation(user_id):
    other = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).filter_by(is_deleted=False).order_by(Message.created_at).all()

    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()

    return render_template('chat/conversation.html', other=other, messages=messages)


# ─── FILE UPLOAD ──────────────────────────────────────────────────────────────

@chat_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    receiver_id = request.form.get('receiver_id', type=int)

    if not file or not file.filename:
        return jsonify({'error': 'Empty file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return jsonify({'error': f'File too large (max {MAX_FILE_SIZE_MB}MB)'}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)
    file.save(file_path)

    file_url = f'/static/uploads/chat/{unique_name}'
    msg_type = 'image' if is_image(filename) else 'file'

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=filename,
        msg_type=msg_type,
        file_url=file_url,
        file_name=filename,
        file_size=size,
    )
    db.session.add(msg)
    db.session.commit()

    room = f"chat_{min(current_user.id, receiver_id)}_{max(current_user.id, receiver_id)}"
    socketio.emit('receive_message', {
        'msg_id':     msg.id,
        'content':    filename,
        'msg_type':   msg_type,
        'file_url':   file_url,
        'file_name':  filename,
        'file_size':  size,
        'sender_id':  current_user.id,
        'timestamp':  msg.created_at.strftime('%H:%M'),
    }, room=room)

    return jsonify({'success': True, 'file_url': file_url, 'msg_id': msg.id})


# ─── DELETE MESSAGE ───────────────────────────────────────────────────────────

@chat_bp.route('/message/<int:msg_id>/delete', methods=['POST'])
@login_required
def delete_message(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.sender_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    msg.is_deleted = True
    db.session.commit()
    return jsonify({'success': True})


# ─── SOCKET EVENTS ────────────────────────────────────────────────────────────

@socketio.on('join')
def on_join(data):
    room = f"chat_{min(data['user_id'], data['other_id'])}_{max(data['user_id'], data['other_id'])}"
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    content   = data.get('content', '').strip()
    msg_type  = data.get('msg_type', 'text')   # text or code
    code_lang = data.get('code_lang', '')

    if not content:
        return

    msg = Message(
        sender_id=data['sender_id'],
        receiver_id=data['receiver_id'],
        content=content,
        msg_type=msg_type,
        code_lang=code_lang if msg_type == 'code' else None,
    )
    db.session.add(msg)
    db.session.commit()

    room = f"chat_{min(data['sender_id'], data['receiver_id'])}_{max(data['sender_id'], data['receiver_id'])}"
    emit('receive_message', {
        'msg_id':    msg.id,
        'content':   content,
        'msg_type':  msg_type,
        'code_lang': code_lang,
        'sender_id': data['sender_id'],
        'timestamp': msg.created_at.strftime('%H:%M'),
    }, room=room)

@socketio.on('typing')
def handle_typing(data):
    room = f"chat_{min(data['user_id'], data['other_id'])}_{max(data['user_id'], data['other_id'])}"
    emit('user_typing', {'user_id': data['user_id']}, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = f"chat_{min(data['user_id'], data['other_id'])}_{max(data['user_id'], data['other_id'])}"
    emit('user_stop_typing', {'user_id': data['user_id']}, room=room, include_self=False)