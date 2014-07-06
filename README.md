eZchat
=======
Manifesto
--------------------------------------------------------------------------------
eZchat is a network-driven decentralized chat program.
It has the flexibility of a P2P network without the drawbacks,
especially it does not require chat partners to be online at the same time.

A `network` is a group of users which are willing to transmit the messages of
the network, similar to torrent users.
Each user is client and server.
Since all messages are encrypted, each user can still only read the messages
that are dedicated to them.
For now, we still need a `tracker` where the IPs of the user of a network are
stored.
An interesting alternative might be the Kademlia algorithm, which would promote
`eZchat` to a truly independent decentralized protocol.

Messages can be addressed to single `persons` or groups.
A `message` can be pure text or have a file associated.
Messages stay in the network and allow to view the chat history.
The only unencrypted information visible is the user name of the recipient and
the time stamp of the message.
Optionally, one can chose to drop messages from the network to the local archive
after some time.

`eZchat` also gives anonymity as it is by construction impossible to tell
whether the `sender` is also the `author` of the message.

Developer Guidelines
--------------------------------------------------------------------------------
- 2 spaces for indentation. No tabs. No whitespace at the end of a line
- Surround operators like `+`, `-`, `=`, .. with a single space
- Never write more than 80 characters in a line. Try to avoid `&` by abusing
  that python will look in the next line after `,`
- Use `git add -p` to add content. It will warn you of trailing spaces and you
  reflect about your work
- Write a test for every function you write
    - Our tools are `nose` and `mock`. Look at written tests to see how it
    works.
    - Just run `nosetests` in the main directory and it will find and check
    all tests and assertions you add in `tests` automagically. Run `nosetests
    -p` to see stdout
- Add at least a line of docstring with `"""some meaningful words"""` to each
  function that is more complex than `__str__` or `__init__`
- Every module has its own file. Use a lot of modules to improve parallel
  programming and overall structure
- Namespace: `ezc_modulename`, `tests/test_modulename`
