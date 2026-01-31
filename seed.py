import os
from app import create_app
from extensions import db
from models.user import Users
from models.category import Category, SubCategory
from models import Staff


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

        # Create sample staff members if they don't exist
        staff_members = [
            {'name': 'Sarah Johnson', 'email': 'sarah@aneri.local', 'phone': '+91-9876543210'},
            {'name': 'Mike Chen', 'email': 'mike@aneri.local', 'phone': '+91-9876543211'},
            {'name': 'Priya Patel', 'email': 'priya@aneri.local', 'phone': '+91-9876543212'},
            {'name': 'David Kumar', 'email': 'david@aneri.local', 'phone': '+91-9876543213'},
        ]

        for staff_data in staff_members:
            if not Users.query.filter_by(email=staff_data['email']).first():
                staff_user = Users(name=staff_data['name'], email=staff_data['email'], role='staff')
                staff_user.set_password('staff123')  # Default password
                db.session.add(staff_user)
                db.session.flush()  # Get user ID

                # Create staff profile
                staff_profile = Staff(
                    user_id=staff_user.id,
                    phone=staff_data['phone'],
                    is_active=True,
                    is_available=True
                )
                db.session.add(staff_profile)
                print(f'Created staff member: {staff_data["name"]}')

        # Create sample categories and subcategories if they don't exist
        if not Category.query.first():
            print('Creating sample categories and subcategories...')

            # Create categories
            hair_category = Category(name='Hair Care', description='Hair styling and treatment services')
            skin_category = Category(name='Skin Care', description='Skin treatment and care services')
            makeup_category = Category(name='Makeup', description='Professional makeup services')
            nails_category = Category(name='Nails', description='Nail care and styling services')

            db.session.add_all([hair_category, skin_category, makeup_category, nails_category])
            db.session.flush()  # Get IDs

            # Create subcategories
            hair_subcategories = [
                SubCategory(name='Hair Cut', category_id=hair_category.id, description='Professional hair cutting'),
                SubCategory(name='Hair Coloring', category_id=hair_category.id, description='Hair dyeing and coloring'),
                SubCategory(name='Hair Treatment', category_id=hair_category.id, description='Hair conditioning and treatment'),
                SubCategory(name='Hair Styling', category_id=hair_category.id, description='Hair styling and blowout'),
            ]

            skin_subcategories = [
                SubCategory(name='Facial', category_id=skin_category.id, description='Facial treatments and cleansing'),
                SubCategory(name='Skin Treatment', category_id=skin_category.id, description='Specialized skin treatments'),
                SubCategory(name='Body Scrub', category_id=skin_category.id, description='Body exfoliation and cleansing'),
            ]

            makeup_subcategories = [
                SubCategory(name='Bridal Makeup', category_id=makeup_category.id, description='Complete bridal makeup'),
                SubCategory(name='Party Makeup', category_id=makeup_category.id, description='Party and event makeup'),
                SubCategory(name='Regular Makeup', category_id=makeup_category.id, description='Regular makeup services'),
            ]

            nails_subcategories = [
                SubCategory(name='Manicure', category_id=nails_category.id, description='Hand and nail care'),
                SubCategory(name='Pedicure', category_id=nails_category.id, description='Foot and nail care'),
                SubCategory(name='Nail Art', category_id=nails_category.id, description='Decorative nail designs'),
            ]

            db.session.add_all(hair_subcategories + skin_subcategories + makeup_subcategories + nails_subcategories)
            db.session.commit()

            print('Created sample categories and subcategories')
        else:
            print('Categories and subcategories already exist')


if __name__ == '__main__':
    run()
