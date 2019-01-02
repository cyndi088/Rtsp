import json
import time
import re
import urllib.request
from flask import Flask
from flask import jsonify
from flask import request
from concurrent.futures import ThreadPoolExecutor


app = Flask(__name__)

executor = ThreadPoolExecutor(10)    # 同时处理的最大线程数


@app.route('/', methods=['GET'])
def index():
    return "Hello，欢迎访问API！"


@app.route('/getrtsp', methods=['POST'])
def get_rtsp():
    rtsp = Rtsp()
    cam_id_3d = request.form.get('dev_id')
    streaming_url, session, token, t = rtsp.get_streaming_url(cam_id_3d)
    if streaming_url:
        streaming_url = streaming_url
        executor.submit(rtsp.keep_alive, session, token)
        json_data = {}
        status = 1
    else:
        streaming_url = ''
        json_data = {}
        status = 2
    output = {'rtsp_url': streaming_url, 'json_data': json_data, 'time': t, 'status': status}
    return jsonify(output)


class Rtsp(object):

    def __init__(self):
        self.API_URL = "http://111.1.30.117:8089/api/"
        self.USERNAME = "admin"
        self.PASSWD = "123456"

    def api_auth(self):
        url = self.API_URL + 'v1/login'
        req = urllib.request.Request(url)
        data = {"userName": self.USERNAME, "userPassword": self.PASSWD, "effectiveTime": 3600000}
        jsondata = json.dumps(data)
        jsondataasbytes = jsondata.encode('utf-8')
        content_length = len(jsondataasbytes)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', content_length)
        response = urllib.request.urlopen(req, jsondataasbytes)
        token = json.loads(response.read().decode('utf8'))['token']
        return token

    def call_api(self, method, token, **kwargs):
        url = self.API_URL + method
        req = urllib.request.Request(url)
        if kwargs:
            req.data = urllib.parse.urlencode(kwargs).encode('utf-8')
        else:
            req.data = None
        req.add_header('Authorization', 'Token {}'.format(token))
        response = urllib.request.urlopen(req)
        ret = response.read()
        if ret:
            json_data = json.loads(ret.decode('utf8'))
        else:
            json_data = None
        return json_data

    def get_streaming_url(self, cameraID):
        token = self.api_auth()
        json_data = self.call_api('media/beginRealplay', token, cameraid='{}$0'.format(cameraID), streamType=1)
        video_urls = json_data['url']
        session = json_data['session']
        pattern = re.compile('rtsp://111.1.30.117:.*')
        try:
            if pattern.search(video_urls):
                streaming_url = pattern.search(video_urls).group(0).split('|')[0]
                t = time.time()
            else:
                streaming_url = None
                t = time.time()
        except TypeError:
            raise Exception('Temporarily unavailable. Please try again.')
        print("#" * 20 + "URL" + "#" * 20)
        print(streaming_url)
        print("#"*40)
        return streaming_url, session, token, t

    def keep_alive(self, session, token):
        t = time.time()
        print('2222222222222222')
        while time.time() - t < 3600:
            self.call_api('media/sendHeartbeat', token, session=session)
            time.sleep(30)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
