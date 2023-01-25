Timer Module written in Python with start, pause, reset and profiling features.

___
## Timer Usage:
```
import time
from timer_module import TimerModule

timer_module = TimerModule().start_time()

timer_module.pause_time()
time.sleep(2)

timer_module.start_time()
time.sleep(2)

timer = timer_module.get_time()
```

#### set the timer
```
timer_module = TimerModule().set_time(5).start_time()
```

#### refresh time (keeps state)
```
timer_module.refresh_time()
```

#### reset time (stops and resets)
```
timer_module.reset_time()
```

___
## Profiler Usage:
```
import time
from timer_module import TimeProfiler


@TimeProfiler().class_decorator
class SimpleClass():
    def method1(self):
        time.sleep(1)

    def method2(self):
        time.sleep(2)


sc = SimpleClass()
sc.method1()
sc.method2()
```

#### Output:
```
=========
Name: SimpleClass.method1
Time Taken: [1000.64990234375ms]
=========
Name: SimpleClass.method2
Time Taken: [2000.67041015625ms]
```
