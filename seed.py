import os
from app import create_app
from extensions import db
from models.user import Users


def run():
    app = create_app()
    with app.app_context():
        # create all tables if migrations haven't been applied
        db.create_all()

        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@aneri.local')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

        if not Users.query.filter_by(email=admin_email).first():
            admin = Users(name='Admin', email=admin_email, role='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print('Created admin user:', admin_email)
        else:
            print('Admin user already exists')


if __name__ == '__main__':
    run()
