import heapq

INTENSITY_WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3
}

FATIGUE_CAP = 85.0        # max fatigue before we refuse to continue a task
FATIGUE_THRESHOLD = 70.0  # threshold for channel selection logic

def fatigue_rate(intensity, stamina):
    """Fatigue increase per minute of work."""
    return INTENSITY_WEIGHT.get(intensity, 2) / max(0.1, float(stamina))

def calculate_fatigue_increase(intensity, stamina, duration):
    return fatigue_rate(intensity, stamina) * duration

def clamp(value):
    return max(0.0, min(100.0, value))

class TaskScheduler:
    def __init__(self, user_name, brain_stamina, body_stamina):
        self.user_name = user_name
        self.brain_stamina = brain_stamina
        self.body_stamina = body_stamina
        
        self.current_time = 0
        self.brain_fatigue = 0.0
        self.body_fatigue = 0.0
        
        self.logs = []
        self.timeline = []
        
    def schedule(self, tasks):
        self.timeline = []
        self.logs = []
        self.current_time = 0
        self.brain_fatigue = 0.0
        self.body_fatigue = 0.0
        
        remaining_tasks = []
        for t in tasks:
            remaining_tasks.append(dict(t, remaining_duration=int(t["duration"])))
        
        max_iterations = len(remaining_tasks) * 20 + 50
        iteration = 0
        
        while remaining_tasks:
            iteration += 1
            if iteration > max_iterations:
                break
                
            if self.brain_fatigue > FATIGUE_THRESHOLD and self.body_fatigue > FATIGUE_THRESHOLD:
                self.rest()
                continue
                
            best_task = None
            
            deadline_tasks = [t for t in remaining_tasks if t.get("deadline")]
            no_deadline_tasks = [t for t in remaining_tasks if not t.get("deadline")]
            
            # --- DEADLINE TASKS FIRST (closest deadline wins) ---
            if deadline_tasks:
                best_score = -float('inf')
                for task in deadline_tasks:
                    time_left = task["deadline"] - self.current_time
                    urgency = 1000.0 + (1.0 / max(0.1, time_left + 1.0)) * 100.0
                    fp = self.brain_fatigue if task["type"] == "brain" else self.body_fatigue
                    score = urgency - (fp / 100.0)
                    if score > best_score:
                        best_score = score
                        best_task = task
            else:
                # --- NO DEADLINE: hardest first, alternate by least fatigued channel ---
                brain_ok = self.brain_fatigue < FATIGUE_THRESHOLD
                body_ok = self.body_fatigue < FATIGUE_THRESHOLD
                
                brain_tasks = [t for t in no_deadline_tasks if t["type"] == "brain"]
                body_tasks = [t for t in no_deadline_tasks if t["type"] == "body"]
                rest_tasks = [t for t in no_deadline_tasks if t["type"] == "rest"]
                
                intensity_order = {"high": 3, "medium": 2, "low": 1}
                brain_tasks.sort(key=lambda t: intensity_order.get(t["intensity"], 0), reverse=True)
                body_tasks.sort(key=lambda t: intensity_order.get(t["intensity"], 0), reverse=True)
                
                # If fatigued, prefer rest-type tasks (sleep, movie, etc.) over forced REST
                if (not brain_ok and not body_ok) and rest_tasks:
                    best_task = rest_tasks[0]
                elif brain_ok and body_ok:
                    if self.brain_fatigue <= self.body_fatigue:
                        preferred = brain_tasks if brain_tasks else body_tasks
                    else:
                        preferred = body_tasks if body_tasks else brain_tasks
                    if preferred:
                        best_task = preferred[0]
                elif brain_ok and brain_tasks:
                    best_task = brain_tasks[0]
                elif body_ok and body_tasks:
                    best_task = body_tasks[0]
                elif rest_tasks:
                    # Both channels tired but rest tasks available
                    best_task = rest_tasks[0]
                else:
                    if brain_ok and body_tasks:
                        body_tasks.reverse()
                        best_task = body_tasks[0]
                    elif body_ok and brain_tasks:
                        brain_tasks.reverse()
                        best_task = brain_tasks[0]
                    else:
                        best_task = None
                
            if best_task:
                self._execute_or_split(best_task, remaining_tasks)
            else:
                self.rest()

    def _max_doable_minutes(self, task):
        """How many minutes of this task can we do before hitting FATIGUE_CAP?"""
        if task["type"] == "rest":
            return task["remaining_duration"]  # rest tasks can always be done fully
        
        tp = task["type"]
        stamina = self.brain_stamina if tp == "brain" else self.body_stamina
        current_fp = self.brain_fatigue if tp == "brain" else self.body_fatigue
        
        headroom = FATIGUE_CAP - current_fp
        if headroom <= 0:
            return 0
        
        rate = fatigue_rate(task["intensity"], stamina)
        if rate <= 0:
            return task["remaining_duration"]
        
        max_mins = int(headroom / rate)
        return max(0, max_mins)

    def _execute_or_split(self, task, remaining_tasks):
        """Execute the task fully, or split it if fatigue would exceed the cap."""
        remaining_dur = task["remaining_duration"]
        max_mins = self._max_doable_minutes(task)
        
        if max_mins >= remaining_dur:
            # Can finish the whole task
            self._run_chunk(task, remaining_dur, is_partial=False)
            remaining_tasks.remove(task)
        elif max_mins >= 10:
            # Can do a meaningful chunk (at least 10 min), then pause
            self._run_chunk(task, max_mins, is_partial=True)
            task["remaining_duration"] -= max_mins
            # Don't remove — it stays in remaining_tasks with reduced duration
        else:
            # Can't even do 10 minutes — check if alternate-type tasks exist
            opposite = "body" if task["type"] == "brain" else "brain"
            alt_tasks = [t for t in remaining_tasks if t["type"] == opposite and t is not task]
            
            if alt_tasks:
                # Switch to an alternate-type task instead (the main loop will pick it)
                # Force a rest first to recover a bit
                self.rest()
            else:
                # This is the only task or only type left — rest then retry
                self.rest()

    def _run_chunk(self, task, duration, is_partial):
        """Execute `duration` minutes of a task."""
        start_time = self.current_time
        stamina = self.brain_stamina if task["type"] == "brain" else self.body_stamina
        fatigue_inc = calculate_fatigue_increase(task["intensity"], stamina, duration)
        
        old_brain = self.brain_fatigue
        old_body = self.body_fatigue
        
        if task["type"] == "rest":
            # Rest-type tasks (sleep, movie, etc.) RECOVER fatigue
            recovery = 15.0 * (duration / 10.0)
            self.brain_fatigue = clamp(self.brain_fatigue - recovery)
            self.body_fatigue = clamp(self.body_fatigue - recovery)
            fatigue_inc = 0.0
        elif task["type"] == "brain":
            self.brain_fatigue = clamp(self.brain_fatigue + fatigue_inc)
            self.body_fatigue = clamp(self.body_fatigue - 5.0 * (duration / 10.0))
        else:
            self.body_fatigue = clamp(self.body_fatigue + fatigue_inc)
            self.brain_fatigue = clamp(self.brain_fatigue - 5.0 * (duration / 10.0))
            
        self.current_time += duration
        
        label = task["name"]
        if is_partial:
            done_so_far = task["duration"] - task["remaining_duration"] + duration
            label = f"{task['name']} (Part — {done_so_far}/{task['duration']} min done)"
        
        reason = "Completed" if not is_partial else f"Paused — fatigue too high to continue"
        
        log_entry = (
            f"[Time {start_time}] -> [Time {self.current_time}]\n"
            f"Task: {label}\n"
            f"Type: {task['type'].capitalize()} (LLM)\n"
            f"Intensity: {task['intensity'].capitalize()}\n"
            f"Duration: {duration} min\n"
            f"Fatigue Increase: {fatigue_inc:.1f}\n"
            f"Brain Fatigue: {old_brain:.1f} -> {self.brain_fatigue:.1f}\n"
            f"Body Fatigue: {old_body:.1f} -> {self.body_fatigue:.1f}\n"
            f"Status: {reason}\n"
            "---------------------------------------"
        )
        self.logs.append(log_entry)
        
        self.timeline.append({
            "name": label,
            "start": start_time,
            "end": self.current_time,
            "type": task["type"],
            "missed_deadline": bool(task.get("deadline") and self.current_time > int(task["deadline"]))
        })
        
    def rest(self):
        duration = int((self.brain_fatigue + self.body_fatigue) / 4.0)
        if duration < 10: 
            duration = 10
            
        start_time = self.current_time
        old_brain = self.brain_fatigue
        old_body = self.body_fatigue
        
        recovery_units = duration / 10.0
        self.brain_fatigue = clamp(self.brain_fatigue - 15.0 * recovery_units)
        self.body_fatigue = clamp(self.body_fatigue - 15.0 * recovery_units)
        
        self.current_time += duration
        
        log_entry = (
            f"[Time {start_time}] -> [Time {self.current_time}]\n"
            f"Task: REST\n"
            f"Duration: {duration} min\n"
            f"Brain Fatigue: {old_brain:.1f} -> {self.brain_fatigue:.1f}\n"
            f"Body Fatigue: {old_body:.1f} -> {self.body_fatigue:.1f}\n"
            "---------------------------------------"
        )
        self.logs.append(log_entry)
        
        self.timeline.append({
            "name": "REST",
            "start": start_time,
            "end": self.current_time,
            "type": "rest",
            "missed_deadline": False
        })
