import json
import os

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")

    assets = db.relationship("UserAsset", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        # Explicitly use pbkdf2 to avoid environments without hashlib.scrypt support
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    historical_returns_json = db.Column(db.Text, nullable=False)
    default_amount = db.Column(db.Float, default=1000.0)

    user_assets = db.relationship("UserAsset", back_populates="asset")

    @property
    def historical_returns(self):
        data = json.loads(self.historical_returns_json or "[]")
        return data


class UserAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey("asset.id"), nullable=False)
    invested_amount = db.Column(db.Float, nullable=False, default=0.0)
    allocation_percent = db.Column(db.Float, nullable=False, default=0.0)
    monthly_contribution = db.Column(db.Float, nullable=False, default=0.0)
    yearly_contribution = db.Column(db.Float, nullable=False, default=0.0)

    user = db.relationship("User", back_populates="assets")
    asset = db.relationship("Asset", back_populates="user_assets")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_assets():
    inspector = db.inspect(db.engine)
    if not inspector.has_table("asset"):
        return

    default_assets = [
        {
            "name": "ETF S&P 500",
            "returns": [0.12, -0.03, 0.08, 0.10, 0.15],
            "amount": 1000,
        },
        {
            "name": "Bond Governativi EU",
            "returns": [0.02, 0.015, 0.018, 0.01, 0.022],
            "amount": 1000,
        },
        {
            "name": "Bitcoin",
            "returns": [0.50, -0.40, 0.30, 0.10, 0.60],
            "amount": 1000,
        },
        {
            "name": "Real Estate Europe",
            "returns": [0.06, 0.05, 0.04, 0.03, 0.05],
            "amount": 1000,
        },
    ]

    if Asset.query.count() == 0:
        for entry in default_assets:
            asset = Asset(
                name=entry["name"],
                historical_returns_json=json.dumps(entry["returns"]),
                default_amount=entry["amount"],
            )
            db.session.add(asset)
        db.session.commit()


def ensure_admin_user():
    inspector = db.inspect(db.engine)
    if not inspector.has_table("user"):
        return

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")

    admin = User.query.filter_by(email=admin_email).first()
    if admin is None:
        admin = User(username="admin", email=admin_email, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()


def recalculate_allocations(user_id: int):
    assets = UserAsset.query.filter_by(user_id=user_id).all()
    total = sum(asset.invested_amount for asset in assets)
    for asset in assets:
        asset.allocation_percent = round((asset.invested_amount / total) * 100, 2) if total else 0.0
    db.session.commit()
