#!/usr/bin/env python
# encoding=utf-8

# author        : seongcheol jeon
# created date  : 2024.02.17
# modified date : 2024.02.17
# description   :


class ProgressBar:
    DEFAULT_PROGRESS_STYLE = '''
    QProgressBar {
        text-align: center;
        height: 15px;
    }
    
    QProgressBar::chunk {
        width: 10px;
    }
    '''

    ORANGE_PROGRESS_STYLE = '''
    QProgressBar {
        text-align: center;
        height: 15px;
    }
    
    QProgressBar::chunk {
        background-color: orange;
        width: 10px;
        margin: 1px;
    }
    '''


if __name__ == '__main__':
    pass
