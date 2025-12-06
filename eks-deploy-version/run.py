
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()

with app.app_context():
    # Use Flask-Migrate in production instead of db.create_all()
    db.create_all()

    # Default admin user setup
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin = User.query.filter_by(username=admin_username).first()

    if not admin:
        db.session.add(User(username=admin_username,
                            password=generate_password_hash(admin_password)))
        db.session.commit()
        print(f"Default admin user created -> username: {admin_username}, password: {admin_password}")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
