#==============================================================================#
#                                ez_db_sync.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base, p2pCommand, p2pReply, command_args
import cPickle as pickle
import ez_process_preferences as epp

#==============================================================================#
#                               class ez_db_sync                               #
#==============================================================================#

class ez_db_sync(ez_process_base):
  """
  A method for requesting a message database update.

  The call db_sync_request_out will request syncs with online users. The method
  db_sync_request_in is not intended to be called by the user, but is
  automaticallly invoked as a db sync request enters.
  """

  def __init__(self, *args, **kwargs):
    super(ez_db_sync, self).__init__(*args, **kwargs)

  @command_args
  def db_sync_request_out(self, user_id):
    """
    Start a message database sync request with the specified user.

    :param user_id: the user with whom to sync
    :type  user_id: string
    """

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      cmd_dct = {'user_id': self.name, 'UID_list': self.MsgDatabase.UID_list()}
      db_sync_request = {'db_sync_request_in': cmd_dct}
      msg = pickle.dumps(db_sync_request)
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.error(str(e))

  @command_args
  def db_sync_request_in(self, user_id, UID_list):
    """
    Answer to a db_sync_request_out. Do not call.
    """

    if user_id in self.ips:
      self.success('Received msg db sync request from: ' + user_id)
      user_addr = self.ips[user_id]
      self.success('Received ' + str(UID_list))
      UIDs_to_sync = self.MsgDatabase.complement_entries(UID_list)
      self.success('Sending ' + str(UIDs_to_sync))
      if len(UIDs_to_sync) != 0:
        msges = self.MsgDatabase.get_entries(UIDs_to_sync)

        self.success('Sending ' + str(len(msges)) + ' messages  to : ' +
                     user_id)
        for msg in msges:
          data = pickle.dumps(msg)
          cmd_dct = {'user_id': user_id, 'data': data}
          self.commandQueue.put(p2pCommand('send', cmd_dct))

  @command_args
  def db_sync_background(self):
    process_id = ('db_sync_request_out', 'all')

    def db_sync_func(self_timer, queue, user_ips):
      user_ids = user_ips.keys()

      for user_id in user_ids:
        cmd_dct = {'user_id': user_id}
        queue.put(p2pCommand('db_sync_request_out', cmd_dct))

      if process_id in self.background_processes:
        self.reset_background_process(process_id)

    bgp = p2pCommand('start_background_process',
                     {'process_id': process_id,
                      'callback': db_sync_func,
                      'interval': epp.db_bgsync_timeout,
                      'callback_args': (self.commandQueue, self.ips, )})
    self.commandQueue.put(bgp)

