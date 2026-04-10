# ThermoApp - Application Thermodynamique

Application web Flask complète pour résoudre des exercices sur les pressions saturantes du toluène et du benzène.

## Fonctionnalités

- ✅ Calcul des pressions saturantes (loi d'Antoine)
- ✅ Loi de Raoult pour mélanges
- ✅ Authentification complète (inscription/connexion)
- ✅ Historique des calculs par utilisateur
- ✅ Dashboard admin
- ✅ Réinitialisation de mot de passe par email
- ✅ Géolocalisation et heatmap des connexions
- ✅ Rate limiting anti-DDOS
- ✅ Interface responsive et minimaliste

## Installation

### 1. Prérequis

- Python 3.8+
- Git

### 2. Cloner le projet

```bash
git clone <votre-repo>
cd thermo-app
```

### 3. Configuration SQLite

Le projet utilise SQLite par défaut. Aucun serveur MySQL n’est nécessaire.

Copiez le fichier d'exemple et éditez :

```bash
cp .env.example .env
```

Laissez `DATABASE_URL` à `sqlite:///thermo_app.db` ou changez le chemin si vous voulez un autre fichier.

### 4. Variables d'environnement

Copiez le fichier exemple et configurez :

```bash
cp .env.example .env
```

Éditez `.env` avec vos valeurs :
- `DATABASE_URL` (par défaut `sqlite:///thermo_app.db`)
- `MAIL_USERNAME`, `MAIL_PASSWORD` (pour Gmail, utilisez un mot de passe d'application)

Pour Gmail :
- activez l'authentification à deux facteurs
- créez un mot de passe d'application et placez-le dans `MAIL_PASSWORD`
- si vous n'utilisez pas Gmail, utilisez les paramètres SMTP de votre fournisseur

### 5. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 6. Initialisation de la base de données

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Utilisation

### Lancement

```bash
python app.py
```

Accédez à http://127.0.0.1:5000

### Création d'un admin

Dans Python :

```python
from app import app, db
from models import Utilisateur
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = Utilisateur(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
```

## Déploiement

### Sur Render

1. Créez un compte sur Render
2. Connectez votre repo GitHub
3. Configurez les variables d'environnement
4. Déployez

### Variables d'environnement pour production

Assurez-vous de définir :
- `SECRET_KEY`
- `DATABASE_URL` pour SQLite ou autre base
- `MAIL_*` pour l'email

## Structure du projet

```
thermo-app/
├── app.py              # Application principale
├── models.py           # Modèles de base de données
├── auth.py             # Routes d'authentification
├── calculs.py          # Logique des calculs
├── admin.py            # Dashboard admin
├── templates/          # Templates HTML
├── static/css/         # Styles CSS
├── requirements.txt    # Dépendances
├── .env.example        # Exemple de config
└── README.md
```

## Sécurité

- Hashage des mots de passe avec PBKDF2
- Rate limiting (10 requêtes/minute)
- Logs des authentifications avec géolocalisation
- Protection SQL injection via SQLAlchemy
- Sessions sécurisées

## API Géolocalisation

Utilise ipinfo.io pour obtenir pays/ville/coordonnées des connexions.

## Heatmap

Utilise Folium pour générer une carte interactive des connexions mondiales.

## Problèmes courants

### Erreur de connexion à la base de données
- Vérifiez `DATABASE_URL` dans `.env`
- Pour SQLite, assurez-vous que le chemin est accessible et que le fichier est créé automatiquement
- Si vous utilisez une base externe, vérifiez les credentials et l'hôte


### Erreur mail
- Pour Gmail, générez un mot de passe d'application
- Vérifiez les paramètres SMTP

### Import circulaire
- Résolu en important mail localement dans auth.py

### Limiter erreur
- Syntaxe corrigée pour Flask-Limiter 3.x

Visit `http://127.0.0.1:5000` in your web browser to view the application.