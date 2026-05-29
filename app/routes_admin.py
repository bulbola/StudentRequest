from flask import Blueprint, render_template, Response
from flask_login import login_required
from openpyxl import Workbook
from io import BytesIO
from .models import User, Request, RequestCategory
from .security import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    stats = {
        'users': User.query.count(),
        'requests': Request.query.count(),
        'created': Request.query.filter_by(status='created').count(),
        'closed': Request.query.filter_by(status='closed').count(),
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    return render_template('admin/users.html', users=User.query.order_by(User.full_name).all())

@admin_bp.route('/categories')
@login_required
@role_required('admin')
def categories():
    return render_template('admin/categories.html', categories=RequestCategory.query.order_by(RequestCategory.name).all())

@admin_bp.route('/reports/requests.xlsx')
@login_required
@role_required('admin')
def export_requests():
    wb = Workbook()
    ws = wb.active
    ws.title = 'Заявки'
    ws.append(['ID', 'Тема', 'Категория', 'Статус', 'Приоритет', 'Дата создания'])
    for req in Request.query.order_by(Request.created_at.desc()).all():
        ws.append([req.id, req.title, req.category.name, req.status, req.priority, req.created_at.strftime('%d.%m.%Y %H:%M')])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return Response(bio.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition':'attachment; filename=requests.xlsx'})
