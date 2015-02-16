#!/usr/bin/env python
#encoding: utf-8
import os
import gnupg
import ez_preferences as ep

###############
#  functions  #
###############

class ez_gpg(object):

  """Docstring for ez_gpg. """
  # ep.join(ep.location['gpg'], fname)
  gpg_path = os.path.join(os.environ['HOME'], '.gnupg')
  gpg_params = {'encoding': "utf-8",
                'init': {'gnupghome': gpg_path},
                'key_server_list': ['keys.gnupg.net', 'pgp.mit.edu']}

  gpg = gnupg.GPG(**gpg_params['init'])
  gpg.encoding = gpg_params['encoding']

  #@staticmethod
  #def gpg_path(systemwide=False, fname=None):
    #if systemwide:
      #return os.path.join(os.environ['HOME'], ".ez_gnupg")  # eventually .gnupg
    #else:
      #return ep.join(ep.location['gpg'], fname)

  @classmethod
  def find_key(self, nickname=None):
    if nickname is None:
      print("yolowtf!!")
      return None

    thatkey = [(any(nickname in u for u in key['uids']))
               for key in self.gpg.list_keys()]
    if not any(thatkey):
      raise Exception('Key not found')
    thatkey = self.gpg.list_keys()[thatkey.index(True)]
    print "nick, fingerprint"
    print nickname, thatkey['fingerprint']
    return thatkey['fingerprint']

  @classmethod
  def check_keys(self, key_id=None, remote_check=True):
    """ Check if given `key_id` matches a database.

    If provided with a key ID, first checks locally, then remotely for the key.
    Without arguments it just return all local keys.

    @param: key_id
    @type:  string
    """

    local_list = self.gpg.list_keys()

    if key_id is None:
      return local_list
    elif key_id in [key['keyid'] for key in local_list]:
      #return [{key_id: 'LOCAL'}]
      return key
    elif remote_check:
      remote_list = [key_id for server in self.gpg_params['key_server_list']
                     if self.gpg.recv_keys(server, key_id)]
      if remote_list:
        return remote_list
    raise NameError('Key with ID \'' + key_id + '\' not found')

  @classmethod
  def generate_key(self, user=None, params=None, secret=True):
    """ Generates a gpg-key object and exports it to a file.

    The `params` dictionary contains various options, see
    gpg_params['key_params'] for required fields.

    @param: user
    @type:  string

    @param: params
    @type:  dict

    @param: secret
    @type:  bool
    """

    if params is None:
      key_params = {'key_type': "RSA",
                    'key_length': 4096,
                    'name_real': os.environ['USER'],
                    'name_comment': "eZchat communication key"}
      params = self.gpg.gen_key_input(**key_params)

    new_key = self.gpg.gen_key(params)

    if user:
      if secret:
        ext = 'sec'
      else:
        ext = 'pub'
      uname = '.'.join((user, ext))
      with open(self.gpg_path(fname=uname), 'w') as f:
        f.write(new_key.gpg.export_keys(new_key.fingerprint, secret))
    else:
      return new_key

  @classmethod
  def encrypt_msg(self, nickname, msg):
    try:
      fingerprint = self.find_key(nickname)
    except:
      raise
    cipher = self.gpg.encrypt(msg, fingerprint)
    return cipher

  @classmethod
  def decrypt_msg(self, cipher):
    msg = self.gpg.decrypt_msg(cipher)
    return msg

  @classmethod
  def sign_msg(self, msg):
    signed_msg = self.gpg.sign(msg)
    return signed_msg

  @classmethod
  def verify_signed_msg(self, signed_msg):
    verified = self.gpg.verify(signed_msg.data)
    if(verified.trust_level is not None and
       verified.trust_level >= verified.TRUST_FULLY):
      return True
    else:
      return False

################################################################################
#                                     main                                     #
################################################################################

if __name__ == '__main__':
  #ez_gpg.generate_key('yolo')
  #data = 'randomdata'
  #print ez_gpg.gpg.list_keys()

  #with open('ez.pub', 'r') as f:
    #ez_key = f.read()
    #ez_gpg.gpg.import_keys(ez_key)

    #f.write(ez_gpg.gpg.export_keys(u'8D38E2A7CC1D9602'))
  #print(gpg.list_keys())
  #print find_key('gsec')
  #fp = find_key('gsec')
  #print  gpg.import_keys(fp)
  #print gpg.encrypt(data, fp)
  #try:
    #print ez_gpg.encrypt_msg('yolo', data)
  #except Exception as e:
    #print(e)

  #signed_data = ez_gpg.gpg.sign(data.data)
  #verified = ez_gpg.gpg.verify(signed_data)

  #stream = open("example.txt", "rb")

  signed_data = ez_gpg.gpg.sign(data)

  verified = ez_gpg.gpg.verify(signed_data.data)
  print "verified:", verified.__dict__
  if verified.trust_level is not None and verified.trust_level >= verified.TRUST_FULLY:
    print('Trust level: %s' % verified.trust_text)

  print "Verified" if verified else "Unverified"