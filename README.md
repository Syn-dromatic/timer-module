Timer Module written in Python with profiling features.

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


@TimeProfiler().class_profiler
class SimpleClass():
    def method1(self):
        time.sleep(1)
        self.method2()

    def method2(self):
        time.sleep(2)
        self.method3()


    def method3(self):
        time.sleep(3)


sc = SimpleClass()
sc.method1()
```

#### Output:
```
█ PROFILE: __main__.SimpleClass █
=================================
Profile Time: [0.00ms]


█ PROFILE: __main__.SimpleClass.method1 █
=========================================
Name: __main__.SimpleClass.method3
Time: [3000.15ms] — T%: 49.99%
——
Name: __main__.SimpleClass.method2
Time: [5000.62ms] — T%: 83.33%
——
Profile Time: [6001.09ms]

――― Total Time: [6001.09ms] ―――
```
