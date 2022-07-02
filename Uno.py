import json
from multiprocessing import connection
import random
import socket
import threading
import tkinter
import select

import bcrypt
from PIL import Image, ImageTk

""" 
====Ideas====
Main Menu Animation
Deck and player size

"""


colours = ("R", "G", "B", "Y")
values = (
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "Stop",
    "Reverse",
    "Draw2",
    "Draw4",
    "Colour",
)
types = {
    "0": "casual",
    "1": "casual",
    "2": "casual",
    "3": "casual",
    "4": "casual",
    "5": "casual",
    "6": "casual",
    "7": "casual",
    "8": "casual",
    "9": "casual",
    "Stop": "active",
    "Reverse": "active",
    "Draw2": "active",
    "Draw4": "wild",
    "Colour": "wild",
}


class Card:
    def __init__(self, colour, value, playability, genimg=True):

        self.value = value
        self.type = playability

        if types[value] == "wild":
            self.colour = "nocolour"
            if genimg:
                self.filep = f"Uno Cards/{value}.png"
                self.img = ImageTk.PhotoImage(Image.open(self.filep))
        else:
            self.colour = colour
            if genimg:
                self.filep = f"Uno Cards/{colour+value}.png"
                self.img = ImageTk.PhotoImage(Image.open(self.filep))

    def __str__(self):
        return f"{self.colour} {self.value} {self.type}"

    def check(self):
        print(self.colour, self.value)


class Deck:
    def __init__(self, basicset=1, draw4=4, load=False, data=None, server=False):
        self.drawpile = []
        self.discardpile = []
        if load:
            for card in data["drawpile"]:
                self.drawpile.append(Card(card[0], card[1], card[2]))
            for card in data["discardpile"]:
                self.discardpile.append(Card(card[0], card[1], card[2]))
        else:
            for colour in colours:
                for value in values:
                    if types[value] != "wild" and value != "0":
                        for setnum in range(basicset):
                            if not server:
                                self.drawpile.append(Card(colour, value, types[value]))
                                self.drawpile.append(Card(colour, value, types[value]))
                            else:
                                self.drawpile.append(
                                    Card(colour, value, types[value], False)
                                )
                                self.drawpile.append(
                                    Card(colour, value, types[value], False)
                                )
                    elif value == "0":
                        for setnum in range(basicset):
                            if not server:
                                self.drawpile.append(Card(colour, value, types[value]))
                            else:
                                self.drawpile.append(
                                    Card(colour, value, types[value], False)
                                )

            for draw4 in range(draw4):
                if not server:
                    self.drawpile.append(Card("nocolour", "Draw4", types[value]))
                    self.drawpile.append(Card("nocolour", "Colour", types[value]))
                else:
                    self.drawpile.append(Card("nocolour", "Draw4", types[value], False))
                    self.drawpile.append(
                        Card("nocolour", "Colour", types[value], False)
                    )
            self.cardnum = len(self.drawpile)
            self.shuffle()
            counter = 0
            if basicset > 0:
                while self.drawpile[counter].type != "casual":
                    counter += 1
            self.discardpile.append(self.drawpile.pop(counter))

    def shuffle(self):
        random.shuffle(self.drawpile)

    def deal(self):

        if len(self.drawpile) >= 1:
            return self.drawpile.pop()

        else:
            print("Shuffle")
            last = self.discardpile.pop()
            for i in range(len(self.discardpile) - 1):
                self.drawpile.append(self.discardpile.pop(0))
            self.shuffle()
            return last


class Player:
    def __init__(
        self,
        playerid,
        load=False,
        startingcards=7,
        contact=None,
        data=None,
        deck=None,
        uicards=None,
    ):

        if deck == None:
            deck = Deck()
        self.id = playerid
        self.contact = contact
        self.cards = []
        self.uicards = uicards
        if load:
            for i in data[str(self.id)]:
                self.cards.append(Card(i[0], i[1], i[2]))
        else:
            for card in range(startingcards):
                self.cards.append(deck.deal())

    def __str__(self):
        op = f"PLAYER {self.id}:\n"
        for i in self.cards:
            op += f"{i}\n"
        op += "8====================D"
        return op


class Program:
    def __init__(self):
        # ==============Tkinter Init==============#
        self.root = tkinter.Tk()
        self.root.title("Uno")
        self.root.attributes("-fullscreen", True)
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.c = tkinter.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg="#780C0A",
        )
        self.c.pack(fill=tkinter.BOTH, expand=True)
        # ==================End===================#

        try:
            with open("user.txt", "r", encoding="utf8") as logfile:
                self.loggeduser = tuple(logfile.read().split())
            with open("USERDB.txt", "r", encoding="utf8"):
                dbdata = json.load(open("USERDB.json", encoding="utf8"))
                if self.loggeduser[0] not in dbdata:
                    self.loggeduser = False
                else:
                    if bcrypt.checkpw(
                        self.loggeduser[1].encode("utf-8"),
                        dbdata[self.loggeduser[0]].encode("utf-8"),
                    ):
                        self.loggeduser = self.loggeduser[0]

        except:
            self.loggeduser = False
        self.playercount = 2
        self.orderorder = ["R", "Y", "G", "B", "nocolour"]
        self.playerlist = []
        self.end = 0
        self.menu()

    def menu(self):
        # ===============Main Menu===============#

        background = ImageTk.PhotoImage(Image.open("Background.png"))
        backgroundid = self.c.create_image(
            self.width / 2, self.height / 2, image=background
        )

        logo = ImageTk.PhotoImage(Image.open("Logo.png"))
        logoid = self.c.create_image(self.width / 2, 265, image=logo)

        def mainmenu(action):
            if action == "create":
                self.newgame = tkinter.Button(
                    width=25,
                    height=2,
                    text="Nová hra",
                    command=lambda: [newsettings("create"), mainmenu("destroy")],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.newgame.place(x=self.width / 2, y=550, anchor="n")

                self.profilebutton = tkinter.Button(
                    width=10,
                    height=1,
                    text="Používateľ",
                    command=lambda: [profile("create"), mainmenu("destroy")],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.profilebutton.place(x=self.width - 140, y=250, anchor="n")

                self.loadgameb = tkinter.Button(
                    width=25,
                    height=2,
                    text="Načítať hru",
                    command=lambda: [mainmenu("destroy"), loadgame()],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.loadgameb.place(x=self.width / 2, y=650, anchor="n")

                self.multiplayerb = tkinter.Button(
                    width=25,
                    height=2,
                    text="Online",
                    command=lambda: [mainmenu("destroy"), multiplayerchoice("create")],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.multiplayerb.place(x=self.width / 2, y=750, anchor="n")

                self.exit = tkinter.Button(
                    width=10,
                    height=1,
                    text="Ukončiť",
                    command=lambda: [exit()],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "5"),
                )
                self.exit.place(x=self.width / 2, y=1000, anchor="n")

            elif action == "destroy":
                self.newgame.destroy()
                self.loadgameb.destroy()
                self.exit.destroy()
                self.profilebutton.destroy()
                self.multiplayerb.destroy()

        # ==========New Game==========#

        def newsettings(action):
            if action == "create":

                # Počet hráčov#
                player_menu_height = self.height / 2 + 70
                self.playerlabel = tkinter.Label(
                    text="Počet hráčov:",
                    font=("Lobster", "16"),
                    anchor="center",
                    bg="gold",
                )
                self.playerlabel.place(
                    x=self.width / 2 - 200, y=player_menu_height - 16
                )

                self.playernum = tkinter.Label(
                    text=self.playercount,
                    justify="center",
                    bg="gold",
                    font=("Lobster"),
                    anchor="center",
                )
                self.playernum.place(
                    x=self.width / 2, y=player_menu_height, anchor="center"
                )

                self.playerbuttonadd = tkinter.Button(
                    command=lambda: self.setplayers(value=1),
                    text=">",
                    font=("Lobster"),
                    bg="gold",
                    relief="groove",
                )
                self.playerbuttonadd.place(
                    x=self.width / 2 + 30, y=player_menu_height, anchor="center"
                )

                self.playerbuttonsub = tkinter.Button(
                    command=lambda: self.setplayers(value=-1),
                    text="<",
                    font=("Lobster"),
                    bg="gold",
                    relief="groove",
                )
                self.playerbuttonsub.place(
                    x=self.width / 2 - 30, y=player_menu_height, anchor="center"
                )

                # Začať hru#
                self.startbutton = tkinter.Button(
                    width=15,
                    height=2,
                    text="Začať hru",
                    command=lambda: [
                        self.c.delete("all"),
                        newsettings("destroy"),
                        self.startgame(),
                    ],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.startbutton.place(x=self.width / 2, y=800, anchor="n")

                # Vrátiť sa späť#
                self.returnbutton = tkinter.Button(
                    width=30,
                    height=2,
                    text="Späť",
                    command=lambda: [newsettings("destroy"), mainmenu("create")],
                    bg="gold",
                    relief="groove",
                    font=("Lobster", "15"),
                )
                self.returnbutton.place(x=self.width / 2, y=930, anchor="n")

            elif action == "destroy":
                self.playerbuttonadd.destroy()
                self.playerbuttonsub.destroy()
                self.startbutton.destroy()
                self.playernum.destroy()
                self.playerlabel.destroy()
                self.returnbutton.destroy()

        # ============END=============#

        # =========Load Game==========#
        def loadgame():
            self.c.delete("all")
            self.startgame(True)

        # ============END=============#
        def profile(action):
            if action == "create":

                self.returnbutton = tkinter.Button(
                    width=30,
                    height=2,
                    text="Späť",
                    command=lambda: [profile("destroy"), mainmenu("create")],
                    bg="gold",
                    relief="groove",
                    font=("Lobster", "15"),
                )
                self.returnbutton.place(x=self.width / 2, y=930, anchor="n")

                if not self.loggeduser:
                    self.usernamelabel = tkinter.Label(
                        text="Prihlasovacie meno:",
                        justify="center",
                        bg="gold",
                        font=("Lobster"),
                    )
                    self.usernamelabel.place(
                        x=self.width / 2 - 300, y=600, anchor="n", width=300, height=50
                    )
                    self.usernameentry = tkinter.Entry()
                    self.usernameentry.place(
                        x=self.width / 2, y=600, anchor="n", width=340, height=50
                    )

                    self.passwordlabel = tkinter.Label(
                        text="Heslo:",
                        justify="center",
                        bg="gold",
                        font=("Lobster"),
                    )
                    self.passwordlabel.place(
                        x=self.width / 2 - 300, y=660, anchor="n", width=300, height=50
                    )
                    self.passwordentry = tkinter.Entry(show="*")
                    self.passwordentry.place(
                        x=self.width / 2, y=660, anchor="n", width=340, height=50
                    )

                    self.loginbutton = tkinter.Button(
                        width=30,
                        height=2,
                        text="Login",
                        command=lambda: [
                            checklogin(
                                (self.usernameentry.get(), self.passwordentry.get())
                            ),
                        ],
                        bg="gold",
                        relief="groove",
                        font=("Lobster", "15"),
                    )
                    self.loginbutton.place(x=self.width / 2, y=760, anchor="n")

                    self.registerbutton = tkinter.Button(
                        width=30,
                        height=2,
                        text="Register",
                        command=lambda: [register(), profile("create")],
                        bg="gold",
                        relief="groove",
                        font=("Lobster", "15"),
                    )
                    self.registerbutton.place(x=self.width / 2, y=830, anchor="n")

                    self.login = tkinter.Button(
                        width=30,
                        height=2,
                        text="Login",
                        command=lambda: [
                            checklogin(
                                (self.usernameentry.get(), self.passwordentry.get())
                            ),
                        ],
                    )
                else:
                    self.uname = self.c.create_text(
                        self.width / 2,
                        540,
                        text="Prihlasený používateľ: " + self.loggeduser,
                        font=("Lobster", 40),
                    )
                    self.logoutbutton = tkinter.Button(
                        width=30,
                        height=2,
                        text="Logout",
                        command=lambda: [
                            profile("destroy"),
                            logout(),
                            profile("create"),
                        ],
                        bg="gold",
                        relief="groove",
                        font=("Lobster", "15"),
                    )
                    self.logoutbutton.place(x=self.width / 2, y=760, anchor="n")

            elif action == "destroy":
                self.returnbutton.destroy()
                if self.loggeduser:
                    self.c.delete(self.uname)
                    self.logoutbutton.destroy()
                else:
                    self.loginbutton.destroy()
                    self.usernameentry.destroy()
                    self.usernamelabel.destroy()
                    self.passwordentry.destroy()
                    self.passwordlabel.destroy()
                    self.registerbutton.destroy()

        def multiplayerchoice(action):
            if action == "create":
                self.hostb = tkinter.Button(
                    width=25,
                    height=2,
                    text="Vytvoriť hru",
                    command=lambda: hostgame(),
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.hostb.place(x=self.width / 2, y=650, anchor="n")

                self.joinb = tkinter.Button(
                    width=25,
                    height=2,
                    text="Pripojiť sa do hry",
                    command=lambda: joingame(),
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )
                self.joinb.place(x=self.width / 2, y=750, anchor="n")

                self.returnbutton = tkinter.Button(
                    width=30,
                    height=2,
                    text="Späť",
                    command=lambda: [multiplayerchoice("destroy"), mainmenu("create")],
                    bg="gold",
                    relief="groove",
                    font=("Lobster", "15"),
                )
                self.returnbutton.place(x=self.width / 2, y=930, anchor="n")

            elif action == "destroy":
                self.hostb.destroy()
                self.joinb.destroy()
                self.returnbutton.destroy()

        # ===========EXIT=============#
        def checklogin(login):
            data = json.load(open("USERDB.json"))
            if login[0] in data and bcrypt.checkpw(
                login[1].encode("utf-8"),
                data[login[0]].encode("utf-8"),
            ):
                profile("destroy")
                suclog = self.c.create_text(
                    self.width / 2,
                    540,
                    text="Úspešne ste sa prihlásili",
                    font=("Lobster"),
                )
                self.loggeduser = login[0]
                self.c.update()
                self.c.after(5000)
                self.c.delete(suclog)
                profile("create")

            elif login not in data:
                profile("destroy")
                faillog = self.c.create_text(
                    self.width / 2,
                    540,
                    text="Vaše meno alebo heslo je zlé",
                    font=("Lobster"),
                )
                self.c.update()
                self.c.after(5000)
                self.c.delete(faillog)
                profile("create")

        def logout():
            self.loggeduser = False

        def register():
            data = json.load(open("USERDB.json"))
            username = self.usernameentry.get()
            password = bcrypt.hashpw(
                self.passwordentry.get().encode("utf-8"),
                bcrypt.gensalt(10),
            ).decode("utf-8")
            profile("destroy")
            if username != "" and password != "":
                if username in data.keys():

                    faillog = self.c.create_text(
                        self.width / 2,
                        540,
                        text="Zadané meno už existuje v databáze",
                        font=("Lobster"),
                    )
                    self.c.update()
                    self.c.after(1000)
                    self.c.delete(faillog)
                else:
                    data[username] = password
                    json.dump(data, open("USERDB.json", "w"))
                    suclog = self.c.create_text(
                        self.width / 2,
                        540,
                        text="Boli ste úspešne zaregistrovaní",
                        font=("Lobster"),
                    )
                    self.c.update()
                    self.c.after(3000)
                    self.c.delete(suclog)
                    self.loggeduser = username
                    suclog = self.c.create_text(
                        self.width / 2,
                        540,
                        text="Úspešne ste sa prihlásili",
                        font=("Lobster"),
                    )
                    self.c.update()
                    self.c.after(5000)
                    self.c.delete(suclog)
            else:
                faillog = self.c.create_text(
                    self.width / 2,
                    540,
                    text="Nezadané meno alebo heslo",
                    font=("Lobster"),
                )
                self.c.update()
                self.c.after(1000)
                self.c.delete(faillog)

        def hostgame():

            if not self.loggeduser:
                faillog = self.c.create_text(
                    self.width / 2,
                    540,
                    text="Pred začatím hry sa prihláste",
                    font=("Lobster"),
                )
                self.c.update()
                self.c.after(1000)
                self.c.delete(faillog)

            else:
                self.connections = dict()
                print(socket.gethostbyname(socket.gethostname()))
                multiplayerchoice("destroy")
                lobby = self.c.create_text(
                    self.width / 2,
                    540,
                    text="Lobby",
                    font=("Lobster"),
                )

                self.returnbutton = tkinter.Button(
                    width=30,
                    height=2,
                    text="Späť",
                    command=lambda: [
                        multiplayerchoice("create"),
                        self.startbutton.destroy(),
                        self.players.destroy(),
                        self.returnbutton.destroy(),
                        self.c.delete(lobby),
                        self.connections.clear(),
                        stop(),
                        self.server.close(),
                        frame.pack_forget(),
                        frame.destroy(),
                    ],
                    bg="gold",
                    relief="groove",
                    font=("Lobster", "15"),
                )
                self.returnbutton.place(x=self.width / 2, y=930, anchor="n")

                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.bind((socket.gethostbyname(socket.gethostname()), 8080))
                self.server.listen()

                self.localuser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.localuser.connect(
                    (socket.gethostbyname(socket.gethostname()), 8080)
                )

                client, addr = self.server.accept()
                self.connections["127.0.0.1"] = (
                    client,
                    addr,
                )
                self.waiting = True

                frame = tkinter.Frame(self.root)
                scrollbar = tkinter.Scrollbar(frame, orient=tkinter.VERTICAL)
                self.players = tkinter.Listbox(
                    frame, yscrollcommand=scrollbar.set, selectmode=tkinter.EXTENDED
                )
                scrollbar.config(command=self.players.yview)
                scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
                frame.place(x=self.width / 2, y=675, anchor="center")
                self.players.pack()

                self.players.insert(
                    0,
                    "  IP:".join(
                        [self.loggeduser, socket.gethostbyname(socket.gethostname())],
                    ),
                )

                def updateconnected():
                    while self.waiting:

                        try:
                            client, addr = self.server.accept()
                            self.connections[addr[0]] = (
                                client,
                                addr,
                            )
                            menu = threading.Thread(
                                target=komunike, args=((client, addr))
                            )
                            menu.start()
                            self.c.update()
                            print("A new hand touches the beacon!")
                        except:
                            break

                def komunike(client, addr):
                    connection = client

                    username = str(connection.recv(4096), "utf_8")
                    connection.send(
                        bytes(
                            "Vitajte v hre: " + username,
                            "utf_8",
                        )
                    )
                    try:
                        self.players.insert(
                            tkinter.END,
                            "  IP:".join([username, addr[0]]),
                        )
                    except tkinter.TclError:
                        pass

                    while True:
                        try:
                            data = str(connection.recv(4096), "utf_8")
                            if data == "end":
                                connection.close()
                                self.connections.pop(addr[0])
                                self.players.delete(
                                    self.players.get(0, tkinter.END).index(
                                        "  IP:".join([username, addr[0]])
                                    )
                                )
                                break
                            if not self.waiting:
                                connection.send(bytes("start", "utf_8"))
                                break
                        except ConnectionAbortedError and ConnectionResetError:
                            break

                def stop():
                    self.waiting = False

                def startmp():
                    if len(self.connections) > 1:
                        self.playernames = self.players.get(0, tkinter.END)
                        stop()
                        self.c.delete("all")
                        self.returnbutton.destroy()
                        self.startbutton.destroy()
                        self.players.destroy()
                        frame.pack_forget()
                        frame.destroy()
                        self.localuser.send(bytes("HANDSHAKE", "utf_8"))
                        print(str(self.connections["127.0.0.1"][0].recv(4096), "utf_8"))
                        server = threading.Thread(target=self.serverstart)
                        server.start()
                        self.startgame(client=self.localuser)

                    else:
                        warning = self.c.create_text(
                            self.width / 2,
                            550,
                            fill="red",
                            font="Arial 50",
                            text="V hre nemôže byť menej ako 2 hráči",
                        )

                        self.c.after(2000, lambda: self.c.delete(warning))

                self.startbutton = tkinter.Button(
                    width=15,
                    height=2,
                    text="Začať hru",
                    command=lambda: [startmp()],
                    relief="groove",
                    bg="gold",
                    font=("Lobster", "20"),
                )

                self.startbutton.place(x=self.width / 2, y=800, anchor="n")
                self.c.update()
                connect = threading.Thread(target=updateconnected)
                connect.start()

        def joingame():
            if not self.loggeduser:
                faillog = self.c.create_text(
                    self.width / 2,
                    540,
                    text="Pred začatím hry sa prihláste",
                    font=("Lobster"),
                )
                self.c.update()
                self.c.after(1000)
                self.c.delete(faillog)
            else:
                multiplayerchoice("destroy")
                self.IPL = tkinter.Label(
                    text="IP adresa:",
                    justify="center",
                    bg="gold",
                    font=("Lobster"),
                )
                self.IPL.place(
                    x=self.width / 2 - 300, y=600, anchor="n", width=300, height=50
                )
                self.IP = tkinter.Entry()
                self.IP.place(
                    x=self.width / 2,
                    y=600,
                    anchor="n",
                    width=340,
                    height=50,
                )
                self.IP.insert(tkinter.END, socket.gethostbyname(socket.gethostname()))

                self.returnbutton = tkinter.Button(
                    width=30,
                    height=2,
                    text="Späť",
                    command=lambda: [
                        self.IPL.destroy(),
                        self.IP.destroy(),
                        self.connectb.destroy(),
                        self.returnbutton.destroy(),
                        multiplayerchoice("create"),
                    ],
                    bg="gold",
                    relief="groove",
                    font=("Lobster", "15"),
                )
                self.returnbutton.place(x=self.width / 2, y=930, anchor="n")

                def connect(ip):
                    def ClientConnection(client):
                        data = str(client.recv(4096), "utf_8")
                        if data == "start":
                            self.c.delete("all")
                            self.returnbutton.destroy()
                            self.c.update()
                            self.startgame(client=client)

                    try:
                        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        client.connect((ip, 8080))
                        client.send(bytes(self.loggeduser, "utf_8"))
                        self.IPL.destroy()
                        self.IP.destroy()
                        self.connectb.destroy()
                        self.returnbutton.destroy()
                        welcome = self.c.create_text(
                            self.width / 2,
                            540,
                            text=client.recv(4096),
                            font=("Lobster"),
                        )
                        self.returnbutton = tkinter.Button(
                            width=30,
                            height=2,
                            text="Späť",
                            command=lambda: [
                                self.c.delete(welcome),
                                multiplayerchoice("create"),
                                client.send(bytes("end", "utf_8")),
                            ],
                            bg="gold",
                            relief="groove",
                            font=("Lobster", "15"),
                        )
                        self.returnbutton.place(x=self.width / 2, y=930, anchor="n")
                        self.c.update()
                        connection = threading.Thread(target=ClientConnection(client))
                        connection.start()

                    except:
                        faillog = self.c.create_text(
                            self.width / 2,
                            540,
                            text="Nepodarilo sa pripojiť k serveru",
                            font=("Lobster"),
                        )
                        self.c.update()
                        self.c.after(1000)
                        self.c.delete(faillog)

                self.connectb = tkinter.Button(
                    width=30,
                    height=2,
                    text="Pripojiť sa",
                    command=lambda: [
                        connect(self.IP.get()),
                    ],
                    bg="gold",
                    relief="groove",
                    font=("Lobster", "15"),
                )
                self.connectb.place(x=self.width / 2, y=830, anchor="n")

        # ==================End===================#
        mainmenu("create")
        tkinter.mainloop()

    def setplayers(self, value):

        if self.playercount + value <= 1:
            warning = self.c.create_text(
                self.width / 2,
                550,
                fill="red",
                font="Arial 50",
                text="V hre nemôže byť menej ako 2 hráči",
            )

            self.c.after(2000, lambda: self.c.delete(warning))
        else:
            self.playercount += value
        self.playernum.config(text=self.playercount)

    def startgame(self, load=False, client=False):

        pauseimg = ImageTk.PhotoImage(Image.open("Home.png"))
        cards = [[]]
        self.paused = False
        pos = []
        pausebutton = tkinter.Button(
            width=35,
            height=35,
            image=pauseimg,
            command=lambda: [pause(not self.paused)],
        )
        pausebutton.place(x=self.width - 50, y=30, anchor="center")

        def sort(player, sorttype=("colour", "value")):
            working = player.cards.copy()
            for stype in reversed(sorttype):
                if stype == "colour":
                    tmp = dict()
                    for card in working:
                        if card.colour in tmp:
                            tmp[card.colour].append(card)
                        else:
                            tmp[card.colour] = [card]
                    working.clear()
                    for i in self.orderorder:

                        if i in tmp:
                            for j in tmp[i]:
                                working.append(j)

                elif stype == "value":
                    tmp = dict()
                    for card in working:
                        if card.value in tmp:
                            tmp[card.value].append(card)
                        else:
                            tmp[card.value] = [card]
                    working.clear()
                    for i in values:

                        if i in tmp:
                            for j in tmp[i]:
                                working.append(j)
            player.cards = working

        if not client:

            def pause(state):
                if state and client == False:
                    self.save = tkinter.Button(
                        width=10, height=2, text="Uložiť", command=save
                    )
                    self.save.place(x=self.width - 50, y=70, anchor="e")
                    self.tomenu = tkinter.Button(
                        width=10, height=2, command=lambda: [exit()], text="Ukončiť"
                    )
                    self.tomenu.place(
                        x=self.width - 50,
                        y=110,
                        anchor="e",
                    )
                    self.sortbutton = tkinter.Button(
                        width=10,
                        height=2,
                        command=lambda: [sort(self.player)],
                        text="Zoraď",
                    )
                    self.sortbutton.place(
                        x=self.width - 50,
                        y=150,
                        anchor="e",
                    )
                elif client == False:
                    self.save.destroy()
                    self.tomenu.destroy()
                    self.sortbutton.destroy()
                self.paused = not self.paused

        else:

            def pause(state):
                if state:
                    self.sortbutton = tkinter.Button(
                        width=10,
                        height=2,
                        command=lambda: [
                            sort(self.player),
                            showcards(self.player, self.currentset),
                        ],
                        text="Zoraď",
                    )
                    self.sortbutton.place(
                        x=self.width - 50,
                        y=70,
                        anchor="e",
                    )
                else:
                    self.sortbutton.destroy()

                self.paused = not self.paused

        def save():
            with open("game.txt", "w") as son:
                sf = dict()
                sf["playercount"] = self.playercount
                for player in self.playerlist:
                    sf[player.id] = [[x.colour, x.value, x.type] for x in player.cards]
                sf["drawpile"] = [[x.colour, x.value, x.type] for x in deck.drawpile]
                sf["discardpile"] = [
                    [x.colour, x.value, x.type] for x in deck.discardpile
                ]
                sf["activeplayer"] = playing
                sf["stop"] = self.stop
                sf["draw2"] = self.draw2
                sf["draw4"] = self.draw4
                sf["CW"] = self.CW
                sf["uno"] = self.uno
                sf["changecolour"] = self.changecolour
                json.dump(sf, son, indent=4)

        self.discardplacement = [
            [
                self.width / 2 + random.randrange(-30, 30),
                375 + random.randrange(-30, 30),
            ]
            for x in range(108)
        ]
        wide = 115
        pos = []
        for i in range(-5, 6):
            if i == 0:
                pass
            elif i in [-1, 1]:
                pos.append(self.width / 2 + i * (wide / 2))
            else:
                if i < 0:
                    pos.append(self.width / 2 + i * (wide) + wide / 2)
                else:
                    pos.append(self.width / 2 + i * (wide) - wide / 2)

        def showcards(player, currentset):
            for i in player.uicards:
                self.c.delete(i)
            self.player.uicards.clear()

            for card in range(min(len(player.cards) - self.currentset * 10, 10)):
                player.uicards.append(
                    self.c.create_image(
                        pos[card % 10],
                        820,
                        image=player.cards[currentset * 10 + card].img,
                    )
                )

        if client != False:
            cards = [[]]

            def Clientgame(client):
                def ack():
                    client.send(bytes("rdy", "utf_8"))

                def sendmessage(data):
                    client.send(bytes(data, "utf_8"))

                def punish():
                    self.unopunish.destroy()
                    self.c.update()
                    self.unop = True

                self.currentset = 0
                self.player = ""
                self.unop = False
                self.uno = False

                def scroll(way):
                    for i in self.player.uicards:
                        self.c.delete(i)
                    if way == 1:
                        if (self.currentset + 1) * 10 >= len(self.player.cards):
                            self.currentset = 0
                        else:
                            self.currentset += 1
                    else:
                        if self.currentset - 1 < 0:
                            self.currentset = len(self.player.cards) // 10
                            if not len(self.player.cards) % 10:
                                self.currentset -= 1
                        else:
                            self.currentset -= 1
                    showcards(self.player, self.currentset)

                def scrollcheck():
                    if len(self.player.cards) > 10:
                        scrollright = tkinter.Button(
                            text=">", command=lambda: scroll(1)
                        )
                        scrollright.place(x=self.width / 2 + 5 * (wide) + wide, y=820)
                        scrollleft = tkinter.Button(
                            text="<", command=lambda: scroll(-1)
                        )
                        scrollleft.place(x=self.width / 2 + -5 * (wide) - wide, y=820)
                    else:
                        try:
                            scrollleft.destroy()
                            scrollright.destroy()
                        except:
                            pass

                def unocheck():
                    self.uno = True
                    self.unob.destroy()

                self.c.delete("all")
                cards = dict()
                cards[self.loggeduser] = []
                discardpile = []
                drawpile = []

                self.myturn = False
                self.changecolour = ""
                ack()
                ack()
                data = str(client.recv(4096), "utf_8")
                data = str(client.recv(4096), "utf_8")
                while data != "end":
                    if data != "":
                        if data != "start":
                            data = data.split()
                            print(data)
                            cards[self.loggeduser].append((data[0], data[1], data[2]))
                        ack()
                    data = str(client.recv(4096), "utf_8")
                ack()
                data = cards
                cards = []
                self.chcborder = None
                self.player = Player(
                    self.loggeduser, True, data=data, deck="Not Required", uicards=cards
                )
                data = str(client.recv(4096), "utf_8").split()
                ack()
                print("start => ", data)
                self.drawlen = int(str(client.recv(4096), "utf_8"))
                ack()
                discardpile.append(Card(data[0], data[1], data[2]))
                img = ImageTk.PhotoImage(Image.open("Uno Cards/Back.png"))
                print("DRAW SIZE: " + str(self.drawlen))
                for i in range(self.drawlen):
                    drawpile.append(
                        self.c.create_image(
                            self.width / 2 + 500,
                            375 - i * 2,
                            image=img,
                        )
                    )
                self.c.create_image(
                    self.discardplacement[0][0],
                    self.discardplacement[0][1],
                    image=discardpile[0].img,
                )
                showcards(self.player, self.currentset)
                self.c.update()

                cplabel = self.c.create_text(
                    10, 30, text="Na rade je hráč: ", anchor="w", font="Arial 25"
                )
                currentplayer = self.c.create_text(
                    250,
                    30,
                    text="Hra sa začína",
                    anchor="w",
                    font="Arial 25",
                    width=300,
                )

                self.c.update()

                def Communication(client):
                    def afterdel(time, target):
                        self.c.after(time, self.c.delete(target))

                    while not self.end:
                        # ready = select.select([client], [], [])
                        # if ready[0]:
                        data = str(client.recv(4096), "utf_8").split()
                        while data:
                            if data[0] == "turn":
                                self.c.itemconfigure(currentplayer, text=data[1])
                                ack()
                                del data[0:2]
                            elif data[0] == "discard":

                                def discardanim():
                                    animlength = 70
                                    newdiscard = self.c.create_image(
                                        self.width / 2,
                                        -300,
                                        image=discardpile[len(discardpile) - 1].img,
                                    )
                                    x, y = self.width / 2, -300
                                    for _ in range(animlength):
                                        self.c.move(
                                            newdiscard,
                                            (
                                                self.discardplacement[len(discardpile)][
                                                    0
                                                ]
                                                - x
                                            )
                                            / animlength,
                                            (
                                                self.discardplacement[len(discardpile)][
                                                    1
                                                ]
                                                - y
                                            )
                                            / animlength,
                                        )
                                        self.c.update()
                                        self.c.after(10)

                                discardpile.append(Card(data[1], data[2], data[3]))

                                a = threading.Thread(target=discardanim)
                                a.start()
                                ack()
                                if self.chcborder != None:
                                    self.c.delete(self.chcborder)
                                    self.chcborder = None
                                    self.changecolour = ""
                                del data[0:4]
                            elif data[0] == "drawlen":
                                self.drawlen = int(data[1])
                                if len(drawpile) < self.drawlen:
                                    for i in range(self.drawlen - len(drawpile)):
                                        img = ImageTk.PhotoImage(
                                            Image.open("Uno Cards/Back.png")
                                        )
                                        drawpile.append(
                                            self.c.create_image(
                                                1400,
                                                375 - i * 2,
                                                image=img,
                                            )
                                        )
                                        self.c.update()
                                else:
                                    for i in range(len(drawpile) - self.drawlen):
                                        self.c.delete(i)
                                self.c.update()
                                ack()
                                del data[0:2]
                            elif data[0] == "start":
                                print("My turn!")
                                self.myturn = True
                                data.pop(0)
                                if len(self.player.cards) == 2:
                                    self.unob = tkinter.Button(
                                        width=12,
                                        height=4,
                                        text="UNO!",
                                        command=lambda: unocheck(),
                                    )
                                    self.unob.place(x=300, y=100)
                            elif data[0] == "draw":

                                def drawanim():
                                    animlength = 70
                                    x, y = self.c.coords(drawpile[-1])
                                    for _ in range(animlength):
                                        self.c.move(
                                            drawpile[-1],
                                            0,
                                            (-200 - y) / animlength,
                                        )
                                        self.c.update()
                                    self.c.delete(drawpile[-1])
                                    drawpile.pop()

                                self.drawlen -= int(data[1])
                                a = threading.Thread(target=drawanim)
                                a.start()
                                ack()
                                del data[0:2]
                            elif data[0] == "add":
                                self.player.cards.append(
                                    Card(data[1], data[2], data[3])
                                )
                                animlength = 70
                                if drawpile:
                                    new = self.player.uicards.append(
                                        self.c.create_image(
                                            self.c.coords(drawpile[-1]),
                                            image=self.player.cards[-1].img,
                                        )
                                    )
                                else:
                                    new = self.player.uicards.append(
                                        self.c.create_image(
                                            self.width / 2 + 500,
                                            375,
                                            image=self.player.cards[-1].img,
                                        )
                                    )
                                x, y = self.c.coords(self.player.uicards[-1])
                                if len(self.player.uicards) == 11:
                                    for i in range(animlength):
                                        self.c.move(
                                            self.player.uicards[-1],
                                            (pos[9] - x) / animlength,
                                            (820 - y) / animlength,
                                        )
                                    self.c.after(1500)
                                    self.c.delete(new)
                                    self.player.uicards.pop()
                                else:
                                    for i in range(animlength):
                                        self.c.move(
                                            self.player.uicards[-1],
                                            (pos[len(self.player.uicards) - 1] - x)
                                            / animlength,
                                            (820 - y) / animlength,
                                        )

                                showcards(self.player, self.currentset)
                                scrollcheck()
                                del data[0:4]
                                if len(data) == 0:
                                    ack()
                            elif data[0] == "stop":
                                lt = self.c.create_text(
                                    self.width / 2,
                                    500,
                                    text=f"Prichádzate o ťah",
                                    justify="center",
                                    font=("Lobster", 46),
                                    fill="gold",
                                )
                                wait = threading.Thread(
                                    target=afterdel, args=(3000, lt)
                                )
                                wait.start()
                                client.send(bytes("stop", "utf_8"))
                                data.pop()
                            elif data[0] == "CHC":
                                if data[1] == "R":
                                    self.chcborder = self.c.create_rectangle(
                                        self.width / 2 - 260,
                                        375 - 80,
                                        self.width / 2 - 180,
                                        375 + 80,
                                        fill="red",
                                    )
                                elif data[1] == "G":
                                    self.chcborder = self.c.create_rectangle(
                                        self.width / 2 - 260,
                                        375 - 80,
                                        self.width / 2 - 180,
                                        375 + 80,
                                        fill="green",
                                    )
                                elif data[1] == "B":
                                    self.chcborder = self.c.create_rectangle(
                                        self.width / 2 - 260,
                                        375 - 80,
                                        self.width / 2 - 180,
                                        375 + 80,
                                        fill="cornflowerblue",
                                    )
                                elif data[1] == "Y":
                                    self.chcborder = self.c.create_rectangle(
                                        self.width / 2 - 260,
                                        375 - 80,
                                        self.width / 2 - 180,
                                        375 + 80,
                                        fill="yellow",
                                    )
                                self.changecolour = data[1]
                                del data[0:2]
                            elif data[0] == "UnoPunish":
                                self.unopunish = tkinter.Button(
                                    width=12,
                                    height=4,
                                    text="Nezavolané UNO!",
                                    command=lambda: punish(),
                                )
                                self.unopunish.place(x=100, y=100)
                                data.pop(0)
                            elif data[0] == "win":
                                ack()
                                client.shutdown(socket.SHUT_RDWR)
                                celebtxt = self.c.create_text(
                                    self.width / 2,
                                    500,
                                    text=f"Hráč {data[1]} vyhral.",
                                    font=("Lobster", 46),
                                    fill="gold",
                                )
                                victoryceleb = True

                                returno = tkinter.Button(
                                    width=25,
                                    height=3,
                                    text="Späť do menu",
                                    relief="groove",
                                    bg="gold",
                                    font=("Lobster", "20"),
                                    command=lambda: [
                                        victoryceleb := False,
                                        returno.destroy(),
                                        self.c.delete("all"),
                                        self.menu(),
                                    ],
                                )
                                returno.place(x=self.width / 2, y=700, anchor="center")
                                while victoryceleb:
                                    self.c.itemconfig(
                                        celebtxt,
                                        fill=f"#{random.randrange(256**3):06x}",
                                    )
                                    self.c.update()
                                    self.c.after(500)
                    # after draw

                servercomm = threading.Thread(target=Communication, args=([client]))
                servercomm.start()
                self.currentset = 0

                def click(e):
                    if (
                        self.width / 2 + -5 * (wide) - wide / 2 + 6 < e.x
                        and e.x
                        < self.width / 2
                        + -5 * (wide)
                        - wide / 2
                        + (len(self.player.uicards) - 1) * (wide)
                        + wide * 2
                        - 6
                        and 649 < e.y
                        and e.y < 991
                        and self.myturn
                    ):
                        picked = int(
                            abs(
                                (e.x - (self.width / 2 + -5 * (wide) - wide / 2)) / wide
                            )
                        )
                        if picked == len(self.player.uicards):
                            picked = len(self.player.uicards) - 1
                        if picked > len(self.player.uicards):
                            picked = ""
                        else:
                            pickedcard = self.player.cards[
                                picked + self.currentset * 10
                            ]
                        last = discardpile[-1]

                        print(pickedcard.colour, pickedcard.value, self.changecolour)
                        if (
                            (
                                pickedcard.colour == last.colour
                                and self.changecolour == ""
                            )
                            or pickedcard.value == last.value
                            or pickedcard.type == "wild"
                            or pickedcard.colour == self.changecolour
                        ):
                            animlength = 70
                            x, y = self.c.coords(self.player.uicards[picked])
                            for i in range(animlength):
                                self.c.move(
                                    self.player.uicards[picked],
                                    (self.discardplacement[len(discardpile)][0] - x)
                                    / animlength,
                                    (self.discardplacement[len(discardpile)][1] - y)
                                    / animlength,
                                )
                                self.c.update()

                            def colchange(colour):
                                self.changecolour = colour

                            if pickedcard.type == "wild":
                                red = green = blue = yellow = "placeholder"
                                if self.uno == False and len(self.player.cards) == 2:
                                    uc = " uno"
                                else:
                                    uc = ""
                                    self.uno = False
                                if self.unop:
                                    uc += " unop"
                                    self.unop = False
                                if len(self.player.cards) == 1:
                                    uc = " win"

                                def destroybuttons():
                                    for i in red, green, blue, yellow:
                                        i.destroy()

                                red = tkinter.Button(
                                    width=30,
                                    height=2,
                                    text="červená",
                                    command=lambda: [
                                        colchange("R"),
                                        destroybuttons(),
                                        sendmessage(
                                            f"{pickedcard.colour} {pickedcard.value} {pickedcard.type} R{uc}"
                                        ),
                                    ],
                                    bg="red",
                                    relief="flat",
                                )
                                red.place(x=460, y=600)
                                green = tkinter.Button(
                                    width=30,
                                    height=2,
                                    text="zelená",
                                    command=lambda: [
                                        colchange("G"),
                                        destroybuttons(),
                                        sendmessage(
                                            f"{pickedcard.colour} {pickedcard.value} {pickedcard.type} G{uc}"
                                        ),
                                    ],
                                    bg="green",
                                    relief="flat",
                                )
                                green.place(x=760, y=600)
                                blue = tkinter.Button(
                                    width=30,
                                    height=2,
                                    text="modrá",
                                    command=lambda: [
                                        colchange("B"),
                                        destroybuttons(),
                                        sendmessage(
                                            f"{pickedcard.colour} {pickedcard.value} {pickedcard.type} B{uc}"
                                        ),
                                    ],
                                    bg="cornflowerblue",
                                    relief="flat",
                                )
                                blue.place(x=1060, y=600)
                                yellow = tkinter.Button(
                                    width=30,
                                    height=2,
                                    text="žltá",
                                    command=lambda: [
                                        colchange("Y"),
                                        destroybuttons(),
                                        sendmessage(
                                            f"{pickedcard.colour} {pickedcard.value} {pickedcard.type} Y{uc}"
                                        ),
                                    ],
                                    bg="yellow",
                                    relief="flat",
                                )
                                yellow.place(x=1360, y=600)
                                self.c.update()
                            else:
                                if self.uno == False and len(self.player.cards) == 2:
                                    uc = " uno"
                                    self.unob.destroy()
                                else:
                                    uc = ""
                                    self.uno = False
                                if self.unop:
                                    uc += " unop"
                                    self.unop = False
                                if len(self.player.cards) == 1:
                                    uc = " win"
                                sendmessage(
                                    f"{pickedcard.colour} {pickedcard.value} {pickedcard.type}{uc}"
                                )
                            discardpile.append(
                                self.player.cards.pop(picked + self.currentset * 10)
                            )
                            self.c.create_image(
                                self.discardplacement[len(discardpile) - 1][0],
                                self.discardplacement[len(discardpile) - 1][1],
                                image=discardpile[-1].img,
                            )
                            self.c.delete(self.player.uicards[picked])
                            self.player.uicards.pop(picked)
                            showcards(self.player, self.currentset)
                            scrollcheck()
                            self.changecolour = ""
                            if self.chcborder != None:
                                self.c.delete(self.chcborder)
                                self.chcborder = None
                            self.myturn = False

                    else:
                        if drawpile:
                            xd, yd = self.c.coords(drawpile[-1])
                        else:
                            xd, yd = self.width / 2 + 500, 375
                        if (
                            xd - 110 < e.x
                            and e.x < xd + 110
                            and yd - 171 < e.y
                            and e.y < yd + 171
                            and self.myturn
                        ):
                            if drawpile:
                                self.c.delete(drawpile[-1])
                                drawpile.pop()
                            if self.uno or len(self.player.cards) == 2:
                                self.uno = False
                                self.unob.destroy()
                            if not self.unop:
                                sendmessage("draw")
                            else:
                                sendmessage("draw unop")
                            self.myturn = False

                self.c.bind("<ButtonRelease-1>", click)
                self.c.mainloop()

            Clientgame(client)

        else:
            self.end = 0
            if load:
                data = json.load(open("game.txt"))
                deck = Deck(load=True)
                self.playerlist = []
                self.playercount = data["playercount"]
                for i in range(self.playercount):
                    self.playerlist.append(Player(list(data.keys())[i + 1], True))

                self.stop = data["stop"]
                self.draw2 = data["draw2"]
                self.draw4 = data["draw4"]
                self.CW = data["CW"]
                self.uno = data["uno"]
                self.changecolour = data["changecolour"]
                if self.CW:
                    playing = data["activeplayer"] - 1
                else:
                    playing = data["activeplayer"] + 1
            else:
                deck = Deck()

                self.playerlist = []
                if self.loggeduser:
                    self.playerlist.append(Player(self.loggeduser))
                    for i in range(self.playercount - 1):
                        self.playerlist.append(
                            Player(
                                i + 2,
                            )
                        )
                else:
                    for i in range(self.playercount):
                        self.playerlist.append(
                            Player(
                                i + 1,
                            )
                        )
                for player in self.playerlist:
                    print(player)

                playing = -1
                self.stop = False
                self.draw2 = False
                self.draw4 = False
                self.CW = True
                self.uno = 0
                self.changecolour = "No"

            # GAMELOOP
            while self.end == 0:
                if self.CW:
                    playing += 1
                    if playing > (len(self.playerlist) - 1):
                        playing = 0
                else:
                    playing -= 1
                    if playing < 0:
                        playing = len(self.playerlist) - 1
                player = self.playerlist[playing]
                self.player = player
                cards = [[]]

                self.currentset = 0
                self.c.delete("all")

                if not self.stop:
                    self.c.create_text(
                        self.width / 2,
                        500,
                        text=f"Na rade je hráč {player.id}.\nPre začatie "
                        "ťahu kliknite do hracej plochy",
                        justify="center",
                        font=("Lobster", 46),
                        fill="gold",
                    )

                    wait = tkinter.IntVar()
                    self.c.bind("<ButtonRelease-1>", lambda x: [wait.set(1)])
                    self.c.wait_variable(wait)
                    self.c.delete("all")

                    if self.changecolour != "No":
                        if self.changecolour == "R":
                            self.c.create_rectangle(
                                self.width / 2 - 60,
                                375 - 80,
                                self.width / 2 + 60,
                                375 + 80,
                                fill="red",
                            )
                        elif self.changecolour == "G":
                            self.c.create_rectangle(
                                self.width / 2 - 60,
                                375 - 80,
                                self.width / 2 + 60,
                                375 + 80,
                                fill="green",
                            )
                        elif self.changecolour == "B":
                            self.c.create_rectangle(
                                self.width / 2 - 60,
                                375 - 80,
                                self.width / 2 + 60,
                                375 + 80,
                                fill="cornflowerblue",
                            )
                        elif self.changecolour == "Y":
                            self.c.create_rectangle(
                                self.width / 2 - 60,
                                375 - 80,
                                self.width / 2 + 60,
                                375 + 80,
                                fill="yellow",
                            )

                    for card in range(len(deck.discardpile)):
                        self.c.create_image(
                            self.discardplacement[card][0],
                            self.discardplacement[card][1],
                            image=deck.discardpile[card].img,
                        )
                    back = ImageTk.PhotoImage(Image.open("Uno Cards/Back.png"))
                    for i in range(min(len(deck.drawpile), 35)):
                        if i != min(len(deck.drawpile), 35) - 1:
                            self.c.create_image(1400, 375 - i * 2, image=back)
                            self.c.update()
                        else:
                            lastdraw = self.c.create_image(
                                1400, 375 - i * 2, image=back
                            )

                    for n, card in enumerate(player.cards):
                        cards[-1].append(
                            self.c.create_image(pos[n % 10], 820, image=card.img)
                        )
                        if n % 10 == 9:
                            cards.append([])
                    for i in range(len(cards) - 1):
                        for j in cards[i + 1]:
                            self.c.move(j, 0, 500)
                    if len(cards) > 1 and len(cards[-1]) != 0:
                        scrollright = tkinter.Button(
                            text=">", command=lambda: scroll(1)
                        )
                        scrollright.place(x=self.width / 2 + 5 * (wide) + wide, y=820)
                        scrollleft = tkinter.Button(
                            text="<", command=lambda: scroll(-1)
                        )
                        scrollleft.place(x=self.width / 2 + -5 * (wide) - wide, y=820)

                    def unocheck():
                        self.uno = 2
                        uno.destroy()

                    def punish():
                        for i in range(2):
                            if self.CW:
                                self.playerlist[playing - 1].cards.append(deck.deal())
                            if not self.CW:
                                self.playerlist[playing + 1].cards.append(deck.deal())
                        self.uno = 0
                        unopunish.destroy()

                    if self.uno == 1:
                        unopunish = tkinter.Button(
                            width=12,
                            height=4,
                            text="Nezavolané UNO!",
                            command=lambda: punish(),
                        )
                        unopunish.place(x=100, y=100)

                    if len(player.cards) == 2:
                        uno = tkinter.Button(
                            width=12, height=4, text="UNO!", command=lambda: unocheck()
                        )
                        uno.place(x=300, y=100)

                    def scroll(way):
                        for card in cards[self.currentset]:
                            self.c.move(card, 0, 500)
                        if way == 1:
                            if self.currentset + 1 > len(cards) - 1:
                                self.currentset = 0
                            else:
                                self.currentset += 1
                        else:
                            if self.currentset - 1 < 0:
                                self.currentset = len(cards) - 1
                            else:
                                self.currentset -= 1
                        for card in cards[self.currentset]:
                            self.c.move(card, 0, -500)

                    def click(e):
                        if (
                            self.width / 2 + -5 * (wide) - wide / 2 < e.x
                            and e.x < self.width / 2 + 5 * (wide) + wide / 2
                            and 649 < e.y
                            and e.y < 991
                        ):
                            try:
                                uno.destroy()
                                unopunish.destroy()
                            except:
                                pass
                            picked = int(
                                abs(
                                    (e.x - (self.width / 2 + -5 * (wide) - wide / 2))
                                    / wide
                                )
                            )
                            print(
                                (e.x - (self.width / 2 + -5 * (wide) - wide / 2)) / wide
                            )
                            print(picked)
                            if picked == len(cards[self.currentset]):
                                picked = len(cards[self.currentset]) - 1

                            pickedcard = player.cards[picked + (self.currentset * 10)]
                            last = deck.discardpile[-1]

                            print(
                                pickedcard.colour, pickedcard.value, self.changecolour
                            )
                            if (
                                pickedcard.colour == last.colour
                                or pickedcard.value == last.value
                                or pickedcard.type == "wild"
                                or pickedcard.colour == self.changecolour
                            ):
                                animlength = 70
                                x, y = self.c.coords(cards[self.currentset][picked])
                                for i in range(animlength):
                                    self.c.move(
                                        cards[self.currentset][picked],
                                        (
                                            self.discardplacement[
                                                len(deck.discardpile)
                                            ][0]
                                            - x
                                        )
                                        / animlength,
                                        (
                                            self.discardplacement[
                                                len(deck.discardpile)
                                            ][1]
                                            - y
                                        )
                                        / animlength,
                                    )
                                    self.c.update()

                                def colchange(colour):
                                    self.changecolour = colour

                                if self.changecolour != "No":
                                    self.changecolour = "No"
                                if len(cards) > 1 and len(cards[-1]) != 0:
                                    scrollleft.destroy()
                                    scrollright.destroy()

                                if pickedcard.value == "Stop":
                                    self.stop = True
                                elif pickedcard.value == "Draw2":
                                    self.draw2 = True
                                    self.stop = True
                                elif pickedcard.value == "Reverse":
                                    self.CW = not self.CW
                                elif pickedcard.value == "Draw4":
                                    self.draw4 = True
                                    self.stop = True
                                if pickedcard.type == "wild":
                                    red = tkinter.Button(
                                        width=30,
                                        height=2,
                                        text="červená",
                                        command=lambda: [
                                            colchange("R"),
                                            waitero.set(1),
                                        ],
                                        bg="red",
                                        relief="flat",
                                    )
                                    red.place(x=460, y=600)
                                    green = tkinter.Button(
                                        width=30,
                                        height=2,
                                        text="zelená",
                                        command=lambda: [
                                            colchange("G"),
                                            waitero.set(1),
                                        ],
                                        bg="green",
                                        relief="flat",
                                    )
                                    green.place(x=760, y=600)
                                    blue = tkinter.Button(
                                        width=30,
                                        height=2,
                                        text="modrá",
                                        command=lambda: [
                                            colchange("B"),
                                            waitero.set(1),
                                        ],
                                        bg="cornflowerblue",
                                        relief="flat",
                                    )
                                    blue.place(x=1060, y=600)
                                    yellow = tkinter.Button(
                                        width=30,
                                        height=2,
                                        text="žltá",
                                        command=lambda: [
                                            colchange("Y"),
                                            waitero.set(1),
                                        ],
                                        bg="yellow",
                                        relief="flat",
                                    )
                                    yellow.place(x=1360, y=600)
                                    self.c.update()
                                    waitero = tkinter.IntVar()
                                    self.c.wait_variable(waitero)
                                    red.destroy()
                                    green.destroy()
                                    blue.destroy()
                                    yellow.destroy()

                                deck.discardpile.append(
                                    player.cards.pop(picked + (self.currentset * 10))
                                )

                                self.c.after(3000)
                                wait.set(1)
                        xd, yd = self.c.coords(lastdraw)
                        if (
                            xd - 110 < e.x
                            and e.x < xd + 110
                            and yd - 171 < e.y
                            and e.y < yd + 171
                        ):
                            try:
                                uno.destroy()
                                unopunish.destroy()
                            except:
                                pass

                            if len(cards) > 1 and len(cards[-1]) != 0:
                                scrollleft.destroy()
                                scrollright.destroy()
                            drawing = self.c.create_image(
                                xd, yd, image=deck.drawpile[-1].img
                            )
                            self.c.update()
                            self.c.delete(lastdraw)
                            for i in range(20):
                                self.c.move(drawing, 0, -(yd - 820) / 20)
                                self.c.update()
                            player.cards.append(deck.deal())
                            self.c.after(3000)
                            wait.set(1)

                    wait = tkinter.IntVar()
                    self.c.bind("<ButtonRelease-1>", click)
                    self.c.wait_variable(wait)
                    self.c.delete("all")

                else:
                    if self.draw2:
                        for i in range(2):
                            player.cards.append(deck.deal())
                        self.c.create_text(
                            self.width / 2,
                            300,
                            text=f"Hráč {player.id} si ťahá 2 karty.",
                            justify="center",
                            font=("Lobster", 46),
                            fill="gold",
                        )
                        self.draw2 = False
                    if self.draw4:
                        for i in range(4):
                            player.cards.append(deck.deal())
                        self.c.create_text(
                            self.width / 2,
                            300,
                            text=f"Hráč {player.id} si ťahá 4 karty.",
                            justify="center",
                            font=("Lobster", 46),
                            fill="gold",
                        )
                        self.draw4 = False
                        d4img = self.c.create_image(self.width / 2, 820)
                        for i in range(80):
                            img = ImageTk.PhotoImage(
                                Image.open(f"Four Animation/{i+1}.png")
                            )
                            self.c.itemconfig(d4img, image=img)
                            self.c.update()
                            self.c.after(2)

                    self.c.create_text(
                        self.width / 2,
                        500,
                        text=f"Hráč {player.id} prichádza o ťah.",
                        justify="center",
                        font=("Lobster", 46),
                        fill="gold",
                    )
                    self.c.update()
                    self.c.after(3000)
                    self.stop = False
                if len(player.cards) > 1:
                    self.uno = 0
                if len(player.cards) == 1 and self.uno == 0:
                    self.uno = 1
                if len(player.cards) == 0:
                    self.end = player.id

            celebtxt = self.c.create_text(
                self.width / 2,
                500,
                text=f"Hráč číslo {self.end} vyhral.",
                font=("Lobster", 46),
                fill="gold",
            )
            victoryceleb = True

            returno = tkinter.Button(
                width=25,
                height=3,
                text="Späť do menu",
                relief="groove",
                bg="gold",
                font=("Lobster", "20"),
                command=lambda: [
                    victoryceleb := False,
                    returno.destroy(),
                    self.c.delete("all"),
                    self.menu(),
                ],
            )
            returno.place(x=self.width / 2, y=700, anchor="center")
            while victoryceleb:
                self.c.itemconfig(celebtxt, fill=f"#{random.randrange(256**3):06x}")
                self.c.update()
                self.c.after(500)

    class Server:
        def game(self):
            winner = ""

            def broadcast(data, exception=None):
                for i in set(self.playerlist) - set([exception]):
                    self.trans(i[0].contact, data)

            def createsql():
                sql = ""

                if self.draw2:
                    for _ in range(2):
                        card = self.deck.deal()
                        sql += f" add {card.colour} {card.value} {card.type}"
                    self.draw2 = False
                if self.draw4:
                    for _ in range(4):
                        card = self.deck.deal()
                        sql += f" add {card.colour} {card.value} {card.type}"
                    self.draw4 = False

                if self.changecolour != "No":
                    sql += " CHC " + self.changecolour
                    if not self.stop:
                        self.changecolour = "No"
                if self.uno and not self.stop:
                    sql += " UnoPunish"
                    self.uno = False
                if self.stop:
                    sql += " stop"
                    self.stop = False
                else:
                    sql += " start"
                return sql.strip()

            broadcast(len(self.deck.drawpile))
            while not self.end:
                if self.CW:
                    self.playing += 1
                    if self.playing > (len(self.playerlist) - 1):
                        self.playing = 0
                else:
                    self.playing -= 1
                    if self.playing < 0:
                        self.playing = len(self.playerlist) - 1
                player = self.playerlist[self.playing]
                if self.playing == 0:
                    broadcast("turn " + self.playerlist[self.playing + 1][1].split()[0])
                elif self.playing == 1:
                    broadcast("turn " + self.playerlist[self.playing - 1][1].split()[0])
                response = self.trans(player[0].contact, createsql()).split()
                if response[-1] == "unop":
                    if self.CW:
                        punish = self.playing + 1
                        if punish > (len(self.playerlist) - 1):
                            punish = 0
                    else:
                        punish = self.playing - 1
                        if punish < 0:
                            punish = len(self.playerlist) - 1
                    sql = ""
                    for _ in range(2):
                        card = self.deck.deal()
                        sql += f" add {card.colour} {card.value} {card.type}"
                    self.playerlist[punish][0].contact.send(bytes(sql.strip(), "utf_8"))
                    broadcast("draw 2", self.playerlist[punish])
                    response.pop()

                if response[-1] == "uno":
                    self.uno = True
                    response.pop()

                if response[0] == "draw":
                    if not self.deck.drawpile:
                        a = self.deck.deal()
                        broadcast("drawlen " + str(len(self.deck.drawpile)))
                    else:
                        a = self.deck.deal()
                    print(a, len(self.deck.drawpile))
                    broadcast("draw 1", player)
                    self.trans(player[0].contact, f"add {a.colour} {a.value} {a.type}")
                elif response[0] == "stop":
                    pass

                else:
                    if response[-1] == "win":
                        winner = player[1].split()[0]
                        response.pop()

                    if len(response) == 3:
                        self.deck.discardpile.append(
                            Card(response[0], response[1], response[2], False)
                        )
                        broadcast(
                            " ".join(
                                ["discard", response[0], response[1], response[2]],
                            ),
                            player,
                        )
                    elif len(response) == 4:
                        self.deck.discardpile.append(
                            Card(response[0], response[1], response[2], False)
                        )
                        self.changecolour = response[3]
                        broadcast(
                            " ".join(
                                ["discard", response[0], response[1], response[2]],
                            ),
                            player,
                        )
                    if winner != "":
                        for i in set(self.playerlist):
                            connection = i[0].contact
                            a = select.select([], [connection], [])
                            if a[1]:
                                connection.send(
                                    bytes(str("win " + player[1].split()[0]), "utf_8")
                                )
                        self.end = True
                        break
                    print("SERVER RECEIVED: ", end="")
                    print(self.deck.discardpile[-1])
                    if self.deck.discardpile[-1].value == "Draw2":
                        self.draw2 = True
                        self.stop = True
                    elif self.deck.discardpile[-1].value == "Draw4":
                        self.draw4 = True
                        self.stop = True
                    elif self.deck.discardpile[-1].value == "Stop":
                        self.stop = True
                    elif self.deck.discardpile[-1].value == "Reverse":
                        self.CW = not self.CW

        def __init__(self, connectionlist, playernames):
            self.playing = 0
            self.stop = False
            self.draw2 = False
            self.draw4 = False
            self.CW = True
            self.uno = False
            self.unop = False
            self.end = 0
            self.changecolour = "No"
            self.deck = Deck(server=True)
            start = self.deck.discardpile[0]
            self.deck.discardpile.append(start)
            self.playerlist = []
            self.playernames = playernames

            for i, player in enumerate(reversed(connectionlist)):
                sock = connectionlist[player][0]
                self.playerlist.append(
                    (Player(player, contact=sock, deck=self.deck), self.playernames[i])
                )
                self.trans(sock, "start")
                for j in self.playerlist[i][0].cards:
                    self.trans(sock, " ".join([j.colour, j.value, j.type]))
                self.trans(sock, "end")
                self.trans(sock, " ".join([start.colour, start.value, start.type]))

            self.game()

        def trans(self, connection, data):
            a = select.select([], [connection], [])
            if a[1]:
                connection.send(bytes(str(data), "utf_8"))
            return str(connection.recv(4096), "utf_8")

    def serverstart(self):
        self.Server(self.connections, self.playernames)


Program()
