import csv
import io

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from models import db, Produit, Client, Commande
from seed import seed_db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
CORS(app)  # autorise le frontend Reflex à appeler l'API

with app.app_context():
    db.create_all()
    seed_db()  # peuple la base si elle vient d'être créée (clone sur une autre machine)


# ---------- PRODUITS ----------

@app.route("/api/produits", methods=["GET"])
def get_produits():
    produits = Produit.query.all()
    return jsonify([p.to_dict() for p in produits])


@app.route("/api/produits/<int:produit_id>", methods=["GET"])
def get_produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    return jsonify(produit.to_dict())


@app.route("/api/produits", methods=["POST"])
def create_produit():
    data = request.get_json()
    produit = Produit(
        nom=data["nom"],
        description=data.get("description"),
        categorie=data.get("categorie", "Général"),
        prix=data["prix"],
        stock=data.get("stock", 0),
        seuil_alerte=data.get("seuil_alerte", 5),
    )
    db.session.add(produit)
    db.session.commit()
    return jsonify(produit.to_dict()), 201


@app.route("/api/produits/<int:produit_id>", methods=["PUT"])
def update_produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    data = request.get_json()
    produit.nom = data.get("nom", produit.nom)
    produit.description = data.get("description", produit.description)
    produit.categorie = data.get("categorie", produit.categorie)
    produit.prix = data.get("prix", produit.prix)
    produit.stock = data.get("stock", produit.stock)
    produit.seuil_alerte = data.get("seuil_alerte", produit.seuil_alerte)
    db.session.commit()
    return jsonify(produit.to_dict())


@app.route("/api/produits/<int:produit_id>", methods=["DELETE"])
def delete_produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    db.session.delete(produit)
    db.session.commit()
    return jsonify({"message": "Produit supprimé"})


@app.route("/api/produits/stock-bas", methods=["GET"])
def get_produits_stock_bas():
    produits = Produit.query.filter(Produit.stock <= Produit.seuil_alerte).all()
    return jsonify([p.to_dict() for p in produits])


# ---------- CLIENTS ----------

@app.route("/api/clients", methods=["GET"])
def get_clients():
    clients = Client.query.all()
    return jsonify([c.to_dict() for c in clients])


@app.route("/api/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict())


@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.get_json()
    client = Client(
        nom=data["nom"],
        email=data.get("email"),
        telephone=data.get("telephone"),
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(client.to_dict()), 201


@app.route("/api/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    client.nom = data.get("nom", client.nom)
    client.email = data.get("email", client.email)
    client.telephone = data.get("telephone", client.telephone)
    db.session.commit()
    return jsonify(client.to_dict())


@app.route("/api/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({"message": "Client supprimé"})


@app.route("/api/clients/<int:client_id>/commandes", methods=["GET"])
def get_commandes_client(client_id):
    Client.query.get_or_404(client_id)
    commandes = Commande.query.filter_by(client_id=client_id).order_by(Commande.date_commande.desc()).all()
    return jsonify([c.to_dict() for c in commandes])


# ---------- COMMANDES ----------

@app.route("/api/commandes", methods=["GET"])
def get_commandes():
    commandes = Commande.query.all()
    return jsonify([c.to_dict() for c in commandes])


@app.route("/api/commandes/<int:commande_id>", methods=["GET"])
def get_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    return jsonify(commande.to_dict())


@app.route("/api/commandes", methods=["POST"])
def create_commande():
    data = request.get_json()

    produit = Produit.query.get_or_404(data["produit_id"])
    quantite = data.get("quantite", 1)

    if produit.stock < quantite:
        return jsonify({"error": "Stock insuffisant"}), 400

    total = produit.prix * quantite

    commande = Commande(
        client_id=data["client_id"],
        produit_id=data["produit_id"],
        quantite=quantite,
        total=total,
        statut=data.get("statut", "en_attente"),
    )

    # mise à jour du stock
    produit.stock -= quantite

    db.session.add(commande)
    db.session.commit()
    return jsonify(commande.to_dict()), 201


@app.route("/api/commandes/<int:commande_id>", methods=["PUT"])
def update_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    data = request.get_json()

    nouvelle_quantite = data.get("quantite", commande.quantite)
    produit = commande.produit

    difference = nouvelle_quantite - commande.quantite

    if difference > 0 and produit.stock < difference:
        return jsonify({"error": "Stock insuffisant pour cette modification"}), 400

    produit.stock -= difference
    commande.quantite = nouvelle_quantite
    commande.total = produit.prix * nouvelle_quantite
    commande.statut = data.get("statut", commande.statut)

    db.session.commit()
    return jsonify(commande.to_dict())


@app.route("/api/commandes/<int:commande_id>/statut", methods=["PATCH"])
def update_statut_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    data = request.get_json()
    nouveau_statut = data.get("statut")

    if nouveau_statut not in ("en_attente", "livree", "annulee"):
        return jsonify({"error": "Statut invalide"}), 400

    # si on annule une commande qui n'était pas déjà annulée, on restitue le stock
    if nouveau_statut == "annulee" and commande.statut != "annulee":
        commande.produit.stock += commande.quantite

    commande.statut = nouveau_statut
    db.session.commit()
    return jsonify(commande.to_dict())


@app.route("/api/commandes/<int:commande_id>", methods=["DELETE"])
def delete_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    db.session.delete(commande)
    db.session.commit()
    return jsonify({"message": "Commande supprimée"})


# ---------- STATISTIQUES ----------

@app.route("/api/stats", methods=["GET"])
def get_stats():
    total_ventes = db.session.query(db.func.sum(Commande.total)).filter(
        Commande.statut != "annulee"
    ).scalar() or 0
    nb_commandes = Commande.query.count()
    nb_clients = Client.query.count()
    nb_produits = Produit.query.count()
    nb_alertes_stock = Produit.query.filter(Produit.stock <= Produit.seuil_alerte).count()

    return jsonify({
        "total_ventes": total_ventes,
        "nb_commandes": nb_commandes,
        "nb_clients": nb_clients,
        "nb_produits": nb_produits,
        "nb_alertes_stock": nb_alertes_stock,
    })


@app.route("/api/stats/ventes-par-produit", methods=["GET"])
def get_ventes_par_produit():
    resultats = (
        db.session.query(Produit.nom, db.func.sum(Commande.total).label("total"))
        .join(Commande, Commande.produit_id == Produit.id)
        .filter(Commande.statut != "annulee")
        .group_by(Produit.nom)
        .all()
    )
    return jsonify([{"produit": r.nom, "total": r.total} for r in resultats])


@app.route("/api/stats/ventes-par-mois", methods=["GET"])
def get_ventes_par_mois():
    resultats = (
        db.session.query(
            db.func.strftime("%Y-%m", Commande.date_commande).label("mois"),
            db.func.sum(Commande.total).label("total"),
        )
        .filter(Commande.statut != "annulee")
        .group_by("mois")
        .order_by("mois")
        .all()
    )
    return jsonify([{"mois": r.mois, "total": r.total} for r in resultats])


@app.route("/api/stats/top-clients", methods=["GET"])
def get_top_clients():
    resultats = (
        db.session.query(Client.nom, db.func.sum(Commande.total).label("total"))
        .join(Commande, Commande.client_id == Client.id)
        .filter(Commande.statut != "annulee")
        .group_by(Client.nom)
        .order_by(db.func.sum(Commande.total).desc())
        .limit(5)
        .all()
    )
    return jsonify([{"client": r.nom, "total": r.total} for r in resultats])


# ---------- EXPORT ----------

@app.route("/api/export/commandes.csv", methods=["GET"])
def export_commandes_csv():
    commandes = Commande.query.order_by(Commande.date_commande.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "client", "produit", "quantite", "total", "statut", "date"])
    for c in commandes:
        writer.writerow([
            c.id,
            c.client.nom if c.client else "",
            c.produit.nom if c.produit else "",
            c.quantite,
            c.total,
            c.statut,
            c.date_commande.isoformat(),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=commandes.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)