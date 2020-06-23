# CONTRIBUTING
## Stream manipulation
If you are writing an object to manipulate a stream, it will either be a transformation (e.g. FFT) or a filter (e.g. highpass). In either case, the implementation will involve extending the `StreamManipulator` base class found in `templates.py`. Detailed instructions are below.

Before beginning to write any code, it is highly recommended to take a look at the `StreamManipulator` base class and getting familiar with the base methods. Understanding these methods is vital as it lets you know which functionality needs to be added for your own class, and what functionality can be covered by simply called the `super()` method.

If you are unfamiliar with object oriented programming in Python, this is a good resource to better understand some of the terminology used in this document: https://realpython.com/python3-object-oriented-programming/.

### Transforms
To implement a new transform, you will need to write a new class that extends the `StreamManipulator` class.

The `StreamManipulator` class has 3 methods: `__init__`, `initialize_output_stream`, `_backend`. When the class is initialized, the `__init__` method calls the `initialize_output_stream` method once and then calls the `_backend` method in a thread to run continuously. To write your own extension class, you will need to modify each of these methods. The recommended procedures for each method are as follows.

#### __init__()
First, make a dictionary called with each of the additional parameters required. Then, call `super().__init()` with the default arguments and the newly created dictionary. The dictionary should be passed as a kwarg to the `super()` function, i.e. using the `**kwargs` notation.

The `StreamManipulator.__init__()` method takes all `**kwargs` passed to it and makes them self attributes so they can be later referenced in the backend function.

#### initialize_output_stream()
This typically doesn't need to be changed but if you decide to do so, first call the `super()` as well. The typical changes made are to append meta information to the output stream.

#### _backend()
This is the function that will run in the thread once your object has been initialized. By default, it will simply pass chunks through without modifying them. Since the implementation uses a `while True` loop, you should not call the `super()` function and instead write your own loop.

### Filters
To implement a filter, the steps are slightly different. A `custom_filter` class has already been implemented (following the steps listed in the above section) and additional filter type can easily be added by modifying its `_backend` method. This class can be found in `filtering.py`

### Examples
For detailed examples, look at the `psd` class in the `transforms.py` or the `custom_filter` class in `filtering.py`. It will be useful to addtionally open the `templates.py` file to see what changes are made for each of the methods.

For usage examples, see `streamstaff/USAGE.md`
