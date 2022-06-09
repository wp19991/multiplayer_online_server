import time
import grpc

from src.protobuf import rpc_pb2_grpc, rpc_pb2


def run():
    # 与grpc服务器建立连接
    channel = grpc.insecure_channel('localhost:50051')
    # 调用 rpc 服务
    while True:
        time.sleep(1)
        stub = rpc_pb2_grpc.MultiplayerOnlineStub(channel)
        response = stub.Hello(rpc_pb2.HelloRequest(name='abc{}'.format(time.time())))
        print("client received: ", response)


if __name__ == "__main__":
    run()
