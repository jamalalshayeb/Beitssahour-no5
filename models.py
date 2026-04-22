from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'site_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='editor')  # admin / editor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'


class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False, default=0, index=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))
    full_legal_name_ar = db.Column(db.String(300))
    title_ar = db.Column(db.String(120))  # e.g., "المهندس" / "المحاسب القانوني"
    tagline_ar = db.Column(db.String(300))  # short one-line tagline under name
    photo_filename = db.Column(db.String(200))  # relative to static/uploads/photos/
    bio_ar = db.Column(db.Text)  # paragraph bio
    bio_en = db.Column(db.Text)
    why_running_ar = db.Column(db.Text)
    why_running_en = db.Column(db.Text)
    is_head_of_list = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cv_items = db.relationship('CandidateCVItem', backref='candidate',
                               lazy='dynamic', cascade='all, delete-orphan',
                               order_by='CandidateCVItem.category, CandidateCVItem.sort_order')
    promises = db.relationship('CandidatePromise', backref='candidate',
                               lazy='dynamic', cascade='all, delete-orphan',
                               order_by='CandidatePromise.sort_order')

    @property
    def display_name_ar(self):
        if self.title_ar:
            return f"{self.title_ar} {self.name_ar}"
        return self.name_ar

    @property
    def photo_url(self):
        if self.photo_filename:
            return f"/static/uploads/photos/{self.photo_filename}"
        return None

    def cv_by_category(self):
        """Return {category_code: [items]} for rendering."""
        buckets = {}
        for item in self.cv_items.all():
            buckets.setdefault(item.category, []).append(item)
        return buckets


class CandidateCVItem(db.Model):
    __tablename__ = 'candidate_cv_items'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    # category codes: education / experience / memberships / community / awards / skills
    category = db.Column(db.String(30), nullable=False, default='experience')
    text_ar = db.Column(db.String(500), nullable=False)
    text_en = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)


class CandidatePromise(db.Model):
    __tablename__ = 'candidate_promises'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    icon = db.Column(db.String(20))  # emoji
    text_ar = db.Column(db.String(500), nullable=False)
    text_en = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)


class ProgramSection(db.Model):
    """Sections of the list's election program (قائمة البناء والتنمية)."""
    __tablename__ = 'program_sections'
    id = db.Column(db.Integer, primary_key=True)
    sort_order = db.Column(db.Integer, default=0, index=True)
    icon = db.Column(db.String(20))  # emoji
    title_ar = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    summary_ar = db.Column(db.Text)
    summary_en = db.Column(db.Text)
    body_ar = db.Column(db.Text)  # full detail, HTML allowed
    body_en = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    list_name_ar = db.Column(db.String(200), default='قائمة البناء والتنمية')
    list_name_en = db.Column(db.String(200), default='Building & Development List')
    list_number = db.Column(db.String(10), default='5')  # رقم القائمة في ورقة الاقتراع
    municipality_ar = db.Column(db.String(200), default='بلدية بيت ساحور')
    municipality_en = db.Column(db.String(200), default='Beit Sahour Municipality')
    election_year = db.Column(db.Integer, default=2026)
    election_date = db.Column(db.Date)  # exact date — drives countdown & CTA
    polling_location_ar = db.Column(db.String(300))
    slogan_ar = db.Column(db.String(300), default='بيت ساحور تستحق الأفضل — معاً نبني مستقبلنا')
    slogan_en = db.Column(db.String(300), default='Beit Sahour Deserves the Best — Together We Build Our Future')
    hero_headline_ar = db.Column(db.String(300), default='مَعًا نَبْنِي الغَدَ الأَفْضَل… مَعًا نَمْضِي وَنَزْدَهِرُ')
    hero_subheadline_ar = db.Column(db.String(400),
        default='قائمة تجمع الخبرات الهندسية والمالية والإدارية والمجتمعية — لخدمة مدينة تستحق الأفضل.')
    hero_intro_ar = db.Column(db.Text, default='قائمة بيت ساحور للبناء والتنمية — خبرات متنوعة تخدم المدينة')
    hero_intro_en = db.Column(db.Text)

    # Editable hero stats (numeric + label). Admin can tweak as roster evolves.
    stat_1_value = db.Column(db.String(20), default='13')
    stat_1_label = db.Column(db.String(120), default='مرشحاً ومرشحة')
    stat_2_value = db.Column(db.String(20), default='+90')
    stat_2_label = db.Column(db.String(120), default='سنة خبرة مجتمعة')
    stat_3_value = db.Column(db.String(20), default='8')
    stat_3_label = db.Column(db.String(120), default='تخصصات مهنية متنوعة')
    stat_4_value = db.Column(db.String(20), default='100%')
    stat_4_label = db.Column(db.String(120), default='التزام بخدمة بيت ساحور')

    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(120))
    contact_address_ar = db.Column(db.String(300))
    facebook_url = db.Column(db.String(300))
    tiktok_url = db.Column(db.String(300))
    instagram_url = db.Column(db.String(300))
    whatsapp_url = db.Column(db.String(300))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Priority(db.Model):
    """Signature top-level commitments — 3–6 big promises shown on the landing page."""
    __tablename__ = 'priorities'
    id = db.Column(db.Integer, primary_key=True)
    sort_order = db.Column(db.Integer, default=0, index=True)
    icon = db.Column(db.String(20))  # emoji
    title_ar = db.Column(db.String(200), nullable=False)
    body_ar = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FAQItem(db.Model):
    __tablename__ = 'faq_items'
    id = db.Column(db.Integer, primary_key=True)
    sort_order = db.Column(db.Integer, default=0, index=True)
    question_ar = db.Column(db.String(400), nullable=False)
    answer_ar = db.Column(db.Text, nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Endorsement(db.Model):
    """Real quotes from supporters — admin-entered only, never auto-generated."""
    __tablename__ = 'endorsements'
    id = db.Column(db.Integer, primary_key=True)
    sort_order = db.Column(db.Integer, default=0)
    quote_ar = db.Column(db.Text, nullable=False)
    author_name_ar = db.Column(db.String(200), nullable=False)
    author_role_ar = db.Column(db.String(200))
    photo_filename = db.Column(db.String(200))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    """Inbound messages from /join page — simple visitor intake."""
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(200))
    interest = db.Column(db.String(50))  # volunteer / donate / question / reminder
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


# --- Meetings module (stubs — details to be finalized by user) ----------------

class MeetingBody(db.Model):
    """A body that holds meetings: Council, a specific committee, etc."""
    __tablename__ = 'meeting_bodies'
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))
    body_type = db.Column(db.String(30), default='committee')  # council / committee
    description_ar = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meetings = db.relationship('Meeting', backref='body', lazy='dynamic', order_by='Meeting.scheduled_at.desc()')


class Meeting(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True)
    body_id = db.Column(db.Integer, db.ForeignKey('meeting_bodies.id'), nullable=False, index=True)
    title_ar = db.Column(db.String(300), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False, index=True)
    location_ar = db.Column(db.String(300))
    status = db.Column(db.String(30), default='scheduled')  # scheduled / in_progress / held / cancelled
    agenda_ar = db.Column(db.Text)  # raw/HTML
    minutes_ar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
