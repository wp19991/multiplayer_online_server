import asyncio
from grpc.experimental import aio
from concurrent import futures

from src.protobuf import rpc_pb2_grpc, rpc_pb2


class RequestRpc(rpc_pb2_grpc.MultiplayerOnlineServicer):
    async def Hello(self, request, context):
        return rpc_pb2.HelloReply(message='hello {}'.format(request.name))


async def server_start():
    server = aio.server(futures.ThreadPoolExecutor(max_workers=10), options=[
        ('grpc.so_reuseport', 0),
        ('grpc.max_send_message_length', 100 * 1024 * 1024),
        ('grpc.max_receive_message_length', 100 * 1024 * 1024),
        ('grpc.enable_retries', 1),
        ('grpc.keepalive_permit_without_calls', 0),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_time_ms', 10000)
    ])
    # 注册服务
    rpc_pb2_grpc.add_MultiplayerOnlineServicer_to_server(RequestRpc(), server)
    server.add_insecure_port('[::]:50051')
    # 启动服务
    await server.start()
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([server_start()]))
    loop.close()
