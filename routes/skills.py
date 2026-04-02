from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Skill

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/browse')
def browse():
    q = request.args.get('q', '')
    cat = request.args.get('category', '')
    
    skills = Skill.query

    if current_user.is_authenticated:
        skills = skills.filter(Skill.user_id != current_user.id)
    
    if q:
        skills = skills.filter(Skill.title.ilike(f'%{q}%'))
    
    if cat:
        skills = skills.filter_by(category=cat)
    
    skills = skills.order_by(Skill.created_at.desc()).all()  # .all() only once, at the end
    
    return render_template('skills/browse.html', skills=skills, q=q, cat=cat)

@skills_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        skill = Skill(
            user_id=current_user.id,
            title=request.form['title'],
            description=request.form['description'],
            category=request.form['category'],
            level=request.form['level'],
            wants=request.form['wants']
        )
        db.session.add(skill)
        db.session.commit()
        flash('Skill added!', 'success')
        return redirect(url_for('dashboard.index'))
    return render_template('skills/add.html')

@skills_bp.route('/<int:skill_id>')
def detail(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    return render_template('skills/detail.html', skill=skill)

@skills_bp.route('/delete/<int:skill_id>', methods=['POST'])
@login_required
def delete(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard.index'))
    db.session.delete(skill)
    db.session.commit()
    flash('Skill deleted.', 'success')
    return redirect(url_for('dashboard.index'))
