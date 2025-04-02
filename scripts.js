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

    // Initialize habit heatmaps
    initHabitTrackers();
    
    // Load habit data from localStorage
    loadHabitData();
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

// Habit tracking functionality
// Initialize habit tracker
function initHabitTrackers() {
    const habits = ['meditation', 'exercise', 'reading'];
    const today = new Date();
    
    habits.forEach(habit => {
        const heatmapEl = document.getElementById(`${habit}-heatmap`);
        if (!heatmapEl) return;
        
        // Generate cells for the past 90 days
        for (let i = 89; i >= 0; i--) {
            const date = new Date();
            date.setDate(today.getDate() - i);
            
            const dayEl = document.createElement('div');
            dayEl.className = 'habit-day level-0';
            dayEl.title = formatDate(date);
            dayEl.dataset.date = formatDate(date, 'yyyy-MM-dd');
            dayEl.dataset.habit = habit;
            
            // Add click event to manually toggle status
            dayEl.addEventListener('click', function() {
                toggleHabitDay(this);
            });
            
            heatmapEl.appendChild(dayEl);
        }
    });
}

// Load habit data
function loadHabitData() {
    const habits = ['meditation', 'exercise', 'reading'];
    
    habits.forEach(habit => {
        // Read data from localStorage
        const habitData = JSON.parse(localStorage.getItem(`habit_${habit}`)) || {
            days: {},
            streak: 0,
            longestStreak: 0,
            totalCount: 0,
            totalMinutes: 0
        };
        
        // Update UI
        updateHabitStats(habit, habitData);
        
        // Update heatmap
        for (const date in habitData.days) {
            const level = getActivityLevel(habitData.days[date].minutes);
            const dayEl = document.querySelector(`.habit-day[data-date="${date}"][data-habit="${habit}"]`);
            if (dayEl) {
                dayEl.className = `habit-day level-${level}`;
            }
        }
    });
}

// Log habit
function logHabit(habit) {
    const today = formatDate(new Date(), 'yyyy-MM-dd');
    
    // Get current habit data
    const habitData = JSON.parse(localStorage.getItem(`habit_${habit}`)) || {
        days: {},
        streak: 0,
        longestStreak: 0,
        totalCount: 0,
        totalMinutes: 0
    };
    
    // Prompt user to input duration
    const minutes = parseInt(prompt(`Enter ${getHabitName(habit)} duration (minutes):`, "30"));
    if (isNaN(minutes) || minutes <= 0) return;
    
    // Update today's record
    habitData.days[today] = {
        minutes: minutes,
        timestamp: new Date().toISOString()
    };
    
    // Calculate streak
    updateStreaks(habitData);
    
    // Update total data
    habitData.totalCount = Object.keys(habitData.days).length;
    habitData.totalMinutes += minutes;
    
    // Save to localStorage
    localStorage.setItem(`habit_${habit}`, JSON.stringify(habitData));
    
    // Update UI
    updateHabitStats(habit, habitData);
    
    // Update heatmap
    const level = getActivityLevel(minutes);
    const dayEl = document.querySelector(`.habit-day[data-date="${today}"][data-habit="${habit}"]`);
    if (dayEl) {
        dayEl.className = `habit-day level-${level}`;
    }
}

// Toggle habit day status
function toggleHabitDay(dayEl) {
    const habit = dayEl.dataset.habit;
    const date = dayEl.dataset.date;
    
    // Get current habit data
    const habitData = JSON.parse(localStorage.getItem(`habit_${habit}`)) || {
        days: {},
        streak: 0,
        longestStreak: 0,
        totalCount: 0,
        totalMinutes: 0
    };
    
    // If the date exists, delete it; otherwise add it
    if (habitData.days[date]) {
        habitData.totalMinutes -= habitData.days[date].minutes;
        delete habitData.days[date];
        dayEl.className = 'habit-day level-0';
    } else {
        const minutes = parseInt(prompt(`Enter ${getHabitName(habit)} duration (minutes):`, "30"));
        if (isNaN(minutes) || minutes <= 0) return;
        
        habitData.days[date] = {
            minutes: minutes,
            timestamp: new Date().toISOString()
        };
        
        habitData.totalMinutes += minutes;
        
        const level = getActivityLevel(minutes);
        dayEl.className = `habit-day level-${level}`;
    }
    
    // Update statistics
    habitData.totalCount = Object.keys(habitData.days).length;
    updateStreaks(habitData);
    
    // Save to localStorage
    localStorage.setItem(`habit_${habit}`, JSON.stringify(habitData));
    
    // Update UI
    updateHabitStats(habit, habitData);
}

// Update habit statistics
function updateHabitStats(habit, data) {
    document.getElementById(`${habit}-streak`).textContent = data.longestStreak;
    document.getElementById(`${habit}-current`).textContent = data.streak;
    document.getElementById(`${habit}-total`).textContent = data.totalCount;
    
    const avgMinutes = data.totalCount > 0 ? (data.totalMinutes / data.totalCount).toFixed(2) : "0.00";
    document.getElementById(`${habit}-avg`).textContent = avgMinutes;
}

// Calculate consecutive days
function updateStreaks(habitData) {
    const dates = Object.keys(habitData.days).sort();
    if (dates.length === 0) {
        habitData.streak = 0;
        habitData.longestStreak = 0;
        return;
    }
    
    // Calculate current streak
    let currentStreak = 1;
    const today = formatDate(new Date(), 'yyyy-MM-dd');
    const yesterday = formatDate(new Date(Date.now() - 86400000), 'yyyy-MM-dd');
    
    // Check if there's a record for today or yesterday, if not the streak is 0
    if (!habitData.days[today] && !habitData.days[yesterday]) {
        habitData.streak = 0;
    } else {
        // If there's a record for today, start counting from today
        // If no record for today but there's one for yesterday, start from yesterday
        const startDate = habitData.days[today] ? today : yesterday;
        const startIdx = dates.indexOf(startDate);
        
        if (startIdx >= 0) {
            for (let i = startIdx; i > 0; i--) {
                const currentDate = new Date(dates[i]);
                const prevDate = new Date(dates[i-1]);
                
                // Check if the dates are consecutive
                const diffDays = Math.round((currentDate - prevDate) / (1000 * 60 * 60 * 24));
                if (diffDays === 1) {
                    currentStreak++;
                } else {
                    break;
                }
            }
        }
        
        habitData.streak = currentStreak;
    }
    
    // Update longest streak
    if (currentStreak > habitData.longestStreak) {
        habitData.longestStreak = currentStreak;
    }
}

// Get activity level based on duration
function getActivityLevel(minutes) {
    if (minutes < 15) return 1;
    if (minutes < 30) return 2;
    if (minutes < 60) return 3;
    return 4;
}

// Get habit name in English
function getHabitName(habit) {
    const names = {
        'meditation': 'Meditation',
        'exercise': 'Exercise',
        'reading': 'Reading'
    };
    return names[habit] || habit;
}

// Format date in English
function formatDate(date, format = 'MMM dd, yyyy') {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    if (format === 'yyyy-MM-dd') {
        return `${year}-${month}-${day}`;
    }
    
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthName = months[date.getMonth()];
    
    return `${monthName} ${day}, ${year}`;
} 