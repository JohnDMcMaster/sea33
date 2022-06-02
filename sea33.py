import serial
import platform
import glob
import os
import time


def default_port():
    if platform.system() == "Linux":
        acms = glob.glob('/dev/ttyUSB*')
        if len(acms) == 0:
            return None
        return acms[0]
    else:
        return None


class NoSuchLine(Exception):
    pass


class BadCommand(Exception):
    pass


class Timeout(Exception):
    pass


"""
class SerialExpect(pexpect.spawnbase.SpawnBase):
    '''A pexpect class that works through a serial.Serial instance.
       This is necessary for compatibility with Windows. It is basically
       a pexpect.fdpexpect, except for serial.Serial, not file descriptors.
    '''
    def __init__(self,
                 ser,
                 args=None,
                 timeout=30,
                 maxread=2000,
                 searchwindowsize=None,
                 logfile=None,
                 encoding=None,
                 codec_errors='strict',
                 use_poll=False):
        self.ser = ser
        if not isinstance(ser, serial.Serial):
            raise Exception(
                'The ser argument is not a serial.Serial instance.')
        self.args = None
        self.command = None
        pexpect.spawnbase.SpawnBase.__init__(self,
                                             timeout,
                                             maxread,
                                             searchwindowsize,
                                             logfile,
                                             encoding=encoding,
                                             codec_errors=codec_errors)
        self.child_fd = None
        self.own_fd = False
        self.closed = False
        self.name = ser.name
        self.use_poll = use_poll

    def close(self):
        self.flush()
        self.ser.close()
        self.closed = True

    def flush(self):
        self.ser.flush()

    def isalive(self):
        return not self.closed

    def terminate(self, force=False):
        raise Exception('This method is not valid for serial objects')

    def send(self, s):
        s = self._coerce_send_string(s)
        self._log(s, 'send')
        b = self._encoder.encode(s, final=False)
        self.ser.write(b)

    def sendline(self, s):
        s = self._coerce_send_string(s)
        return self.send(s + self.linesep)

    def write(self, s):
        b = self._encoder.encode(s, final=False)
        self.ser.write(b)

    def writelines(self, sequence):
        for s in sequence:
            self.write(s)

    def read_nonblocking(self, size=1, timeout=None):
        s = self.ser.read(size)
        s = self._decoder.decode(s, final=False)
        self._log(s, 'read')
        return s
"""


class C8033:
    def __init__(self, device=None, verbose=None):
        if device is None:
            device = default_port()
            if device is None:
                raise Exception("Failed to find serial port")
        if verbose is None:
            verbose = os.getenv("VERBOSE", "N") == "Y"
        self.verbose = verbose
        self.verbose and print("port: %s" % device)
        self.ser = serial.Serial(device,
                                 timeout=0,
                                 baudrate=9600,
                                 writeTimeout=0)
        if 0:
            self.e = SerialExpect(self.ser, encoding="ascii")

            # send dummy newline to clear any commands in progress
            self.e.write('\n')
            self.e.flush()
            self.flushInput()

    def __del__(self):
        self.ser.close()

    def wait_rx(self, tidle=0.1):
        ret = ""
        tlast = time.time()
        while time.time() - tlast < tidle:
            buf = self.ser.read(1024)
            if buf:
                tlast = time.time()
            ret += tostr(buf)
        return ret

    def expect(self, s, timeout=0.5):
        self.e.expect(s, timeout=timeout)
        return self.e.before

    def send_line(self, l):
        self.ser.write(tobytes(l + "\r"))
        self.ser.flush()

    def cmd(self, cmd, reply=True, check=True):
        '''Send raw command and get string result'''
        strout = cmd + "\r"
        self.verbose and print("cmd out: %s" % strout.strip())
        self.e.write(strout)
        self.e.flush()

        if not reply:
            return None

        ret = self.expect('>>>')
        self.verbose and print('cmd ret: chars %u' % (len(ret), ))
        if "Traceback (most recent call last):" in ret:
            outterse = ret.strip().replace('\r', '').replace('\n', '; ')
            raise BadCommand("Failed command: %s, got: %s" %
                             (strout.strip(), outterse))
        return ret

    def match_line(self, a_re, res):
        # print(len(self.e.before), len(self.e.after), len(res))
        lines = res.split('\n')
        for l in lines:
            l = l.strip()
            m = re.match(a_re, l)
            if m:
                self.verbose and print("match: %s" % l)
                return m
        else:
            if self.verbose:
                print("Failed lines %d" % len(lines))
                for l in lines:
                    print("  %s" % l.strip())
            raise NoSuchLine("Failed to match re: %s" % a_re)


def tobytes(buff):
    if type(buff) is str:
        #return bytearray(buff, 'ascii')
        return bytearray([ord(c) for c in buff])
    elif type(buff) is bytearray or type(buff) is bytes:
        return buff
    else:
        assert 0, type(buff)


def tostr(buff):
    if type(buff) is str:
        return buff
    elif type(buff) is bytearray or type(buff) is bytes:
        return ''.join([chr(b) for b in buff])
    else:
        assert 0, type(buff)


"""
> HLP

Control commands
HIV_0-1300    CUR_0-300
PHV_0-1300    PCU_0-300
AGN_N_N       XON    XOF
CXT    RST    CFL    CFS

Status commands
STX    SHV    SCU    SPV
SPC    SOV    SIN    SAG
STS    SRB    SRL    DAG
SER

Micro Foucus X-Ray Controller
Version 1.03p 00/03/25 sat.
KOU PLANNING  CO.LTD.

> STX
X-RAY OFF

> SHV
HIV 0.0kV

> SCU
CUR 0uA

> SPV
PHV 90.0kV

> SPC
PCU 2uA

> SOV
NORMAL

> SIN
INTER LOCK ON

> SAG
AGING OFF

> STS
NOT READY

> SRB
READY

> SRL
OFF

> DAG
AGING 3 1 YET

> SER
ERR 0

"""
