import asyncio
import threading
import grpc

from src.protobuf import rpc_pb2_grpc, rpc_pb2
from src.server.multiplayer_online_server import server_start


def server_thread():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(asyncio.wait([server_start()]))
    loop.close()


def test_hello():
    # 新建线程启动服务器
    server_t = threading.Thread(target=server_thread)
    server_t.start()
    # 与grpc服务器建立连接
    channel = grpc.insecure_channel('localhost:50051')
    # 调用 rpc 服务
    for i in range(2):
        stub = rpc_pb2_grpc.MultiplayerOnlineStub(channel)
        response = stub.Hello(rpc_pb2.HelloRequest(name='abc'))
        assert str(response) == 'message: "hello abc"\n'


if __name__ == "__main__":
    test_hello()
