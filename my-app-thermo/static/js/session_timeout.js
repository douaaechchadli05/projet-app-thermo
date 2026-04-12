// Session Timeout Manager
class SessionTimeoutManager {
    constructor(timeoutMinutes = 10, warningSeconds = 10) {
        this.timeoutMinutes = timeoutMinutes;
        this.warningSeconds = warningSeconds;
        this.timeout = null;
        this.warningTimeout = null;
        this.lastActivity = Date.now();
        
        this.init();
    }
    
    init() {
        // Réinitialiser le timer à chaque activité
        this.resetTimer();
        
        // Écouter les événements d'activité
        this.setupActivityListeners();
        
        // Vérifier périodiquement l'état de la session
        this.startSessionCheck();
    }
    
    setupActivityListeners() {
        const events = [
            'mousedown', 'mousemove', 'keypress', 'scroll', 
            'touchstart', 'click', 'focus', 'blur'
        ];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.resetTimer();
            }, true);
        });
    }
    
    resetTimer() {
        this.lastActivity = Date.now();
        
        // Annuler les timers existants
        if (this.timeout) clearTimeout(this.timeout);
        if (this.warningTimeout) clearTimeout(this.warningTimeout);
        
        // Configurer le timer d'avertissement
        this.warningTimeout = setTimeout(() => {
            this.showWarning();
        }, (this.timeoutMinutes * 60 * 1000) - (this.warningSeconds * 1000));
        
        // Configurer le timer de déconnexion
        this.timeout = setTimeout(() => {
            this.logout();
        }, this.timeoutMinutes * 60 * 1000);
    }
    
    showWarning() {
        // Créer une modale d'avertissement
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            font-family: 'Inter', sans-serif;
        `;
        
        modal.innerHTML = `
            <div style="
                background: var(--glass-bg, rgba(255, 255, 255, 0.1));
                backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.2));
                border-radius: 20px;
                padding: 2rem;
                max-width: 400px;
                text-align: center;
                color: var(--text-primary, #ffffff);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem; color: var(--accent-sky, #87ceeb);">
                    <i class="fas fa-clock"></i>
                </div>
                <h3 style="margin-bottom: 1rem; font-size: 1.5rem;">Session expirée bientôt</h3>
                <p style="margin-bottom: 1.5rem; opacity: 0.9;">
                    Votre session expirera dans ${this.warningSeconds} secondes en raison d'inactivité.
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button id="extendSession" style="
                        background: linear-gradient(135deg, var(--accent-sky, #87ceeb), var(--accent-purple, #9f7aea));
                        border: none;
                        color: white;
                        padding: 0.75rem 1.5rem;
                        border-radius: 10px;
                        cursor: pointer;
                        font-weight: 600;
                    ">
                        Prolonger la session
                    </button>
                    <button id="logoutNow" style="
                        background: transparent;
                        border: 1px solid var(--accent-rose, #ff6b9d);
                        color: var(--accent-rose, #ff6b9d);
                        padding: 0.75rem 1.5rem;
                        border-radius: 10px;
                        cursor: pointer;
                        font-weight: 600;
                    ">
                        Se déconnecter
                    </button>
                </div>
                <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.7;">
                    Temps restant: <span id="countdown">${this.warningSeconds}</span>s
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Gérer le compte à rebours
        let countdown = this.warningSeconds;
        const countdownElement = modal.querySelector('#countdown');
        const countdownInterval = setInterval(() => {
            countdown--;
            countdownElement.textContent = countdown;
            if (countdown <= 0) {
                clearInterval(countdownInterval);
            }
        }, 1000);
        
        // Gérer les boutons
        modal.querySelector('#extendSession').addEventListener('click', () => {
            clearInterval(countdownInterval);
            document.body.removeChild(modal);
            this.resetTimer();
            this.showNotification('Session prolongée', 'success');
        });
        
        modal.querySelector('#logoutNow').addEventListener('click', () => {
            clearInterval(countdownInterval);
            document.body.removeChild(modal);
            this.logout();
        });
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? 'linear-gradient(135deg, var(--accent-sky, #87ceeb), var(--accent-purple, #9f7aea))' : 'linear-gradient(135deg, var(--accent-rose, #ff6b9d), var(--accent-purple, #9f7aea))'};
            color: white;
            border-radius: 10px;
            font-weight: 600;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            font-family: 'Inter', sans-serif;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    logout() {
        // Afficher une notification de déconnexion
        this.showNotification('Session expirée - Déconnexion automatique', 'warning');
        
        // Rediriger vers la page de déconnexion après un court délai
        setTimeout(() => {
            window.location.href = '/logout';
        }, 2000);
    }
    
    startSessionCheck() {
        // Vérifier toutes les 30 secondes si la session est toujours valide
        setInterval(() => {
            const timeSinceActivity = Date.now() - this.lastActivity;
            const maxInactivity = this.timeoutMinutes * 60 * 1000;
            
            if (timeSinceActivity >= maxInactivity) {
                this.logout();
            }
        }, 30000);
    }
}

// Ajouter les animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialiser le gestionnaire de session timeout
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si l'utilisateur est connecté
    if (document.body.contains(document.querySelector('a[href="/logout"]')) || 
        window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        new SessionTimeoutManager(1, 10); // 1 minute timeout, 10 secondes d'avertissement
    }
});
