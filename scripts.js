// Firebase initialization (should be updated with your Firebase config)
const firebaseConfig = {
    apiKey: "AIzaSyBHPRWuP6wg4hNZx1wm-5k1zv9yGtGFEME",
    authDomain: "personal-website-efcd6.firebaseapp.com",
    databaseURL: "https://personal-website-efcd6-default-rtdb.firebaseio.com",
    projectId: "personal-website-efcd6",
    storageBucket: "personal-website-efcd6.appspot.com",
    messagingSenderId: "538307028479",
    appId: "1:538307028479:web:8acbd8d2c5c9c25d74dc38"
};

// Initialize Firebase
if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
    
    // Update visitor counter
    const database = firebase.database();
    const visitorCountRef = database.ref('visitorCount');
    
    visitorCountRef.transaction(function(currentCount) {
        return (currentCount || 0) + 1;
    });
    
    visitorCountRef.on('value', function(snapshot) {
        const count = snapshot.val() || 0;
        document.getElementById('visitorCount').textContent = count;
    });
}

// Theme Toggling
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const themeButton = document.querySelector('.theme-switch');
    if (newTheme === 'dark') {
        themeButton.textContent = '☀️ Light Mode';
    } else {
        themeButton.textContent = '🌙 Dark Mode';
    }
}

// Check for saved theme preference
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const html = document.documentElement;
    html.setAttribute('data-theme', savedTheme);
    
    const themeButton = document.querySelector('.theme-switch');
    if (savedTheme === 'dark') {
        themeButton.textContent = '☀️ Light Mode';
    } else {
        themeButton.textContent = '🌙 Dark Mode';
    }
    
    // Adding blinking cursor animation
    setInterval(() => {
        const cursors = document.querySelectorAll('.cursor-blink');
        cursors.forEach(cursor => {
            cursor.style.visibility = cursor.style.visibility === 'hidden' ? 'visible' : 'hidden';
        });
    }, 500);

    // Add typing effect to terminal titles
    addTypingEffect();
});

// Message system functionality
function showMessageDialog() {
    document.getElementById('messageDialog').style.display = 'flex';
}

function hideMessageDialog() {
    document.getElementById('messageDialog').style.display = 'none';
    document.getElementById('messageArea').style.display = 'none';
    document.getElementById('clearAllBtn').style.display = 'none';
    document.getElementById('password').value = '';
}

// Close dialog when clicking outside
window.addEventListener('click', function(event) {
    const dialog = document.getElementById('messageDialog');
    if (event.target === dialog) {
        hideMessageDialog();
    }
});

// Password verification for viewing messages
function checkPassword() {
    const password = document.getElementById('password').value;
    // Simple password check - in a real app, use secure authentication
    if (password === 'admin123') {
        loadMessages();
        document.getElementById('messageArea').style.display = 'block';
        document.getElementById('clearAllBtn').style.display = 'block';
    } else {
        alert('Authentication failed. Access denied.');
    }
}

// Load messages from Firebase
function loadMessages() {
    if (typeof firebase !== 'undefined') {
        const messagesRef = firebase.database().ref('messages');
        const messageArea = document.getElementById('messageArea');
        messageArea.innerHTML = '<h3>Messages:</h3>';
        
        messagesRef.once('value', function(snapshot) {
            const messages = snapshot.val();
            if (messages) {
                Object.keys(messages).forEach(key => {
                    const message = messages[key];
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message-item';
                    messageElement.innerHTML = `
                        <p><strong>${message.author}</strong>: ${message.text}</p>
                        <p class="message-date">${new Date(message.timestamp).toLocaleString()}</p>
                        <button onclick="deleteMessage('${key}')">Delete</button>
                    `;
                    messageArea.appendChild(messageElement);
                });
            } else {
                messageArea.innerHTML += '<p>No messages yet.</p>';
            }
        });
    }
}

// Send a new message
function sendMessage() {
    const authorInput = document.getElementById('messageAuthor');
    const textInput = document.getElementById('messageText');
    
    const author = authorInput.value.trim();
    const text = textInput.value.trim();
    
    if (!author || !text) {
        alert('Please enter your name and message.');
        return;
    }
    
    if (typeof firebase !== 'undefined') {
        const messagesRef = firebase.database().ref('messages');
        const newMessage = {
            author: author,
            text: text,
            timestamp: Date.now()
        };
        
        messagesRef.push(newMessage)
            .then(() => {
                authorInput.value = '';
                textInput.value = '';
                alert('Message sent successfully!');
            })
            .catch(error => {
                console.error('Error sending message:', error);
                alert('Error sending message. Please try again.');
            });
    }
}

// Delete a specific message
function deleteMessage(messageId) {
    if (typeof firebase !== 'undefined') {
        const messageRef = firebase.database().ref('messages/' + messageId);
        messageRef.remove()
            .then(() => {
                loadMessages();
            })
            .catch(error => {
                console.error('Error deleting message:', error);
                alert('Error deleting message. Please try again.');
            });
    }
}

// Clear all messages
function clearAllMessages() {
    if (typeof firebase !== 'undefined') {
        const messagesRef = firebase.database().ref('messages');
        if (confirm('Are you sure you want to delete ALL messages?')) {
            messagesRef.remove()
                .then(() => {
                    document.getElementById('messageArea').innerHTML = '<h3>Messages:</h3><p>No messages yet.</p>';
                })
                .catch(error => {
                    console.error('Error clearing messages:', error);
                    alert('Error clearing messages. Please try again.');
                });
        }
    }
}

// Add terminal typing effect
function addTypingEffect() {
    const terminalTitles = document.querySelectorAll('.terminal-title');
    
    terminalTitles.forEach(title => {
        const text = title.textContent;
        title.textContent = '';
        
        let i = 0;
        const typing = setInterval(() => {
            if (i < text.length) {
                title.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(typing);
            }
        }, 50);
    });
} 