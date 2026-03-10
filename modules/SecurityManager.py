import subprocess
import hashlib
from Crypto.Cipher import AES
import base64
import os
import keyring
import winreg
import ctypes
from ctypes import wintypes


class SecurityManager:

    @staticmethod
    def get_machine_guid():
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            )

            guid, _ = winreg.QueryValueEx(key, "MachineGuid")

        except Exception as e:
            raise RuntimeError(f"Failed to read MachineGuid: {e}")

        guid = guid.replace("-", "")

        return guid

    @staticmethod
    def get_encryption_key():
        guid = SecurityManager.get_machine_guid()

        # 加盐
        salt = "InterKnot2026"

        key = hashlib.sha256((guid + salt).encode()).digest()
        # print("Encryption key:", key.hex())

        return key
    
    @staticmethod
    def encrypt(data: str, key: bytes) -> str:
        cipher = AES.new(key, AES.MODE_GCM)

        ciphertext, tag = cipher.encrypt_and_digest(data.encode())

        result = cipher.nonce + tag + ciphertext

        return base64.b64encode(result).decode()
    
    @staticmethod
    def decrypt(token: str, key: bytes) -> str:
        raw = base64.b64decode(token)

        nonce = raw[:16]
        tag = raw[16:32]
        ciphertext = raw[32:]

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        data = cipher.decrypt_and_verify(ciphertext, tag)

        return data.decode()
    
    @staticmethod
    def save_password(username: str, password: str):
        key = SecurityManager.get_encryption_key()

        encrypted_password = SecurityManager.encrypt(password, key)

        keyring.set_password("InterKnot", username, encrypted_password)
        print(f"Password for {username} saved securely.")

    @staticmethod
    def get_password(username: str) -> str:
        key = SecurityManager.get_encryption_key()

        encrypted_password = keyring.get_password("InterKnot", username)

        if encrypted_password is None:
            return None

        try:
            decrypted_password = SecurityManager.decrypt(encrypted_password, key)
        except Exception as e:
            print(f"Error decrypting password for {username}: {e}")
            keyring.delete_password("InterKnot", username)
            return ""

        return decrypted_password

    @staticmethod
    def delete_password(username: str):
        try:
            keyring.delete_password("InterKnot", username)
            print(f"Password for {username} deleted.")
        except: pass

class CredentialManager:

    advapi32 = ctypes.WinDLL("Advapi32.dll")

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.c_void_p),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    PCREDENTIAL_PTR = ctypes.POINTER(ctypes.POINTER(CREDENTIAL))

    CredEnumerate = advapi32.CredEnumerateW
    CredFree = advapi32.CredFree

    CredEnumerate.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(PCREDENTIAL_PTR),
    ]

    CredFree.argtypes = [ctypes.c_void_p]

    @staticmethod
    def list_usernames(service=None):
        """返回凭据管理器中的用户名列表，如 ['a','b']"""
        count = wintypes.DWORD()
        creds = CredentialManager.PCREDENTIAL_PTR()
        users = []

        if CredentialManager.CredEnumerate(None, 0, ctypes.byref(count), ctypes.byref(creds)):
            for i in range(count.value):
                cred = creds[i].contents
                target = cred.TargetName
                username = cred.UserName

                # service 过滤（包含匹配）
                if username and (service is None or (target and service in target)):
                    users.append(username)

            CredentialManager.CredFree(creds)

        # 去重
        return list(dict.fromkeys(users))
    

# a = CredentialManager.list_usernames(service="InterKnot")
# print(a) 