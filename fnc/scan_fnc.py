import time
import threading


class ScanSignals():
    def __init__(self, lte_stick, ardu):
        self.lte_stick = lte_stick
        self.arduino = ardu
        self.scanres = {}
        self.run_trigger = False       # Loop stopper

    def scan_complete(self, resolution=32, lte_duration=5, ardu_duration=1):
        f = resolution
        scan_count = lte_duration
        self.run_trigger = True

        # TODO Werte zu 270 grad mappen + Heading vom ardu
        for i in range(int(1024/f)):
            val = int(i * f)
            self.arduino.set_servo(servo=1, val=val)
            temp = [0, 0, 0]
            for n in range(scan_count):     # Get average of scan values
                while True:                 # Sometimes got None value back
                    sigs = self.lte_stick.get_string()
                    if(all(sigs)):
                        temp = [temp[0] + sigs[0], temp[1] + sigs[1], temp[2] + sigs[2], sigs[3]]
                        # print("{} - {} {} {}".format(val, sigs[0], sigs[1], sigs[2]))
                        break
                if(not self.run_trigger):
                    print("EM Break")
                    break
            if(not self.run_trigger):
                print("EM Break")
                break
            #                    mode, rsrq, rsrp, sirn
            self.scanres[val] = [temp[3], temp[0] / scan_count, temp[1] / scan_count, temp[2] / scan_count]
        self.run_trigger = False
        #print("{} \n".format(scanres[val]))

    def scan_thread(self, duration=2, timer=-1):
        print("Run Scan Thread")
        if(timer != -1):
            self.run_trigger = True
            ti = time.time()
            while self.run_trigger:
                print("Timed Thread")
                self.scan_complete()
                if((time.time() - ti) > timer):
                    break
        else:
            for n in range(duration):
                print("Scan Nr: " + str(n))
                self.scan_complete()
        self.run_trigger = False

    def run_scan_thread(self, duration, timer=-1):
        return threading.Thread(target=self.scan_thread, args=(duration, timer)).start()

    def get_peak(self):
        res, key = None, None
        for i in self.scanres.keys():
            if(res):
                temp = self.scanres[i]
                if(temp[0] > res[0]):
                    res, key = temp, i
                if(temp[0] == res[0] and temp[1] > res[1]):     # Check 3G or 4G
                    res, key = temp, i
            else:
                res, key = self.scanres[i], i

        return res, key
