from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from pathlib import Path
from . import db
from .models import Request, RequestCategory, RequestFile, RequestComment
from .security import role_required

student_bp = Blueprint('student', __name__)

@student_bp.route('/')
@login_required
@role_required('student')
def dashboard():
    requests = Request.query.filter_by(student_id=current_user.id).order_by(Request.created_at.desc()).all()
    return render_template('student/dashboard.html', requests=requests)

@student_bp.route('/requests/create', methods=['GET','POST'])
@login_required
@role_required('student')
def create_request():
    categories = RequestCategory.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        req = Request(
            student_id=current_user.id,
            category_id=int(request.form.get('category_id')),
            title=request.form.get('title'),
            description=request.form.get('description'),
            priority=request.form.get('priority','normal')
        )
        db.session.add(req)
        db.session.flush()
        file = request.files.get('file')
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / f'request_{req.id}_{filename}'
            file.save(file_path)
            db.session.add(RequestFile(request_id=req.id, file_name=filename, file_path=str(file_path)))
        db.session.commit()
        flash('Заявка создана')
        return redirect(url_for('student.dashboard'))
    return render_template('student/create_request.html', categories=categories)

@student_bp.route('/requests/<int:request_id>')
@login_required
@role_required('student')
def request_detail(request_id):
    req = Request.query.get_or_404(request_id)
    comments = RequestComment.query.filter_by(request_id=request_id).order_by(RequestComment.created_at.asc()).all()
    return render_template('student/request_detail.html', req=req, comments=comments)
