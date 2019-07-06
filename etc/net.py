# Author : DerHirschi
import os
import subprocess

from etc.var import string2array, array2string


def ip_online(ip, timeout=5, interval=0.250, count=1):
    _out = subprocess.getoutput("ping {} -i {} -w {} -c {}".format(ip, interval, timeout, count))
    _i = _out.find("time=")
    if not _i == -1:
        _out = _out[_i:(_i + 13)]
        _out = _out.replace("time=", "")
        _out = _out.replace(" ms", "")
        return float(_out)
    else:
        return float(-1)


def wol(mac):
    if subprocess.getoutput("wakeonlan {}".format(mac)):
        return True
    else:
        return False


def keepalive_winhost(ip):
    out = subprocess.getoutput("smbclient -L //{}/ -N".format(ip))
    if out.find("NT_STATUS_IO_TIMEOUT") == -1:
        return True
    else:
        return False


# TODO Kein Pipe mehr via cmd ... Stringsuche
def getdefault_iface(opt='ip'):
    return subprocess.getoutput("ip route | grep default " + (
                                    {
                                        'ip': "| awk {'print $3'}",
                                        'iface': "| awk {'print $5'}",
                                    }[opt])
                              )


def getall_iface(opt='ip'):
    return {
        'ip': string2array(subprocess.getoutput("ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | " +
                                              "awk {'print $2'} | sed -ne 's/addr\:/ /p'")[1:], '\n '),
        'iface': os.listdir('/sys/class/net/'),
    }[opt]

# Subnet Integer (8 or 16 or 24 or 28 ...) or string ('255.255.255.0' or '255.255.255.128' ...)
def calc_ip_subnet(ip, subnet):
    def _byte_to_bit(byte):
        for c in range(4):
            byte[c] = bin(byte[c])[2:]
            for n in range(8 - (len(byte[c]))):
                byte[c] = '0' + byte[c]

        return byte

    if type(subnet) == int:
        _sub = ['', '', '', '']
        for a in range(4):
            _temp = ''
            for b in range(8):
                if subnet >= 1:
                    _te = '1'
                    subnet -= 1
                else:
                    _te = '0'
                _temp = _temp + _te
            _sub[a] = _temp

    else:
        _sub = _byte_to_bit(string2array(subnet, '.'))

    _ip  = _byte_to_bit(string2array(ip, '.'))

    for i in range(4):
        _tmp_ip = _ip[i]
        _temp_sub = _sub[i]
        _tempres = ''
        for j in range(8):
            if bool(int(_tmp_ip[j])) and bool(int(_temp_sub[j])):
                _flag = '1'
            else:
                _flag = '0'

            _tempres = _tempres + _flag

        _ip[i] = int(_tempres, 2)

    return array2string(_ip, '.')

# Args
# 1. Rule string to reverse (Switch from A to D or D to A) | leave '' if not use .. default -> not in use
# 2. Switch Add/Delete Rule True/False .. default -> False
# 3. Protocoll ('tcp','udp'...) .. default 'tcp'
# 4. Ports .. leave blank for any <- default.Example: '21' or '5900:6200' !! in STRING
# 5. (optional) Source IP(range) .. leave blank '' -> for any IP 0.0.0.0/0 <- default
# 6. (optional) Destination IP(range) .. default -> default output IP -> '' for any IP 0.0.0.0/0
# 7. (optional) Mode ('ACCEPT'/'REJECT'/'DROP'/'LOG') default -> 'ACCEPT'
#   Examples :
#   fw('', False, 'tcp', '7777', '', '') -> tcp port 7777 close from any to any
#   fw('', True, 'tcp', '7777:8888', '10.0.0.0/8') -> open tcp port from 7777 to 8888 from 10.0.0.0/8 to default out IP
#   fw('', True, 'tcp', '7777:8888', '10.0.0.0/8', '') -> open tcp port from 7777 to 8888 from 10.0.0.0/8 to any IP
#   fw('Rulestring (returned) from this fnc') -> Revert this incomming Rule ( A -> D or D -> A )
#
#   return (executed Rulestring, Consol Output ( has to be '' if all fine) )
#
# TODO FW als extra Modul ...
# TODO LIMIT Rules ( DOS ) Protect
# TODO Idee DDOS Protection .. later ...
def fw(revrule='', switch=False, proto='tcp', port='', src='', dest=getdefault_iface(), mode='ACCEPT'):
    # Root User check
    if os.geteuid() != 0:
        print ('You must be super-user. Cant change Firewall Rules for u..')
        return ''
    else:
        # Rule Reverse Fnc
        def _fnc_rev_rules(instr):
            return instr[0:10] + {
                'A': 'D',
                'D': 'A',
            }[instr[10:11]] + instr[11:]

        # Check Rule
        def _fnc_chk_rules(rule):
            _cmd = rule[0:10] + 'C' + rule[11:]
            if rule[10:11] == 'D':
                if subprocess.getoutput(_cmd) == '':
                    return True
                else:
                    return False
            else:
                if subprocess.getoutput(_cmd) != '':
                    return True
                else:
                    return False
        # Arg 1
        if revrule != '':
            _st = _fnc_rev_rules(revrule)
            if _fnc_chk_rules(_st):
                return _st, subprocess.getoutput(_st)
            else:
                return ''
        else:
            switch = {
                True:  'A',
                False: 'D',
            }[switch]
        # 3
        if port != '':
            port = '--dport ' + port + ' '
        # 4
        if src == '':
            src = '0.0.0.0/0'
        # 5
        if dest == '':
            dest = '0.0.0.0/0'
        _st = 'iptables -{} ufw-user-input -s {} -d {} -p {} {}-j {}'.format(
            switch,
            src,
            dest,
            proto,
            port,
            mode
        )

        if _fnc_chk_rules(_st):
            return _st, subprocess.getoutput(_st)
        else:
            return ''


# Test it !!
if __name__ == '__main__':

    print (calc_ip_subnet('192.168.1.101', 16))
    print (calc_ip_subnet('192.168.1.101', '255.255.255.128'))
