# Timer-Module
Timer Module written in Python with start, pause, reset.


## Usage:
```
import time
from timer_module import TimerModule

timer_module = TimerModule().start_time()

time.sleep(2)
timer_module.pause_time()
time.sleep(2)

timer = timer_module.get_time()
```

### set the timer
```
timer_module = TimerModule().set_time(5).start_time()
```

### refresh time (keeps state)
```
timer_module.refresh_time()
```

### reset time (stops and resets)
```
timer_module.reset_time()
```

### switch to floating-point timestamps
```
timer_module = TimerModule(float).start_time()
```
