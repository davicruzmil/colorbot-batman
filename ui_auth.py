import os
import sys
import hashlib
from keyauth import api
from ui_colorbot import start_colorbot_interface

def clear():
    if sys.platform == 'win32':
        os.system('cls')
    elif sys.platform.startswith('linux'):
        os.system('clear')

def get_checksum():
    md5_hash = hashlib.md5()
    with open(''.join(sys.argv), "rb") as file:
        md5_hash.update(file.read())
    digest = md5_hash.hexdigest()
    return digest

keyauthapp = api(
    name = "BatmanSpoofer", # Application Name
    ownerid = "xUAJqxfOK8", # Owner ID
    secret = "06181572c98a641c13f77f47f7eebbbeeb48d13e976268a76d2c9cf1517e93c9", # Application Secret
    version = "1.0", # Application Version
    hash_to_check = getchecksum()
)
def authenticate():
    key = input("Digite a chave de autenticação: ")
    if keyauthapp.license(key):
        return True
    else:
        print("Chave de autenticação inválida.")
        return False

if __name__ == "__main__":
    clear()
    print("Bem-vindo ao ColorBot!")
    print("Por favor, faça a autenticação para continuar.")
    
    authenticated = False
    while authenticated == False:
        authenticated = authenticate()
    
    print("Autenticação bem-sucedida! Iniciando o ColorBot...")
    start_colorbot_interface()
