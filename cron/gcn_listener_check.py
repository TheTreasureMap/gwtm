import os
import datetime
import subprocess

class scripts():
    def __init__(self, script, log):
        self.script = script
        self.log = log

def main():
    scrips = [
                scripts('gcn_listener.py', 'gwtm_gcn.log')
            ]

    cwd = os.getcwd()
    for s in scrips:
        status = os.system("ps -fe | grep -v grep | grep "+s.script)
        if status == 0:
            print(s.script+' is running')
        else:
            print('Warning: '+s.script+' not running !! ')
            os.system('python /var/www/gwtm/cron/gcn_listener.py >> '+cwd+'/cron/'+s.log+' 2>&1 &')

main()

