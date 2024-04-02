import os
import sys
import shlex
import typing
import pathlib
import threading
import subprocess


class System:
    @staticmethod
    def get_files(parent_dir: pathlib.Path, pattern: typing.List[str]) -> typing.Generator:
        """
        사용자가 지정한 부모 디렉토리로부터 모든 하위 디렉토리를 검색하여
        특정 확장자를 가진 파일들을 반환하는 제네레이터
        :param parent_dir:
        :param pattern:
        :return:
        """
        for f in parent_dir.glob('**/*'):
            if not f.is_file():
                continue
            if '*' in pattern:
                yield f
            else:
                if f.suffix in pattern:
                    yield f

    @staticmethod
    def get_files_lst(parent_dir: pathlib.Path, pattern: typing.List[str]) -> typing.List[pathlib.Path]:
        """
        사용자가 지정한 부모 디렉토리로부터 모든 하위 디렉토리를 검색하여
        특정 확장자를 가진 파일들을 반환하는 메서드
        :param parent_dir:
        :param pattern:
        :return:
        """
        lst = list()
        for f in parent_dir.glob('**/*'):
            if not f.is_file():
                continue
            if '*' in pattern:
                lst.append(f)
            else:
                if f.suffix in pattern:
                    lst.append(f)
        return lst

    @staticmethod
    def get_files_recursion(dpath: str, pattern: typing.List[str], depth: int = 0) -> typing.Generator:
        """
        :param dpath:
        :param pattern:
        :param depth:
        :return:
        """
        lst = list()
        file_lst = os.listdir(dpath)
        for f in file_lst:
            fullpath = os.path.join(dpath, f)
            if os.path.isdir(fullpath):
                lst += System.get_files_recursion(fullpath, pattern, depth+1)
            else:
                if os.path.isfile(fullpath):
                    if '*' in pattern:
                        lst.append(fullpath)
                    else:
                        ext = f'.{fullpath.split(".")[-1]}'
                        if ext in pattern:
                            lst.append(fullpath)
        yield from lst

    @staticmethod
    def open_with_terminal(cmd: str) -> str:
        return "gnome-terminal -e 'bash -c \"{command}; cd $OLDPATH; exec bash\"' &".format(command=cmd)

    @staticmethod
    def open_folder(dirpath: pathlib.Path) -> bool:
        assert isinstance(dirpath, pathlib.Path)
        if not dirpath.is_dir():
            dirpath = dirpath.parent
        if not dirpath.is_dir():
            sys.stderr.write(f'디렉토리가 존재하지 않습니다. {dirpath.as_posix()}')
            return False
        os.startfile(dirpath.as_posix())
        return True

    @staticmethod
    def open_file_using_thread(
            cmdpath: pathlib.Path, filepath: typing.Union[pathlib.Path, None], with_term: bool = False) -> bool:
        assert isinstance(cmdpath, pathlib.Path)
        if (filepath is not None) and (not filepath.exists()):
            sys.stderr.write('"{0}" 오픈하려는 파일을 찾을 수 없습니다.'.format(filepath.as_posix()))
            return False
        if not cmdpath.exists():
            sys.stderr.write(f'{cmdpath.as_posix()} 실행 파일을 찾을 수 없습니다.')
            return False
        t = threading.Thread(target=System.open_file_with_arguments, args=(cmdpath, filepath, with_term))
        t.daemon = True
        t.start()
        return True

    @staticmethod
    def open_file_with_arguments(
            cmdpath: pathlib.Path, filepath: typing.Union[pathlib.Path, None], with_term: bool = False) -> int:
        if filepath is not None:
            cmd = '{0} {1}'.format(cmdpath.as_posix(), filepath.as_posix())
        else:
            cmd = cmdpath.as_posix()
        if with_term:
            cmd = System.open_with_terminal(cmd)
        result = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        out = out.decode('utf8')
        exitcode = result.returncode
        if exitcode != 0:
            sys.stderr.write('{0}, {1}, {2}'.format(exitcode, out.decode('utf8'), err.decode('utf8')))
            return 127
        return exitcode
