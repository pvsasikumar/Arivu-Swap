import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Skill, Review
from PIL import Image

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/<int:user_id>')
def view(user_id):
    user = User.query.get_or_404(user_id)
    skills = Skill.query.filter_by(user_id=user_id).all()
    reviews = Review.query.filter_by(reviewee_id=user_id).order_by(Review.created_at.desc()).all()
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return render_template('profile/view.html', user=user, skills=skills, reviews=reviews, avg_rating=avg_rating)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        # ── Avatar upload ──────────────────────────────────────────
        file = request.files.get('avatar')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext not in {'png', 'jpg', 'jpeg', 'webp'}:
                flash('Invalid file type. Use PNG, JPG or WEBP.', 'danger')
                return redirect(url_for('profile.edit'))

            filename = f"user_{current_user.id}.{ext}"
            folder = os.path.join(current_app.root_path, 'static', 'avatars')
            os.makedirs(folder, exist_ok=True)

            img = Image.open(file)
            img = img.convert('RGB')
            img.thumbnail((256, 256))
            img.save(os.path.join(folder, filename))

            current_user.avatar = filename   # ← this was missing before

        # ── Other fields ───────────────────────────────────────────
        current_user.name = request.form.get('name', current_user.name).strip()
        current_user.bio  = request.form.get('bio',  current_user.bio or '').strip()

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile.view', user_id=current_user.id))

    return render_template('profile/edit.html')