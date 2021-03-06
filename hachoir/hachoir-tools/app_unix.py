from os import kill, waitpid, P_NOWAIT, \
    WCOREDUMP, WIFSIGNALED, WSTOPSIG, WIFEXITED, WEXITSTATUS
from base_app import BaseApplication
from signal import SIGABRT, SIGFPE, SIGINT, SIGSEGV, SIGHUP, SIGKILL
from errno import ESRCH, ECHILD

# Create SIGNAME dictionay using dir(signal)
import signal
NAMES = [ name for name in dir(signal) if name.startswith("SIG") ]
SIGNAME = dict( (getattr(signal,name), name) for name in NAMES )
del NAMES
del signal

#SIGNAME = {
#    SIGABRT: "SIGABRT",
#    SIGINT: "SIGINT",
#    SIGFPE: "SIGFPE",
#    SIGSEGV: "SIGSEGV",
#    SIGHUP: 'SIGHUP',
#    SIGKILL: 'SIGKILL',
#}


class Application(BaseApplication):
    def _signal(self, signum, raise_error=True):
        if not self.process:
            if raise_error:
                raise RuntimeError("Unable to kill %s: it's not running" % self)

        # Log action
        name = SIGNAME.get(signum, signum)
        if signum in (SIGINT, SIGHUP):
            log_func = self.warning
        else:
            log_func = self.error
        log_func("kill(%s)" % name)

        # Send signal
        try:
            kill(self.process.pid, signum)
        except OSError, err:
            if err[0] == ESRCH:
                self.exited(None)
                raise RuntimeError(
                    "Unable to send signal %s to %s: process is dead"
                    % (name, self))
            else:
                raise

    def displayExit(self, status):
        self.exit_code = None

        # Display exit code
        if status is not None:
            log_func = self.warning
            info = []
            if WCOREDUMP(status):
                info.append("core dumped!")
                self.exit_failure = True
                log_func = self.error
            if WIFSIGNALED(status):
                signal = WSTOPSIG(status)
                signal = SIGNAME.get(signal, signal)
                self.exit_failure = True
                info.append("signal %s" % signal)
            if WIFEXITED(status):
                self.exit_code = WEXITSTATUS(status)
                info.append("exitcode=%s" % self.exit_code)
                self.exit_failure = (self.exit_code != 0)
            if self.exit_failure:
                if info:
                    log_func("Exit (%s)" % ", ".join(info))
                else:
                    log_func("Exit")
        else:
            self.exit_failure = True
            self.error("Process exited (ECHILD error)")

    def interrupt(self):
        self._signal(SIGINT)

    def kill(self):
        self._signal(SIGKILL)

    def _wait(self, blocking):
        """
        Wait process end.
        Return (is_still_running, exit_status).
        """
        try:
            if blocking:
                option = 0
            else:
                option = P_NOWAIT
            finished, status = waitpid(self.process.pid, option)
            if finished == 0:
                return (True, None)
            else:
                return (False, status)
        except OSError, err:
            if err[0] == ECHILD:
                return (False, None)
            else:
                raise

