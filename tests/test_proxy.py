from nboost.helpers import prepare_response, dump_json
from nboost.protocol import HttpProtocol
from nboost.server import SocketServer
from nboost.proxy import Proxy
import requests
import unittest


class TestServer(SocketServer):
    def loop(self, client_socket, address):
        response = {}
        protocol = HttpProtocol(2048)
        protocol.set_response(response)
        response['body'] = dump_json(RESPONSE)
        client_socket.send(prepare_response(response))
        client_socket.close()


class TestProxy(unittest.TestCase):
    def test_proxy(self):
        server = TestServer(port=9500, verbose=True)
        proxy = Proxy(host='0.0.0.0', port=8000, uhost='0.0.0.0',
                      model_dir='shuffle-model', uport=9500,
                      bufsize=2048, delim='. ', multiplier=5, verbose=True)
        proxy.start()
        server.start()
        proxy.is_ready.wait()
        server.is_ready.wait()

        # search
        params = dict(q='test_field;test query', size=3)

        proxy_res = requests.get('http://localhost:8000/test/_search', params=params)
        print(proxy_res.content)
        self.assertTrue(proxy_res.ok)
        json = proxy_res.json()
        self.assertEqual(3, len(json['hits']['hits']))

        # fallback
        server_res = requests.get('http://localhost:9500/test', params=params)
        print(server_res.content)
        self.assertTrue(server_res.ok)

        # status
        status_res = requests.get('http://localhost:8000/nboost/status')
        self.assertTrue(status_res.ok)
        print(status_res.content.decode())
        # self.assertEqual(0.5, status_res.json()['vars']['upstream_mrr']['avg'])

        # invalid host
        proxy.config['uport'] = 2000
        invalid_res = requests.get('http://localhost:8000')
        print(invalid_res.content)
        self.assertFalse(invalid_res.ok)

        proxy.close()
        server.close()


RESPONSE = {
    "took": 5,
    "timed_out": False,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 1.3862944,
        "hits": [
            {
                "_index": "twitter",
                "_type": "_doc",
                "_id": "0",
                "_score": 1.4,
                "_source": {
                    "message": "trying out Elasticsearch",
                }
            }, {
                "_index": "twitter",
                "_type": "_doc",
                "_id": "1",
                "_score": 1.34245,
                "_source": {
                    "message": "second result",
                }
            },
            {
                "_index": "twitter",
                "_type": "_doc",
                "_id": "2",
                "_score": 1.121234,
                "_source": {
                    "message": "third result",
                }
            }
        ]
    }
}
