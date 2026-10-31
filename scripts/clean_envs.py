"""
Delete the built environments in `_envs/`. Their recipes are in `docs/models/<framework>`, so `lingua_franca envs install` builds them again.

    python scripts/clean_envs.py               # All of them
    python scripts/clean_envs.py camdl odin    # Some of them
"""
import os
import sys
import stat
import shutil
import pathlib

built = pathlib.Path(__file__).resolve().parent.parent / '_envs'


def make_writable(func, path, error):
    """ Retry a failed deletion: dune and Go leave read-only folders behind """
    os.chmod(os.path.dirname(path), stat.S_IRWXU)
    os.chmod(path, stat.S_IRWXU)
    func(path)
    return


def main(names=None):
    names = names or sorted(path.name for path in built.iterdir()) if built.exists() else []
    for name in names:
        folder = built / name
        if not folder.is_dir():
            print(f'{name}: not built')
            continue
        shutil.rmtree(folder, onexc=make_writable)
        print(f'{name}: deleted')
    return


if __name__ == '__main__':
    main(sys.argv[1:])
