import re
from datetime import date
from flask import (Blueprint, render_template, abort, request, redirect,
                   url_for, flash, make_response)
from models import (db, Candidate, ProgramSection, Priority, FAQItem,
                    Endorsement, ContactMessage, SiteSettings)

public_bp = Blueprint('public', __name__)


@public_bp.route('/home')
def home():
    head = (Candidate.query
            .filter_by(is_head_of_list=True, is_published=True)
            .first())
    candidates = (Candidate.query
                  .filter_by(is_published=True)
                  .order_by(Candidate.position.asc())
                  .all())
    priorities = (Priority.query
                  .filter_by(is_published=True)
                  .order_by(Priority.sort_order.asc())
                  .all())
    program = (ProgramSection.query
               .filter_by(is_published=True)
               .order_by(ProgramSection.sort_order.asc())
               .limit(8)
               .all())
    endorsements = (Endorsement.query
                    .filter_by(is_published=True)
                    .order_by(Endorsement.sort_order.asc())
                    .limit(3)
                    .all())
    stats = _build_stats(SiteSettings.query.first())
    return render_template('home.html',
                           head=head, candidates=candidates,
                           priorities=priorities, program=program,
                           endorsements=endorsements, stats=stats)


_STAT_NUM_RE = re.compile(r'^([^\d.-]*)(\d+(?:\.\d+)?)([^\d]*)$')


def _build_stats(site):
    """Return a list of dicts (prefix, number, suffix, label, animate)
    so the template doesn't need to parse values."""
    defaults = [
        ('13', 'مرشحاً ومرشحة'),
        ('+90', 'سنة خبرة مجتمعة'),
        ('8', 'تخصصات مهنية متنوعة'),
        ('100%', 'التزام بخدمة بيت ساحور'),
    ]
    out = []
    for i, (dv, dl) in enumerate(defaults, start=1):
        v = (getattr(site, f'stat_{i}_value', None) if site else None) or dv
        l = (getattr(site, f'stat_{i}_label', None) if site else None) or dl
        m = _STAT_NUM_RE.match(str(v).strip())
        if m:
            prefix, num, suffix = m.group(1), m.group(2), m.group(3)
            out.append({'prefix': prefix, 'number': num, 'suffix': suffix,
                        'raw': v, 'label': l, 'animate': True})
        else:
            out.append({'prefix': '', 'number': '', 'suffix': '',
                        'raw': v, 'label': l, 'animate': False})
    return out


@public_bp.route('/candidates')
def candidates_list():
    candidates = (Candidate.query
                  .filter_by(is_published=True)
                  .order_by(Candidate.position.asc())
                  .all())
    return render_template('candidates/list.html', candidates=candidates)


@public_bp.route('/candidates/<int:candidate_id>')
def candidate_detail(candidate_id):
    c = Candidate.query.get_or_404(candidate_id)
    if not c.is_published:
        abort(404)
    return render_template('candidates/detail.html', c=c, cv=c.cv_by_category(),
                           promises=c.promises.all())


@public_bp.route('/priorities')
def priorities():
    items = (Priority.query
             .filter_by(is_published=True)
             .order_by(Priority.sort_order.asc())
             .all())
    return render_template('priorities.html', priorities=items)


@public_bp.route('/program')
def program():
    sections = (ProgramSection.query
                .filter_by(is_published=True)
                .order_by(ProgramSection.sort_order.asc())
                .all())
    return render_template('program.html', sections=sections)


@public_bp.route('/faq')
def faq():
    items = (FAQItem.query
             .filter_by(is_published=True)
             .order_by(FAQItem.sort_order.asc())
             .all())
    return render_template('faq.html', items=items)


@public_bp.route('/about')
def about():
    return render_template('about.html')


@public_bp.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('الرجاء إدخال الاسم', 'warning')
            return redirect(url_for('public.join'))
        msg = ContactMessage(
            name=name,
            phone=request.form.get('phone', '').strip()[:50],
            email=request.form.get('email', '').strip()[:200],
            interest=request.form.get('interest', 'question'),
            message=request.form.get('message', '').strip()[:4000],
        )
        db.session.add(msg)
        db.session.commit()
        flash('شكراً لك — تم استلام رسالتك، سنتواصل معك قريباً.', 'success')
        return redirect(url_for('public.join'))
    return render_template('join.html')


@public_bp.route('/sitemap.xml')
def sitemap():
    pages = [
        url_for('public.home', _external=True),
        url_for('public.candidates_list', _external=True),
        url_for('public.priorities', _external=True),
        url_for('public.program', _external=True),
        url_for('public.faq', _external=True),
        url_for('public.about', _external=True),
        url_for('public.join', _external=True),
    ]
    for c in Candidate.query.filter_by(is_published=True).all():
        pages.append(url_for('public.candidate_detail', candidate_id=c.id, _external=True))
    today = date.today().isoformat()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        xml.append(f'<url><loc>{p}</loc><lastmod>{today}</lastmod></url>')
    xml.append('</urlset>')
    resp = make_response('\n'.join(xml))
    resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return resp


@public_bp.route('/robots.txt')
def robots():
    lines = [
        'User-agent: *',
        'Disallow: /admin',
        f'Sitemap: {url_for("public.sitemap", _external=True)}',
    ]
    resp = make_response('\n'.join(lines))
    resp.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return resp


CATEGORY_LABELS_AR = {
    'education': 'التعليم',
    'experience': 'الخبرة المهنية',
    'memberships': 'العضويات',
    'awards': 'الجوائز والتكريمات',
    'community': 'العمل المجتمعي',
    'skills': 'المهارات',
    'other': 'أخرى',
}

CATEGORY_ICONS = {
    'education': '🎓',
    'experience': '💼',
    'memberships': '🌍',
    'awards': '🏆',
    'community': '🤝',
    'skills': '🛠️',
    'other': '•',
}


@public_bp.app_context_processor
def inject_cv_labels():
    return {
        'cv_label_ar': CATEGORY_LABELS_AR,
        'cv_icon': CATEGORY_ICONS,
    }
