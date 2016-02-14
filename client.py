# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os, signal
import threading
import urllib2
import subprocess


WORKING_DIR = os.getcwd()


class classproperty(object):

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        if instance is None:
            instance = owner()
        return self.getter(instance)


class Config(object):

    def __init__(self):
        self.env = {
            'apps_path': os.path.join(WORKING_DIR, 'apps'),
            'logs_path': os.path.join(WORKING_DIR, 'logs'),
            'tmp_path': os.path.join(WORKING_DIR, 'tmp'),
        }

    @classproperty
    def env(cls):
        return cls.env


class HTTPClient(object):

    @staticmethod
    def download(url, path=None, filename=None):
        """ Doing stream processing on a http response.
        Reference: http://stackoverflow.com/a/22776/286994
        """

        path = path or os.getcwd()
        filename = os.path.join(path, filename or url.split('/')[-1])

        # Avoid overwriting.
        if os.path.isfile(filename):
            raise Exception('File exists!')

        response = urllib2.urlopen(url)
        meta = response.info()
        file_sz = int(meta.getheaders('Content-Length')[0])

        with open(os.path.join(path, filename), 'wb') as fout:
            down_sz = 0
            block_sz = 1024 * 4

            while True:
                chunk = response.read(block_sz)
                if not chunk: break
                fout.write(chunk)

                # Download progress.
                # down_sz += len(chunk)
                # percent = float(down_sz) / file_sz
                # status = r'{0}  [{1:.2%}]'.format(down_sz, percent)
                # status = status + chr(8) * (len(status) + 1)
                # sys.stdout.write(status,)


class Agent(object):
    def __init__(self, name):
        self.name = name
        self.app_path = os.path.join(Config.env.get('apps_path'), self.name)
        self.log_path = os.path.join(Config.env.get('logs_path'), self.name)
        self.script_file = os.path.join(self.app_path, 'start.py')
        self.stdout_file = os.path.join(self.log_path, 'stdout.log')
        self.stderr_file = os.path.join(self.log_path, 'stderr.log')
        self.pid_file = os.path.join(self.log_path, 'server.pid')
        if not os.path.isdir(self.app_path):
            os.makedirs(self.app_path)
        if not os.path.isdir(self.log_path):
            os.makedirs(self.log_path)

    def download(self, url):
        HTTPClient.download(url, self.app_path)
        # unzip

    def fetch(self, url):
        thread = threading.Thread(
            target = self.download,
            args=(url,),
        )
        thread.start()

    def start(self, port):
        kwargs = {'script': self.script_file, 'port': port}
        cmd = 'python {0[script]} --port={0[port]}'.format(kwargs)
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=open(self.stdout_file, 'w'),
                                stderr=open(self.stderr_file, 'a'),
                                preexec_fn=os.setpgrp)
        with open(self.pid_file, 'wb') as fout:
            fout.write(str(proc.pid))
        proc.communicate()

    def stop(self, port):
        # Kill /bin/sh -c python xx --port=xx
        with open(self.pid_file, 'r') as fin:
            val = fin.read()
            if val:
                os.kill(int(val), signal.SIGTERM)
        # Kill python xx --port=xx
        cmd = 'fuser -k -n tcp {0}'.format(port)
        proc = subprocess.Popen(cmd, shell=True)

    def restart(self, port):
    	try:
            self.stop(port)
        except:
        	pass
        self.start(port)


class HTTPServer(object):
    pass

def main(argv):
    agent = Agent('hello')
    # agent.fetch('http://static.ricoxie.com/robots.txt')
    agent.restart(8080)
    # import subprocess
    # p = subprocess.Popen(['ls', '-a'], stdout=subprocess.PIPE, 
    #                                    stderr=subprocess.PIPE)
    # out, err = p.communicate()
    # print out

if __name__ == "__main__":
    sys.exit(main(sys.argv))


