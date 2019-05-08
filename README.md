# PyTracer

Prints function calls of the Python program.

    $ cat example.py
    def f(a):
        return g(a, "20")

    def g(a, b):
        return b, a

    f(10)
    
    $ pytracer example.py
    >example.<module>()
        >example.f(10)
            >example.g(10, '20') = ('20', 10)
        <example.f(10) = ('20', 10)
    <example.<module>() = None


## Installing ##

`pip install pytracer`

## Usage ##

    pytracer.py [-h] [-s S] [-i I] [-f F] filename ...

    positional arguments:
      filename    a name of the Python program

    optional arguments:
      -h, --help  show this help message and exit
      -s S        max argument length to print (the default is 32)
      -i I        modules to ignore (comma delimited, the default is
                  re,glob,random,codecs,argparse)
      -f F        modules to focus at (comma delimited)

