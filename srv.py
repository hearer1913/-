import socket
import time

UDP_IP = "192.168.17.116"
UDP_PORT = 5005


class Player:
    def __init__(self, game):
        self.GameID = game
        self.lastCon = time.time()
        self.Cubes = "00000"
        self.isRolling = False
        self.Selected_dice = "00000"


# ---------------------
PLAYERS: dict[str: Player] = {}  # {PlayerAddr: Player, ...}
GAMES: dict[int: tuple[str, str]] = {}  # {GameID: [PlayerAddr1 PlayerAddr2], ...}
# ---------------------

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(5)

while True:
    for address in list(PLAYERS.keys()):
        try:
            if time.time() - PLAYERS[address].lastCon >= 5:
                gameID = PLAYERS[address].GameID
                if gameID in GAMES.keys():  # Проверить запущена ли игра
                    for player in GAMES[gameID]:
                        del PLAYERS[player]  # Кик всех
                    del GAMES[gameID]
                else:  # Иначе просто кикает игрока
                    del PLAYERS[address]  # Кик игрока, если он не отправлял запросы больше 5 секунд
        except KeyError:
            continue
    try:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    except TimeoutError:
        continue

    received_message = data.decode("utf-8").split("/")
    match received_message[0]:
        case "STEAL":  # Отпрака данных с сервера
            if addr[0] not in PLAYERS.keys():  # Если игрок берёт данные, когда не подключен к серверу
                sock.sendto(b"400", addr)
                continue
            PLAYERS[addr[0]].lastCon = time.time()
            if PLAYERS[addr[0]].GameID not in GAMES.keys():  # Ожидание второго игрока
                sock.sendto(b"0", addr)
                continue
            for p in GAMES.get(PLAYERS[addr[0]].GameID):
                if p == addr[0]:
                    continue
                if PLAYERS[p].isRolling:
                    sock.sendto(("/" + PLAYERS[p].Selected_dice).encode(), addr)
                else:
                    sock.sendto(PLAYERS[p].Cubes.encode(), addr)

        case "START":  # Подключение к серверу
            if addr[0] in PLAYERS.keys():  # Ошибка, если игрок уже подключен
                sock.sendto(b"400", addr)
                continue
            gameID = (list(GAMES.keys())[-1] + 1) if GAMES else 0
            if PLAYERS:
                GAMES[gameID] = (list(PLAYERS.keys())[-1], addr[0])  # Создание игры
            PLAYERS[addr[0]] = Player(gameID)
            sock.sendto(b"200", addr)

        case "SEND":  # Получение данных на сервер
            if addr[0] not in PLAYERS.keys():  # Ошибка, если игрок уже подключен
                sock.sendto(b"400", addr)
                continue

            try:
                PLAYERS[addr[0]].lastCon = time.time()
            except KeyError:
                continue

            if received_message[1] == "1":
                PLAYERS[addr[0]].isRolling = True
                try:
                    PLAYERS[addr[0]].Selected_dice = received_message[2]
                except:
                    print("old version Client")
                    continue
            else:
                PLAYERS[addr[0]].isRolling = False
                PLAYERS[addr[0]].Cubes = received_message[1]
            sock.sendto(b"200", addr)

        case "LEAVE":  # Выход с сервера
            if addr[0] not in PLAYERS.keys():
                sock.sendto(b"400", addr)
                continue
            gameID = PLAYERS[addr[0]].GameID
            if gameID in GAMES.keys():
                for player in GAMES[gameID]:
                    del PLAYERS[player]  # Кик второго человека
                del GAMES[gameID]
            else:
                del PLAYERS[addr[0]]
            sock.sendto(b"200", addr)
