import collections


def foreach(body, iterable):
    if not callable(body):
        raise ValueError("{} is not callable.".format(body))
    if not isinstance(iterable, collections.Iterable):
        raise ValueError("{} is not iterable.".format(iterable))

    for element in iterable:
        body(element)


def raise_if_not_callable(arg):
    if not callable(arg):
        raise ValueError("{} is not callable".format(arg))


def noop():
    pass
