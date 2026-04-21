import os
from functools import wraps
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, current_app, abort)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
from models import (db, User, Candidate, CandidateCVItem, CandidatePromise,
                    ProgramSection, SiteSettings, Priority, FAQItem,
                    ContactMessage)

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login'))
        if not current_user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


# --- auth ------------------------------------------------------------------

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('admin.dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.home'))


# --- dashboard -------------------------------------------------------------

@admin_bp.route('/')
@admin_required
def dashboard():
    counts = {
        'candidates': Candidate.query.count(),
        'published': Candidate.query.filter_by(is_published=True).count(),
        'program_sections': ProgramSection.query.count(),
        'priorities': Priority.query.count(),
        'faq': FAQItem.query.count(),
        'messages': ContactMessage.query.count(),
        'unread_messages': ContactMessage.query.filter_by(is_read=False).count(),
    }
    latest_messages = (ContactMessage.query
                       .order_by(ContactMessage.created_at.desc())
                       .limit(5)
                       .all())
    return render_template('admin/dashboard.html', counts=counts,
                           latest_messages=latest_messages)


# --- candidates ------------------------------------------------------------

@admin_bp.route('/candidates')
@admin_required
def candidates_list():
    candidates = Candidate.query.order_by(Candidate.position.asc()).all()
    return render_template('admin/candidates_list.html', candidates=candidates)


@admin_bp.route('/candidates/new', methods=['GET', 'POST'])
@admin_required
def candidate_new():
    if request.method == 'POST':
        c = Candidate(name_ar='(مرشح جديد)', position=(Candidate.query.count() + 1))
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('admin.candidate_edit', candidate_id=c.id))
    return render_template('admin/candidate_edit.html', c=None)


@admin_bp.route('/candidates/<int:candidate_id>/edit', methods=['GET', 'POST'])
@admin_required
def candidate_edit(candidate_id):
    c = Candidate.query.get_or_404(candidate_id)
    if request.method == 'POST':
        c.position = int(request.form.get('position') or 0)
        c.title_ar = request.form.get('title_ar', '').strip()
        c.name_ar = request.form.get('name_ar', '').strip()
        c.name_en = request.form.get('name_en', '').strip()
        c.full_legal_name_ar = request.form.get('full_legal_name_ar', '').strip() or None
        c.tagline_ar = request.form.get('tagline_ar', '').strip()
        c.bio_ar = request.form.get('bio_ar', '').strip() or None
        c.bio_en = request.form.get('bio_en', '').strip() or None
        c.why_running_ar = request.form.get('why_running_ar', '').strip() or None
        c.why_running_en = request.form.get('why_running_en', '').strip() or None
        c.is_head_of_list = bool(request.form.get('is_head_of_list'))
        c.is_published = bool(request.form.get('is_published'))
        photo = request.files.get('photo')
        if photo and photo.filename:
            saved = _save_photo(photo, slug_hint=f'c{c.id}')
            if saved:
                c.photo_filename = saved
        db.session.commit()
        flash('تم الحفظ', 'success')
        return redirect(url_for('admin.candidate_edit', candidate_id=c.id))
    return render_template('admin/candidate_edit.html', c=c,
                           cv_items=c.cv_items.all(),
                           promises=c.promises.all())


@admin_bp.route('/candidates/<int:candidate_id>/delete', methods=['POST'])
@admin_required
def candidate_delete(candidate_id):
    c = Candidate.query.get_or_404(candidate_id)
    db.session.delete(c)
    db.session.commit()
    flash('تم حذف المرشح', 'info')
    return redirect(url_for('admin.candidates_list'))


# --- CV items (inline on candidate edit page) ------------------------------

@admin_bp.route('/candidates/<int:candidate_id>/cv/add', methods=['POST'])
@admin_required
def cv_add(candidate_id):
    c = Candidate.query.get_or_404(candidate_id)
    item = CandidateCVItem(
        candidate_id=c.id,
        category=request.form.get('category', 'experience'),
        text_ar=request.form.get('text_ar', '').strip(),
        sort_order=c.cv_items.count(),
    )
    if item.text_ar:
        db.session.add(item)
        db.session.commit()
    return redirect(url_for('admin.candidate_edit', candidate_id=c.id) + '#cv')


@admin_bp.route('/cv/<int:item_id>/delete', methods=['POST'])
@admin_required
def cv_delete(item_id):
    item = CandidateCVItem.query.get_or_404(item_id)
    cid = item.candidate_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin.candidate_edit', candidate_id=cid) + '#cv')


# --- program --------------------------------------------------------------

@admin_bp.route('/program')
@admin_required
def program_list():
    sections = ProgramSection.query.order_by(ProgramSection.sort_order.asc()).all()
    return render_template('admin/program_list.html', sections=sections)


@admin_bp.route('/program/<int:section_id>/edit', methods=['GET', 'POST'])
@admin_required
def program_edit(section_id):
    s = ProgramSection.query.get_or_404(section_id)
    if request.method == 'POST':
        s.icon = request.form.get('icon', '').strip()
        s.title_ar = request.form.get('title_ar', '').strip()
        s.summary_ar = request.form.get('summary_ar', '').strip()
        s.body_ar = request.form.get('body_ar', '').strip() or None
        s.sort_order = int(request.form.get('sort_order') or 0)
        s.is_published = bool(request.form.get('is_published'))
        db.session.commit()
        flash('تم الحفظ', 'success')
        return redirect(url_for('admin.program_list'))
    return render_template('admin/program_edit.html', s=s)


# --- site settings --------------------------------------------------------

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    s = SiteSettings.query.first() or SiteSettings()
    if request.method == 'POST':
        s.list_number = request.form.get('list_number', '').strip() or '5'
        s.election_year = int(request.form.get('election_year') or s.election_year or 2026)
        ed = request.form.get('election_date', '').strip()
        s.election_date = datetime.strptime(ed, '%Y-%m-%d').date() if ed else None
        s.polling_location_ar = request.form.get('polling_location_ar', '').strip()
        s.hero_headline_ar = request.form.get('hero_headline_ar', '').strip() or s.hero_headline_ar
        s.hero_subheadline_ar = request.form.get('hero_subheadline_ar', '').strip() or s.hero_subheadline_ar
        s.hero_intro_ar = request.form.get('hero_intro_ar', '').strip()
        s.slogan_ar = request.form.get('slogan_ar', '').strip()
        s.slogan_en = request.form.get('slogan_en', '').strip()
        for i in (1, 2, 3, 4):
            setattr(s, f'stat_{i}_value', request.form.get(f'stat_{i}_value', '').strip() or getattr(s, f'stat_{i}_value'))
            setattr(s, f'stat_{i}_label', request.form.get(f'stat_{i}_label', '').strip() or getattr(s, f'stat_{i}_label'))
        s.contact_phone = request.form.get('contact_phone', '').strip()
        s.contact_email = request.form.get('contact_email', '').strip()
        s.contact_address_ar = request.form.get('contact_address_ar', '').strip()
        s.facebook_url = request.form.get('facebook_url', '').strip()
        s.tiktok_url = request.form.get('tiktok_url', '').strip()
        s.instagram_url = request.form.get('instagram_url', '').strip()
        s.whatsapp_url = request.form.get('whatsapp_url', '').strip()
        if not s.id:
            db.session.add(s)
        db.session.commit()
        flash('تم حفظ إعدادات الموقع', 'success')
        return redirect(url_for('admin.settings'))
    return render_template('admin/settings.html', s=s)


# --- priorities -----------------------------------------------------------

@admin_bp.route('/priorities')
@admin_required
def priorities_list():
    items = Priority.query.order_by(Priority.sort_order.asc()).all()
    return render_template('admin/priorities_list.html', items=items)


@admin_bp.route('/priorities/new', methods=['POST'])
@admin_required
def priority_new():
    p = Priority(sort_order=Priority.query.count(),
                 title_ar=request.form.get('title_ar', '(أولوية جديدة)'))
    db.session.add(p)
    db.session.commit()
    return redirect(url_for('admin.priority_edit', item_id=p.id))


@admin_bp.route('/priorities/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def priority_edit(item_id):
    p = Priority.query.get_or_404(item_id)
    if request.method == 'POST':
        p.sort_order = int(request.form.get('sort_order') or 0)
        p.icon = request.form.get('icon', '').strip()
        p.title_ar = request.form.get('title_ar', '').strip()
        p.body_ar = request.form.get('body_ar', '').strip() or None
        p.is_published = bool(request.form.get('is_published'))
        db.session.commit()
        flash('تم الحفظ', 'success')
        return redirect(url_for('admin.priorities_list'))
    return render_template('admin/priority_edit.html', p=p)


@admin_bp.route('/priorities/<int:item_id>/delete', methods=['POST'])
@admin_required
def priority_delete(item_id):
    p = Priority.query.get_or_404(item_id)
    db.session.delete(p)
    db.session.commit()
    flash('تم الحذف', 'info')
    return redirect(url_for('admin.priorities_list'))


# --- FAQ ------------------------------------------------------------------

@admin_bp.route('/faq')
@admin_required
def faq_list():
    items = FAQItem.query.order_by(FAQItem.sort_order.asc()).all()
    return render_template('admin/faq_list.html', items=items)


@admin_bp.route('/faq/new', methods=['POST'])
@admin_required
def faq_new():
    q = FAQItem(sort_order=FAQItem.query.count(),
                question_ar=request.form.get('question_ar', '(سؤال جديد)'),
                answer_ar=request.form.get('answer_ar', '—'))
    db.session.add(q)
    db.session.commit()
    return redirect(url_for('admin.faq_edit', item_id=q.id))


@admin_bp.route('/faq/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def faq_edit(item_id):
    q = FAQItem.query.get_or_404(item_id)
    if request.method == 'POST':
        q.sort_order = int(request.form.get('sort_order') or 0)
        q.question_ar = request.form.get('question_ar', '').strip()
        q.answer_ar = request.form.get('answer_ar', '').strip()
        q.is_published = bool(request.form.get('is_published'))
        db.session.commit()
        flash('تم الحفظ', 'success')
        return redirect(url_for('admin.faq_list'))
    return render_template('admin/faq_edit.html', q=q)


@admin_bp.route('/faq/<int:item_id>/delete', methods=['POST'])
@admin_required
def faq_delete(item_id):
    q = FAQItem.query.get_or_404(item_id)
    db.session.delete(q)
    db.session.commit()
    flash('تم الحذف', 'info')
    return redirect(url_for('admin.faq_list'))


# --- Messages -------------------------------------------------------------

@admin_bp.route('/messages')
@admin_required
def messages_list():
    items = (ContactMessage.query
             .order_by(ContactMessage.created_at.desc())
             .all())
    return render_template('admin/messages_list.html', items=items)


@admin_bp.route('/messages/<int:item_id>/toggle-read', methods=['POST'])
@admin_required
def message_toggle_read(item_id):
    m = ContactMessage.query.get_or_404(item_id)
    m.is_read = not m.is_read
    db.session.commit()
    return redirect(url_for('admin.messages_list'))


@admin_bp.route('/messages/<int:item_id>/delete', methods=['POST'])
@admin_required
def message_delete(item_id):
    m = ContactMessage.query.get_or_404(item_id)
    db.session.delete(m)
    db.session.commit()
    flash('تم الحذف', 'info')
    return redirect(url_for('admin.messages_list'))


# --- helpers --------------------------------------------------------------

ALLOWED_PHOTO_EXT = {'.jpg', '.jpeg', '.png', '.webp'}


def _save_photo(fs, slug_hint='photo'):
    filename = secure_filename(fs.filename or '')
    if not filename:
        return None
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_PHOTO_EXT:
        flash('امتداد الصورة غير مدعوم', 'warning')
        return None
    out_name = f'{slug_hint}.jpg'
    out_path = os.path.join(current_app.config['UPLOAD_DIR'], out_name)
    with Image.open(fs.stream) as im:
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGB')
        w, h = im.size
        if w > 900:
            im = im.resize((900, int(h * 900 / w)), Image.LANCZOS)
        im.save(out_path, 'JPEG', quality=85, optimize=True)
    return out_name
