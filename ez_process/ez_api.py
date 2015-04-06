#==============================================================================#
#                                  ez_api.py                                   #
#==============================================================================#

#============#
#  Includes  #
#============#

import cPickle as pickle
from ez_process_base import ez_process_base, p2pCommand, AmbiguousMaster

# adding the eZchat path to search directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             os.pardir))
import ez_user as eu
import ez_message as em
import ez_preferences as ep

from ez_gpg import ez_gpg

#==============================================================================#
#                                 class ez_api                                 #
#==============================================================================#

class ez_api(ez_process_base):
  """
  Retrieving user information and handling commands.

  Class ez_api brings along abunch of methods intended to be called directly by
  the user. The class is inherited by the client via ez_process which makes the
  methods available for the UI. It also takes care of the user and message
  database.

  Class variable *name*, declareing the user_id, is required for
  initiating ez_api and is specified by the keyword ``'name'``

  Class variable *UserDatabase* represents the Database where contact
  information is stored, i.e. Usernames, Database user ids (UIDs), possibly
  current IP and latest IPs and the Public key.

  Class variable *MsgDatabase* represents the Database storing messages.
  Messages cannot be read unless a valid private key is available.

  """
  def __init__(self, **kwargs):
    super(ez_api, self).__init__(**kwargs)
    assert('name' in kwargs)
    self.name = kwargs['name']

    # TODO: (bcn 2014-10-19) @JNicL:
    # This would give every client a fresh database.
    #user_db_name = 'sqlite:///:memory:'
    #msg_db_name = 'sqlite:///:memory:'
    # Doesn't work, however, as you seem to be relying on files. There
    # is also no need for seperate user and msg databases.
    user_db_name = ('sqlite:///' + ep.join(ep.location['db'], self.name) +
                    '_contacts')
    msg_db_name = ('sqlite:///' + ep.join(ep.location['db'], self.name) +
                   '_messages')

    # uncomment here -> problem with private/public keys
    # TODO: (bcn 2014-10-19) It is peculiar that it works in the cli when both
    # share the SAME user database which is local/ez.db. The tests work with
    # both versions. We should craft a test that is closer to the implementation
    # used in ez_process and find the problem.
    #self.UserDatabase = eu.UserDatabase(localdb=user_db_name)
    self.UserDatabase = eu.user_database
    self.MsgDatabase = em.MessageDatabase(localdb=msg_db_name)
    for key in ez_gpg.gpg.list_keys():
      name = key['uids'][0].split()[0]
      fingerprint = key['fingerprint']
      if not eu.user_database.in_DB(UID=fingerprint):
        new_user = eu.User(UID=fingerprint, name=name)
        self.UserDatabase.add_entry(new_user)

    try:
      self.fingerprint = ez_gpg.find_key(nickname=self.name)
      if not self.UserDatabase.in_DB(UID=self.fingerprint):
        raise Exception('Impossible to find identify ' + str(self.name) +
                        ' in key ring')
      self.myself = self.UserDatabase.get_entry(UID=self.fingerprint)
    except Exception, e:
      raise

  def cmd_close(self):
    """ Client shutdown """
    self.enableCLI = False
    self.enqueue('shutdown')

  def cmd_get_contact_names(self):
    UIDs = self.UserDatabase.UID_list()
    #return [entry.name for entry in self.UserDatabase.get_entries(UIDs)]
    print [entry.name for entry in self.UserDatabase.get_entries(UIDs)]

  def cmd_ping(self, user_id):
    """Ping a user given his ID."""
    try:
      cmd_dct = {'user_id': user_id}
      self.enqueue('ping_request', cmd_dct)
    except:
      self.error("Syntax error in ping")

  def cmd_add(self, user_id, host, port, fingerprint=None):
    """
    Add user IP to clients IP list.

    :param user_id: id specifying the username
    :type  user_id: string

    :param host: hosts IP
    :type  host: string

    :param port: hosts port
    :type  port: integer
    """
    try:
      cmd_dct = {'user_id': user_id, 'host': host, 'port': port}
      if fingerprint is not None:
        cmd_dct['fingerprint'] = fingerprint
      self.add_client(**cmd_dct)
      self.enqueue('ping_request', cmd_dct)
    except Exception as e:
      self.error("Error in cmd_add: " + str(e))

  def cmd_servermode(self, host, port):
    """
    Switch the client to servermode enabling to connect other users.

    A users in the network can use the method
    :py:meth:`ez_process.ez_api.ez_api.cmd_ips` to ask the client for
    connection. The client then relays the request to other users and connects
    them which each other. The connection process is described by the class
    :py:class:`ez_process.ez_relay.ez_relay`

    :param host: hosts IP
    :type  host: string

    :param port: port on which to listen to
    :type  port: integer
    """
    try:
      cmd_dct = {'host': host, 'port': port}
      self.enqueue('servermode', cmd_dct)
    except:
      self.error("Syntax error in servermode")

  def cmd_authenticate(self, host, port):
    """
    Connect to the eZchat server with authentication.

    A connection to a server enables the use of
    :py:meth:`ez_process.ez_api.ez_api.cmd_ips`.

    :param host: server IP
    :type  host: string

    :param port: server port
    :type  port: integer
    """
    cmd_dct = {'host': host, 'port': int(port)}
    try:
      self.enqueue('authentication_request', cmd_dct)
      eZchat = 'ez'
      fingerprint = ez_gpg.find_key(nickname=eZchat)
      cmd_dct['user_id'] = eZchat
      cmd_dct['fingerprint'] = fingerprint

      self.add_client(**cmd_dct)
      self.success("Started cmd_authenticate")
    except:
      self.error("Syntax error in cmd_authenticate")

  def cmd_connect(self, host, port):
    """
    Connect to a server.

    A connection to a server enables the use of
    :py:meth:`ez_process.ez_api.ez_api.cmd_ips`.

    :param host: server IP
    :type  host: string

    :param port: server port
    :type  port: integer
    """
    #master = (host, int(port))
    cmd_dct = {'host': host, 'port': int(port)}
    try:
      self.enqueue('connect_server', cmd_dct)
      cmd_dct['user_id'] = 'server'
      self.add_client(**cmd_dct)
    except:
      self.error("Syntax error in connect")

  def cmd_bg(self):
    """ Show background processes """
    try:
      print ("background_processes:", self.background_processes)
    except:
      self.error("Syntax error in bp")

  def cmd_sync(self, user_id):
    """
    Initiate mesage database sync request.

    :param user_id: the user with thom to sync
    :type  user_id: string
    """
    try:
      cmd_dct = {'user_id': user_id}
      self.enqueue('db_sync_request_out', cmd_dct)
    except:
      self.error("Syntax error in cmd_sync")

  def cmd_passive_sync(self):
    """
    Initiate passive mesage database syncing. The frequency is determined in
    ez_process_preferences.
    """
    try:
      self.enqueue('db_sync_background')
    except:
      self.error("Error in cmd_passive_sync")

  def cmd_ips(self, user_id):
    """
    Request IPs from a user in servermode.

    :param user_id: clients username
    :type  user_id: string
    """
    try:
      master = self.get_master(user_id=user_id)
    except Exception as e:
      self.error('error in cmd_ips: ' + str(e))
      return

    cmd_dct = {'master': master}
    self.enqueue('ips_request', cmd_dct)

  def cmd_key(self, user_id):
    """
    Public key request.

    :param user_id: clients username
    :type  user_id: string
    """
    try:
      cmd_dct = {'user_id': user_id}
      self.enqueue('contact_request_out', cmd_dct)
    except:
      self.error("Syntax error in key")

  def cmd_send_msg(self, msg, user_id=None, fingerprint=None):
    """ Sends an encrypted message.

    The method requires the target client to be online. The encryption can only
    be done if a valid public key of the targets client is available.

    :param user_id: clients username
    :type  user_id: string

    :param msg: message
    :type  msg: string
    """
    try:
      if not self.UserDatabase.in_DB(UID=fingerprint):
        # raise error instead
        self.error("User not in DB")
        return

      # store msg in db
      try:
        self.success(str(self.fingerprint))
        mx = em.Message(str(self.fingerprint), fingerprint, str(msg))
        self.success('Put UID: ' + str(mx.UID) + ' to the msg database')
      except Exception as e:
        self.error('In cmd_send_msg: ' + str(e))
        return
      self.MsgDatabase.add_entry(mx)

      try:
        masters = (self.get_master(fingerprint=unicode(fingerprint)),)
      except AmbiguousMaster as e:
        masters = e.masters
        for master in masters:
          self.enqueue('ping_request', {'master': master})
      except Exception as e:
        self.error('Message was not delivered: ' + str(e))
        return

      for master in masters:
        data = pickle.dumps(mx)
        cmd_data = {'user_specs': master, 'data': data}
        self.enqueue('send', cmd_data)

    except Exception as e:
      self.error("Syntax error in command: " + str(e))

  def cmd_ping_background(self):
    """ start background ping process """
    self.enqueue('ping_background')

  def cmd_stop_background_process(self, process_id, queued=False):
    """
    Stops a backgroundprocess specified by a process_id.

    :process_id: Usually a tuple of strings. See, for instance,
                 :py:meth:`ez_process.ez_ping.ez_ping.ping_background`.

    This process is by default not queued.
    """
    try:
      assert(len(process_id) > 0)
    except:
      raise Exception('No process ID given.')

    cmd_dct = {'process_id': process_id}
    if queued:
      self.enqueue('stop_background_process', cmd_dct)
    else:
      self.stop_background_process(process_id)
