## multiplayer online server

- 多人在线服务器
- 使用grpc通信

## 当前进度

- 向服务器发送 `name`，返回 `hello name`
- 完善`pytest`测试

## 生成protobuf文件

- `./src/protobuf/rpc.proto`: protobuf文件
- `/src/protobuf/rpc_pb2.py`: 用来和 protobuf 数据进行交互，这个就是根据proto文件定义好的数据结构类型生成的python化的数据结构文件
- `/src/protobuf/rpc_pb2_grpc.py`: 用来和 grpc 进行交互，这个就是定义了rpc方法的类，包含了类的请求参数和响应等等，可用python直接实例化调用

```bash
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. ./src/protobuf/rpc.proto
```

## 运行程序

```bash
# 创建conda环境
conda create -n multiplayer python=3.8
# 激活conda环境
conda activate multiplayer
# 安装第三方库
pip install -r requirements.txt

# 测试程序
pytest test\rpc_test.py
```
