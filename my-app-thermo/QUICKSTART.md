# 🚀 DEMARRAGE RAPIDE - ThermoApp

## ✅ Base de données initialisée!

La base de données SQLite a été créée automatiquement: `thermo_app.db`

### 📝 Étapes suivantes:

#### 1. Configurer l'email (optionnel)

Éditez `.env` et remplissez les paramètres MAIL:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-app-password
```

**Pour Gmail:**
- Activez l'authentification à deux facteurs
- Créez un mot de passe d'application
- Utilisez-le dans MAIL_PASSWORD

#### 2. Lancer l'application

```bash
python app.py
```

Accédez à: http://127.0.0.1:5000

#### 3. Se connecter

- **Username:** admin
- **Password:** admin123

#### 4. Changer le mot de passe admin

⚠️ Changez immédiatement le mot de passe par défaut!

### 📋 Fonctionnalités disponibles:

- 📊 Calcul des pressions saturantes (loi d'Antoine)
- 📈 Loi de Raoult pour mélanges binaires
- 👤 Authentification complète
- 📜 Historique des calculs
- 🔑 Réinitialisation de mot de passe (si email configuré)
- 📍 Géolocalisation des connexions (IP)
- 👨‍💼 Dashboard admin

### 🗄️ Structure de la base de données

Tables créées:
- `utilisateur` - Utilisateurs et authentification
- `logs_auth` - Historique des connexions avec géolocalisation
- `historique_calculs` - Calculs sauvegardés par utilisateur
- `pression_saturante` - Constantes thermodynamiques

### 🐛 Dépannage

**La page d'inscription ne fonctionne pas?**
- Vérifiez les permissions du fichier `thermo_app.db`

**Erreur SMTP?**
- Vérifiez les credentials MAIL_* dans `.env`
- Gmail nécessite un mot de passe d'application, pas le mot de passe normal

**Réinitialiser la base?**
```bash
rm thermo_app.db
python init_db.py
```

---

**Besoin d'aide?** Consultez le fichier `README.md`
