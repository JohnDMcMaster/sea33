import serial
import platform
import glob
import os
import time
import re


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


class C8033Raw:
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
        self.wait_rx()

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

    def send_line(self, l):
        self.ser.write(tobytes(l + "\r"))
        self.ser.flush()

    def cmd(self, cmd, reply=True):
        '''Send raw command and get string result'''
        strout = cmd + "\r"
        self.verbose and print("cmd out: %s" % strout.strip())
        self.send_line(cmd)

        if not reply:
            return None

        # NOTE: lines are \r terminated
        return self.wait_rx()

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

    """
    Control
    """

    def RST(self):
        """
        > RST
        NORMAL
        """
        return self.cmd("RST")

    """
    spot sizes?
    HIV_0-1300    CUR_0-300
    PHV_0-1300    PCU_0-300
    """
    """
    AGN_N_N       XON    XOF
    CXT    RST    CFL    CFS
    """

    def XON(self):
        """
        x-ray on
        Equivalent to pressing white on button
        """
        ret = self.cmd("XON").strip()
        """
        Returns XON if off, otherwise ERROR
        """
        return ret

    def XOF(self):
        """
        x-ray off
        Equivalent to pressing red off button
        """
        ret = self.cmd("XOF").strip()
        # Always even if x-ray is already off
        assert ret == "XOF"

    """
    Status
    """

    def STX(self):
        """Is x-ray on?"""
        return self.cmd("STX").strip()

    def SHV(self):
        """Return actual voltage"""
        return self.cmd("SHV").strip()

    def SCU(self):
        """Return actual current"""
        return self.cmd("SCU").strip()

    def SPV(self):
        """Return set voltage"""
        return self.cmd("SPV").strip()

    def SPC(self):
        """Return set current"""
        return self.cmd("SPC").strip()

    def SOV(self):
        return self.cmd("SOV").strip()

    def SIN(self):
        return self.cmd("SIN").strip()

    def SAG(self):
        """Aging status"""
        return self.cmd("SAG").strip()

    def STS(self):
        return self.cmd("STS").strip()

    def SRB(self):
        return self.cmd("SRB").strip()

    def SRL(self):
        """
        One of:
        -LOCAL 
        -REMOTE
        Can by changed by turning knob on front
        """
        ret = self.cmd("SRL").strip()
        assert ret in ("LOCAL", "REMOTE")
        return ret

    def DAG(self):
        """Aging status?"""
        return self.cmd("DAG").strip()

    def SER(self):
        """If error LED is on?"""
        return self.cmd("SER").strip()

    def print_status(self):
        """
        STX: X-RAY OFF
        SHV: HIV 0.0kV
        SCU: CUR 0uA
        SPV: PHV 90.0kV
        SPC: PCU 2uA
        SOV: NORMAL
        SIN: INTER LOCK ON
        SAG: AGING OFF
        STS: STANDBY
        SRB: READY
        SRL: LOCAL
        DAG: AGING 3 1 YET
        SER: ERR 0
        """
        print("STX: " + self.STX())
        print("SHV: " + self.SHV())
        print("SCU: " + self.SCU())
        print("SPV: " + self.SPV())
        print("SPC: " + self.SPC())
        print("SOV: " + self.SOV())
        print("SIN: " + self.SIN())
        print("SAG: " + self.SAG())
        print("STS: " + self.STS())
        print("SRB: " + self.SRB())
        print("SRL: " + self.SRL())
        print("DAG: " + self.DAG())
        print("SER: " + self.SER())


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
