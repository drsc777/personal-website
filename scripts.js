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
        
        // Clear existing content
        heatmapEl.innerHTML = '';
        
        // 创建GitHub风格的日历布局
        const calendarEl = document.createElement('div');
        calendarEl.className = 'habit-calendar';
        
        // 计算一年需要多少周（52周）
        const totalWeeks = 52;
        
        // 添加周行用于网格布局（52周 = 一年）
        const weeks = [];
        for (let w = 0; w < totalWeeks; w++) {
            const weekEl = document.createElement('div');
            weekEl.className = 'calendar-week';
            weeks.push(weekEl);
            calendarEl.appendChild(weekEl);
        }
        
        // 生成过去一年的单元格
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        oneYearAgo.setDate(today.getDate() + 1);
        
        // 计算天数
        const daysBetween = Math.floor((today.getTime() - oneYearAgo.getTime()) / (1000 * 3600 * 24));
        
        // 从一年前开始生成日期
        for (let i = 0; i <= daysBetween; i++) {
            const date = new Date(oneYearAgo);
            date.setDate(oneYearAgo.getDate() + i);
            
            const dayEl = document.createElement('div');
            dayEl.className = 'habit-day level-0';
            dayEl.title = formatDate(date);
            dayEl.dataset.date = formatDate(date, 'yyyy-MM-dd');
            dayEl.dataset.habit = habit;
            
            // 确定这一天属于哪一周
            // 将一年的天数平均分配到52周
            const weekIndex = Math.floor(i * totalWeeks / daysBetween);
            
            // 添加点击事件以手动切换状态
            dayEl.addEventListener('click', function() {
                toggleHabitDay(this);
            });
            
            // 添加到适当的周
            if (weeks[weekIndex]) {
                weeks[weekIndex].appendChild(dayEl);
            }
        }
        
        heatmapEl.appendChild(calendarEl);
        
        // 添加调试信息
        console.log(`初始化 ${habit} 热图，创建了 ${daysBetween} 天的数据`);
    });
}

// Load habit data
function loadHabitData() {
    const habits = ['meditation', 'exercise', 'reading'];
    
    habits.forEach(habit => {
        // Get saved data from localStorage
        let data = localStorage.getItem(`habit_${habit}`);
        
        if (data) {
            data = JSON.parse(data);
            
            // Update heatmap UI (work with both old and new class names)
            Object.keys(data.days).forEach(dateStr => {
                // Try both selectors to handle both old and new layouts
                const dayEl = document.querySelector(`.calendar-day.habit-day[data-date="${dateStr}"][data-habit="${habit}"]`) || 
                             document.querySelector(`.habit-day[data-date="${dateStr}"][data-habit="${habit}"]`);
                
                if (dayEl) {
                    const level = getActivityLevel(data.days[dateStr].minutes);
                    
                    // Update classes for both old and new layouts
                    if (dayEl.classList.contains('calendar-day')) {
                        dayEl.className = `calendar-day habit-day level-${level}`;
                    } else {
                        dayEl.className = `habit-day level-${level}`;
                    }
                    
                    // Add tooltip data
                    dayEl.dataset.count = data.days[dateStr].minutes;
                    dayEl.title = `${data.days[dateStr].minutes} minutes on ${formatDate(new Date(dateStr))}`;
                    
                    // Add journal entry if available
                    if (data.days[dateStr].journal) {
                        dayEl.dataset.journal = data.days[dateStr].journal;
                    }
                }
            });
            
            // Update streak and stats
            updateStreaks(data);
            updateHabitStats(habit, data);
        }
    });
}

// Log habit with modal interface
function logHabit(habit) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'habit-modal';
    
    // Format date for display
    const today = new Date();
    const dateValue = formatDate(today, 'yyyy-MM-dd');
    
    // Create modal content
    modal.innerHTML = `
        <div class="habit-modal-content">
            <div class="habit-modal-header">
                <h3>${getHabitName(habit)}</h3>
                <button class="habit-modal-close">esc</button>
            </div>
            <div class="habit-modal-body">
                <div class="habit-modal-row">
                    <label>Date:</label>
                    <input type="date" id="habit-date" value="${dateValue}">
                </div>
                <div class="habit-modal-row">
                    <label>Minutes:</label>
                    <input type="number" id="habit-minutes" value="30" min="1">
                </div>
                <div class="habit-modal-row">
                    <label>Journal entry:</label>
                    <textarea id="habit-journal" placeholder="Write about your ${getHabitName(habit).toLowerCase()} session..."></textarea>
                </div>
                <button class="habit-modal-save">Save</button>
            </div>
        </div>
    `;
    
    // Add modal to the page
    document.body.appendChild(modal);
    
    // Focus on minutes input
    setTimeout(() => document.getElementById('habit-minutes').focus(), 100);
    
    // Add event listeners
    const closeBtn = modal.querySelector('.habit-modal-close');
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    // Handle save button
    const saveBtn = modal.querySelector('.habit-modal-save');
    saveBtn.addEventListener('click', () => {
        const dateInput = document.getElementById('habit-date');
        const minutesInput = document.getElementById('habit-minutes');
        const journalInput = document.getElementById('habit-journal');
        
        const date = dateInput.value;
        const minutes = parseInt(minutesInput.value);
        const journal = journalInput.value.trim();
        
        if (isNaN(minutes) || minutes <= 0) {
            alert('Please enter a valid number of minutes');
            return;
        }
        
        // Get current habit data
        const habitData = JSON.parse(localStorage.getItem(`habit_${habit}`)) || {
            days: {},
            streak: 0,
            longestStreak: 0,
            totalCount: 0,
            totalMinutes: 0
        };
        
        // Check if this date already exists
        if (habitData.days[date]) {
            // Subtract previous minutes
            habitData.totalMinutes -= habitData.days[date].minutes;
        }
        
        // Update record for selected date
        habitData.days[date] = {
            minutes: minutes,
            timestamp: new Date().toISOString(),
            journal: journal
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
        const dayEl = document.querySelector(`.habit-day[data-date="${date}"][data-habit="${habit}"]`);
        if (dayEl) {
            dayEl.className = `habit-day level-${level}`;
        }
        
        // Close modal
        document.body.removeChild(modal);
    });
    
    // Handle keyboard events
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            document.body.removeChild(modal);
            document.removeEventListener('keydown', escHandler);
        }
    });
}

// Toggle habit day status using modal interface
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
    
    // If the date already exists, delete it
    if (habitData.days[date]) {
        if (confirm(`Remove ${getHabitName(habit)} entry for ${formatDate(new Date(date))}?`)) {
            habitData.totalMinutes -= habitData.days[date].minutes;
            delete habitData.days[date];
            dayEl.className = 'habit-day level-0';
            
            // Update statistics
            habitData.totalCount = Object.keys(habitData.days).length;
            updateStreaks(habitData);
            
            // Save to localStorage
            localStorage.setItem(`habit_${habit}`, JSON.stringify(habitData));
            
            // Update UI
            updateHabitStats(habit, habitData);
        }
        return;
    }
    
    // Otherwise show the logging modal with the selected date
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'habit-modal';
    
    // Parse date for the modal
    const selectedDate = new Date(date);
    const formattedDate = formatDate(selectedDate, 'MMM dd, yyyy');
    
    // Create modal content
    modal.innerHTML = `
        <div class="habit-modal-content">
            <div class="habit-modal-header">
                <h3>${getHabitName(habit)}</h3>
                <button class="habit-modal-close">esc</button>
            </div>
            <div class="habit-modal-body">
                <div class="habit-modal-row">
                    <label>Date:</label>
                    <input type="date" id="habit-date" value="${date}" readonly>
                </div>
                <div class="habit-modal-row">
                    <label>Minutes:</label>
                    <input type="number" id="habit-minutes" value="30" min="1">
                </div>
                <div class="habit-modal-row">
                    <label>Journal entry:</label>
                    <textarea id="habit-journal" placeholder="Write about your ${getHabitName(habit).toLowerCase()} session..."></textarea>
                </div>
                <button class="habit-modal-save">Save</button>
            </div>
        </div>
    `;
    
    // Add modal to the page
    document.body.appendChild(modal);
    
    // Focus on minutes input
    setTimeout(() => document.getElementById('habit-minutes').focus(), 100);
    
    // Add event listeners
    const closeBtn = modal.querySelector('.habit-modal-close');
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    // Handle save button
    const saveBtn = modal.querySelector('.habit-modal-save');
    saveBtn.addEventListener('click', () => {
        const dateInput = document.getElementById('habit-date');
        const minutesInput = document.getElementById('habit-minutes');
        const journalInput = document.getElementById('habit-journal');
        
        const entryDate = dateInput.value;
        const minutes = parseInt(minutesInput.value);
        const journal = journalInput.value.trim();
        
        if (isNaN(minutes) || minutes <= 0) {
            alert('Please enter a valid number of minutes');
            return;
        }
        
        // Update record for selected date
        habitData.days[entryDate] = {
            minutes: minutes,
            timestamp: new Date().toISOString(),
            journal: journal
        };
        
        // Update total data
        habitData.totalCount = Object.keys(habitData.days).length;
        habitData.totalMinutes += minutes;
        
        // Calculate streak
        updateStreaks(habitData);
        
        // Save to localStorage
        localStorage.setItem(`habit_${habit}`, JSON.stringify(habitData));
        
        // Update UI
        updateHabitStats(habit, habitData);
        
        // Update heatmap
        const level = getActivityLevel(minutes);
        dayEl.className = `habit-day level-${level}`;
        
        // Close modal
        document.body.removeChild(modal);
    });
    
    // Handle keyboard events
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            document.body.removeChild(modal);
            document.removeEventListener('keydown', escHandler);
        }
    });
}

// Update habit statistics
function updateHabitStats(habit, data) {
    const streakEl = document.getElementById(`${habit}-streak`);
    const currentEl = document.getElementById(`${habit}-current`);
    const totalEl = document.getElementById(`${habit}-total`);
    const avgEl = document.getElementById(`${habit}-avg`);
    
    // Only update if elements exist
    if (streakEl) streakEl.textContent = data.longestStreak || 0;
    if (currentEl) currentEl.textContent = data.currentStreak || 0;
    if (totalEl) totalEl.textContent = data.count || 0;
    if (avgEl) avgEl.textContent = data.avgMinutes ? data.avgMinutes.toFixed(2) : '0.00';
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