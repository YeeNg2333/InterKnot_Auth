import subprocess
import hashlib
from Crypto.Cipher import AES
import base64
import os
import keyring
import winreg



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

        return SecurityManager.decrypt(encrypted_password, key)