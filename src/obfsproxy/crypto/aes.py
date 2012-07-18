from Crypto.Cipher import AES
from Crypto.Util import Counter
import base64
import os

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# the character used for padding--with a block cipher such as AES, the value
# you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
# used to ensure that your value is always a multiple of BLOCK_SIZE
PADDING = '{'

# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

class AESCoder(object):
  def __init__(self, key):
    counterIn=Counter.new(128)
    self.cipherIn=AES.new(key, mode=AES.MODE_CTR, counter=counterIn)

    counterOut=Counter.new(128)
    self.cipherOut=AES.new(key, mode=AES.MODE_CTR, counter=counterOut)

  def encrypt(self, data):
    return self.cipherOut.encrypt(pad(data))

  def decrypt(self, data):
    return self.cipherIn.decrypt(data).rstrip(PADDING)
