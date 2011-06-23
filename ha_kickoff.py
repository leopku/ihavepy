#!/usr/bin/env python

__author__ = 'leopku@qq.com'
__version__ = '%prog 1.0'
__doc__ = """HAProxy kickoff is a console kit for enable/disable
server(s) from haproxy.
Author: %s
Version: %s

History:
    2011-06-22:
        + first create this kit. add class 
          AppServer & HAProxy. and test code.
    2011-06-23:
        + add argument parser to using easily
          under console.
          add --dry-run and --test mode.
""" % (__author__, __version__)

import os
import os.path
import sys
import re
import optparse
import shutil

class AppServer:
    def __init__(self, ip, port, is_enable=False):
        self.is_enable = is_enable
        self.ip = ip
        self.port = port
        self.enable_switched = False

    def switch_enable(self, is_enable):
        self.is_enable = is_enable
        self.enable_switched = True

class HAProxy:
    def __init__(self, config_path):
        self.config_path = config_path
        self.lines = open(config_path).readlines()
        self.appservers = []
        self.ip_list = []

    def parse_config(self):
        for line in self.lines:
            if re.match('server', line.strip()) or re.match('#\s*server', line.strip()):
                m = re.search(r'(\S+):(\d+)', line)
                ip = m.group(1)
                port = m.group(2)
                is_enable = False if re.match('#', line.strip()) else True
                appserver = AppServer(ip, port, is_enable)
                self.appservers.append(appserver)
                self.ip_list.append(ip)

    def refresh_config(self):
        for i in range(len(self.lines)):
            for appserver in self.appservers:
                if appserver.enable_switched:
                    server_pattern = '%s:%s' % (appserver.ip, appserver.port)
                    if re.search(server_pattern, self.lines[i]):
                        self.lines[i] = re.sub('#', '', self.lines[i]) if appserver.is_enable else re.sub('^', '#', self.lines[i])

    def print_config(self):
        for line in self.lines:
            print(line)

    def save_config(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        fp = open(config_path, 'w')
        fp.writelines(self.lines)
        fp.close()

if __name__ == "__main__":

    __HAProxyCFG__ = '/etc/haproxy/haproxy.cfg'
    # for test
    #__HAProxyCFG__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'haproxy.cfg')
    #
    __HAProxyReloadCmd__ = '/etc/init.d/haproxy reload'
    __usage__ = 'python %prog [--ip=ip] [--port=port] <--enable|disable> <--dry-run> <--reload> <--test>'
    __desc__ = 'HAProxy kickoff is a console kit for enable/disable server(s) from haproxy written by leo(leopku#qq.com).Feel free for this smart kit.'

    parser = optparse.OptionParser(usage=__usage__, version=__version__, description=__desc__,)
    parser.add_option('--ip', metavar='192.168.0.123', help='Ip address which to be enabled/disabled. Comma seperated for multi ip.')
    parser.add_option('--port', metavar='321', help='Port number of one ip which to be enabled/disabled. NOTE: this parameter only work with single ip.')
    parser.add_option('-e', '--enable', dest='switch_status', action='store_true', help='Enable a service listenning on ip(s)[:port]. This option is OFF by default.')
    parser.add_option('-d', '--disable', dest='switch_status', action='store_false', help='Disable a service listenning on ip(s)[:port]. This option is ON by default. Do not specify both --enable and --disable was same as --disable.')
    parser.add_option('--reload', action='store_true', help='Reload haproxy after services enabled/disabled.')
    parser.add_option('--dry-run', dest='dry', action='store_true', help='Only print new config and any changes should NOT save to config file.')
    parser.add_option('--test', action='store_true', help='Make a copy of haproxy config file to the same folder of this script for testing. Any read/write should affect in the copy version.')
    opts, args = parser.parse_args()

    if opts.ip is None:
        sys.exit('ERROR: one of followed parameters were required: --ip.\n\nUse -h to get help.')
    else:
        if opts.test:
            haproxy_cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'haproxy.cfg')
            if not os.path.exists(haproxy_cfg):
                shutil.copy(__HAProxyCFG__, haproxy_cfg)
            __HAProxyCFG__ = haproxy_cfg
        haproxy = HAProxy(__HAProxyCFG__)
        haproxy.parse_config()
        if opts.port is None:
            for appserver in haproxy.appservers:
                if appserver.ip in opts.ip.split(',') and appserver.is_enable is not opts.switch_status:
                    appserver.switch_enable(opts.switch_status)
        else:
            for appserver in haproxy.appservers:
                if appserver.ip == opts.ip and appserver.port == port and appserver.is_enable is not opts.switch_status:
                    appserver.switch_enable(opts.switch_status)

        haproxy.refresh_config()
        if opts.dry:
            haproxy.print_config()
        else:
            haproxy.save_config()
            if opts.reload:
                os.system(__HAProxyReloadCmd__)
