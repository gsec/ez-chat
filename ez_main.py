#==============================================================================#
#                                   ez_main                                    #
#==============================================================================#

#============#
#  Includes  #
#============#
import sys, os, time

from ez_client import *
from ez_server import *
import Queue

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from ips import *

#==============================================================================#
#                                 class ez_Gui                                 #
#==============================================================================#

class ez_Gui(QtGui.QWidget):

  def __init__(self):

    #super(ez_Gui, self).__init__()
    QtGui.QMainWindow.__init__(self)

    # variables
    self.history_path = os.path.join(os.path.dirname(__file__), 'history',
                                     'history_database.txt')
    self.gui_path = os.path.join(os.path.dirname(__file__), 'ui02.ui')
    self.group_members=["Nick","Bijan","Gui","Uli"]
    self.user = "Ul]["

    #loading the GUI
    self.chatwindow = loadUi(self.gui_path, self)

    # Data are imported from the database into a Model class
    self.history_modell = Model(self.history_path)

    # Data are transfered from the modell class to the View class
    self.show_history = View(self.history_modell, self.chatwindow.listView)


    # connections and actions
    self.chatwindow.connect(self.chatwindow.Send_Button, SIGNAL("released()"),
                            self.message_send)
    self.chatwindow.connect(self.chatwindow.pushButton_5, SIGNAL("clicked()"),
                            self.clear_history)
    self.chatwindow.connect(self.chatwindow.pushButton_3, SIGNAL("clicked()"),
                            self.connect_client)

    ports = [u['port'] for u in ips_open.db.all()]
    self.port = ports[0]

    self.server = server()
    self.server.start()
    self.server.commandQueue.put(ServerCommand(ServerCommand.connect,
                                              ("localhost",self.port)))
    ips_open.remove_port(self.port)
    ips_taken.add_port(self.port)

    self.clients = []
    #self.clients.append(client())

    self.update_timer()

    # execute application
    self.chatwindow.show()


#==============================================================================#
#                            client related methods                            #
#==============================================================================#

  def update_timer(self):
    self.client_reply_timer = QtCore.QTimer(self)
    self.client_reply_timer.timeout.connect(self.on_reply_timer)
    self.client_reply_timer.start(100)

  def on_reply_timer(self):
    """
    Whenever client_reply_timer timesout on_reply_timer is called, allowing to:

      - accept new connections (server related)
      - check if messages have been received (client related)
      - check if client maintaind connection, otherwise shutdown client
    """

#---------------              server related part               ---------------#

    # The select function monitors all the client sockets and the master
    # socket for readable activity. If any of the client socket is readable
    # then it means that one of the chat client has send a message.

    # Get the list sockets which are ready to be read through select
    try:
      readable, _, _ = select.select(self.server.clients, [], [], 0)
      read = bool(readable)
    except socket.error:
      pass
    if read:
      for user in readable:
        # Found new client
        if user == self.server.server_socket:
          # Handle the case in which there is a new connection recieved through
          # server_socket
          self.server.commandQueue.put(ServerCommand(ServerCommand.accept))

        #Some incoming message from a client
        else:
          # Sofar we do not allow to send data from client to server
          pass

    # check if server logged results in the replyQueue
    try:
      reply = self.server.replyQueue.get(block=False)
      status = "success" if reply.replyType == ServerReply.success else "ERROR"
      self.log('Server reply %s: %s' % (status, reply.data))
    except Queue.Empty:
      pass

#---------------              client related part               ---------------#

    for client in self.clients:
      if not client.alive.isSet():
        client.shutdown()
        self.clients.remove(client)
        self.server.replyQueue.put(self.server.error("removed client"))
        continue

      # If data has been sent to the client readable is active
      try:
        readable, _, _ = select.select([client.client_socket], [], [], 0)
        read = bool(readable)
      except socket.error:
        pass
      # triggered if there is something to read
      if read:
        client.commandQueue.put(ClientCommand(ClientCommand.receive))
      # check if client logged results in the replyQueue
      try:
        reply = client.replyQueue.get(block=False)
        status = "success" if reply.replyType == ClientReply.success         \
                           else "ERROR"
        self.log('Client reply %s: %s' % (status, reply.data))
      except Queue.Empty:
        pass

  def connect_client(self):
    ports = [u['port'] for u in ips_taken.db.all()]
    if self.port in ports:
      ports.remove(self.port)
    if len(ports) > 0:
      for port in ports:
        cl = client()
        cl.alive.set()
        cl.start()
        self.clients.append(cl)
        cl.commandQueue.put(ClientCommand(ClientCommand.connect,
                                         ("localhost", port)))
        cl.replyQueue.put(cl.success("Connection to " +                        \
                                     str(port) + " established"))
    else:
      self.server.replyQueue.put(self.server.error("Connection failed"))


  def closeEvent(self, event):
    reply = QtGui.QMessageBox.question( self, 'Message',
                                        "Are you sure to quit?",
                                        QtGui.QMessageBox.Yes,
                                        QtGui.QMessageBox.No )

    if reply == QtGui.QMessageBox.Yes:

      ips_open.add_port(self.port)
      ips_taken.remove_port(self.port)

      for client in self.clients:
        client.shutdown()

      self.server.shutdown()

      event.accept()
    else:
      event.ignore()

  def log(self, message):
    timestamp = '[%010.3f]' % time.clock()
    f = open(self.history_path, 'a')
    message = timestamp + str(message)
    f.write("\n"+self.user+":\n"+message+"\n")
    f.close()

    self.history_modell.reload(self.history_path)
    self.history_modell.emit(QtCore.SIGNAL("layoutChanged()"))

#---------------      non client or server related methods      ---------------#

  # functions called by the GUI
  def message_send(self):
    # retrieve message
    message = str(self.chatwindow.textEdit.toPlainText())

    # save to history
    f = open(self.history_path, 'a')
    f.write("\n"+self.user+":\n"+message+"\n")
    f.close()

    # Send message to other clients. The client class confirms if sending was
    # successful.
    self.server.commandQueue.put(ServerCommand(ServerCommand.send, message))

    # clear text entry
    self.chatwindow.textEdit.clear()

    # send signal for repainting
    self.history_modell.reload(self.history_path)
    self.history_modell.emit(QtCore.SIGNAL("layoutChanged()"))

  def clear_history(self):
    # opening a file with the write flag ('w') clears the file
    f = open(self.history_path, 'w')
    f.close()

    self.history_modell.reload(self.history_path)
    self.history_modell.emit(QtCore.SIGNAL("layoutChanged()"))

#==============================================================================#
#                                 class Model                                  #
#==============================================================================#

class Model(QtCore.QAbstractListModel):
  def __init__(self, dateiname):
    QtCore.QAbstractListModel.__init__(self)
    self.data = []

    # we could define this later as a variable
    word_wrap_length = 80

    # load data
    f = open(dateiname)

    try:
      lst = []
      for line in f:
        if not line.strip():
          self.data.append(QtCore.QVariant(lst))
          lst = []
        else:
          if len(line.strip()) > word_wrap_length and len(line.split()) > 1:
            sum = 0
            line = ""
            list_of_words = line.split()
            for i in range(len(list_of_words)):
              sum += len(list_of_words[i]) + 1
              if sum < word_wrap_length:
                line += list_of_words[i]+" "
              else:
                sum = len(list_of_words[i])
                lst.append(QtCore.QVariant(line))
                line = list_of_words[i] + " "
            if line:
              lst.append(QtCore.QVariant(line))
          else:
            lst.append(line.strip())
      if lst:
          self.data.append(QtCore.QVariant(lst))
    finally:
        f.close()

  def reload(self, dateiname):
    self.data = []

    word_wrap_length=80     # we could define this later as a variable
    f = open(dateiname)

    try:
      lst = []
      for line in f:
        if not line.strip():
          self.data.append(QtCore.QVariant(lst))
          lst = []
        else:
          if len(line.strip()) > word_wrap_length and len(line.split()) > 1:
            sum = 0
            line = ""
            list_of_words = line.split()
            for i in range(len(list_of_words)):
              sum += len(list_of_words[i]) + 1
              if sum < word_wrap_length:
                line += list_of_words[i]+" "
              else:
                sum = len(list_of_words[i])
                lst.append(QtCore.QVariant(line))
                line = list_of_words[i] + " "
            if line:
              lst.append(QtCore.QVariant(line))
          else:
            lst.append(line.strip())
      if lst:
          self.data.append(QtCore.QVariant(lst))
    finally:
        f.close()

  def rowCount(self, parent=QtCore.QModelIndex()):
      return len(self.data)

  def data(self, index, role=QtCore.Qt.DisplayRole):
      return QtCore.QVariant(self.data[index.row()])

#==============================================================================#
#                                  class View                                  #
#==============================================================================#

class View(QtGui.QListView):
  def __init__(self, modell, parent=None):
    QtGui.QListView.__init__(self, parent)
    self.resize(5000, 3000)
    self.delegate = ViewDelegate()
    self.setItemDelegate(self.delegate)
    self.setModel(modell)
    self.setVerticalScrollMode(QtGui.QListView.ScrollPerPixel)

#==============================================================================#
#                              class ViewDelegate                              #
#==============================================================================#

class ViewDelegate(QtGui.QItemDelegate):
  def __init__(self):
    QtGui.QItemDelegate.__init__(self)

    self.borderColor    = QtGui.QPen(QtGui.QColor(0, 0, 0))
    self.titleTextColor = QtGui.QPen(QtGui.QColor(255, 255, 255))
    self.titleColor     = QtGui.QBrush(QtGui.QColor(120, 120, 120))
    self.textColor      = QtGui.QPen(QtGui.QColor(0, 0, 0))
    self.titleFont      = QtGui.QFont("Helvetica", 10, QtGui.QFont.Bold)
    self.textFont       = QtGui.QFont("Helvetica", 10)

    self.lineHeight  = 15
    self.titleHeight = 20
    self.dist        = 4
    self.innerDist   = 2
    self.textDist    = 4

  def sizeHint(self, option, index):
    n_lines = len(index.data().toList())
    return QtCore.QSize(170, self.lineHeight*n_lines + self.titleHeight)

  def paint(self, painter, option, index):
    border = option.rect.adjusted(self.dist, self.dist,
                                  -self.dist, -self.dist)
    borderTitle = border.adjusted(self.innerDist,
                  self.innerDist, -self.innerDist + 1, 0)
    borderTitle.setHeight(self.titleHeight)
    borderTitleText = borderTitle.adjusted(self.textDist, 0, self.textDist, 0)
    painter.save()
    painter.setPen(self.borderColor)
    # painter.drawRect(rahmen)
    painter.fillRect(borderTitle, self.titleColor)

    # Titel schreiben
    painter.setPen(self.titleTextColor)
    painter.setFont(self.titleFont)
    data = index.data().toList()
    # Do not draw if theres nothing to draw
    if len(data) > 0:
      stringData = data[0].toString()
      painter.drawText(borderTitleText,
                       QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                       data[0].toString())

    # write address
    painter.setPen(self.textColor)
    painter.setFont(self.textFont)
    for i, entry in enumerate(data[1:]):
        painter.drawText(borderTitle.x() + self.textDist,
                         borderTitle.bottom() + (i+1)*self.lineHeight,
                         "%s" % entry.toString())
    painter.restore()

#==============================================================================#
#                                     MAIN                                     #
#==============================================================================#

if __name__ == "__main__":
  app = QApplication(sys.argv)
  myapp = ez_Gui()
  sys.exit(app.exec_())
