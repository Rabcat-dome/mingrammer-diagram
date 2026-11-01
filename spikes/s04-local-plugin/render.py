"""Render directly from literal JSON on stdin, without an MCP client."""
import sys
sys.dont_write_bytecode = True
from launch import run

if __name__ == '__main__':
    try:
        run('cli.py')
    except (RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
