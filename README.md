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
||PROFILE - SimpleClass.method1||
=================================
Name: SimpleClass.method3
Time: [3000.131103515625ms]
——
Name: SimpleClass.method2
Time: [5001.62841796875ms]
——
Name: SimpleClass.method1
Total Time: [6006.07861328125ms]
===
```
