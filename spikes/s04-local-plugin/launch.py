"""Start the native renderer helper. No startup download, Docker or listening port."""
import os
import subprocess
import sys
sys.dont_write_bytecode = True
from common import ROOT, preflight, environment


def run(entrypoint='local_server.py'):
    state = preflight()
    os.execve(state['python'], [state['python'], str(ROOT / 'runtime' / entrypoint)], environment(state))


if __name__ == '__main__':
    try:
        run()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
