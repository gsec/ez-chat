# encoding=utf-8
from __future__ import print_function
from test_tools import *

import ez_crypto as ec
import ez_message as em
import ez_database as ed
import ez_user as eu

text01 = """
If your public attribute name collides with a reserved keyword, append a single
trailing underscore to your attribute name. This is preferable to an
abbreviation or corrupted spelling. (However, notwithstanding this rule, 'cls'
is the preferred spelling for any variable or argument which is known to be a
class, especially the first argument to a class method.)
"""
text02 = "hi, was geht"
author = 'Alice'
reader = 'Bob'
extime = '2014-07-15 11:09:43.059036'

def test_AES():
  """
  Symmetric AES Encryption tests
  """
  kwargs_package = {'plain':text01, 'crypt_mode':0}
  aes_object = ec.eZ_AES(**kwargs_package)
  geheim01 = aes_object.encrypt()
  print("\nCrypted Object KWARGS:\n", geheim01)

  aes_object = ec.eZ_AES(text02)
  geheim02 = aes_object.encrypt()
  print("\nCrypted Object ARG:\n", geheim02)

  crypt_object = ec.eZ_AES(**geheim01)
  ungeheim = crypt_object.decrypt()
  print("Plain:\n", ungeheim)
  eq_(text01, ungeheim['plain'])

  # Text Padding
  text03 = "123456"
  text04 = "123456\1\0\0\0\0\0\0\0\0\0\1\1\1\0\0\0"
  text05 = "1234567890abcdef"
  pad_block = "\1" + 15 * "\0"
  aes_object = ec.eZ_AES(text02)
  eq_(aes_object.add_padding(text03), "123456\1\0\0\0\0\0\0\0\0\0")
  # covers line (if pad_length = 0 ) in pad function:
  eq_(aes_object.add_padding(text05), text05 + pad_block)

  eq_(aes_object.remove_padding(aes_object.add_padding(text04)), text04)

def test_RSA():
  """
  Asymmetric RSA encryption tests
  """
  er = ec.eZ_RSA()
  # temporary key generation
  priv_key, pub_key = er.generate_keys(user="FAKE_USER", testing=True)
  #er.generate_keys(user='Bob')
  sig02 =  er.sign(priv_key, text02)
  wrongsig = 'somerandomstuff'
  eq_(er.verify(pub_key, text02, sig02), True)
  eq_(er.verify(pub_key, text02, wrongsig), False)
  eq_(er.verify(pub_key, text01, sig02), False)

def test_OmniScheme():
  """
  Overall Crypto Scheme with AES + RSA(AES_key)
  """
  er = ec.eZ_RSA()
  if not eu.user_database.in_DB(name=author):
    print("\nAdding " + author + " to database\n")
    eu.user_database.add_entry(eu.User(author, '0.0.0.0' + ':' + '0'))
  if not eu.user_database.in_DB(name=reader):
    print("\nAdding " + reader + " to database\n")
    eu.user_database.add_entry(eu.User(reader, '0.0.0.0' + ':' + '0'))
  package = {'etime':extime, 'sender':author,
             'recipient':reader, 'content':text01}
  es = ec.eZ_CryptoScheme(**package)
  supergeheim = es.encrypt_sign()

  print("::::::::::::::::::::::::::::::::::::::::::")
  print("\nSupergeheim\n==========")
  for k,v in supergeheim.iteritems():
    print(k, "=", v)
  dees = ec.eZ_CryptoScheme(**supergeheim)
  vollungeheim = dees.decrypt_verify()
  print("::::::::::::::::::::::::::::::::::::::::::")
  print("\nWieder in normal\n==========")
  for k,v in vollungeheim.iteritems():
    print(k, "=", v)
