from flask import Flask, render_template, request, redirect, url_for
import pymysql
import yaml
from werkzeug.security import generate_password_hash  # Ajoutez cette ligne

app = Flask(__name__)

# Charger la configuration de la base de données
try:
    db = yaml.safe_load(open('db.yaml'))
except FileNotFoundError:
    print("Le fichier db.yaml est introuvable.")

def get_db_connection():
    """ Créer une connexion MySQL à chaque appel """
    connection = pymysql.connect(
        host=db['mysql_host'],
        user=db['mysql_user'],
        password=db['mysql_password'],
        database=db['mysql_db']
    )
    return connection

def test_db_connection():
    """ Test de la connexion à la base de données """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # Test simple
        print("Connexion à la base de données réussie!")
    except pymysql.MySQLError as e:
        print(f"Erreur de connexion à la base de données: {e}")
    finally:
        connection.close()

@app.route("/")
def index():
    return redirect(url_for('users'))

@app.route('/users')
def users():
    try:
        connection = get_db_connection()  # Obtenir une nouvelle connexion
        cur = connection.cursor()
        resultValue = cur.execute("SELECT * FROM user")
        users = cur.fetchall() if resultValue > 0 else []
        print(f"Liste des utilisateurs dans la base de données : {users}")  # Affichez les utilisateurs
        return render_template('users.html', users=users)
    except pymysql.MySQLError as e:
        print(f"Erreur lors de l'exécution de la requête: {e}")
    finally:
        cur.close()
        connection.close()  # Fermer la connexion
    return render_template('users.html', message='Aucun utilisateur trouvé.')

@app.route("/addUser/", methods=["GET", "POST"])
def addUser():
    test_db_connection()  # Test de la connexion à la base de données
    if request.method == "POST":
        form = request.form
        name = form["username"].strip()  # Supprimez les espaces
        email = form["email"].strip()  # Supprimez les espaces
        password = form["password"].strip()  # Obtenez le mot de passe
        
        # Vérifiez que les champs ne sont pas vides
        if not name or not email or not password:
            return render_template('addUser.html', error="Les champs username, email et password ne peuvent pas être vides.")
        
        # Hachez le mot de passe avant de l'insérer dans la base de données
        hashed_password = generate_password_hash(password)
        
        try:
            connection = get_db_connection()  # Obtenir une nouvelle connexion
            cur = connection.cursor()
            # Insérer l'utilisateur avec le mot de passe haché
            cur.execute("INSERT INTO user(username, email, password) VALUES(%s, %s, %s)", (name, email, hashed_password))
            connection.commit()
            print("Utilisateur ajouté avec succès!")  # Ajoutez cette ligne
        except pymysql.MySQLError as e:
            print(f"Erreur lors de l'insertion des données: {e}")  # Affichez l'erreur
        finally:
            cur.close()
            connection.close()  # Fermer la connexion
        return redirect(url_for('users'))  # Rediriger vers la page des utilisateurs
    return render_template('addUser.html')

@app.route('/deleteUser/<int:user_id>', methods=['POST'])
def deleteUser(user_id):
    try:
        connection = get_db_connection()  # Obtenir une nouvelle connexion
        cur = connection.cursor()
        cur.execute("DELETE FROM user WHERE id = %s", (user_id,))
        connection.commit()
        print(f"Utilisateur avec l'ID {user_id} supprimé avec succès.")
    except pymysql.MySQLError as e:
        print(f"Erreur lors de la suppression de l'utilisateur: {e}")
    finally:
        cur.close()
        connection.close()  # Fermer la connexion
    return redirect(url_for('users'))  # Rediriger vers la page des utilisateurs

@app.route('/editUser/<int:user_id>', methods=['GET', 'POST'])
def editUser(user_id):
    try:
        connection = get_db_connection()  # Obtenir une nouvelle connexion
        cur = connection.cursor()
        
        # Si la méthode est POST, mettez à jour les informations de l'utilisateur
        if request.method == 'POST':
            form = request.form
            name = form["username"].strip()
            email = form["email"].strip()
            password = form["password"].strip()
            
            # Hachez le mot de passe si un nouveau mot de passe est fourni
            hashed_password = generate_password_hash(password) if password else None
            
            # Mettre à jour l'utilisateur dans la base de données
            if hashed_password:
                cur.execute(
                    "UPDATE user SET username = %s, email = %s, password = %s WHERE id = %s",
                    (name, email, hashed_password, user_id)
                )
            else:
                cur.execute(
                    "UPDATE user SET username = %s, email = %s WHERE id = %s",
                    (name, email, user_id)
                )
            connection.commit()
            return redirect(url_for('users'))  # Redirige vers la liste des utilisateurs

        # Si la méthode est GET, récupérez les informations de l'utilisateur
        cur.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if user:
            return render_template('editUser.html', user=user)
        else:
            return "Utilisateur non trouvé", 404
    except pymysql.MySQLError as e:
        print(f"Erreur lors de l'édition de l'utilisateur: {e}")
    finally:
        cur.close()
        connection.close()  # Fermer la connexion


if __name__ == "__main__":
    app.run(debug=True, port=5004)
