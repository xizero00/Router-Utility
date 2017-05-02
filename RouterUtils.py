#/usr/bin/env python
#encoding:utf-8
import sys
import base64
import requests
import re
import pickle as p
import socket
import time
import logging
import os
import urllib


class RouterUtils():


    def __init__(self):
        self.sess = requests.Session()
        self.log = logging.basicConfig(level=logging.WARNING,
                                       filename='./log.txt',
                                       filemode='w',
                                       format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    def setServerChanID(self, id):
        self.serverchanID = id

    def doLogin(self, routerip, password):
        self.routerip = routerip
        self.password = password

        url_login = 'http://' + routerip
        cookie_dict = {"Authorization":"Basic%20" + base64.b64encode("admin:" + password).replace('==','') + "%3D%3D"}
        # convert dict cookit_dict to cookiejar
        cookies = requests.utils.cookiejar_from_dict(cookie_dict, cookiejar=None, overwrite=True)
        # set cookie
        self.sess.cookies = cookies

        login_response = self.sess.get(url=url_login)
        regex_success = r'window.parent.location.href = "/userRpm/Index.htm";'
        result = re.search(regex_success, login_response.text)
        if result == None:
            self.success_login = False
            return False
        else:
            self.success_login = True
            return True

    def doTryLogin(self, routerip, password, trynum=2):
        c = 0
        result = False
        while c < trynum:
            result = self.doLogin(routerip, password)
            if result:
                break
            else:
                c += 1
        return result


    def getRouterStatus(self):
        if self.success_login == False:
            return None

        # we must update header，or it will occurs unauthorized access
        # set header
        url_status_referer = 'http://' + self.routerip + '/userRpm/MenuRpm.htm'
        self.sess.headers.update(Referer=url_status_referer)

        # get router status
        url_status = 'http://' + self.routerip + '/userRpm/StatusRpm.htm'
        status_response = self.sess.get(url=url_status)
        str_status = status_response.text


        status = {}
        status['routerparam'] = self.getRouterParam(str_status)
        status['lanparam'] = self.getLanParam(str_status)
        status['wanparam'] = self.getWanParam(str_status)
        status['wlanparam'] = self.getWlanParam(str_status)
        status['statparam'] = self.getStatParam(str_status)

        with open('status.pkl', 'wb') as fd:
            p.dump(status, fd)
        return status


    def getRouterParam(self, status):
        regex_routerinfo = r'var statusPara=new Array\(([\w\W]+) \);\n</script>\n<script type="text/javascript">\nvar\ lanPara=new Array\('
        routerparam = re.findall(regex_routerinfo, status)[0].strip().replace('\n', '').replace('"', '')
        return routerparam

    def getLanParam(self, status):
        regex_lanparam = r'var lanPara=new Array\(([\w\W]+) \);\n</script>\n<script type="text/javascript">\nvar wlanPara=new Array'
        lanparam = re.findall(regex_lanparam, status)[0].strip().replace('\n', '').replace('"', '')
        return lanparam

    def getWlanParam(self, status):
        regex_wlanparam = r'var wlanPara=new Array\(([\w\W]+) \);\n</script>\n<script type="text/javascript">\nvar wanPara=new Array'
        wlanparam = re.findall(regex_wlanparam, status)[0].strip().replace('\n', '').replace('"', '')
        return wlanparam

    def getWanParam(self, status):
        regex_wanparam = r'var wanPara=new Array\(([\w\W]+) \);\n</script>\n<script type="text/javascript">\nvar statistList=new Array'
        wanparam = re.findall(regex_wanparam, status)[0].strip().replace('\n', '').replace('"', '')
        return wanparam

    def getStatParam(self, status):
        regex_statparam = r'var statistList=new Array\(([\w\W]+) \);\n</script>\n<meta http-equiv="Pragma" content="no-cache">'
        statparam = re.findall(regex_statparam, status)[0].strip().replace('\n', '').replace('"', '')
        return statparam

    def dict2str(self, d):
        str_d = ''
        for k,v in d.iteritems():
            str_d += str(k) + ':\t' + str(v) + '\n\n'
        return str_d

    def parseRouterParam(self, routerparam):
        '''
        routerinfo structure
        0   isvalid
        1   number of wan ports
        2   number of rows
        3   timeout
        4   current time
        5   firmware version
        6   hardware version
        7   unknown
        8   unknown
        '''
        if len(routerparam) == 0:
            return

        rp = routerparam.split(',')

        keylist = ['number of wan ports', 'current time', 'firmware version', 'hardware version']
        valuelist = [rp[1], rp[4], rp[5], rp[6]]
        routerparam_dict = dict(zip(keylist, valuelist))

        return self.dict2str(routerparam_dict)

    def parseLanParam(self, lanparam):
        if len(lanparam) == 0:
            return

        rp = lanparam.split(',')

        keylist = ['lan mac address', 'lan ip address', 'lan mask']
        valuelist = [rp[0], rp[1], rp[2]]
        lanparam_dict = dict(zip(keylist, valuelist))

        return self.dict2str(lanparam_dict)

    def parseWlanParam(self, wlanparam):
        if len(wlanparam) == 0:
            return

        wp = wlanparam.split(',')

        keylist = ['wlan status', 'wlan name', 'wlan channel', 'wlan mode index', 'wlan mac address', 'wlan ip address', 'wlan wds status']
        valuelist = [wp[0], wp[1], wp[2], wp[3], wp[4], wp[5], wp[10]]
        wlanparam_dict = dict(zip(keylist, valuelist))

        return self.dict2str(wlanparam_dict)

    def parseWanParam(self, wanparam):
        if len(wanparam) == 0:
            return

        wp = wanparam.split(',')

        keylist = ['wan mac address', 'wan ip address', 'wan mask', 'wan gateway', 'wan dns1', 'wan dns2', 'running time']
        valuelist = [wp[1], wp[2], wp[4], wp[7], wp[4], wp[11], wp[12], wp[13]]
        wanparam_dict = dict(zip(keylist, valuelist))

        return self.dict2str(wanparam_dict)

    def parseStatParam(self, statparam):
        if len(statparam) == 0:
            return

        sp = statparam.split(',')

        keylist = ['recv bytes', 'send bytes', 'recv packets', 'send packets']
        valuelist = [sp[0], sp[1], sp[2], sp[3]]
        wanparam_dict = dict(zip(keylist, valuelist))

        return self.dict2str(wanparam_dict)

    def checkConnectivity(self, host='114.114.114.114', port=53, timeout=3):
        '''
        quick test whether router is online
        :param host: 
        :param port: 
        :param timeout: 
        :return: 
        '''
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception as ex:
            print ex.message
            return False

    def doReboot(self):
        url_status_referer = 'http://' + self.routerip + '/userRpm/SysRebootRpm.htm'
        self.sess.headers.update(Referer=url_status_referer)

        # get router status
        url_reboot = 'http://' + self.routerip + '/userRpm/SysRebootRpm.htm?Reboot=%D6%D8%C6%F4%C2%B7%D3%C9%C6%F7'
        status_reboot = self.sess.get(url=url_reboot)
        time.sleep(10)
        regex_reboot = r'路由器正在重启中，请耐心等待。'
        result = re.search(regex_reboot, status_reboot.text)
        if result == None:
            return False
        else:
            return True

    def doTryCheckOnline(self, trynum=5):
        onlinecounter = 0
        c = 0
        while c<trynum:
            if self.checkConnectivity():
                onlinecounter += 1
            c += 1
            time.sleep(5)

        if onlinecounter/float(trynum) > 0.5:
            return True
        else:
            return False

    def ensureOnline(self):
        routerip = '192.168.0.1'
        password = 'cvlabpassword'
        ru = RouterUtils()
        while True:
            if not ru.checkConnectivity():
                login_result = ru.doTryLogin(routerip, password)
                if login_result:
                    print('login success')
                    reboot_result = ru.doReboot()
                else:
                    print('login failed')
            else:
                print('on line')
            time.sleep(5)

    def send2Wx(self, title, msg):
        data = {}
        data['text'] = title
        data['desp'] = msg
        url_wx = r'http://sc.ftqq.com/SCU7736Te0e5d71dac130d18634d03e2fac2e17558fb57cb29536.send?' + urllib.urlencode(data)
        requests.post(url_wx)
        return

    def getStatusStr(self, status):
        rp = self.parseRouterParam(status['routerparam'])
        lp = self.parseLanParam(status['lanparam'])
        wp = self.parseWlanParam(status['wlanparam'])
        wap = self.parseWanParam(status['wanparam'])
        stp = self.parseStatParam(status['statparam'])
        finalstr = rp + lp + wp + wap + stp
        return finalstr

    def doTryOnlineAndReportIp(self, routerip, password):
        # routerip = '192.168.0.1'
        # password = 'cvlabpassword'
        ru = RouterUtils()

        login_result = ru.doTryLogin(routerip, password)
        if login_result:
            status = ru.getRouterStatus()
            ru.send2Wx('router status', ru.getStatusStr(status))

        while True:
            if not ru.doTryCheckOnline():
                self.send2Wx('router is off-line', "router is off-line")
                login_result = ru.doTryLogin(routerip, password)
                if login_result:
                    reboot_result = ru.doReboot()
                    self.log.info('rebooting router...')
                    if reboot_result:
                        self.send2Wx('router reboot succeeded', "router reboot succeeded'")
                        lr = ru.doTryLogin(routerip, password)
                        if lr:
                            self.log.warning('login after reboot succeed')
                            status = ru.getRouterStatus()
                            wanparam = status['wanparam']
                            ip = wanparam.split(',')[2]
                            #self.send2Wx('路由器的ip地址', ip)
                            self.send2Wx('router status', self.getStatusStr(status))
                            self.log.warning('login after reboot, router ip :' + ip)
                        else:
                            self.send2Wx('ogin after reboot failed', "ogin after reboot failed")
                            self.log.warning('login after reboot failed')
                    else:
                        self.send2Wx('reboot router failed', 'reboot router failed')
                        self.log.warning('reboot router failed')
                else:
                    self.log.warning('login router failed')
            else:
                print('router is  on-line')




def test():
    ru = RouterUtils()
    # ru.ensureTryOnline()
    # ru.test()
    routerip = '192.168.0.1'
    password = 'cvlabpassword'

    status = None
    if os.path.exists('status.pkl'):
        # if False:
        with open('status.pkl', 'rb') as fd:
            status = p.load(fd)
            print(status)
            rp = ru.parseRouterParam(status['routerparam'])
            print(rp)
            lp = ru.parseLanParam(status['lanparam'])
            print(lp)
            wp = ru.parseWlanParam(status['wlanparam'])
            print(wp)
            wap = ru.parseWanParam(status['wanparam'])
            print(wap)
            stp = ru.parseStatParam(status['statparam'])
            print(stp)
    else:
        # login router
        result = ru.doLogin(routerip, password)
        if result:
            print(ru.doReboot())
            while ru.checkConnectivity():
                pass
            print('off line')

            status = ru.getRouterStatus()
            rp = ru.parseRouterParam(status['routerparam'])
            print(rp)
            lp = ru.parseLanParam(status['lanparam'])
            print(lp)
            wp = ru.parseWlanParam(status['wlanparam'])
            print(wp)
            wap = ru.parseWanParam(status['wanparam'])
            print(wap)
            stp = ru.parseStatParam(status['statparam'])
            print(stp)

def testWx():
    ru = RouterUtils()
    routerip = '192.168.0.1'
    password = 'cvlabpassword'
    login_result = ru.doTryLogin(routerip, password)
    if login_result:
        status = ru.getRouterStatus()
        ru.send2Wx('router status', ru.getStatusStr(status))


if __name__ == "__main__":
    ru = RouterUtils()
    sercerchanid = r'http://sc.ftqq.com/[Your ID here]send?'
    ru.setServerChanID(sercerchanid)
    routerip = '192.168.1.1'
    routerpassword = 'routerpassword'

    # check network connectivity and if the router is off line then reboot reboot and then report router status throught wechat
    ru.doTryOnlineAndReportIp(routerip, routerpassword)
