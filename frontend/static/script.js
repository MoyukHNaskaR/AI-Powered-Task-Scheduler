// index.html logic
const userForm = document.getElementById('userForm');
if (userForm) {
    ['brain', 'body'].forEach(type => {
        const ratingContainer = document.getElementById(`${type}-rating`);
        const inputField = document.getElementById(`${type}_stamina`);
        
        if (ratingContainer) {
            const stars = ratingContainer.querySelectorAll('span');
            updateStars(stars, 3);
            
            stars.forEach(star => {
                star.addEventListener('click', () => {
                    const val = star.getAttribute('data-val');
                    inputField.value = val;
                    updateStars(stars, val);
                });
            });
        }
    });

    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('name').value;
        const brain = document.getElementById('brain_stamina').value;
        const body = document.getElementById('body_stamina').value;
        
        const res = await fetch('/api/user', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, brain_stamina: brain, body_stamina: body })
        });
        
        if (res.ok) {
            window.location.href = '/tasks';
        }
    });
}

function updateStars(stars, val) {
    stars.forEach(s => {
        if (s.getAttribute('data-val') <= val) {
            s.classList.add('active');
            s.style.color = '#f59e0b';
        } else {
            s.classList.remove('active');
            s.style.color = '#ccc';
        }
    });
}

// tasks.html logic
function addTaskRow() {
    const tbody = document.getElementById('taskBody');
    if (!tbody) return;
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="task-name" placeholder="e.g. Study AI" required></td>
        <td><input type="number" class="task-duration" placeholder="e.g. 60" min="1" required></td>
        <td><input type="number" class="task-deadline" placeholder="e.g. 120" min="1"></td>
        <td><button class="delete-btn" onclick="this.closest('tr').remove()">X</button></td>
    `;
    tbody.appendChild(tr);
}

async function submitTasks() {
    const rows = document.querySelectorAll('#taskBody tr');
    const tasks = [];
    
    rows.forEach(row => {
        const name = row.querySelector('.task-name').value;
        const duration = row.querySelector('.task-duration').value;
        const deadline = row.querySelector('.task-deadline').value;
        
        if (name && duration) {
            const taskObj = { name, duration: parseInt(duration) };
            if (deadline) taskObj.deadline = parseInt(deadline);
            tasks.push(taskObj);
        }
    });
    
    if (tasks.length === 0) {
        alert("Please add at least one task!");
        return;
    }
    
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';
    
    const loadingTexts = ["Analyzing tasks...", "Connecting to LLM...", "Calculating optimal schedule..."];
    let textIndex = 0;
    const textEl = document.getElementById('loadingText');
    const interval = setInterval(() => {
        textIndex = (textIndex + 1) % loadingTexts.length;
        textEl.innerText = loadingTexts[textIndex];
    }, 1500);
    
    try {
        await fetch('/api/tasks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ tasks })
        });
        
        const res = await fetch('/api/schedule', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (res.ok) {
            window.location.href = '/results';
        } else {
            alert("Failed to schedule.");
            overlay.style.display = 'none';
        }
    } catch (e) {
        console.error(e);
        alert("An error occurred.");
        overlay.style.display = 'none';
    } finally {
        clearInterval(interval);
    }
}

// results.html logic
async function fetchResults() {
    if (!document.getElementById('timelineContainer')) return;
    
    const res = await fetch('/api/results');
    if (!res.ok) {
        window.location.href = '/tasks';
        return;
    }
    
    const data = await res.json();
    
    document.getElementById('totalTime').innerText = data.total_time;
    document.getElementById('missedCount').innerText = data.misses;
    document.getElementById('finalBrain').innerText = data.final_brain_fatigue.toFixed(1);
    document.getElementById('finalBody').innerText = data.final_body_fatigue.toFixed(1);
    
    document.getElementById('brainProgress').style.width = `${Math.min(100, data.final_brain_fatigue)}%`;
    document.getElementById('bodyProgress').style.width = `${Math.min(100, data.final_body_fatigue)}%`;
    
    document.getElementById('logsContent').innerText = data.logs.join('\n\n');
    
    const container = document.getElementById('timelineContainer');
    container.innerHTML = '';
    
    data.timeline.forEach(item => {
        const div = document.createElement('div');
        div.className = 'timeline-item';
        if (item.type === 'rest') div.classList.add('rest');
        if (item.missed_deadline) div.classList.add('missed');
        
        div.innerHTML = `
            <div class="timeline-time">${item.start} - ${item.end} min</div>
            <div class="timeline-title">${item.name}</div>
            <div class="timeline-meta">Type: ${item.type} ${item.missed_deadline ? '<span style="color:red;font-weight:bold;">(Missed Deadline)</span>' : ''}</div>
        `;
        container.appendChild(div);
    });
}

function showLogs() {
    const el = document.getElementById('logsModal');
    if(el) el.style.display = 'flex';
}

function closeLogs() {
    const el = document.getElementById('logsModal');
    if(el) el.style.display = 'none';
}
