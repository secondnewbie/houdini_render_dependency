#!/usr/bin/env python
# -*- coding: utf-8 -*-

# author        : Seongcheol Jeon
# created date  : 2024.02.15
# modified date : 2024.02.15
# description   :

import typing
import functools
import threading


# 매개변수 타입 체크
class CheckType:
    def __init__(self, var_type: tuple):
        if not isinstance(var_type, tuple):
            raise TypeError('{0}은(는) {1}형식이 아닙니다.'.format(var_type, repr(tuple)))

        self.__var_type: tuple = var_type

    def __call__(self, func: typing.Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(self.__var_type) != len(args):
                raise ValueError('매개변수와 형식의 개수가 서로 다릅니다.')
            for i in range(len(args)):
                if not isinstance(args[i], self.__var_type[i]):
                    raise TypeError('{0}은(는) {1}형식이 아닙니다.'.format(args[i], repr(self.__var_type[i])))
            return func(*args, **kwargs)
        return wrapper


def using_thread(func: typing.Callable):
    def wrapper(*args):
        th = threading.Thread(target=func, args=args)
        th.start()
        return th
    return wrapper


if __name__ == '__main__':
    pass
