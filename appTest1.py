from flask import Flask, render_template, flash, url_for,redirect
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES, UploadNotAllowed
from flask_admin import Admin, AdminIndexView
from flask_admin.form import ImageUploadField
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash
import os
import pymysql

# Installer MySQLdb pour la compatibilité avec pymysql
pymysql.install_as_MySQLdb()

# Initialisation de l'application Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/testapplicationthree'
app.config['SECRET_KEY'] = os.urandom(24)  # Utiliser une clé constante pour le développement
app.config["UPLOADED_PHOTOS_DEST"] = os.path.join(app.root_path, 'static/image')  

# Initialisation de Flask-Uploads pour gérer les images
photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

# Initialisation de SQLAlchemy
db1 = SQLAlchemy(app)

# Initialisation de Flask-Babel
babel = Babel(app)

# Modèle User pour SQLAlchemy
class User(db1.Model):
    __tablename__ = 'user'
    id = db1.Column(db1.Integer, primary_key=True)
    username = db1.Column(db1.String(80), nullable=False, unique=True)
    email = db1.Column(db1.String(200), nullable=False, unique=True)
    password = db1.Column(db1.String(200))
    is_active = db1.Column(db1.Boolean(), default=False)
    created_at = db1.Column(db1.TIMESTAMP, server_default=db1.func.current_timestamp(), nullable=True)
    updated_at = db1.Column(db1.TIMESTAMP, server_onupdate=db1.func.now(), nullable=True)
    photo = db1.Column(db1.String(255))
    recipes = db1.relationship('Recipe', backref='user')

    # Relation avec le modèle Order
    orders = db1.relationship("Order", back_populates="user")

# Modèle Order pour SQLAlchemy
class Order(db1.Model):
    __tablename__ = "order"
    id = db1.Column(db1.Integer, primary_key=True, nullable=False)
    order_date = db1.Column(db1.DateTime, unique=False, nullable=False)
    user_id = db1.Column(db1.Integer, db1.ForeignKey('user.id', onupdate="CASCADE", ondelete='CASCADE'), nullable=False)
    user = db1.relationship("User", back_populates="orders")

# Modèle Recipe pour SQLAlchemy
class Recipe(db1.Model):
    __tablename__ = 'recipe'
    id = db1.Column(db1.Integer, primary_key=True)
    title = db1.Column(db1.String(200), nullable=False)
    description = db1.Column(db1.Text, nullable=True)
    user_id = db1.Column(db1.Integer, db1.ForeignKey('user.id'), nullable=False)

# Formulaire pour le modèle User
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    photo = FileField('Photo', validators=[FileRequired()])

# ModelView pour Flask-Admin avec des configurations personnalisées
class UserAdmin(ModelView):
    column_exclude_list = ['password']  # Exclure le champ mot de passe de la vue

    form_extra_fields = {
        'photo': ImageUploadField('photo', base_path='static/image/', 
                                  url_relative_path='image/', 
                                  validators=[FileRequired()])
    }

    # Pour afficher l'image dans la liste des utilisateurs
    def _image_formatter(view, context, model, name):
        if model.photo:
            try:
                img_tag = f'<img src="/static/image/{model.photo}" alt="photos" style="max-width: 100px;"/>'
                return Markup(img_tag)
            except Exception as e:
                return f"Error loading image: {str(e)}"
        return "No image"


    # Utiliser le formateur d'image pour la colonne photo
    column_formatters = {
        'photo': _image_formatter
    }
    
    # Optionnel : Pour afficher le champ photo dans la liste
    column_list = ['username', 'email', 'photo']  # Photo est maintenant formaté comme image

    def on_model_change(self, form, model, is_created):
        # Chiffrer le mot de passe si fourni
        if form.password.data:
            model.password = generate_password_hash(form.password.data)

        # Gérer le fichier photo
        if form.photo.data:
            filename = form.photo.data.filename
            full_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)

            # Si l'utilisateur a déjà une photo, la garder dans la base de données
            if model.photo:
                existing_photo_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], model.photo)

                # Si la nouvelle image a le même nom que l'existante, on l'écrase
                if os.path.exists(full_path) and full_path != existing_photo_path:
                    os.remove(full_path)
                    flash(f"The new photo '{filename}' has been removed because it conflicts with an existing one.", 'warning')

            else:
                # Si aucune photo n'existe, sauvegarder la nouvelle
                model.photo = photos.save(form.photo.data, name=filename)


    def _handle_file_upload(self, photo_file):
        if photo_file and allowed_image(photo_file.filename):
            return photos.save(photo_file)  # Sauvegarder le fichier et renvoyer son nom
        return None

class OrdersAdmin(ModelView):
    form_columns = ["order_date", "user"]
    column_list = ["order_date", "user"]

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')  # Utilise un template personnalisé si besoin

# Initialisation de Flask-Admin
admin = Admin(app, template_mode='bootstrap3', index_view=AdminIndexView(name='Admin Panel'))

# Ajouter la vue UserAdmin à Flask-Admin
admin.add_view(UserAdmin(User, db1.session))
admin.add_view(OrdersAdmin(Order, db1.session))  # Ajouter la vue OrdersAdmin

@app.route('/')
def index():
    return redirect(url_for('admin.index')) 
#@app.route('/test-image')
#def test_image():
#    return '<img src="/static/image/sesame_1.png" alt="Test Image">'


def allowed_image(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

if __name__ == '__main__':
    app.run(debug=True)
