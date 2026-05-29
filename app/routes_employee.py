from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db
from .models import Request, RequestComment, StatusHistory
from .security import role_required

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/')
@login_required
@role_required('employee')
def dashboard():
    status = request.args.get('status')
    query = Request.query.order_by(Request.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    requests = query.all()
    return render_template('employee/dashboard.html', requests=requests)

@employee_bp.route('/requests/<int:request_id>', methods=['GET','POST'])
@login_required
@role_required('employee')
def process_request(request_id):
    req = Request.query.get_or_404(request_id)
    if request.method == 'POST':
        old_status = req.status
        new_status = request.form.get('status')
        comment_text = request.form.get('comment_text')
        if new_status and new_status != old_status:
            req.status = new_status
            db.session.add(StatusHistory(request_id=req.id, old_status=old_status, new_status=new_status, changed_by=current_user.id))
        if comment_text:
            db.session.add(RequestComment(request_id=req.id, user_id=current_user.id, comment_text=comment_text))
        db.session.commit()
        flash('Заявка обновлена')
        return redirect(url_for('employee.dashboard'))
    comments = RequestComment.query.filter_by(request_id=request_id).order_by(RequestComment.created_at.asc()).all()
    return render_template('employee/process_request.html', req=req, comments=comments)
