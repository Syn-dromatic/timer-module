___
## 📋 Prerequisite:
```
Requires Python >= 3.10
TimeProfiler makes use of new features from Python's typing module.
```

___
## 🛠️ Installation:
```
pip install timer-module
```

___
## 🖥️ Timer Usage:
### Example Usage:
```python
import time
from timer_module import TimerModule

timer_module = TimerModule().start()

timer_module.pause()
time.sleep(0.2)

timer_module.start()
time.sleep(0.5)

seconds = timer_module.get_time()
print(seconds)
```

#### Get the current time
```python
# Seconds
TimerModule().get_time() # float

# Milliseconds
TimerModule().get_time_ms() # float

# Nanoseconds
TimerModule().get_time_ns() # float
```


#### Set the starting time
```python
# Seconds
TimerModule().set_time(1.0)

# Milliseconds
TimerModule().set_time_ms(1.0)

# Nanoseconds
TimerModule().set_time_ns(1.0)
```

#### Pause timer:
```python
TimerModule().pause()
```

#### Refresh timer (preserves timer run state):
```python
TimerModule().refresh()
```

#### Reset timer (resets everything)
```python
TimerModule().reset()
```

___
## 🖥️ Profiler Usage:
TimeProfiler also includes a "function_profiler" and "async_function_profiler", in a class the asynchronous methods are handled automatically, but for functions you need to select the appropriate decorator.

```python
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
![profiler_output](https://github.com/syn-chromatic/timer-module/assets/68112904/155f7515-fc5a-480b-b7eb-d1e710acae3f)

