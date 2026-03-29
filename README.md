# Timer App
A simple desktop timer application built with Python and Tkinter.
It has three modes: stopwatch, countdown timer, and pomodoro timer, with sounds alerts and end-time display.

## Features
- Stopwach (count up from zero)
- Countdown timer (set hours, minutes, seconds)
- Pomodoro timer (custom work/break intervals, default 25m work, 5m break, 4 intervals)
- Sound alerts with toggle (on/off)
- End-time display for running timers
- Automatic phase switching in pomodoro mode
- Clean and simple desktop GUI

# Screenshots
### Stopwatch
![Stopwatch](/screenshots/timer_app_stopwatch.png)
### Set Timer
![Set Timer](/screenshots/timer_app_setTimer.png)
### Pomodoro Timer
![Pomodoro Timer](/screenshots/timer_app_pomodoro.png)

## Requirements
- Python 3.x
- Tkinter

Note: Sound alerts use the built-in ```winsound``` module on Windows. On other systems, a fallback terminal bell is used.

## How to Run
``` python main.py ```

## Modes
### Stopwatch
Counts upwards from ```00:00:00```. 
Includes start, pause, and reset controls.
### Set Timer
Allows setting hours, minutes, and seconds.
Counts down to zero and displays the expected end time while running.

### Pomodoro Timer
Allows configuration of work duration (minutes), break duration (minutes), and number of intervals.
The timer automatically alternates between work and break phases and displays the current phase (e.g. "Work 1/4").

## Notes
- This is a small desktop project focused on functionality and usability
- The application is built using Tkinter for simplicity and portability
- Sound behavior may vary slightly depending on the operating system

## Future Improvements
- Save user settings
- Multiple simultaneous timer running, optionally multiplying the window (see terminator terminal functionality) 
- Custom alert sounds (besides frequency and duration in the code)
- Better UI styling/themes
- Add full-screen functionality
- Make it usable as standalone executable
