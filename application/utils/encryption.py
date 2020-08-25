import json

from cryptography.fernet import Fernet

from config import config


class Cryptography:
    def __init__(self):
        self.key = config.SECRET_KEY
        self.raw_data = ''
        self.encrypted_data = ''
        self.decrypted_data = ''
        self.supported_types = [str, dict, list, tuple, int, float]

        # cryptographic function definition
        self.crypto_function = Fernet(self.key)

    def encrypt(self, raw_data):
        
        if type(raw_data) in self.supported_types:
            self.raw_data = str.encode(json.dumps(raw_data))
            encrypted_data = self.crypto_function.encrypt(self.raw_data)
            self.encrypted_data = encrypted_data
            return self.encrypted_data.decode("utf-8")
        else:
            raise TypeError("Type %s is not supported. Type must be one of: %s" % (type(raw_data), self.supported_types))

    def decrypt(self, encrypted_data):
        try:
            self.encrypted_data = encrypted_data.encode("utf-8")
        except Exception:
            raise
        decrypted_data = self.crypto_function.decrypt(self.encrypted_data)

        self.decrypted_data = json.loads(decrypted_data.decode('utf-8'))
        return self.decrypted_data


cryptograpy = Cryptography()