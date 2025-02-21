// Variables to track game stats
let counter = 0;  // Current cookie count
let clicks = [];  // Array to store click timestamps
let totalClicks = 0;  // Total clicks since start
let bestCPS = localStorage.getItem('bestCPS') || 0;

// Initialize best CPS display
document.getElementById('bestCPS').textContent = bestCPS;

// Function that runs when cookie is clicked
function addOneToCounter(event) {
    counter++;
    totalClicks++;
    document.getElementById("counter").textContent = counter;
    document.getElementById("totalClicks").textContent = totalClicks;
    
    const now = Date.now();
    clicks.push(now);
    updateClicksPerSecond();
    
    // Add click effect
    createClickEffect(event);
}

function updateClicksPerSecond() {
    const now = Date.now();
    clicks = clicks.filter(time => now - time < 1000);
    const cps = clicks.length;
    document.getElementById("clicksPerSecond").textContent = cps;
    
    // 更新最快点击速度记录
    if (cps > bestCPS) {
        bestCPS = cps;
        localStorage.setItem('bestCPS', bestCPS);
        document.getElementById('bestCPS').textContent = bestCPS;
    }
}

function handleTouch(event) {
    event.preventDefault();
    event.stopPropagation();
    addOneToCounter(event);
    return false;
}

function createClickEffect(event) {
    const effect = document.createElement('div');
    effect.innerText = '+1';
    effect.style.position = 'absolute';
    effect.style.left = (event.pageX - 10) + 'px';
    effect.style.top = (event.pageY - 10) + 'px';
    effect.style.color = '#d2691e';
    effect.style.fontSize = '20px';
    effect.style.pointerEvents = 'none';
    effect.style.userSelect = 'none';
    effect.style.animation = 'fadeUp 0.5s ease-out';
    
    document.body.appendChild(effect);
    
    setTimeout(() => {
        document.body.removeChild(effect);
    }, 500);
}

// Add animation style
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeUp {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(style);

// 每秒更新点击速度
setInterval(updateClicksPerSecond, 100);