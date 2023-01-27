Timer Module written in Python with profiling features.

___
## Timer Usage:
```
import time
from timer_module import TimerModule

timer_module = TimerModule().start()

timer_module.pause()
time.sleep(2)

timer_module.start()
time.sleep(2)

time_seconds = timer_module.get_time()
print(time_seconds)
```

#### set the timer
```
timer_module = TimerModule().set_time(5).start()
```

#### refresh time (keeps timer state)
```
timer_module.refresh()
```

#### reset time (resets everyting)
```
timer_module.reset()
```

___
## Profiler Usage:
TimeProfiler also includes a "function_profiler" and "async_function_profiler", in a class the asynchronous methods are handled automatically, but for functions you need to select the appropriate decorator.

```
import time
from timer_module import TimeProfiler

# You only need this line to profile the entire class 
# The program is run normally, this decorator will wrap 
# The class and its methods in order to track execution time
@TimeProfiler().class_profiler
class ExampleClass:
    def __init__(self):
        time.sleep(0.1)

    def method_1(self):
        time.sleep(0.5)
        self.method_2()

    def method_2(self):
        time.sleep(1)
        self.method_3()

    def method_3(self):
        time.sleep(1)
        self.method_4()

    def method_4(self):
        time.sleep(0.1)
        self.method_5()

    def method_5(self):
        time.sleep(0.1)


ec = ExampleClass()
ec.method_1()
```

#### Output:
![](https://github.com/syn-chromatic/timer-module/blob/main/images/output.png)
