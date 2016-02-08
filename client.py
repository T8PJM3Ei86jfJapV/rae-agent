# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
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
            'app_path': os.path.join(WORKING_DIR, 'apps'),
            'log_path': os.path.join(WORKING_DIR, 'logs'),
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
        self.path = os.path.join(Config.env.get('app_path'), self.name)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def download(self, url):
        HTTPClient.download(url, self.path)
        # unzip

    def fetch(self, url):
        thread = threading.Thread(
            target = self.download,
            args=(url,),
        )
        thread.start()

    def start(self, port=8080):
        script = ''.join(os.path.join(self.path, 'start.py'))
        cmd = ['python', script, '--port={0}'.format(port)]
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE).wait()
        out, err = process.communicate()
        sys.stdout.write(out or err)

    def stop(self):
        pass

    def restart(self):
        self.stop()
        self.start()


class HTTPServer(object):
    pass

def main(argv):
    agent = Agent('hello')
    # agent.fetch('http://static.ricoxie.com/robots.txt')
    agent.start()
    # import subprocess
    # p = subprocess.Popen(['ls', '-a'], stdout=subprocess.PIPE, 
    #                                    stderr=subprocess.PIPE)
    # out, err = p.communicate()
    # print out

if __name__ == "__main__":
    sys.exit(main(sys.argv))

