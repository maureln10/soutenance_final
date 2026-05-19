import mysql.connector
from mysql.connector import Error
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def ajouter_admin():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="site"
        )

        if connection.is_connected():
            cursor = connection.cursor()

            nom          = "Maurel"
            prenom       = "Maurel"
            email        = "admin@gmail.com"
            # Hash avec bcrypt, compatible avec flask_bcrypt.check_password_hash
            mot_de_passe = bcrypt.generate_password_hash("relmau10").decode("utf-8")
            genre        = "M"
            image_file   = "default.jpg"

            sql = """
            INSERT INTO administrateur (nom, prenom, email, mot_de_passe, genre, image_file)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            valeurs = (nom, prenom, email, mot_de_passe, genre, image_file)

            cursor.execute(sql, valeurs)
            connection.commit()

            print(f"✅ Administrateur {nom} {prenom} ajouté avec succès !")
            print(f"   → Email        : {email}")
            print(f"   → Mot de passe : relmau10 (hashé bcrypt)")

    except Error as e:
        print("❌ Erreur MySQL :", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    ajouter_admin()