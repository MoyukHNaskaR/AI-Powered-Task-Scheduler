from flask import Flask, request, jsonify, render_template
from llm import categorize_task
from scheduler import TaskScheduler

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

current_scheduler = None
tasks_backlog = []


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks')
def tasks_page():
    return render_template('tasks.html')

@app.route('/results')
def results_page():
    return render_template('results.html')


@app.route('/api/user', methods=['POST'])
def set_user():
    global current_scheduler, tasks_backlog
    data = request.json
    name = data.get('name', 'User')
    brain_stamina = int(data.get('brain_stamina', 3))
    body_stamina = int(data.get('body_stamina', 3))

    current_scheduler = TaskScheduler(name, brain_stamina, body_stamina)
    tasks_backlog = []
    return jsonify({"status": "success"})

@app.route('/api/tasks', methods=['POST'])
def add_tasks():
    global tasks_backlog
    data = request.json
    new_tasks = data.get('tasks', [])

    analyzed_tasks = []
    for t in new_tasks:
        cat = categorize_task(t['name'])
        t['type'] = cat['type']
        t['intensity'] = cat['intensity']
        t['duration'] = int(t['duration'])
        if t.get('deadline'):
            t['deadline'] = int(t['deadline'])
        t['id'] = len(tasks_backlog) + len(analyzed_tasks) + 1
        analyzed_tasks.append(t)

    tasks_backlog.extend(analyzed_tasks)
    return jsonify({"status": "success", "tasks": analyzed_tasks})

@app.route('/api/schedule', methods=['POST'])
def run_scheduler():
    global current_scheduler, tasks_backlog
    if not current_scheduler:
        return jsonify({"error": "User not set"}), 400

    current_scheduler.schedule(tasks_backlog)
    return jsonify({"status": "success"})

@app.route('/api/results', methods=['GET'])
def get_results():
    global current_scheduler
    if not current_scheduler:
        return jsonify({"error": "No data"}), 400

    return jsonify({
        "timeline": current_scheduler.timeline,
        "logs": current_scheduler.logs,
        "final_brain_fatigue": current_scheduler.brain_fatigue,
        "final_body_fatigue": current_scheduler.body_fatigue,
        "total_time": current_scheduler.current_time,
        "misses": sum(1 for t in current_scheduler.timeline if t.get('missed_deadline'))
    })


if __name__ == '__main__':
    app.run(debug=False, port=5000)
