// Variables to track game stats
let counter = 0;  // Current cookie count
let clicks = [];  // Array to store click timestamps
let totalClicks = 0;  // Total clicks since start

// Image arrays
const scaryImages = [
    'https://i1.sndcdn.com/artworks-tdOaaXXZ26uFxLIS-uefmWw-t500x500.jpg',
    'https://i.ytimg.com/vi/RNoHcWE8tbQ/maxresdefault.jpg',
    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSarr2_v6UOnGDJ1jVmnBdvXARTz2blzWZ3stGzRBJi2zwQ6HKGDauuY-0&s',
    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQwI_MVsbpKFHisFe4Ifpi_-tGFrHL2l6cHytWHiKZGhxIhSBFJ2yAB_UPEj1CrfNQIINM&usqp=CAU',
    'https://play-lh.googleusercontent.com/qBiLTYKuDA9aecK01rKoBYMp19lLOSq3xJvLkjTxlLCOJ_blR9ZPvBUblRaKFbDQ8P29'
];

// Update time
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = 
        `System Time: ${now.toLocaleTimeString()} | Hack Progress: ${Math.floor(Math.random() * 100)}%`;
}

// Update view count
function updateViewCount() {
    const viewCount = document.getElementById('viewCount');
    const currentCount = parseInt(localStorage.getItem('viewCount') || '0');
    localStorage.setItem('viewCount', currentCount + 1);
    viewCount.textContent = currentCount + 1;
}

// Panic button functionality
function panicMode() {
    alert('EMERGENCY! SYSTEM SELF-DESTRUCT INITIATED!');
    document.body.style.animation = 'shake 0.5s infinite';
    setTimeout(() => {
        document.body.style.animation = '';
        alert('Just kidding 😄');
    }, 2000);
}

// Set random scary image
function setRandomScaryImage() {
    try {
        const randomIndex = Math.floor(Math.random() * scaryImages.length);
        const hackerImage = document.getElementById('hackerImage');
        console.log('Setting image:', scaryImages[randomIndex]); // Debug log
        if (hackerImage) {
            hackerImage.src = scaryImages[randomIndex];
            hackerImage.style.display = 'block';
            hackerImage.onerror = () => {
                console.error('Failed to load image:', scaryImages[randomIndex]);
                hackerImage.src = scaryImages[0]; // Fallback to first image
            };
        } else {
            console.error('hackerImage element not found');
        }
    } catch (error) {
        console.error('Error in setRandomScaryImage:', error);
    }
}

// Countdown timer functionality
function startCountdown() {
    let hours = 2;
    let minutes = 0;
    let seconds = 0;
    
    function updateCountdown() {
        if (seconds > 0) {
            seconds--;
        } else if (minutes > 0) {
            minutes--;
            seconds = 59;
        } else if (hours > 0) {
            hours--;
            minutes = 59;
            seconds = 59;
        }
        
        const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('countdown').textContent = formattedTime;
    }
    
    setInterval(updateCountdown, 1000);
}

// Update encryption progress
function updateEncryptionProgress() {
    let progress = 0;
    const progressElement = document.getElementById('encryptionProgress');
    
    function increment() {
        if (progress < 100) {
            progress += Math.floor(Math.random() * 5);
            if (progress > 100) progress = 100;
            progressElement.textContent = progress;
            
            if (progress < 100) {
                setTimeout(increment, Math.random() * 2000 + 1000);
            }
        }
    }
    
    increment();
}

// Simulate system information
function setSystemInfo() {
    // Set Berkeley IP address (UC Berkeley's IP range)
    document.getElementById('ipAddress').textContent = `128.32.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`;
    
    // Set Berkeley location
    document.getElementById('location').textContent = 'Berkeley, California, US';
    
    // Set random device info
    const devices = ['Windows NT 10.0', 'MacOS 11.6.2', 'Linux Ubuntu 20.04', 'iOS 15.2', 'Android 12'];
    document.getElementById('device').textContent = devices[Math.floor(Math.random() * devices.length)];
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('DOM Content Loaded'); // Debug log
        setRandomScaryImage();
        updateViewCount();
        startCountdown();
        updateEncryptionProgress();
        setSystemInfo();
        setInterval(updateTime, 1000);
        
        const panicButton = document.getElementById('panicButton');
        
        if (panicButton) {
            panicButton.addEventListener('click', panicMode);
        } else {
            console.error('Panic button not found');
        }
        
        const hackerText = document.getElementById('hackerText');
        if (hackerText) {
            setInterval(() => {
                const messages = [
                    'Extracting sensitive data...',
                    'Bypassing security...',
                    'Corrupting files...',
                    'Disabling antivirus...',
                    'Uploading personal data...'
                ];
                hackerText.textContent = messages[Math.floor(Math.random() * messages.length)];
            }, 2000);
        }
    } catch (error) {
        console.error('Error in initialization:', error);
    }
}); 