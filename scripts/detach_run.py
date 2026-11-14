#!/usr/bin/env python3
"""P3 调度辅助：以独立 session 启动子进程，避免终端/会话信号（SIGHUP）杀死长任务。

用法: detach_run.py <cmd> [args...]
- os.setsid() 让子进程成为新 session 的首进程，不再属于原进程组
- 父进程打印子进程 PID 并等待其退出，返回相同的退出码
"""
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("usage: detach_run.py <cmd> [args...]", file=sys.stderr)
        return 2
    cmd = sys.argv[1:]
    pid = os.fork()
    if pid == 0:
        # 子进程：脱离进程组
        try:
            os.setsid()
        except OSError:
            pass
        try:
            os.execvp(cmd[0], cmd)
        except OSError as e:
            print(f"exec failed: {e}", file=sys.stderr)
            os._exit(127)
    # 父进程
    with open(os.environ.get("DETACH_PID_FILE", "/dev/null"), "w") as f:
        f.write(str(pid))
    _, status = os.waitpid(pid, 0)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
    return 1


if __name__ == "__main__":
    sys.exit(main())
