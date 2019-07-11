#!/usr/bin/python3
import subprocess, os, time, datetime


def ping(host, iface):
    # Quell: https://stackoverflow.com/questions/2953462/pinging-servers-in-python

    # ping.py  2016-02-25 Rudolf, Edited: 2019-05-13 Masto
    # works under Python 2.7 and 3.4
    # works under Linux

    """
    Returns True if host responds to a ping request
    """
    args = "ping " + host + " -c 1 -I " + iface

    # Ping
    return subprocess.call(args, shell=True, stdout=subprocess.PIPE) == 0


def wpa_supplicant():
    '''
    return subprocess.call(args, shell=True)
    return subprocess.Popen(["sudo wpa_supplicant", "-B -c /etc/wpa_supplicant/wpa_supplicant.conf -i wlan1"])
    '''
    return subprocess.Popen("wpa_supplicant -c /etc/wpa_supplicant/wlan1.conf -i wlan1", shell=True, preexec_fn=os.setsid)


def get_ssid():
    scanoutput = subprocess.check_output(['iwconfig wlan1 | grep Point:'],shell=True,stderr=subprocess.STDOUT)
    scanoutput = str(scanoutput)
    ind = scanoutput.find("Access Point: ")
    indbssid = scanoutput.find("ESSID:")
    if ind != -1 and "Not-Associated" not in scanoutput:
        ind += 14
        scanoutput2 = subprocess.check_output(['iwconfig wlan1 | grep ESSID:'], shell=True, stderr=subprocess.STDOUT)
        scanoutput2 = str(scanoutput2)
        return scanoutput[ind:(ind + 17)], scanoutput2[indbssid:(indbssid + 12)]
    else:
        return False


def add_blacklist_ssid(ssid):
    conffile = open("/etc/wpa_supplicant/wlan1.conf", "r")
    conf = conffile.read()
    ind = conf.find("bssid_blacklist=")
    newstr = conf[:(ind + 16)] + ssid + " " + conf[(ind + 16):]

    args = "echo " + " > /etc/wpa_supplicant/wlan1.conf"
    conffile = open("/etc/wpa_supplicant/wlan1.conf", "w")
    conffile.write(newstr)
    subprocess.call(args, shell=True, stdout=subprocess.PIPE)


def kill_proc():
    id = subprocess.check_output([' ps ax | grep /etc/wpa_supplicant/wlan1.conf'],shell=True,stderr=subprocess.STDOUT)
    id = str(id.decode("UTF-8"))
    id = id[:(id.find("?") - 1)]
    subprocess.call("kill " + id, shell=True, stdout=subprocess.PIPE)


# test call
def test_call():
    logfile = open("/home/pi/ao_wifi/log.txt", "a")
    #logfile.seek(len(logfile.readlines()))
    logfile.write("\n")
    while True:
        proc = wpa_supplicant()
        trigger = False
        while True:
            temp = get_ssid()
            if temp:
                print("AP gefunden.. teste Zugang .. ")
                time.sleep(10)
                if not ping("8.8.8.8", "wlan1") and not trigger:
                    print("AP Blacklist SSID: " + temp[0])
                    add_blacklist_ssid(temp[0])
                    break
                else:
                    print("AP gefunden")
                    # TODO auf 20 o 30 sec setzen
                    if not trigger:
                        logfile.write(str(datetime.datetime.now()) + " " + temp[0] + " ESSID: " + str(temp[1]) + " \n")
                    trigger = True
                    time.sleep(10)
            else:
                print("no AP")
                trigger = False
                time.sleep(1)


        proc.kill()
        time.sleep(1)
        kill_proc()
        print("ende")
        time.sleep(5)


test_call()
#add_blacklist_ssid("00:00:00:00:00:00")

