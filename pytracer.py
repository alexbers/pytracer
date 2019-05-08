#!/usr/bin/env python3
# Alexander Bersenev, 2019
# bay@hackerdom.ru

import sys
import os
import glob
import re
import argparse
import functools

not_interesting_modules = set()
interesting_modules = set()
max_arg_len_to_print = 32
first_call_depth = None
old_tracer = None
no_trace_funcs = set()


class TraceOutputter:
    def __init__(self, file=sys.stderr):
        self.last_output_params = None
        self.last_line_closed = True
        self.file = file

    def output(self, depth, code, event, call_desc, return_desc="", prev_exc_desc=""):
        if self.last_output_params == (depth, code) and event != "call":
            print(return_desc, file=self.file, end="")
            self.last_line_closed = False
        else:
            self.last_output_params = (depth, code)
            if not self.last_line_closed:
                print(prev_exc_desc, file=self.file)
                self.last_line_closed = True

            if not return_desc:
                print(call_desc, file=self.file, end="")
            else:
                print(call_desc + return_desc, file=self.file, end="")
            self.last_line_closed = False

    def __del__(self):
        if not self.last_line_closed:
            print(file=self.file)


trace_outputter = TraceOutputter()


def calc_frame_depth(frame):
    global first_call_depth

    depth = 1
    cur_frame = frame.f_back
    while cur_frame:
        cur_frame = cur_frame.f_back
        depth += 1

    if first_call_depth is None:
        first_call_depth = depth

    return depth - first_call_depth


def is_frame_interesting(frame):
    cur_frame = frame
    while cur_frame:
        if cur_frame.f_code in no_trace_funcs:
            return False
        filename = cur_frame.f_code.co_filename
        if filename.startswith("<") and filename.endswith(">"):
            return False
        module_name = os.path.splitext(os.path.basename(filename))[0]
        if interesting_modules:
            if module_name not in interesting_modules:
                return False
        else:
            if module_name in not_interesting_modules:
                return False
        cur_frame = cur_frame.f_back
    return True


def can_repr(obj):
    try:
        repr(obj)
        return True
    except Exception:
        return False


def format_arg(arg_name, arg_value):
    if not can_repr(arg_value):
        arg_value = "?"
    else:
        arg_value = repr(arg_value)

        if len(arg_value) > max_arg_len_to_print:
            arg_value = arg_value[:max_arg_len_to_print] + "..."

    if arg_name is None:
        return arg_value
    else:
        return str(arg_name) + "=" + arg_value


def format_return(ret_value):
    return format_arg(None, ret_value)


def format_args(frame):
    VARARGS_FLAG = 4
    VARKEYWORDS_FLAG = 8

    args = []

    code = frame.f_code
    var_names = code.co_varnames

    has_varargs = bool(code.co_flags & VARARGS_FLAG)
    has_varkeywords = bool(code.co_flags & VARKEYWORDS_FLAG)

    args_count = code.co_argcount
    kwonly_args_count = code.co_kwonlyargcount

    for var_name in var_names[:args_count]:
        var = frame.f_locals[var_name]
        args.append(format_arg(None, var))

    for var_name in var_names[args_count:args_count+kwonly_args_count]:
        var = frame.f_locals[var_name]
        args.append(format_arg(var_name, var))

    if has_varargs:
        var_arg = var_names[args_count+kwonly_args_count]
        for var in frame.f_locals[var_arg]:
            args.append(format_arg(None, var))

    if has_varkeywords:
        if not has_varargs:
            kw_arg = var_names[args_count+kwonly_args_count]
        else:
            kw_arg = var_names[args_count+kwonly_arg_count+1]

        for k, v in frame.f_locals[kw_arg].items():
            args.append(format_arg(k, v))

    args_repr = "(" + ", ".join(args) + ")"
    return args_repr


def trace_func(frame, event, event_arg):
    if event in ["line", "opcode"]:
        return trace_func

    if event not in ["call", "return", "exception"]:
        return trace_func

    if not is_frame_interesting(frame):
        return trace_func

    depth = calc_frame_depth(frame)

    args_formatted = format_args(frame)
    module = frame.f_code.co_filename
    module = os.path.splitext(os.path.basename(module))[0]
    type_char = ">" if event == "call" else "<"

    call_desc = " " * 4*depth + type_char + module + "." + frame.f_code.co_name + args_formatted

    return_desc = ""
    prev_exc_desc = ""
    if event == "return":
        return_desc = " = " + format_return(event_arg)
    elif event == "exception":
        exception, value, tb = event_arg
        was_propagated = tb.tb_next
        if was_propagated:
            prev_exc_desc = " ! " + format_return(value)

    global trace_outputter
    trace_outputter.output(depth, frame.f_code, event, call_desc, return_desc, prev_exc_desc)

    return trace_func


def no_trace(f=None):
    if f is None:
        return no_trace

    global no_trace_funcs
    no_trace_funcs.add(f.__code__)
    return f


@no_trace
def start_trace(max_arg_len=32,
                modules_to_ignore=["re", "glob", "random", "codecs", "argparse"],
                modules_to_focus=[]):
    global max_arg_len_to_print
    max_arg_len_to_print = max_arg_len

    global not_interesting_modules
    not_interesting_modules = set(sys.builtin_module_names)
    not_interesting_modules |= set(modules_to_ignore)

    global interesting_modules
    interesting_modules = set(modules_to_focus)
    if interesting_modules:
        # pytracer is always interesting
        interesting_modules.add("ptrace")

    global old_tracer
    old_tracer = sys.gettrace()

    sys.settrace(trace_func)


@no_trace
def stop_trace():
    global old_tracer
    sys.settrace(old_tracer)


class trace:
    def __init__(self, **dec_kwargs):
        self.dec_kwargs = dec_kwargs

    def __call__(self, f):
        @functools.wraps(f)
        def new_f(*args, **kwargs):
            start_trace(**self.dec_kwargs)
            ret = f(*args, **kwargs)
            stop_trace()
            return ret
        return new_f

    @no_trace
    def __enter__(self):
        start_trace(**self.dec_kwargs)

    @no_trace
    def __exit__(self, *args):
        stop_trace()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Prints calls and return values of the Python program.')
    parser.add_argument('-s', type=int, default=32,
                        help='max argument length to print (the default is %(default)s)')
    parser.add_argument('-i', default="re,glob,random,codecs,argparse",
                        help='modules to ignore (comma delimited, the default is %(default)s)')
    parser.add_argument('-f', default="", help='modules to focus at (comma delimited)')
    parser.add_argument('filename', help='a name of the Python program')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='program arguments')

    args = parser.parse_args()

    sys.argv = [args.filename] + args.args
    sys.path[0] = os.path.dirname(args.filename)

    modules_to_ignore = [m.strip() for m in args.i.split(",") if m]
    modules_to_focus = [m.strip() for m in args.f.split(",") if m]

    globs = {
        '__file__': args.filename,
        '__name__': '__main__',
        '__package__': None,
        '__cached__': None,
    }

    with open(args.filename) as f:
        code = compile(f.read(), args.filename, 'exec')

    start_trace(max_arg_len=args.s,
                modules_to_ignore=modules_to_ignore,
                modules_to_focus=modules_to_focus)
    try:
        exec(code, globs, globs)
    finally:
        stop_trace()
