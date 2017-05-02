# Router Utility

## Introduction
Router Utility is implemented using python2.7. It monitors router's status, check the network connectivity. It reboots the router and report router's status throught wechat when router is off-line.

Its message sending function is implemented with server chan(http://sc.ftqq.com/3.version), so you have to login server chan with your github account and get a server chan ID.

## Settings
You have to set the router password and ip. In addition, server chan id is necessary.

sercerchanid = r'http://sc.ftqq.com/[Your server chan ID here].send?'

routerip = '192.168.1.1'

routerpassword = 'routerpassword'

you have to know that the log file path is the code directory

## Supported devices
Now Router Utility only supports TP-LINK routers

## Others
please feel free to issue problems
