#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This module is a convenience wrapper for the AES cipher in CTR mode. """

from Crypto.Cipher import AES
from Crypto.Util import Counter

class AES_CTR_128(object):
    """An AES-CTR-128 PyCrypto wrapper."""

    def __init__(self, key, iv):
        """Initialize AES with the given key and IV."""

        assert(len(key) == 16)
        assert(len(iv) == 16)

        self.ctr = Counter.new(128, initial_value=long(iv.encode('hex'), 16))
        self.cipher = AES.new(key, AES.MODE_CTR, counter=self.ctr)

    def crypt(self, data):
        """
        Encrypt or decrypt 'data'.
        """
        return self.cipher.encrypt(data)

