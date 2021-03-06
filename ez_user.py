# encoding=utf-8 ==============================================================#
#                                   ez_user                                    #
#==============================================================================#

#============#
#  Includes  #
#============#
from Crypto.Hash import SHA # Shorter IDs than with 256
import ez_crypto as ec
import ez_database as ed

#==============================================================================#
#                                  class User                                  #
#==============================================================================#

class User(object):
  """
  - ask for username, pw
      - create db entry
      - create private/public key pair
      - store public key public
  - db-entry for groups, network
  - db-entry for with all msg-ids as recipient
  """
  # TODO: (bcn 2014-08-01) will we remove IP again ?
  components = ['UID', 'name', 'public_key', 'IP', 'last_IPs']

  def __init__(self, name='', current_ip='', public_key=None, _dict=None):
    """
    This method will create a new user of the network.
    IP is a string of the form 123.123.123.123:12345.
    """
    if _dict:
      for x in User.components:
        setattr(self, x, _dict[x])
    else:
      self.name = name
      if public_key:
        self.public_key = public_key
      else:
        er = ec.eZ_RSA()
        self.public_key = er.generate_keys(self.name)
      self.UID = SHA.new(self.name + self.public_key).hexdigest()

      self.IP = current_ip
      # The database doesn't like lists. We can join them with some char though
      self.last_IPs = ' '

  def current_ip_and_port(self):
    lst = self.IP.split(':')
    return (lst[0], lst[1])

#==============================================================================#
#                              class UserDatabase                              #
#==============================================================================#

class UserDatabase(ed.Database):
  """
  The UserDatabase class gives access to the saved information about users in
  the SQL database
  """

  def __init__(self, **kwargs):
    """
    Opens a local sqlite database in the default location default_db,
    which is saved to and loaded from disk automatically. To create a merely
    temporary database in memory use 'sqlite:///:memory:'
    """
    ed.Database.__init__(self, 'Users', User, **kwargs)

  def check_for_ip(self, ip, port):
    """
    Given IP and port, check whether the user is in DB is in DB and return UID.
    """
    user = self.get_entry(IP=':'.join([ip, port]))
    return user.UID

#==============================================================================#
#                               Global Instance                                #
#==============================================================================#
user_database = UserDatabase()
