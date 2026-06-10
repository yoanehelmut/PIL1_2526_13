// socket-chat.js - Version simplifiée pour démo
const socket = io('http://127.0.0.1:5000', {
    withCredentials: true
});

let conversations = [
    {
        id: 1, nom: "Kofi Mensah", avatar: "👨‍", statut: "En ligne",
        messages: [
            { contenu: "Bonjour ! Je suis disponible pour t'aider en Python.", expediteur_id: 2, expediteur_nom: "Kofi", timestamp: "10:30" },
            { contenu: "Super ! Je voudrais comprendre les listes.", expediteur_id: 1, expediteur_nom: "Moi", timestamp: "10:32" },
        ],
        unread: true
    },
    {
        id: 2, nom: "Aïcha Traoré", avatar: "👩‍💻", statut: "Hors ligne",
        messages: [
            { contenu: "Tu peux m'expliquer les jointures SQL ?", expediteur_id: 1, expediteur_nom: "Moi", timestamp: "Hier" },
        ],
        unread: false
    }
];

let convActive = null;

document.addEventListener('DOMContentLoaded', () => {
    // Charger les conversations
    renderConvList();

    // Gestion envoi
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    
    if (sendBtn && messageInput) {
        sendBtn.addEventListener('click', envoyerMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') envoyerMessage();
        });
    }

    // Réception temps réel
    socket.on('receive_message', (data) => {
        if (convActive && convActive.id === data.conversation_id) {
            ajouterMessage(data.contenu, 'received', data.expediteur_nom);
        }
    });
});

function renderConvList() {
    const list = document.getElementById('convList');
    if (!list) return;
    
    list.innerHTML = '';
    conversations.forEach(c => {
        const item = document.createElement('div');
        item.className = 'conv-item' + (convActive && convActive.id === c.id ? ' active' : '');
        
        const lastMsg = c.messages && c.messages.length > 0 
            ? c.messages[c.messages.length - 1].contenu 
            : 'Aucun message';
        
        item.innerHTML = `
            <div class="conv-avatar">${c.avatar || '👤'}</div>
            <div class="conv-info">
                <h4>${c.nom}</h4>
                <p>${lastMsg}</p>
            </div>
            ${c.unread ? '<div class="notif-dot"></div>' : ''}
        `;
        
        item.onclick = () => openConv(c);
        list.appendChild(item);
    });
}

function openConv(conv) {
    convActive = conv;
    conv.unread = false;
    renderConvList();

    document.getElementById('emptyState').style.display = 'none';
    const chatContent = document.getElementById('chatContent');
    chatContent.style.display = 'flex';
    chatContent.style.flexDirection = 'column';

    document.getElementById('chatHeader').innerHTML = `
        <div class="conv-avatar">${conv.avatar || '👤'}</div>
        <div class="chat-header-info">
            <h4>${conv.nom}</h4>
            <p>${conv.statut || 'En ligne'}</p>
        </div>
    `;

    socket.emit('join_chat', { conversation_id: conv.id });

    const messagesArea = document.getElementById('messagesArea');
    messagesArea.innerHTML = '';
    
    if (conv.messages) {
        conv.messages.forEach(m => {
            ajouterMessage(m.contenu, 'received', m.expediteur_nom);
        });
    }
}

function ajouterMessage(contenu, type, senderName) {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;
    
    const div = document.createElement('div');
    div.className = `msg-bubble ${type}`;
    
    const now = new Date();
    const time = now.getHours() + ':' + String(now.getMinutes()).padStart(2, '0');
    
    div.innerHTML = `${contenu}<span class="msg-time">${time}</span>`;
    messagesArea.appendChild(div);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function envoyerMessage() {
    if (!convActive) return;
    
    const messageInput = document.getElementById('messageInput');
    const contenu = messageInput.value.trim();
    
    if (!contenu) return;
    
    socket.emit('send_message', {
        conversation_id: convActive.id,
        expediteur_id: 1,
        expediteur_nom: "Moi",
        contenu: contenu
    });
    
    ajouterMessage(contenu, 'sent', 'Moi');
    convActive.messages.push({
        contenu: contenu,
        expediteur_id: 1,
        expediteur_nom: 'Moi'
    });
    
    messageInput.value = '';
    renderConvList();
}