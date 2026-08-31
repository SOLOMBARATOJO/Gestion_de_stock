from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Produit(db.Model):
    __tablename__ = "produits"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    categorie = db.Column(db.String(80), default="Général")
    prix = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    seuil_alerte = db.Column(db.Integer, default=5)  # seuil de stock bas

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "categorie": self.categorie,
            "prix": self.prix,
            "stock": self.stock,
            "seuil_alerte": self.seuil_alerte,
        }


class Client(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    telephone = db.Column(db.String(30))
    commandes = db.relationship("Commande", backref="client", lazy=True)

    def to_dict(self):
        return {"id": self.id, "nom": self.nom, "email": self.email, "telephone": self.telephone}


class Commande(db.Model):
    __tablename__ = "commandes"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    quantite = db.Column(db.Integer, nullable=False, default=1)
    total = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), nullable=False, default="en_attente")  # en_attente | livree | annulee
    date_commande = db.Column(db.DateTime, default=datetime.utcnow)
    produit = db.relationship("Produit")

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_nom": self.client.nom if self.client else None,
            "produit_id": self.produit_id,
            "produit_nom": self.produit.nom if self.produit else None,
            "quantite": self.quantite,
            "total": self.total,
            "statut": self.statut,
            "date_commande": self.date_commande.isoformat(),
        }