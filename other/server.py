import queue
import random
import socket
import threading
import time
from urllib.request import urlopen

# 定义常量
LOG = True
VERSION = "v1.0.0"
PORT = 26104
START_TIME = time.perf_counter()
LOGFILENAME = time.asctime().replace(" ", "_").replace(":", "-")

# 初始化全局变量
busy_player = set()
end = False
lock = False
logQ = queue.Queue()
players = []
total = 0
total_success = 0


def str_num_to_int(num):
    try:
        return int(num)
    except ValueError:
        return None


# 获得服务器当前运行的时间
def getTime():
    sec = round(time.perf_counter() - START_TIME)
    minutes, sec = divmod(sec, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days} days, {hours} hours, {minutes} minutes, {sec} seconds"


# 用来获得外网ip地址，用于判断当前时候连接互联网
def getIp(public):
    if public:
        try:
            ip = urlopen("https://api64.ipify.org").read_1024chars_msg_from_sock().decode()
        except:
            ip = "127.0.0.1"
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
            except:
                ip = '127.0.0.1'
    return ip


# A function to Log/Print text. Used instead of print()
def log(data, key=None):
    global logQ
    if key is None:
        text = "SERVER: "
    else:
        text = f"Player{key}: "

    if data is not None:
        text += data
        print(text)

        if LOG:
            logQ.put(time.asctime() + ": " + text + "\n")
    else:
        logQ.put(None)


# 读取1024个字符，如果出错返回quit
def read_1024chars_msg_from_sock(sock, timeout=None):
    try:
        sock.settimeout(timeout)
        msg = sock.recv(1024).decode("utf-8").strip()
    except:
        msg = "quit"
    if msg:
        return msg
    return "quit"


# 用于向服务器发送消息的函数，此函数用于代替 socket.send()
# 因为它可以缓冲消息，处理数据包丢失，并且在消息无法发送时不会引发异常。
def write_1024chars_msg_with_sock(sock, msg):
    if msg:
        buffed_msg = msg + (" " * (1024 - len(msg)))
        try:
            sock.sendall(buffed_msg.encode("utf-8"))
        except:
            pass


# 生成唯一的随机四位数
def generate_unique_four_digit_number():
    key = random.randint(1000, 9999)
    for p in players:
        if p[1] == key:
            return generate_unique_four_digit_number()
    return key


# 给一个玩家的四位随机数，返回玩家的sock对象
# 如果玩家不存在，则返回None
def get_player_sock_by_four_digit_number(key):
    for p in players:
        if p[1] == str_num_to_int(key):
            return p[0]
    return None


# 使玩家忙碌（将玩家的四位随机数放入忙碌的人列表中）
def make_player_busy(*keys):
    global busy_player
    for key in keys:
        busy_player.add(str_num_to_int(key))


# 使玩家活跃（将玩家的四位随机数从忙碌的列表中移除）
def remove_player_busy(*keys):
    global busy_player
    for key in keys:
        busy_player.discard(str_num_to_int(key))


# 这个简单的函数处理双人比赛。在两个玩家游戏结束后返回。
# 如果玩家在比赛中断开连接，则返回True，否则返回False。
def two_player_game(sock1, sock2):
    while True:
        msg = read_1024chars_msg_from_sock(sock1)
        write_1024chars_msg_with_sock(sock2, msg)
        if msg == "quit":
            return True
        elif msg in ["draw", "resign", "end"]:
            return False


# 这个简单的函数处理三人比赛。在两个玩家游戏结束后返回。
# 如果玩家在比赛中断开连接，则返回True，否则返回False。
def three_player_game(sock1, sock2, sock3):
    while True:
        msg = read_1024chars_msg_from_sock(sock1)
        write_1024chars_msg_with_sock(sock2, msg)
        write_1024chars_msg_with_sock(sock3, msg)
        if msg == "quit":
            return True
        elif msg in ["draw", "resign", "end"]:
            return False


# 它处理每个玩家与服务器的通信。
def player(sock, key):
    while True:
        msg = read_1024chars_msg_from_sock(sock)
        if msg == "quit":
            return

        elif msg == "pStat":
            log("请求玩家统计数据.", key)
            latest_players = list(players)
            latest_busy = list(busy_player)

            if 0 < len(latest_players) < 11:
                write_1024chars_msg_with_sock(sock, "enum" + str(len(latest_players) - 1))
                for _, i in latest_players:
                    if i != key:
                        if i in latest_busy:
                            write_1024chars_msg_with_sock(sock, str(i) + "b")
                        else:
                            write_1024chars_msg_with_sock(sock, str(i) + "a")

        elif msg.startswith("rg"):
            log(f"请求与玩家 {msg[2:]} 一起玩", key)
            oSock = get_player_sock_by_four_digit_number(msg[2:])
            if oSock is not None:
                if str_num_to_int(msg[2:]) not in busy_player:
                    make_player_busy(key, msg[2:])
                    write_1024chars_msg_with_sock(oSock, "gr" + str(key))

                    write_1024chars_msg_with_sock(sock, "msgOk")
                    newMsg = read_1024chars_msg_from_sock(sock)
                    if newMsg == "ready":
                        log(f"玩家 {key} 在游戏里面作为白方")
                        if two_player_game(sock, oSock):
                            return
                        else:
                            log(f"玩家 {key} 结束游戏")

                    elif newMsg == "quit":
                        write_1024chars_msg_with_sock(oSock, "quit")
                        return

                    remove_player_busy(key)

                else:
                    log(f"玩家 {key} 请求一个忙碌的玩家，请求失败")
                    write_1024chars_msg_with_sock(sock, "errPBusy")
            else:
                log(f"玩家 {key} 发送的四位数字无效")
                write_1024chars_msg_with_sock(sock, "errKey")

        elif msg.startswith("gmOk"):
            log(f"接受玩家 {msg[4:]} 请求", key)
            oSock = get_player_sock_by_four_digit_number(msg[4:])
            write_1024chars_msg_with_sock(oSock, "start")
            log(f"玩家 {key} 当前在游戏为黑方")
            if two_player_game(sock, oSock):
                return
            else:
                log(f"玩家 {key} 结束优秀")
                remove_player_busy(key)

        elif msg.startswith("gmNo"):
            log(f"玩家发送了无效四位数字 {msg[4:]} .", key)
            write_1024chars_msg_with_sock(get_player_sock_by_four_digit_number(msg[4:]), "nostart")
            remove_player_busy(key)


# log线程处理log信息，写入到文件中
def logThread():
    global logQ
    while True:
        time.sleep(1)
        with open("SERVER_LOG_" + LOGFILENAME + ".txt", "a") as f:
            while not logQ.empty():
                data = logQ.get()
                if data is None:
                    return
                else:
                    f.write(data)


# 这是一个在后台运行的线程，用于删除断开连接的人
def kickDisconnectedThread():
    global players
    while True:
        time.sleep(10)
        for sock, key in players:
            try:
                ret = sock.send(b"........")
            except:
                ret = 0

            if ret > 0:
                cntr = 0
                diff = 8
                while True:
                    cntr += 1
                    if cntr == 8:
                        ret = 0
                        break

                    if ret == diff:
                        break
                    diff -= ret

                    try:
                        ret = sock.send(b"." * diff)
                    except:
                        ret = 0
                        break

            if ret == 0:
                log(f"玩家 {key} 已断开连接，正在从玩家列表中删除")
                try:
                    players.remove((sock, key))
                except:
                    pass


# 这是一个在后台运行的线程，用于收集用户输入命令
def adminThread():
    global end, lock
    while True:
        msg = input().strip()
        log(msg)

        if msg == "report":
            log(f"{len(players)} players are online right now,")
            log(f"{len(players) - len(busy_player)} are active.")
            log(f"{total} connections attempted, {total_success} were successful")
            log(f"Server is running {threading.active_count()} threads.")
            log(f"Time elapsed since last reboot: {getTime()}")
            if players:
                log("LIST OF PLAYERS:")
                for cnt, (_, player) in enumerate(players):
                    if player not in busy_player:
                        log(f" {cnt + 1}. Player{player}, Status: Active")
                    else:
                        log(f" {cnt + 1}. Player{player}, Status: Busy")

        elif msg == "mypublicip":
            log("Determining public IP, please wait....")
            PUBIP = getIp(public=True)
            if PUBIP == "127.0.0.1":
                log("An error occurred while determining IP")

            else:
                log(f"This machine has a public IP address {PUBIP}")

        elif msg == "lock":
            if lock:
                log("Aldready in locked state")
            else:
                lock = True
                log("Locked server, no one can join now.")

        elif msg == "unlock":
            if lock:
                lock = False
                log("Unlocked server, all can join now.")
            else:
                log("Aldready in unlocked state.")

        elif msg.startswith("kick "):
            for k in msg[5:].split():
                sock = get_player_sock_by_four_digit_number(k)
                if sock is not None:
                    write_1024chars_msg_with_sock(sock, "close")
                    log(f"Kicking player{k}")
                else:
                    log(f"Player{k} does not exist")

        elif msg == "kickall":
            log("Attempting to kick everyone.")
            latestplayers = list(players)
            for sock, _ in latestplayers:
                write_1024chars_msg_with_sock(sock, "close")

        elif msg == "quit":
            lock = True
            log("Attempting to kick everyone.")
            latestplayers = list(players)
            for sock, _ in latestplayers:
                write_1024chars_msg_with_sock(sock, "close")

            log("Exiting application - Bye")
            log(None)

            end = True
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", PORT))
            return

        else:
            log(f"Invalid command entered ('{msg}').")
            log("See 'onlinehowto.txt' for help on how to use the commands.")


# 进行初始检查并允许玩家进入。
def initPlayerThread(sock):
    global players, total, total_success
    log("新客户端正在尝试连接。")
    total += 1

    if read_1024chars_msg_from_sock(sock, 3) != "PyChess":
        log("客户端发送的标头无效，正在关闭连接。")
        write_1024chars_msg_with_sock(sock, "errVer")

    elif read_1024chars_msg_from_sock(sock, 3) != VERSION:
        log("客户端发送了无效的版本信息，正在关闭连接。")
        write_1024chars_msg_with_sock(sock, "errVer")

    elif len(players) >= 10:
        log("服务器正忙，正在关闭新连接。")
        write_1024chars_msg_with_sock(sock, "errBusy")

    elif lock:
        log("SERVER: 服务器已锁定，正在关闭连接。")
        write_1024chars_msg_with_sock(sock, "errLock")

    else:
        total_success += 1
        key = generate_unique_four_digit_number()
        log(f"连接成功，已分配四位数字 - {key}")
        players.append((sock, key))

        write_1024chars_msg_with_sock(sock, "key" + str(key))
        player(sock, key)
        write_1024chars_msg_with_sock(sock, "close")
        log(f"玩家 {key} 退出")
        try:
            players.remove((sock, key))
        except:
            pass
        remove_player_busy(key)
    sock.close()


# Initialize the main socket
log(f"欢迎来到服务器,版本 {VERSION}\n")
log("初始化...")
mainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mainSock.bind(("0.0.0.0", PORT))

IP = getIp(public=False)
if IP == "127.0.0.1":
    log("此计算机似乎未连接到互联网。")
else:
    log(f"此服务器的IP地址为：{IP}:{PORT}")

mainSock.listen(16)
log("已成功启动.")
log(f"接受 {IP}:{PORT} 的连接 \n")

threading.Thread(target=adminThread).start()
threading.Thread(target=kickDisconnectedThread, daemon=True).start()
if LOG:
    log("已启用日志记录。开始记录所有输出")
    threading.Thread(target=logThread).start()

while True:
    s, _ = mainSock.accept()
    if end:
        break

    threading.Thread(target=initPlayerThread, args=(s,), daemon=True).start()
mainSock.close()
