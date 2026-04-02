from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Review, User, Notification

review_bp = Blueprint('review', __name__)

@review_bp.route('/leave/<int:user_id>', methods=['GET', 'POST'])
@login_required
def leave_review(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        review = Review(
            reviewer_id=current_user.id,
            reviewee_id=user_id,
            rating=int(request.form['rating']),
            comment=request.form['comment']
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('profile.view', user_id=user_id))
    return render_template('review/leave.html', user=user)
