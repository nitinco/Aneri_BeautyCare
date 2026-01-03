from flask import Flask
from config import Config
from extensions import db, migrate, jwt
from datetime import datetime, UTC

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # JWT config
    app.config.setdefault('JWT_SECRET_KEY', app.config.get('SECRET_KEY'))

    @app.context_processor
    def inject_current_year():
        # provide `current_year` to all templates
        return {"current_year": datetime.now(UTC).year}

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # register blueprints
    from routes.auth_routes import auth_bp
    from routes.service_routes import svc_bp
    from routes.booking_routes import booking_bp
    from routes.main_routes import main_bp   # 👈 ADD
    from routes.billing_routes import billing_bp
    from routes.product_routes import prod_bp
    from routes.customer_routes import customer_bp
    from routes.order_routes import order_bp
    from routes.delivery_routes import delivery_bp
    from routes.offer_routes import offer_bp
    from routes.staff_routes import staff_bp
    from routes.complaint_routes import cmp_bp
    from routes.payment_routes import pay_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(svc_bp, url_prefix="/api")
    app.register_blueprint(booking_bp, url_prefix="/api")
    app.register_blueprint(main_bp)          # 👈 ADD
    app.register_blueprint(billing_bp)
    app.register_blueprint(prod_bp)
    app.register_blueprint(customer_bp, url_prefix="/api")
    app.register_blueprint(order_bp)
    app.register_blueprint(delivery_bp)
    app.register_blueprint(offer_bp)
    app.register_blueprint(staff_bp, url_prefix="/api")
    app.register_blueprint(cmp_bp)
    app.register_blueprint(pay_bp, url_prefix='/payments')
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
