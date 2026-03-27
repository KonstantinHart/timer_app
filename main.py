import tkinter as tk
from tkinter import ttk, messagebox
import time
import datetime
import threading

try:
    import winsound
except ImportError:
    winsound = None

ALERT_FREQ = 500
ALERT_DURATION = 700

# Play alert sound with specified count
def play_alert_sound(enabled=True, count=1):
    if not enabled:
        return
    def _beep():
        for _ in range(count):
            try:
                if winsound:
                    winsound.Beep(ALERT_FREQ, ALERT_DURATION)
                else:
                    print("\a", end="", flush=True)
            except Exception:
                pass
            time.sleep(0.1)  # short delay between beeps
    threading.Thread(target=_beep, daemon=True).start()


# Format seconds into HH:MM:SS string
def format_hms(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


# Stopwatch timer engine class
class StopwatchEngine:
    def __init__(self):
        self.reset()

    def start(self):
        if not self.running:
            self.running = True
            self.last_time = time.perf_counter()

    def pause(self):
        if self.running:
            self._tick()
            self.running = False

    def reset(self):
        self.elapsed = 0.0
        self.running = False
        self.last_time = None

    def _tick(self):
        if self.running and self.last_time is not None:
            now = time.perf_counter()
            self.elapsed += now - self.last_time
            self.last_time = now

    def update(self):
        self._tick()

    def get_text(self):
        return format_hms(self.elapsed)


# Countdown timer engine class
class CountdownEngine:
    def __init__(self):
        self.reset()

    def set_duration(self, h, m, s):
        self.total = max(0, int(h)) * 3600 + max(0, int(m)) * 60 + max(0, int(s))
        self.remaining = float(self.total)
        self.running = False
        self.start_time = None

    def start(self):
        if self.total <= 0:
            return
        if not self.running and self.remaining > 0:
            self.running = True
            self.start_time = time.perf_counter()

    def pause(self):
        if self.running:
            self._tick()
            self.running = False

    def reset(self):
        self.total = 0
        self.remaining = 0.0
        self.running = False
        self.start_time = None

    def _tick(self):
        if self.running and self.start_time is not None:
            now = time.perf_counter()
            delta = now - self.start_time
            self.remaining = max(0.0, self.remaining - delta)
            self.start_time = now
            if self.remaining <= 0:
                self.running = False

    def update(self):
        self._tick()

    def get_text(self):
        return format_hms(self.remaining)

    def is_finished(self):
        return self.total > 0 and self.remaining <= 0


# Pomodoro timer engine class
class PomodoroEngine:
    def __init__(self):
        self.sound_enabled = True
        self.reset()

    def set_cycle(self, work_min, break_min, intervals):
        self.work_seconds = max(0, int(work_min)) * 60
        self.break_seconds = max(0, int(break_min)) * 60
        self.intervals = max(1, int(intervals))
        self.reset_cycle()

    def reset_cycle(self):
        self.phase = 'work'
        self.current_interval = 1
        self.running = False
        self.remaining = float(self.work_seconds)
        self.start_time = None
        self.finished = False

    def start(self):
        if self.finished:
            return
        if not self.running and self.remaining > 0:
            self.running = True
            self.start_time = time.perf_counter()

    def pause(self):
        if self.running:
            self._tick()
            self.running = False

    def reset(self):
        self.work_seconds = 25 * 60
        self.break_seconds = 5 * 60
        self.intervals = 4
        self.reset_cycle()

    def _tick(self):
        if self.running and self.start_time is not None and not self.finished:
            now = time.perf_counter()
            delta = now - self.start_time
            self.remaining = max(0.0, self.remaining - delta)
            self.start_time = now
            if self.remaining <= 0:
                self.running = False
                phase_event = self._advance_phase()
                if not self.finished:
                    self.running = True
                    self.start_time = time.perf_counter()
                return phase_event
        return None

    def update(self):
        return self._tick()

    # Advance to next phase after current phase ends
    def _advance_phase(self):
        if self.phase == 'work':
            self.phase = 'break'
            self.remaining = float(self.break_seconds)
            play_alert_sound(self.sound_enabled, 3)
            return 'work_done'
        else:
            if self.current_interval >= self.intervals:
                self.finished = True
                self.remaining = 0
                play_alert_sound(self.sound_enabled, 3)
                return 'complete'
            self.current_interval += 1
            self.phase = 'work'
            self.remaining = float(self.work_seconds)
            play_alert_sound(self.sound_enabled, 3)
            return 'break_done'

    def get_phase_label(self):
        if self.finished:
            return 'Finished'
        phase_name = 'Work' if self.phase == 'work' else 'Break'
        return f"{phase_name} {self.current_interval}/{self.intervals}"

    def get_text(self):
        return format_hms(self.remaining)

    def expected_end_time(self):
        if self.running:
            return datetime.datetime.now() + datetime.timedelta(seconds=self.remaining)
        return None


# Main GUI application class
class TimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Timer App – Stopwatch | Set Timer | Pomodoro')
        self.geometry('420x360')
        self.resizable(False, False)
        self.configure(bg='#1f2022')

        self.sound_enabled = tk.BooleanVar(value=True)

        self.mode = tk.StringVar(value='Stopwatch')

        self.stopwatch = StopwatchEngine()
        self.countdown = CountdownEngine()
        self.pomodoro = PomodoroEngine()
        self.pomodoro.sound_enabled = self.sound_enabled.get()

        self.countdown_finished_alerted = False

        self._after_id = None

        self._create_widgets()
        self._switch_mode()
        self._update_ui_loop()

    # Create and layout the main UI widgets
    def _create_widgets(self):
        top_frame = tk.Frame(self, bg='#1f2022')
        top_frame.pack(fill='x', pady=(10, 2))

        tk.Label(top_frame, text='Mode:', fg='white', bg='#1f2022', font=('Arial', 11)).pack(side='left', padx=(8, 4))
        mode_menu = ttk.Combobox(top_frame, textvariable=self.mode, state='readonly', width=14)
        mode_menu['values'] = ['Stopwatch', 'Set Timer', 'Pomodoro Timer']
        mode_menu.pack(side='left')
        mode_menu.bind('<<ComboboxSelected>>', lambda _: self._switch_mode())

        sound_check = tk.Checkbutton(top_frame, text='Sound', variable=self.sound_enabled, onvalue=True, offvalue=False,
                                     bg='#1f2022', fg='white', selectcolor='#1f2022', activebackground='#1f2022',
                                     activeforeground='white', command=self._sound_toggled)
        sound_check.pack(side='right', padx=10)

        self.time_label = tk.Label(self, text='00:00:00', font=('Consolas', 48, 'bold'), fg='#d8dee9', bg='#1f2022')
        self.time_label.pack(pady=(10, 4), fill='x')

        self.phase_label = tk.Label(self, text='', font=('Arial', 12, 'bold'), fg='#88c0d0', bg='#1f2022')
        self.phase_label.pack(pady=2)

        self.end_time_label = tk.Label(self, text='', font=('Arial', 11), fg='#a3be8c', bg='#1f2022')
        self.end_time_label.pack(pady=2)

        self.status_label = tk.Label(self, text='', font=('Arial', 10), fg='#ebcb8b', bg='#1f2022')
        self.status_label.pack(pady=2)

        self.mode_frame = tk.Frame(self, bg='#1f2022')
        self.mode_frame.pack(fill='x', padx=16, pady=10)

        btn_frame = tk.Frame(self, bg='#1f2022')
        btn_frame.pack(pady=(2, 10))

        self.start_btn = tk.Button(btn_frame, text='Start', width=10, command=self._on_start)
        self.pause_btn = tk.Button(btn_frame, text='Pause', width=10, command=self._on_pause)
        self.reset_btn = tk.Button(btn_frame, text='Reset', width=10, command=self._on_reset)

        self.start_btn.grid(row=0, column=0, padx=4, pady=2)
        self.pause_btn.grid(row=0, column=1, padx=4, pady=2)
        self.reset_btn.grid(row=0, column=2, padx=4, pady=2)

    def _sound_toggled(self):
        self.pomodoro.sound_enabled = self.sound_enabled.get()

    def _clear_mode_frame(self):
        for widget in self.mode_frame.winfo_children():
            widget.destroy()

    # Switch between timer modes and reset state
    def _switch_mode(self):
        self._stop_loop()
        self.stopwatch.reset()
        self.countdown.reset()
        self.pomodoro.reset_cycle()
        self.countdown_finished_alerted = False

        self.phase_label.config(text='')
        self.end_time_label.config(text='')
        self.status_label.config(text='')

        self._clear_mode_frame()

        mode = self.mode.get()
        if mode == 'Stopwatch':
            self._build_stopwatch_mode()
        elif mode == 'Set Timer':
            self._build_timer_mode()
        elif mode == 'Pomodoro Timer':
            self._build_pomodoro_mode()

        self._update_buttons_state()
        self._update_ui_loop()

    def _build_stopwatch_mode(self):
        tk.Label(self.mode_frame, text='Stopwatch mode', fg='white', bg='#1f2022').pack(anchor='w')

    # Build UI for set timer mode with dropdowns
    def _build_timer_mode(self):
        frame = self.mode_frame
        self.timer_h = tk.StringVar(value='0')
        self.timer_m = tk.StringVar(value='0')
        self.timer_s = tk.StringVar(value='0')

        hours_values = [str(i) for i in range(100)]
        mins_secs_values = [str(i) for i in range(60)]

        for idx, (label_text, variable, values) in enumerate([('Hours', self.timer_h, hours_values), ('Minutes', self.timer_m, mins_secs_values), ('Seconds', self.timer_s, mins_secs_values)]):
            column = tk.Frame(frame, bg='#1f2022')
            column.grid(row=0, column=idx, padx=4)
            tk.Label(column, text=label_text, fg='white', bg='#1f2022').pack()
            combo = ttk.Combobox(column, width=5, textvariable=variable, justify='center', values=values, state='readonly')
            combo.pack()
            combo.set(variable.get())

    # Build UI for pomodoro mode with dropdowns
    def _build_pomodoro_mode(self):
        frame = self.mode_frame
        self.pomo_work = tk.StringVar(value='25')
        self.pomo_break = tk.StringVar(value='5')
        self.pomo_intervals = tk.StringVar(value='4')

        work_break_values = [str(i) for i in range(0, 121)]
        interval_values = [str(i) for i in range(1, 21)]

        settings = [
            ('Work minutes', self.pomo_work, work_break_values),
            ('Break minutes', self.pomo_break, work_break_values),
            ('Intervals', self.pomo_intervals, interval_values)
        ]
        for idx, (text, var, values) in enumerate(settings):
            column = tk.Frame(frame, bg='#1f2022')
            column.grid(row=0, column=idx, padx=4)
            tk.Label(column, text=text, fg='white', bg='#1f2022').pack()
            combo = ttk.Combobox(column, width=5, textvariable=var, justify='center', values=values, state='readonly')
            combo.pack()
            combo.set(var.get())

    # Validate and clamp integer input
    def _validate_int(self, var, max_value):
        val = var.get().strip()
        if not val:
            var.set('0')
            return
        try:
            i = int(val)
            i = max(0, min(i, max_value))
            var.set(str(i))
        except ValueError:
            var.set('0')

    # Handle start button press
    def _on_start(self):
        mode = self.mode.get()
        if mode == 'Stopwatch':
            self.stopwatch.start()
        elif mode == 'Set Timer':
            if not self._prepare_countdown():
                return
            self.countdown.start()
        elif mode == 'Pomodoro Timer':
            if not self._prepare_pomodoro():
                return
            self.pomodoro.sound_enabled = self.sound_enabled.get()
            self.pomodoro.start()
            if self.pomodoro.running and self.pomodoro.remaining == self.pomodoro.work_seconds:
                self.status_label.config(text='Work phase started')
                play_alert_sound(self.sound_enabled.get())

        self._update_buttons_state()

    # Handle pause button press
    def _on_pause(self):
        mode = self.mode.get()
        if mode == 'Stopwatch':
            self.stopwatch.pause()
        elif mode == 'Set Timer':
            self.countdown.pause()
        elif mode == 'Pomodoro Timer':
            self.pomodoro.pause()

        self._update_buttons_state()

    # Handle reset button press
    def _on_reset(self):
        mode = self.mode.get()
        if mode == 'Stopwatch':
            self.stopwatch.reset()
        elif mode == 'Set Timer':
            self.countdown.reset()
            self.countdown_finished_alerted = False
            self.end_time_label.config(text='')
            self.status_label.config(text='')
        elif mode == 'Pomodoro Timer':
            self.pomodoro.reset_cycle()
            self.phase_label.config(text='')
            self.end_time_label.config(text='')
            self.status_label.config(text='')

        self._update_buttons_state()

    # Prepare countdown timer with user input
    def _prepare_countdown(self):
        h = self.timer_h.get().strip() or '0'
        m = self.timer_m.get().strip() or '0'
        s = self.timer_s.get().strip() or '0'
        try:
            h = int(h); m = int(m); s = int(s)
        except ValueError:
            messagebox.showerror('Input error', 'Please enter valid numbers for hours/minutes/seconds.')
            return False
        if h < 0 or m < 0 or s < 0:
            messagebox.showerror('Input error', 'No negative values allowed.')
            return False
        self.countdown.set_duration(h, m, s)
        self.countdown_finished_alerted = False
        if self.countdown.total <= 0:
            messagebox.showwarning('Input error', 'Please enter a positive duration.')
            return False
        self.status_label.config(text='Timer running...')
        self._update_expected_end_time(self.countdown.remaining)
        return True

    # Prepare pomodoro timer with user input
    def _prepare_pomodoro(self):
        try:
            work = int(self.pomo_work.get())
            brk = int(self.pomo_break.get())
            intervals = int(self.pomo_intervals.get())
        except ValueError:
            messagebox.showerror('Input error', 'Please enter valid integer values for pomodoro settings.')
            return False
        if work <= 0 or brk < 0 or intervals <= 0:
            messagebox.showerror('Input error', 'Work minutes and intervals must be positive; break minutes cannot be negative.')
            return False
        self.pomodoro.set_cycle(work, brk, intervals)
        self.status_label.config(text='Pomodoro started: Work 1')
        self._update_expected_end_time(self.pomodoro.remaining + (work+brk)*(intervals-1)*60)
        return True

    # Update end time label
    def _update_expected_end_time(self, remaining_seconds):
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=remaining_seconds)
        self.end_time_label.config(text=f"Ends at {end_time.strftime('%H:%M:%S')}")

    # Update button states based on current mode
    def _update_buttons_state(self):
        mode = self.mode.get()
        if mode == 'Stopwatch':
            running = self.stopwatch.running
            self.start_btn.config(state='disabled' if running else 'normal')
            self.pause_btn.config(state='normal' if running else 'disabled')
            self.reset_btn.config(state='normal')
        elif mode == 'Set Timer':
            running = self.countdown.running
            self.start_btn.config(state='disabled' if running else 'normal')
            self.pause_btn.config(state='normal' if running else 'disabled')
            self.reset_btn.config(state='normal')
        elif mode == 'Pomodoro Timer':
            running = self.pomodoro.running
            self.start_btn.config(state='disabled' if running else 'normal')
            self.pause_btn.config(state='normal' if running else 'disabled')
            self.reset_btn.config(state='normal')

    # Stop the UI update loop
    def _stop_loop(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    # Periodic UI update
    def _update_ui_loop(self):
        mode = self.mode.get()
        if mode == 'Stopwatch':
            self.stopwatch.update()
            self.time_label.config(text=self.stopwatch.get_text())
            self.phase_label.config(text='')
            self.end_time_label.config(text='')
        elif mode == 'Set Timer':
            self.countdown.update()
            self.time_label.config(text=self.countdown.get_text())
            if self.countdown.running:
                self._update_expected_end_time(self.countdown.remaining)

            if self.countdown.is_finished() and not self.countdown_finished_alerted:
                self.status_label.config(text='Finished!')
                self.start_btn.config(state='normal')
                self.pause_btn.config(state='disabled')
                play_alert_sound(self.sound_enabled.get(), 3)
                self.countdown_finished_alerted = True
        elif mode == 'Pomodoro Timer':
            phase_event = self.pomodoro.update()
            self.time_label.config(text=self.pomodoro.get_text())
            self.phase_label.config(text=self.pomodoro.get_phase_label())

            if self.pomodoro.running:
                self._update_expected_end_time(self.pomodoro.remaining)

            if phase_event == 'work_done':
                self.status_label.config(text=f"Break {self.pomodoro.current_interval}/{self.pomodoro.intervals} started")
            elif phase_event == 'break_done':
                self.status_label.config(text=f"Work {self.pomodoro.current_interval}/{self.pomodoro.intervals} started")
            elif phase_event == 'complete':
                self.status_label.config(text='Pomodoro complete!')

            if self.pomodoro.finished:
                self.start_btn.config(state='normal')
                self.pause_btn.config(state='disabled')

        self._update_buttons_state()

        self._after_id = self.after(200, self._update_ui_loop)

# Main program
def main():
    app = TimerApp()
    app.mainloop()


if __name__ == '__main__':
    main()