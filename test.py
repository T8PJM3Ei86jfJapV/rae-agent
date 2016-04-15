# -*- coding: utf-8 -*-

import requests

# ----------------------------    1、拉取程序包    -------------------------
instruct = {
    'agent_name'  : 'hello',
    'service_port': '8080',
    'agent_action': 'fetch',
    'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
}
print requests.post("http://192.168.229.135:15100/async", data=instruct).text
# > {"code": "200", "msg": ""}

# ------------------------------     2、启动      ---------------------------
instruct = {
    'agent_name'  : 'hello',
    'service_port': '8080',
    'agent_action': 'start',
    'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
}
print requests.post("http://192.168.229.135:15100/async", data=instruct).text
# > {"code": "200", "msg": ""}

# ------------------------------     3、重启      ---------------------------
instruct = {
    'agent_name'  : 'hello',
    'service_port': '8080',
    'agent_action': 'restart',
    'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
}
print requests.post("http://192.168.229.135:15100/async", data=instruct).text
# > {"code": "200", "msg": ""}

# ---------------------------    4、查看活跃状态    -------------------------
instruct = {
    'agent_name'  : 'hello',
    'service_port': '8080',
    'agent_action': 'alive',
    'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
}
print requests.post("http://192.168.229.135:15100/sync", data=instruct).text
# > {"code": "200", "msg": "All well!"}

# ------------------------------      5、停止      ---------------------------
instruct = {
    'agent_name'  : 'hello',
    'service_port': '8080',
    'agent_action': 'stop',
    'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
}
print requests.post("http://192.168.229.135:15100/async", data=instruct).text
# > {"code": "200", "msg": ""}

# --------------------------     6、查看活跃状态    --------------------------
instruct = {
    'agent_name'  : 'hello',
    'service_port': '8080',
    'agent_action': 'alive',
    'package_link': 'http://static.ricoxie.com/tmp/hello-v1.0.0.zip'
}
print requests.post("http://192.168.229.135:15100/sync", data=instruct).text
# > {"code": "300", "msg": "Something bad!"}
