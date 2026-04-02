from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import User, Skill, DesiredSkill, SkillMatch
from extensions import db

matching_bp = Blueprint('matching', __name__)

LEVEL_SCORE = {
    'beginner':     1,
    'intermediate': 2,
    'expert':       3,
}

def normalize(text):
    return text.strip().lower()

def level_compatibility(have_level, want_level):
    """
    Returns 0.5–1.0 based on how well skill level matches what's wanted.
    Expert offering to someone wanting beginner = 1.0 (overqualified is fine).
    Beginner offering to someone wanting expert = 0.3 (underqualified).
    """
    have = LEVEL_SCORE.get(have_level, 2)
    want = LEVEL_SCORE.get(want_level, 2)
    if have >= want:
        return 1.0
    elif have == want - 1:
        return 0.6
    else:
        return 0.3

def compute_match_score(user_a, user_b):
    """
    Bidirectional match score between user_a and user_b.
    Score = average of:
      - How well A's skills satisfy B's desires
      - How well B's skills satisfy A's desires
    Returns float 0–100.
    """
    a_skills    = {normalize(s.title): s for s in user_a.skills}
    b_skills    = {normalize(s.title): s for s in user_b.skills}
    a_desires   = [normalize(d.title) for d in user_a.desired_skills]
    b_desires   = {normalize(d.title): d for d in user_b.desired_skills}

    # Also parse the free-text `wants` field on Skill as fallback
    a_wants_text = set()
    for s in user_a.skills:
        if s.wants:
            for w in s.wants.split(','):
                a_wants_text.add(normalize(w))

    b_wants_text = set()
    for s in user_b.skills:
        if s.wants:
            for w in s.wants.split(','):
                b_wants_text.add(normalize(w))

    # A → B: does A have what B wants?
    b_all_desires = set(b_desires.keys()) | b_wants_text
    ab_score = 0.0
    ab_matches = 0
    for desire_title in b_all_desires:
        if desire_title in a_skills:
            skill = a_skills[desire_title]
            desired = b_desires.get(desire_title)
            level_want = desired.level_wanted if desired else 'intermediate'
            ab_score += level_compatibility(skill.level or 'intermediate', level_want)
            ab_matches += 1

    # B → A: does B have what A wants?
    a_all_desires = set(a_desires) | a_wants_text
    ba_score = 0.0
    ba_matches = 0
    for desire_title in a_all_desires:
        if desire_title in b_skills:
            skill = b_skills[desire_title]
            ba_score += level_compatibility(skill.level or 'intermediate', 'intermediate')
            ba_matches += 1

    # Normalize each direction to 0–1
    ab_norm = (ab_score / len(b_all_desires)) if b_all_desires else 0
    ba_norm = (ba_score / len(a_all_desires)) if a_all_desires else 0

    # Weighted average — both directions matter equally
    if ab_norm == 0 and ba_norm == 0:
        return 0.0

    final = ((ab_norm + ba_norm) / 2) * 100
    return round(min(final, 100), 1)

def get_matches_for_user(user, min_score=10.0):
    """
    Returns list of dicts sorted by score descending.
    Skips users with no skills or desires.
    Caches result in SkillMatch table.
    """
    all_users = User.query.filter(
        User.id != user.id,
        User.is_verified == True
    ).all()

    results = []
    for other in all_users:
        if not other.skills:
            continue
        score = compute_match_score(user, other)
        if score < min_score:
            continue

        # Upsert into SkillMatch cache
        existing = SkillMatch.query.filter_by(
            user_a_id=min(user.id, other.id),
            user_b_id=max(user.id, other.id)
        ).first()
        if existing:
            existing.score = score
        else:
            db.session.add(SkillMatch(
                user_a_id=min(user.id, other.id),
                user_b_id=max(user.id, other.id),
                score=score
            ))

        # Find which skills matched
        my_skill_titles  = {s.title.lower() for s in user.skills}
        their_want_titles = set()
        for s in other.skills:
            if s.wants:
                for w in s.wants.split(','):
                    their_want_titles.add(w.strip().lower())
        for d in other.desired_skills:
            their_want_titles.add(d.title.lower())

        matched_skills = [s for s in user.skills if s.title.lower() in their_want_titles]

        results.append({
            'user':           other,
            'score':          score,
            'matched_skills': matched_skills,
            'their_skills':   other.skills,
            'their_desires':  other.desired_skills,
        })

    db.session.commit()
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

@matching_bp.route('/matches')
@login_required
def matches():
    results = get_matches_for_user(current_user)
    return render_template('matching/matches.html', matches=results)

@matching_bp.route('/matches/api')
@login_required
def matches_api():
    results = get_matches_for_user(current_user)
    return jsonify([{
        'user_id':   m['user'].id,
        'name':      m['user'].name,
        'score':     m['score'],
        'matched':   [s.title for s in m['matched_skills']],
    } for m in results])
from flask import request, redirect, url_for, flash

@matching_bp.route('/desired/add', methods=['POST'])
@login_required
def add_desired():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Skill title is required.', 'danger')
        return redirect(request.referrer or url_for('skills.browse'))
    desired = DesiredSkill(
        user_id=current_user.id,
        title=title,
        category=request.form.get('category'),
        level_wanted=request.form.get('level_wanted', 'intermediate')
    )
    db.session.add(desired)
    db.session.commit()
    flash('Desired skill added!', 'success')
    return redirect(request.referrer or url_for('matching.matches'))