// Configuration BotIA
const appState = {
    database: {
        "voyant_moteur": {
            "keywords": ["voyant moteur", "témoin moteur", "check engine", "voyant orange"],
            "titre": "Voyant moteur allumé",
            "urgence": "moyenne",
            "causes": [
                "Capteur d'oxygène défectueux",
                "Bouchon du réservoir mal serré",
                "Catalyseur endommagé",
                "Bobine d'allumage défaillante"
            ],
            "solutions": [
                "Effectuer un diagnostic OBD2",
                "Vérifier le bouchon du réservoir",
                "Consulter un mécanicien rapidement",
                "Nettoyer le filtre à air"
            ],
            "cout_estime": "30-1500€",
            "contributeur": "système"
        },
        "demarrage_difficile": {
            "keywords": ["démarrage difficile", "moteur ne démarre pas", "starter", "batterie"],
            "titre": "Problèmes de démarrage",
            "urgence": "elevee",
            "causes": [
                "Batterie déchargée",
                "Alternateur défectueux",
                "Starter en panne",
                "Bougies usées"
            ],
            "solutions": [
                "Vérifier la tension batterie",
                "Nettoyer les bornes",
                "Tester l'alternateur",
                "Remplacer les bougies"
            ],
            "cout_estime": "50-800€",
            "contributeur": "système"
        }
    },
    totalQuestions: 0,
    unansweredQuestions: [],
    contributions: []
};

// Fonctions utilitaires
function showNotification(message, type = 'success') {
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;
    notif.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 20px;
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 10px;
        color: #4CAF50;
        z-index: 1001;
        animation: slideIn 0.3s ease-out;
    `;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

function addMessage(content, isUser = false, metadata = {}) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const wrapperDiv = document.createElement('div');
    wrapperDiv.className = `message-wrapper ${isUser ? 'user-message' : 'bot-message'}`;
    
    const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    
    wrapperDiv.innerHTML = `
        <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
        <div>
            <div class="message-content">${content}</div>
            ${!isUser ? `
            <div class="message-footer">
                <span>${time}</span>
                ${metadata.source ? `<span class="source-tag source-${metadata.source}">${
                    metadata.source === 'database' ? '📚 Base locale' : 
                    metadata.source === 'ai' ? '🤖 IA' : 
                    '❓ Sans réponse'
                }</span>` : ''}
            </div>
            ` : ''}
        </div>
    `;
    
    messageDiv.appendChild(wrapperDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function searchDatabase(query) {
    const queryLower = query.toLowerCase();
    let bestMatch = null;
    let bestScore = 0;

    for (const [key, diagnostic] of Object.entries(appState.database)) {
        let score = 0;
        
        for (const keyword of (diagnostic.keywords || [])) {
            if (queryLower.includes(keyword.toLowerCase())) {
                score += keyword.split(' ').length * 2;
            }
        }
        
        if (diagnostic.titre && queryLower.includes(diagnostic.titre.toLowerCase())) {
            score += 3;
        }
        
        if (score > bestScore) {
            bestScore = score;
            bestMatch = diagnostic;
        }
    }

    return bestScore > 0 ? bestMatch : null;
}

function formatDiagnostic(diagnostic) {
    const urgenceColors = {
        'critique': '#f44336',
        'elevee': '#ff9800',
        'moyenne': '#ffc107',
        'faible': '#4caf50'
    };

    return `
        <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1);">
            <h3 style="margin: 0 0 10px 0; color: #fff;">${diagnostic.titre}</h3>
            <span style="display: inline-block; padding: 5px 15px; background: ${urgenceColors[diagnostic.urgence]}; border-radius: 20px; font-size: 13px; margin-bottom: 15px;">
                ⚠️ Urgence ${diagnostic.urgence}
            </span>
            
            <div style="margin: 20px 0;">
                <h4 style="color: #667eea; margin-bottom: 10px;">🔍 Causes possibles</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    ${diagnostic.causes.map(cause => `<li style="margin-bottom: 5px;">${cause}</li>`).join('')}
                </ul>
            </div>
            
            <div style="margin: 20px 0;">
                <h4 style="color: #667eea; margin-bottom: 10px;">🔧 Solutions recommandées</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    ${diagnostic.solutions.map(sol => `<li style="margin-bottom: 5px;">${sol}</li>`).join('')}
                </ul>
            </div>
            
            ${diagnostic.cout_estime ? `
            <div style="margin: 20px 0;">
                <h4 style="color: #667eea; margin-bottom: 10px;">💰 Coût estimé</h4>
                <p style="margin: 0; font-weight: bold;">${diagnostic.cout_estime}</p>
            </div>
            ` : ''}
            
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1); font-size: 12px; color: #666;">
                Contribué par : ${diagnostic.contributeur}
            </div>
        </div>
    `;
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage(message, true);
    input.value = '';
    
    appState.totalQuestions++;
    document.getElementById('stat-questions').textContent = appState.totalQuestions;
    
    const diagnostic = searchDatabase(message);
    
    if (diagnostic) {
        const response = formatDiagnostic(diagnostic);
        addMessage(response, false, { source: 'database' });
    } else {
        const unansweredItem = {
            id: Date.now(),
            question: message,
            timestamp: new Date().toISOString(),
            count: 1
        };
        
        appState.unansweredQuestions.push(unansweredItem);
        updateUnansweredList();
        
        addMessage(`
            <div style="background: rgba(255, 100, 0, 0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 100, 0, 0.3);">
                <p>😕 Je n'ai pas trouvé de diagnostic pour ce problème dans ma base de données.</p>
                <p style="margin-top: 10px;">✨ <strong>Votre question a été enregistrée</strong> et sera utilisée pour enrichir la base de données.</p>
                <p style="margin-top: 10px; font-size: 14px;">💡 Conseils en attendant :</p>
                <ul style="margin: 5px 0 0 20px; font-size: 14px;">
                    <li>Consultez un professionnel pour un diagnostic précis</li>
                    <li>Notez tous les symptômes observés</li>
                    <li>Vérifiez les niveaux de fluides</li>
                </ul>
            </div>
        `, false, { source: 'pending' });
    }
    
    updateStats();
}

function updateStats() {
    document.getElementById('stat-diagnostics').textContent = Object.keys(appState.database).length;
    document.getElementById('stat-questions').textContent = appState.totalQuestions;
    document.getElementById('stat-unanswered').textContent = appState.unansweredQuestions.length;
    document.getElementById('stat-contributions').textContent = appState.contributions.length;
}

function updateUnansweredList() {
    const listDiv = document.getElementById('unanswered-list');
    
    if (appState.unansweredQuestions.length === 0) {
        listDiv.innerHTML = '<p style="text-align: center; color: #666; font-size: 14px;">Aucune question en attente</p>';
        return;
    }
    
    const sorted = [...appState.unansweredQuestions].sort((a, b) => b.count - a.count);
    
    listDiv.innerHTML = sorted.map(item => `
        <div class="unanswered-item" onclick="selectQuestion('${item.id}')" style="background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 10px; cursor: pointer; margin-bottom: 10px;">
            <div style="font-size: 14px; margin-bottom: 5px;">${item.question}</div>
            <div style="font-size: 12px; color: #666; display: flex; justify-content: space-between;">
                <span>Posée ${item.count} fois</span>
                <span>${new Date(item.timestamp).toLocaleDateString()}</span>
            </div>
        </div>
    `).join('');
}

function showContributeModal() {
    document.getElementById('contribute-modal').classList.add('active');
}

function hideContributeModal() {
    document.getElementById('contribute-modal').classList.remove('active');
}

function saveConfig() {
    showNotification('Configuration sauvegardée');
}

function exportUnansweredQuestions() {
    const data = {
        exportDate: new Date().toISOString(),
        unansweredQuestions: appState.unansweredQuestions,
        contributions: appState.contributions,
        statistics: {
            totalQuestions: appState.totalQuestions,
            unansweredCount: appState.unansweredQuestions.length,
            contributionsCount: appState.contributions.length
        }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `botia-diagnostic-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showNotification('📥 Export JSON téléchargé');
}

function generateGitHubIssue() {
    showNotification('🐙 Fonctionnalité GitHub en développement');
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    addMessage(`
        <h3 style="margin-top: 0;">👋 Bienvenue sur BotIA Diagnostic Auto !</h3>
        <p>Je suis votre assistant IA intelligent qui s'améliore grâce à vos questions.</p>
        <div style="margin: 15px 0; padding: 15px; background: rgba(102, 126, 234, 0.1); border-radius: 10px; border: 1px solid rgba(102, 126, 234, 0.3);">
            <p style="margin: 0;"><strong>🧠 Comment ça marche :</strong></p>
            <ul style="margin: 10px 0 0 20px; font-size: 14px;">
                <li>Je cherche d'abord dans ma base de données locale</li>
                <li>Si je ne trouve pas, votre question enrichit mon apprentissage</li>
                <li>Les contributeurs peuvent ensuite ajouter des réponses</li>
                <li>Mon intelligence s'améliore continuellement !</li>
            </ul>
        </div>
        <p>Décrivez votre problème automobile et contribuons ensemble ! 🚗🤖</p>
    `);
    
    document.getElementById('chat-input').focus();
    updateStats();
    
    console.log('🤖 BotIA Diagnostic Auto initialisé avec succès !');
});
