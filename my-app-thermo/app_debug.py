from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    try:
        return render_template('index_test.html')
    except Exception as e:
        return f"Erreur: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            # Simulation de connexion réussie
            if username and password:
                return f"Connexion réussie pour {username}! (Mode test)"
            else:
                return "Veuillez remplir tous les champs", 400
        else:
            return render_template('login_test.html')
    except Exception as e:
        return f"Erreur: {str(e)}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            # Simulation d'inscription réussie
            if username and email and password:
                return f"Inscription réussie pour {username}! (Mode test)"
            else:
                return "Veuillez remplir tous les champs", 400
        else:
            return render_template('register_test.html')
    except Exception as e:
        return f"Erreur: {str(e)}"

if __name__ == '__main__':
    print("Application de test démarrée...")
    print("Accès: http://127.0.0.1:5004")
    print("Cette version utilise un template simplifié pour tester le thème")
    app.run(debug=True, host='127.0.0.1', port=5004)
