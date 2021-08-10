import vlc
import time
import tkinter
import os
from tkinter import filedialog
import threading
from keyboard import is_pressed
from firebase_admin import initialize_app
from firebase_admin import credentials
from firebase_admin import firestore
from threading import Thread
from sys import exit
from win32api import keybd_event
from win32con import VK_MEDIA_PLAY_PAUSE, KEYEVENTF_EXTENDEDKEY
from os import stat, system

n = -1
media_player = None
state = 0
rev = 0
forw = 0
is_host = None
sync = 0

# ___________________________________________________________________________________________________________


def pauseorplay(db=None, Host_name=None):
    global media_player
    global state
    global rev
    global forw
    global sync
    global is_host
    while(True):
        if is_pressed('space'):
            if is_host:
                state = 1 - state
                doc = db.collection("Watch_party").document(Host_name)
                doc.set({"state": state, "rev": rev,
                         "forw": forw, "sync": sync})
            media_player.set_pause(media_player.is_playing())

# ___________________________________________________________________________________________________________


def reverse(db=None, Host_name=None):
    global media_player
    global state
    global rev
    global forw
    global sync
    global is_host
    while(True):
        if is_pressed('left'):
            if is_host:
                rev = 1-rev
                doc = db.collection("Watch_party").document(Host_name)
                doc.set({"state": state, "rev": rev,
                         "forw": forw, "sync": sync})
            cur = vlc.libvlc_media_player_get_time(media_player)
            vlc.libvlc_media_player_set_time(
                media_player, max(0, cur-5000))

# ___________________________________________________________________________________________________________


def forward(db=None, Host_name=None):
    global media_player
    global state
    global rev
    global forw
    global sync
    global is_host
    while(True):
        if is_pressed('right'):
            if is_host:
                forw = 1-forw
                doc = db.collection("Watch_party").document(Host_name)
                doc.set({"state": state, "rev": rev,
                         "forw": forw, "sync": sync})
            cur = vlc.libvlc_media_player_get_time(media_player)
            vlc.libvlc_media_player_set_time(media_player, cur+5000)

# ___________________________________________________________________________________________________________


def change_subs():
    global media_player
    for i in media_player.video_get_spu_description():
        print(i)
    if len(media_player.video_get_spu_description()) > 0:
        n = int(input("Enter the subtitle index:  "))
        vlc.libvlc_video_set_spu(media_player, n)

# ___________________________________________________________________________________________________________


def run_vlc():

    global media_player
    media_player = vlc.MediaPlayer()

    root = tkinter.Tk()
    root.withdraw()

    tempdir = None
    while tempdir == None:
        currdir = os.getcwd()
        tempdir = filedialog.askopenfilename(filetypes=(
            ("Template files", "*.type"), ("All files", "*")))

        if len(tempdir) > 0:
            media = vlc.Media(tempdir)
            media_player.set_media(media)
            media_player.play()
            time.sleep(4)
            media_player.pause()
            vlc.libvlc_media_player_set_time(media_player, 0)

            for i in media_player.video_get_spu_description():
                print(i)
            if len(media_player.video_get_spu_description()) > 0:
                n = int(input("Enter the subtitle index:  "))
                vlc.libvlc_video_set_spu(media_player, n)
            system('cls')

# ___________________________________________________________________________________________________________


def run_host(db, Host_name):
    global media_player
    global state
    global rev
    global forw
    global sync

    thread1 = Thread(target=pauseorplay, args=(db, Host_name,))
    thread1.daemon = True
    thread1.start()

    thread2 = Thread(target=reverse, args=(db, Host_name,))
    thread2.daemon = True
    thread2.start()

    thread3 = Thread(target=forward, args=(db, Host_name,))
    thread3.daemon = True
    thread3.start()


# ___________________________________________________________________________________________________________


def run_client(db, Host_name):

    global state
    global rev
    global forw
    global sync
    callback_done = threading.Event()

    def on_snapshot(doc_snapshot, changes, readtime):
        global media_player
        global state
        global rev
        global forw
        global sync
        global n
        n += 1
        if doc_snapshot[0].get('state') != state:
            media_player.set_pause(media_player.is_playing())
            state = doc_snapshot[0].get('state')
            callback_done.set()
        elif doc_snapshot[0].get('rev') != rev:
            cur = vlc.libvlc_media_player_get_time(media_player)
            vlc.libvlc_media_player_set_time(media_player, cur-5000)
            rev = doc_snapshot[0].get('rev')
            callback_done.set()
        elif doc_snapshot[0].get('forw') != forw:
            cur = vlc.libvlc_media_player_get_time(media_player)
            vlc.libvlc_media_player_set_time(media_player, cur+5000)
            forw = doc_snapshot[0].get('forw')
            callback_done.set()
        elif doc_snapshot[0].get('sync') != sync:
            sync = doc_snapshot[0].get('sync')
            vlc.libvlc_media_player_set_time(media_player, sync)
            callback_done.set()

    doc_ref = db.collection(u'Watch_party').document(Host_name)

    state = doc_ref.get().to_dict()['state']
    rev = doc_ref.get().to_dict()['rev']
    forw = doc_ref.get().to_dict()['forw']
    sync = doc_ref.get().to_dict()['sync']

    doc_watch = doc_ref.on_snapshot(on_snapshot)


# ___________________________________________________________________________________________________________

run_vlc()

creden = {
    "type": "service_account",
    "project_id": "transi-discord",
    "private_key_id": "c02891243e00e4485d7f5ac88bc0751223e41283",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCui8Z610eEtI0g\nuO+zoHn5DihYHCkzVG8lVC7gS9RcmtEjn9CTFno6BHqNQshvHTj9JpeK05QIgIEQ\nMnClxD2XF6zkIdA0gl0E2VRJazkDK+vzT7RRLIZig+wPFR54R4Y2VWaQ5d90wubr\n4oCjVnjYPtVn0mEko2WcOuupcMPYxJkVhrHbuzS8tiLl9f0wN0RROErvO3L8U7hz\nX4IwrGNv0AV2My2pRAje6kY9G5BeCUjZD7Iq0vrVFdCsNK5rtho7bH1XQ4jNYEjf\nt79O+aD+F7468hxeBkuuGPnGUfO6uO0eHHe/Lgayvbdk7xjVcdYqaSaJDIIkHgoh\nGI1w2cW3AgMBAAECggEADl9jGhVlBbfqURH5ZvSlZo00ZED5YYkn186NR5nm5DM5\nWnIb9iipKuLYho5Du+aPnUTSwLM4YtTWC9Pjc7rriWgBLA3eu5wqda5BowQJv0mc\nFb5v7ik47Z7ITtuh1SyqkAnLNs4+7rnn0u+lQQ3rSH8wCmsH5cDwqoMtiZfIAK7Y\ny+rdxPspTkshtVewZD+1RiLwuqH85inEhPJLm/2Bl7AHetDLD6Xp8qm8UL1zoZi3\n2EeSdgYXOAJP68l0oyqDbvrTd4sTNcHygUushJwj7xvhfu/EhvWMwNTt6/ZXdWVb\n51le8Fm3QOUVJe79CoOMi0u9tieh5P0iYQ1/s8qJ0QKBgQDYKAvd8kqeTPGwQuNB\n0wHkpdvkJxyc5Ua37CmpVAUChSljqsHqVe2pK5bN97XE3VW2vGBEZQUIwwpr5fak\nSM1Vki4xG+L14fDGY5b5jNeHgO9WtJTjo9dht0Wa3XEtOE/x2WA0+hAp0DsNwy0s\neEiYHrQrWdXjOIwzZzmI0nRTcQKBgQDOuDkFroZfMm7MUe9hHa8fZea8zq4rTjak\n5CaFnj5Spvl/n3RODKHLws5P2tzSyD7N9JSLLgYNrL0l0bptEBfGUl8syWGhFoCA\n+qMYDNErAWaFCkDhBu896V5IBqIKzyBQ1klN9HPc/4bPuVPqWQGIrF3QL8o++ITY\n1APvwYNHpwKBgQC9oPQ4M9UOZwYo0aU5G/ovMupjj4RkiCewNrid2h3DBjs3OpiA\nEf47SQg1jTijimElvMDff5gZBbJg0g+8NDoe9e0cHBDSEPL/uGK8briuIYjWkfmE\nczoCeZvQrrAZMavAyijCkRYY+Jq2CiHZP3TALz90QI2JlxQ4DDjHNYnjoQKBgQCp\nARw9dO4OrmC/Us1ujKI7/UejXSYv6YXrUUvdOf6h/DlHCcpAdTtiJyYdS0X2Xhha\nsXcwQrRYQb1ySgEsYVfOoFGHgCz9UjRFPqRQaUoo6sAyTKu2TcES0NRv9lxMkgJN\nlKPhw9Vl/NLuyQm+Mn56itE3/5pN2UhjLRL61S7LSQKBgHo1S76GDzrXVQJixZ0j\nzisEHTwUIGYcdNpPyLyAGEHvuhYoUmE6Le0cuUjBBVqcSgDB5FO++3jxF6ZOb7p4\nMyRt3M88qJjKTojnrdbo/LlLe0AVMoT6/6q1kSOLyZcaPHKCDq/bB/JfEvopDeiN\nmAD4NIHDlYS/K4QLochbxtZh\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-c6j1u@transi-discord.iam.gserviceaccount.com",
    "client_id": "112291249322114993643",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-c6j1u%40transi-discord.iam.gserviceaccount.com"
}

cred = credentials.Certificate(
    creden)
initialize_app(cred)
db = firestore.client()

user = input("Are you  a) Host or b) Client (Type 'a' or 'b') :   ")
print("")


# Host _______________________________________________________________________________________________________

if(user == 'a'):

    is_host = True
    Host_name = input("Type Host name:   ")
    print("")
    temp = True

    while(temp):
        temp = False
        docs = db.collection("Watch_party").get()
        for doc in docs:
            if(str(doc.id) == Host_name):
                Host_name = input("Host name already exists Type again:   ")
                print("")
                temp = True
                break

    doc = db.collection("Watch_party").document(Host_name)
    doc.set({"state": state, "rev": rev, "forw": forw, "sync": sync})

    run_host(db, Host_name)

    while(True):
        print("List of Options:")
        print("")
        print("0. Close program")
        print("1. Change subtitles")
        print("2. Sync all player")
        print("")
        check = input("Enter the option number:  ")
        if(check == '0'):
            db.collection("Watch_party").document(
                Host_name).delete()
            exit()
        elif(check == '2'):
            doc = db.collection("Watch_party").document(Host_name)
            sync = vlc.libvlc_media_player_get_time(media_player)
            doc.set({"state": state, "rev": rev, "forw": forw, "sync": sync})
        elif(check == '1'):
            change_subs()
        system('cls')


#  Client __________________________________________________________________________________________________

elif(user == 'b'):

    is_host = False
    docs = db.collection("Watch_party").get()

    names = []

    print("Choose your Host: ")
    for i, doc in enumerate(docs):
        print(f"{i+1})  " + doc.id)
        names.append(doc.id)

    print("")
    host_num = int(input("Enter the corresponding Host number:  "))
    Host_name = str(names[host_num-1])

    print("")

    thread = Thread(target=run_client, args=(db, Host_name,))
    thread.daemon = True
    thread.start()

    while(True):
        print("List of Options:")
        print("")
        print("0. Close program")
        print("1. Change subtitles")
        print("")
        check = input("Enter the option number:  ")
        if(check == '0'):
            exit()
        system('cls')
