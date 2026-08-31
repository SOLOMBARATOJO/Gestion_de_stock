"""
Peuple la base avec des données de démonstration la première fois
qu'elle est vide (ex: juste après un clone du dépôt par un autre
utilisateur, qui n'a pas database.db). N'écrase jamais des données
existantes : ne fait rien si la table produits contient déjà des lignes.
"""

from datetime import datetime, timedelta
from models import db, Produit, Client, Commande


def seed_db():
    if Produit.query.first() is not None:
        return  # la base contient déjà des données, on ne touche à rien

    produits = [
        Produit(nom="Clavier mécanique", description="Switches rouges, rétroéclairé",
                categorie="Informatique", prix=89000, stock=14, seuil_alerte=5),
        Produit(nom="Souris sans fil", description="2.4GHz, capteur optique",
                categorie="Informatique", prix=35000, stock=22, seuil_alerte=8),
        Produit(nom="Écran 24 pouces", description="Full HD, 75Hz",
                categorie="Informatique", prix=420000, stock=3, seuil_alerte=5),
        Produit(nom="Casque audio", description="Bluetooth, réduction de bruit",
                categorie="Audio", prix=120000, stock=10, seuil_alerte=4),
        Produit(nom="Chargeur USB-C", description="65W, charge rapide",
                categorie="Accessoires", prix=25000, stock=40, seuil_alerte=10),
        Produit(nom="Webcam HD", description="1080p, micro intégré",
                categorie="Informatique", prix=65000, stock=2, seuil_alerte=5),
    ]
    db.session.add_all(produits)

    clients = [
        Client(nom="Rakoto Jean", email="rakoto.jean@example.mg", telephone="034 12 345 67"),
        Client(nom="Rasoa Marie", email="rasoa.marie@example.mg", telephone="033 98 765 43"),
        Client(nom="Andry Tech SARL", email="contact@andrytech.mg", telephone="020 22 123 45"),
        Client(nom="Hery Solutions", email="hery@solutions.mg", telephone="032 55 667 78"),
    ]
    db.session.add_all(clients)
    db.session.commit()  # nécessaire pour obtenir les ids avant de créer les commandes

    base_date = datetime.utcnow() - timedelta(days=45)
    commandes_data = [
        (clients[0], produits[0], 1, "livree", 2),
        (clients[1], produits[3], 2, "livree", 5),
        (clients[2], produits[2], 1, "livree", 10),
        (clients[3], produits[1], 3, "en_attente", 15),
        (clients[0], produits[4], 2, "livree", 20),
        (clients[2], produits[5], 1, "annulee", 25),
        (clients[1], produits[0], 1, "en_attente", 30),
        (clients[3], produits[3], 1, "livree", 38),
    ]

    for client, produit, quantite, statut, jours_offset in commandes_data:
        commande = Commande(
            client_id=client.id,
            produit_id=produit.id,
            quantite=quantite,
            total=produit.prix * quantite,
            statut=statut,
            date_commande=base_date + timedelta(days=jours_offset),
        )
        db.session.add(commande)

    db.session.commit()