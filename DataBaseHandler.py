
import sqlite3 as sqlite
from Common_Elements import CommunicationPortsPair, VoiceChatPeer, InputValidator, ContactInfo
import os.path
import base64
import hashlib

# ---- FOR FULL DIRECTORY PATH IF NEEDED ------- #
# package_dir = os.path.abspath(os.path.dirname(__file__))
# self.database_path = os.path.join(package_dir, DATABASE_NAME)

ADDRESS_IP_INDEX = 0
ADDRESS_PORT_INDEX = 1
P2P_PORTS_PACKAGE_SIZE = 20
SMALLEST_P2P_PORT = 9000
DEFAULT_P2P_PORTS = [x for x in range(SMALLEST_P2P_PORT, SMALLEST_P2P_PORT + P2P_PORTS_PACKAGE_SIZE)]  # example ports: 9000 -> 9019 (20 ports)
ACTUAL_CALLING_USER_INDEX = -1
PEER_PORT_PAIRS_NUMBER = 3

USER_INFO_USERNAME_INDEX = 0
USER_INFO_PASSWORD_INDEX = 1
USER_INFO_CONTACTS_INDEX = 2
USER_INFO_PENDING_CONTACTS_INDEX = 3
USER_INFO_PICTURE_PATH_INDEX = 4
CONTACTS_STRING_SEPARATOR = ' '

INCORRECT_LOGIN_INFO_MESSAGE = "Incorrect username or password. Please try again."
USER_ALREADY_EXISTS_MESSAGE = "The username you entered already exists. Please choose a different username."
INVALID_USER_INFO_MESSAGE = "Invalid user information. Please enter valid username and password"
USER_ALREADY_CONNECTED_MESSAGE = "User with the given name is already connected. Unable to connect."

# DATABASE CONSTANTS
DATABASE_NAME = "ServerDB.db"
USERS_TABLE_NAME = "Users"
USERNAME_TABLE_RAW = "Username"
PASSWORD_TABLE_RAW = "Password"
CONTACTS_TABLE_RAW = "Contacts"
PENDING_CONTACTS_TABLE_RAW = "PendingContacts"
PICTURE_PATH_TABLE_RAW = "PicturePath"
CHECK_TABLE_EXISTS_QUERY = "SELECT name FROM sqlite_master WHERE type='table' AND name='{0}';".format(USERS_TABLE_NAME)
CREATE_USERS_TABLE_QUERY = "CREATE TABLE {0} ({1} text, {2} password, {3} text, {4} text, {5})".format(USERS_TABLE_NAME, USERNAME_TABLE_RAW, PASSWORD_TABLE_RAW, CONTACTS_TABLE_RAW, PENDING_CONTACTS_TABLE_RAW, PICTURE_PATH_TABLE_RAW)
VERIFY_USER_INFO_QUERY = "SELECT * FROM Users WHERE Username=? AND Password=?"
FIND_USER_QUERY = "SELECT * FROM Users WHERE Username=?"
ADD_USER_QUERY = "INSERT INTO Users VALUES (?, ?, ?, ?, ?)"
UPDATE_PENDING_CONTACTS_QUERY = "UPDATE Users SET PendingContacts=? WHERE Username=?"
UPDATE_CONTACTS_QUERY = "UPDATE Users SET Contacts=? WHERE Username=?"

SERVER_IMAGES_FOLDER = "ServerImages"
DEFAULT_USER_PICTURE_PATH = os.path.join(SERVER_IMAGES_FOLDER, "DefaultProfile.png")
USER_PICTURE_PATH = os.path.join(SERVER_IMAGES_FOLDER, "{0}Profile.png")  # example path: "aaaProfile.png"


class UserNotConnectedException(Exception):
    pass


class UserAlreadyExistsException(Exception):
    def get_message(self):
        return USER_ALREADY_EXISTS_MESSAGE


class IncorrectLoginInformationException(Exception):
    def get_message(self):
        return INCORRECT_LOGIN_INFO_MESSAGE


class InvalidUserInformationException(Exception):
    def get_message(self):
        return INVALID_USER_INFO_MESSAGE


class UserAlreadyConnectedException(Exception):
    def get_message(self):
        return USER_ALREADY_CONNECTED_MESSAGE


class UserAlreadyBeingCalledException(Exception):
    pass


class UserIsNotBeingCalledException(Exception):
    pass


class UserDoesNotExistException(Exception):
    pass


class UserIsNotActualCallingUser(Exception):
    pass


class BeingCalledInformation(object):
    """
    Stores all the information that has to do with being called.
    A user that is being called will have an instance of this class.
    """
    def __init__(self, call_participants_names, call_name, host_name, not_in_call_members):
        """
        constructs a new object.
        :param call_participants_names: [str], a list of usernames of the users who are already in the
        voice chat that the parent user is being called to.
        :param call_name: str, the name of the call group that the parent user is being call to.
        :param host_name: str, the name of the host of the call.
        :param not_in_call_members: [str], the names of all the group members of the voice chat that the parent user is
        being called to who are not in the voice chat itself but only in the group.
        """
        # [username], the last username in the list is the user who actually started calling the parent user.
        self.call_participants_names = call_participants_names
        self.call_name = call_name
        self.host_name = host_name
        self.not_in_call_members = not_in_call_members


class User(object):
    """
    This class represents a connected user and contains all the relevant information about the user.
    """
    def __init__(self, username, ip, port, client_socket):
        """
        Constructs a new User object.
        being_called_information - information about the user that currently call this user.
        open_p2p_ports - the open ports that the user can use for p2p connections.
        :param username: str, the user's username
        :param ip: str, the user's ip address
        :param port: int, the user's connection port
        :param client_socket: socket, the user's socket
        """
        self.username = username
        self.ip = ip
        self.port = port
        self.client_socket = client_socket
        self.being_called_information = None
        self.open_p2p_ports = DEFAULT_P2P_PORTS  # [:]  # copying the open ports list
        # If you don't want to use the same computer for a few clients, add [:] to the above command for
        # it to work as intended.
        self.biggest_p2p_port = self.open_p2p_ports[-1]

    def start_being_called(self, call_participants_names, call_name, host_name, not_in_call_members):
        """
        Set the user as being called right now.
        parameters are the parameters of BeingCalledInformation object.
        """
        self.being_called_information = BeingCalledInformation(call_participants_names, call_name, host_name, not_in_call_members)

    def stop_being_called(self):
        """
        Set the user as not being called right now.
        """
        self.being_called_information = None

    def is_being_called(self):
        """
        Shows if the user is currently being called
        :return: bool, True if being called right now, else False.
        """
        return self.being_called_information is not None

    def get_open_p2p_port(self):
        """
        gets a port that the user can use for p2p voice chat connections and removes this port from the open
        ports list.
        :return: int, a port that the user can use for p2p connections.
        """
        open_port = self.open_p2p_ports.pop(0)
        if len(self.open_p2p_ports) == 0:
            next_p2p_port = self.biggest_p2p_port + 1
            self.open_p2p_ports.extend([i for i in range(next_p2p_port, next_p2p_port + P2P_PORTS_PACKAGE_SIZE)])
            self.biggest_p2p_port = self.open_p2p_ports[-1]
            print "DEBUG - extended ports list, new biggest port: " + str(self.biggest_p2p_port)
        return open_port

    def add_new_open_p2p_ports(self, new_open_ports):
        """
        Adds a new port that can be used for p2p connections (after it has been opened again).
        :param new_open_ports: [int], a list of ports that the user can use for p2p connections.
        """
        self.open_p2p_ports.extend(new_open_ports)
        print "DEBUG - opened ports " + str(new_open_ports) + " of user " + self.username + " new list: " + str(self.open_p2p_ports)

    def get_actual_calling_username(self):
        """
        Returns the name of the actual calling user, which is the user who actually started calling this user.
        :return:
        """
        if self.is_being_called():
            return self.being_called_information.call_participants_names[ACTUAL_CALLING_USER_INDEX]
        else:
            raise UserIsNotBeingCalledException()


class DataBaseHandler(object):
    """
    This class is the available database of the server. It is the only class with
    access to the real database. It also contains useful information regarding
    connected users (so there won't be a need to access the database often).
    """
    def __init__(self):
        """
        pending_users - users that are connected to the server by socket but are yet to login.
        connected_users - users that are fully connected to the server and can use it's services.
        """
        self.pending_users = {}  # {socket:address}
        self.connected_users = {}  # {socket:User}
        self.conn = sqlite.connect(DATABASE_NAME)
        self.cursor = self.conn.cursor()
        self.create_users_table_if_it_does_not_exist()

    def create_users_table_if_it_does_not_exist(self):
        """
        Checks if the database contains a Users table and creates
        one if it doesn't.
        """
        self.cursor.execute(CHECK_TABLE_EXISTS_QUERY)
        if self.cursor.fetchone() is None:
            self.cursor.execute(CREATE_USERS_TABLE_QUERY)
            self.conn.commit()

    def disconnect_user(self, client_socket):
        """
        Remove a user from the available database lists (wherever he is).
        :param client_socket: socket, the user's socket.
        """
        if client_socket in self.connected_users:
            del(self.connected_users[client_socket])
        elif client_socket in self.pending_users:
            del(self.pending_users[client_socket])
        client_socket.close()
        print "DEBUG - user disconnected"

    def verify_user_login_info(self, username, password):
        """
        Verifies the user's login information with the database.
        Will raise an exception if the information is incorrect.
        :param username: str, the username that the user entered
        :param password: str, the password that the user entered
        """
        self.validate_user_input(username, password)
        hashed_password = hashlib.sha256(password).hexdigest()
        login_info = (username, hashed_password)
        self.cursor.execute(VERIFY_USER_INFO_QUERY, login_info)
        user_info = self.cursor.fetchone()
        if user_info is None:
            raise IncorrectLoginInformationException()

    def connect_user_to_server(self, client_socket, login_message):
        """
        Attempts to connect a pending user to the server.
        :param client_socket: socket, the user's socket
        :param login_message: LoginMessage, the login message of the client.
        :return:
        """
        self.verify_user_login_info(login_message.username, login_message.password)
        if self.is_user_connected(login_message.username):
            raise UserAlreadyConnectedException()
        net_address = self.pending_users[client_socket]
        user = User(username=login_message.username, ip=net_address[ADDRESS_IP_INDEX], port=net_address[ADDRESS_PORT_INDEX], client_socket=client_socket)
        self.connected_users[client_socket] = user
        del(self.pending_users[client_socket])

    def update_called_user_being_called_information(self, sending_client_socket, update_info_message):
        """
        Updates a user BeingCalledInformation object. This function should be called if there was a change
        in the voice chat of the user of who calls another user, for example a new participant was added to the
        voice chat while calling to another user, and thus he became another calling user for said called user.
        :param sending_client_socket: socket, the socket of the actual calling user.
        :param update_info_message: UpdateUserBeingCalledInformationMessage, a message that contains information about
        the new voice chat that the user is being called to.
        """
        calling_user = self.connected_users[sending_client_socket]
        called_user = self.find_connected_user_through_username(update_info_message.called_username)
        if calling_user.username != called_user.get_actual_calling_username():
            raise UserIsNotActualCallingUser()
        participant_names = update_info_message.new_other_participants_names + [calling_user.username]
        called_user.start_being_called(participant_names, update_info_message.new_call_group_name, update_info_message.new_host_name, update_info_message.new_not_in_call_members)

    def add_new_user_to_database(self, username, password):
        """
        Add a new user to the database if a user with the given username doesn't exist.
        :param username: str, the new user's username.
        :param password: str, the new user's password.
        """
        self.validate_user_input(username, password)
        hashed_password = hashlib.sha256(password).hexdigest()
        if self.does_user_exist(username):
            raise UserAlreadyExistsException()
        register_info = (username, hashed_password, "", "", USER_PICTURE_PATH.format(username))
        self.cursor.execute(ADD_USER_QUERY, register_info)
        self.conn.commit()
        self.set_user_picture_as_default(username)
        print "DEBUG - user added successfully"

    def set_user_picture_as_default(self, username):
        """
        Sets a user profile picture as the default profile picture.
        :param username: str, the name of the user.
        """
        picture_path = USER_PICTURE_PATH.format(username)
        user_picture_file = open(picture_path, "wb")
        default_picture_file = open(DEFAULT_USER_PICTURE_PATH, "rb")
        user_picture_file.write(default_picture_file.read())
        default_picture_file.close()
        user_picture_file.close()

    def get_user_encoded_picture_bytes(self, username):
        """
        Gets the bytes of the profile picture of a user encoded in base64.
        :param username: str, the name of the user.
        :return: str, the bytes of the profile picture of a user encoded in base64.
        """
        user_info = self.get_user_info_from_db(username)
        picture_path = user_info[USER_INFO_PICTURE_PATH_INDEX]
        picture_file = open(picture_path, "rb")
        picture_bytes = picture_file.read()
        picture_file.close()
        encoded_picture_bytes = base64.b64encode(picture_bytes)
        return encoded_picture_bytes

    def validate_user_input(self, username, password):
        """
        Validates a user's input (username and password).
        Raises an exception if the info is not valid.
        :param username: str, the username which needs to be checked.
        :param password: str, the password which needs to be checked. should be hashed.
        """
        if not InputValidator.validate_username(username):
            raise InvalidUserInformationException()
        elif not InputValidator.validate_password(password):
            raise InvalidUserInformationException()

    def get_user_info_from_db(self, username):
        """
        Get all the information about a specific user in the database.
        :param username: str, the username that will have his information returned.
        :return: list or None - either a list of all the user information from the database or
        None if the user is not in the database.
        """
        username = (username,)
        self.cursor.execute(FIND_USER_QUERY, username)
        user_info = self.cursor.fetchone()
        return user_info

    def update_user_profile_picture(self, username, encoded_picture_bytes):
        """
        Changes a user profile picture (by changing it in the server's file system).
        :param username: the name of the user.
        :param encoded_picture_bytes: str, the bytes of the new picture encoded in base64.
        """
        picture_path = USER_PICTURE_PATH.format(username)
        user_picture_file = open(picture_path, "wb")
        user_picture_file.write(base64.b64decode(encoded_picture_bytes))
        user_picture_file.close()

    def add_user_pending_contact(self, username, new_pending_contact_name):
        """
        Adds a pending contact to a given user.
        :param username: str, the name of the user.
        :param new_pending_contact_name: str, the name of the new pending contact.
        :return: Bool, True if the pending contact was successfully added, else false.
        """
        user_info = self.get_user_info_from_db(username)
        user_pending_contacts = user_info[USER_INFO_PENDING_CONTACTS_INDEX]
        user_contacts = user_info[USER_INFO_CONTACTS_INDEX]
        if new_pending_contact_name not in user_pending_contacts and new_pending_contact_name not in user_contacts:
            new_user_pending_contacts = user_pending_contacts + new_pending_contact_name + ' '
            update_info = (new_user_pending_contacts, username)
            self.cursor.execute(UPDATE_PENDING_CONTACTS_QUERY, update_info)
            self.conn.commit()
            return True  # added successfully
        return False  # not added

    def add_user_contact(self, username, new_contact_name):
        """
        Adds a contact to a given user.
        :param username: str, the name of the user.
        :param new_contact_name: str, the name of the new contact.
        :return: Bool, True if the contact was successfully added, else false.
        """
        user_contacts = self.get_user_info_from_db(username)[USER_INFO_CONTACTS_INDEX]
        if new_contact_name not in user_contacts:
            new_user_contacts = user_contacts + new_contact_name + ' '
            update_info = (new_user_contacts, username)
            self.cursor.execute(UPDATE_CONTACTS_QUERY, update_info)
            self.conn.commit()
            return True  # added successfully
        return False  # not added

    def remove_user_pending_contact(self, username, pending_contact_name):
        """
        Removes a pending contact from a given user's pending contacts list.
        :param username: str, the name of the user.
        :param pending_contact_name: str, the name of the pending contact.
        :return: Bool, True if the pending contact was successfully removed, else False.
        """
        user_pending_contacts = self.get_user_info_from_db(username)[USER_INFO_PENDING_CONTACTS_INDEX]
        if pending_contact_name in user_pending_contacts:
            new_user_pending_contacts = user_pending_contacts.replace(pending_contact_name, '')
            new_user_pending_contacts = new_user_pending_contacts.replace("  ", ' ')  # delete middle double space
            if new_user_pending_contacts != "" and new_user_pending_contacts[0] == " ":
                new_user_pending_contacts = new_user_pending_contacts[1:]
            update_info = (new_user_pending_contacts, username)
            self.cursor.execute(UPDATE_PENDING_CONTACTS_QUERY, update_info)
            self.conn.commit()
            return True  # removed successfully
        return False  # not removed

    def remove_user_contact(self, username, contact_name):
        """
        Removes a contact from a given user's contacts list.
        :param username: str, the name of the user.
        :param contact_name: str, the name of the contact.
        :return: Bool, True if the contact was successfully removed, else False.
        """
        user_contacts = self.get_user_info_from_db(username)[USER_INFO_CONTACTS_INDEX]
        if contact_name in user_contacts:
            new_user_contacts = user_contacts.replace(contact_name, '')
            new_user_contacts = new_user_contacts.replace("  ", ' ')  # delete middle double space
            if new_user_contacts[0] == " ":
                new_user_contacts = new_user_contacts[1:]
            update_info = (new_user_contacts, username)
            self.cursor.execute(UPDATE_CONTACTS_QUERY, update_info)
            self.conn.commit()
            return True  # removed successfully
        return False  # not removed

    def does_user_exist(self, username):
        """
        Tells whether a user with the given username exists in the database.
        :param username: str, the name of the user.
        :return: Bool, True if the user exists in the database, else False.
        """
        user_info = self.get_user_info_from_db(username)
        return user_info is not None

    def find_connected_user_through_username(self, username):
        """
        Finds a user with the given username.
        :param username: str, a username that needs to be found
        :return: User, the user with said username.
        """
        for user in self.connected_users.values():
            if user.username == username:
                return user
        raise UserNotConnectedException()

    def is_user_connected(self, username):
        """
        Checks whether a user is connected right now or not.
        :param username: str, the user which needs to be checked.
        :return: Bool, True if the user is connected right now, else False.
        """
        for user in self.connected_users.values():
            if user.username == username:
                return True
        return False

    def create_calling_users_list(self, called_user):
        """
        Creates a list of the User objects of the users that are currently calling a given user.
        :param called_user: User, a user that is being called right now.
        :return: [User], a list of the calling users
        """
        calling_users = [self.find_connected_user_through_username(username) for username in called_user.being_called_information.call_participants_names]
        return calling_users

    def create_not_in_call_members_users_list(self, called_user):
        """
        Creates a list of the User objects of the users who are in the call group that calls the user but not in the
        voice chat itself.
        :param called_user: User, a user that is being called right now.
        :return: [User], a list of the not in call members users.
        """
        users_list = [self.find_connected_user_through_username(username) for username in called_user.being_called_information.not_in_call_members]
        return users_list

    def create_users_list_through_names(self, names_list):
        """
        Creates a list of the User objects of the users with the given names.
        :param names_list: [str], a list of user names.
        :return: [User], a list of users with the given names.
        """
        users_list = [self.find_connected_user_through_username(name) for name in names_list]
        return users_list

    def create_voice_chat_peers(self, called_user, calling_users):
        """
        Auxiliary function that creates a list of peers for both the calling users and the called user.
        Peers are objects that contain information that is necessary for starting a p2p connection.
        :param called_user: User, the user who is being called.
        :param calling_users: [User], the users who are calling said user.
        :return: [0]: called_user_peers_list: [Peer], a list of peers that should be sent to the called user.
        [1]: calling_users_peers_list: {User:Peer}, a dictionary that contains the calling user
        as the key and his peer (that contains the called user) as the value.
        """
        called_user_peers_list = []
        calling_users_peers_dict = {}
        called_user_encoded_picture_bytes = self.get_user_encoded_picture_bytes(called_user.username)
        for calling_user in calling_users:
            called_user_pairs, calling_user_pairs = self.create_port_pairs(called_user, calling_user)
            called_user_peer_object = VoiceChatPeer(called_user.username, called_user.ip, called_user_pairs[0], called_user_pairs[1], called_user_pairs[2], called_user_encoded_picture_bytes)
            calling_users_peers_dict[calling_user] = called_user_peer_object
            calling_user_encoded_picture_bytes = self.get_user_encoded_picture_bytes(calling_user.username)
            calling_user_peer_object = VoiceChatPeer(calling_user.username, calling_user.ip, calling_user_pairs[0], calling_user_pairs[1], calling_user_pairs[2], calling_user_encoded_picture_bytes)
            called_user_peers_list.append(calling_user_peer_object)
        return called_user_peers_list, calling_users_peers_dict

    def create_port_pairs(self, called_user, calling_user):
        """
        Creates lists of ports pairs between the called user and the given calling user.
        Ports pair are a pair of ports to listen and receive a specific kind of data between two participants
        in a voice chat. the port that one user sends data to is the port that the other user receives the data from.
        a list of several Port Pairs is created between the called user and each calling user, one pair for each data type.
        :param called_user: User, the called user.
        :param calling_user: User, the calling user who is currently getting his port pairs.
        :return:
        """
        called_user_port_pairs_list = []
        calling_user_port_pairs_list = []
        for i in range(PEER_PORT_PAIRS_NUMBER):
            called_user_listen_port = called_user.get_open_p2p_port()
            calling_user_listen_port = calling_user.get_open_p2p_port()
            called_user_port_pair = CommunicationPortsPair(calling_user_listen_port, called_user_listen_port)
            calling_user_port_pair = CommunicationPortsPair(called_user_listen_port, calling_user_listen_port)
            called_user_port_pairs_list.append(called_user_port_pair)
            calling_user_port_pairs_list.append(calling_user_port_pair)
        return called_user_port_pairs_list, calling_user_port_pairs_list

    def create_contacts_info_list(self, username):
        """
        Creates a list of ContactInfo objects for all the contacts of user. These contain information about
        the contacts.
        :param username: str, the name of the user.
        :return: [ContactInfo], a list of objects that contain information about the user's contacts.
        """
        user_info = self.get_user_info_from_db(username)
        user_contacts_list = user_info[USER_INFO_CONTACTS_INDEX].split(CONTACTS_STRING_SEPARATOR)[0:-1]  # deleting last name which is an empty string
        user_contacts_info_list = []
        for contact_name in user_contacts_list:
            contact_connected = self.is_user_connected(contact_name)
            contact_encoded_picture_bytes = self.get_user_encoded_picture_bytes(contact_name)
            contact_info = ContactInfo(contact_name, contact_connected, contact_encoded_picture_bytes)
            user_contacts_info_list.append(contact_info)
        return user_contacts_info_list

    def create_pending_contacts_list(self, username):
        """
        Creates a list of the names of the user's pending contacts.
        :param username: str, the name of the user.
        :return: [str], a list of the names of the user's pending contacts.
        """
        user_info = self.get_user_info_from_db(username)
        user_pending_contacts_list = user_info[USER_INFO_PENDING_CONTACTS_INDEX].split(CONTACTS_STRING_SEPARATOR)[0:-1]  # deleting last name which is an empty string
        return user_pending_contacts_list

    def create_user_objects_list_of_connected_contacts(self, username):
        """
        Create a User objects list of the user's connected contacts.
        :param username: str, the name of the user.
        :return: [User], a list of all the user's connected contacts.
        """
        user_info = self.get_user_info_from_db(username)
        contact_names_list = user_info[USER_INFO_CONTACTS_INDEX].split(CONTACTS_STRING_SEPARATOR)[0:-1]  # deleting last name which is an empty string
        contact_objects_list = []
        for contact_name in contact_names_list:
            try:
                contact_user_object = self.find_connected_user_through_username(contact_name)
                contact_objects_list.append(contact_user_object)
            except UserNotConnectedException:
                pass
        return contact_objects_list
