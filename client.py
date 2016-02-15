# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import shutil
import signal
import thread
import subprocess

import SimpleHTTPServer
import SocketServer
import cgi
import urllib2

import zipfile


WORKING_DIR = os.getcwd()
AGENT_ADDR = ''
AGENT_PORT = 15100


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

        with open(filename, 'wb') as fout:
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

        return filename

class Agent(object):
    def __init__(self, name):
        self.name = name
        self.app_path = os.path.join(Config.env.get('apps_path'), self.name)
        self.log_path = os.path.join(Config.env.get('logs_path'), self.name)
        self.script_file = os.path.join(self.app_path, 'start.py')

        if not os.path.isdir(self.app_path):
            os.makedirs(self.app_path)
        if not os.path.isdir(self.log_path):
            os.makedirs(self.log_path)

    def fetch(self, url):
        # Delete everything reachable from the directory named in self.app_path,
        # assuming there are no symbolic links.
        # CAUTION:  This is dangerous!  For example, if self.app_path == '/', it
        # could delete all your disk files.
        for root, dirs, files in os.walk(self.app_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        # stream download
        filename = HTTPClient.download(url, self.app_path)

        # unzip
        with zipfile.ZipFile(filename, 'r') as z:
            z.extractall(self.app_path)

    def start(self, port):
        stdout_file = os.path.join(self.log_path, '{0}.stdout.log'.format(port))
        stderr_file = os.path.join(self.log_path, '{0}.stderr.log'.format(port))
        pid_file = os.path.join(self.log_path, '{0}.pid'.format(port))

        kwargs = {'script': self.script_file, 'port': port}
        cmd = 'python {0[script]} --port={0[port]}'.format(kwargs)
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=open(stdout_file, 'w'),
                                stderr=open(stderr_file, 'a'),
                                preexec_fn=os.setpgrp)
        with open(pid_file, 'wb') as fout:
            fout.write(str(proc.pid))
        proc.communicate()

    def stop(self, port):
        pid_file = os.path.join(self.log_path, '{0}.pid'.format(port))

        # Kill /bin/sh -c python xx --port=xx
        with open(pid_file, 'r') as fin:
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

    def execute(cls, name):
        method = getattr(cls, name)
        if not method:
            raise Exception("Method %s not implemented" % name)
        return method


class HTTPServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def write(self, text):
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', len(text))
        self.end_headers()
        self.wfile.write(text)

    def build_body(self, code=200, msg=''):
        return '{\"code\": \"%s\", \"msg\": \"%s\"}' % (code, msg)

    def well_done(self):
        self.write(self.build_body())

    def agent_handler(self, instruct):
        name = instruct.get('agent_name')
        port = instruct.get('service_port')
        action = instruct.get('agent_action')
        link = instruct.get('package_link', '')

        agent = Agent(name)
        if action == ('fetch'):
            agent.execute(action)(link)
        elif action in ('start', 'stop', 'restart'):
            agent.execute(action)(port)

    def do_GET(self):
        # logging.warning("======= GET STARTED =======")
        # logging.warning(self.headers)
        # SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        self.well_done()

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        instruct = dict()
        for item in form.list:
            instruct[item.name] = item.value
        # instruct = {
        #     'agent_name'  : 'hello',
        #     'service_port': '8000',
        #     'agent_action': 'start',
        #     'package_link': 'http://127.0.0.1/packages/hello-v1.0.zip'
        # }

        try:
           thread.start_new_thread(self.agent_handler, (instruct,))
        except:
           print "Error: unable to start thread"
        
        self.well_done()


def main(argv):
    Handler = HTTPServer
    httpd = SocketServer.TCPServer(('', AGENT_PORT), Handler)
    print '@rochacbruno Python http server version 0.1 (for testing purposes only)'
    print 'Serving at: http://%(interface)s:%(port)s' % dict(interface=AGENT_ADDR or 'localhost', port=AGENT_PORT)
    httpd.serve_forever()

    # agent = Agent('hello')
    # agent.fetch('http://static.ricoxie.com/robots.txt')
    # agent.stop(8080)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

# -----------------------------------------------------------------
# ----------------------    Test HTTPServer   ---------------------
# -----------------------------------------------------------------
# import requests
# instruct = {
#     'agent_name'  : 'hello',
#     'service_port': '8021',
#     'agent_action': 'stop',
#     'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
# }
# print requests.post("http://localhost:15100", data=instruct).text
