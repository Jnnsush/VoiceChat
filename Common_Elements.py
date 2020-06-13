# -*- coding: utf-8 -*-

import pickle
import string
from Crypto.Cipher import AES
from hashlib import md5

#  ----------------CONSTANTS-----------------#
LEN_OF_LENGTH = 10
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 16
USERNAME_ALLOWED_CHARACTERS = list(string.ascii_letters) + list(string.digits) + ["_"]
PASSWORD_MIN_LENGTH = 3
PASSWORD_MAX_LENGTH = 16
PASSWORD_ALLOWED_CHARACTERS = list(string.ascii_letters) + list(string.digits) + ["_"]


# ---------------ENCRYPTION---------------#
ENC_KEY = md5("SOMEBODY ORDERED A BOMB?!?!").hexdigest()
PADDING_CHAR = "*"
START_ENCRYPTION_SIGN = "&Encrypt&"
BYTES_TO_ENCRYPT_NUM = 2048


class AESCipher(object):
    """
    This class is used as a cipher of the AES encryption.
    It is responsible for encrypting and decrypting messages.
    """
    def __init__(self):
        """
        Constructs the cipher.
        starts an encryption suite that allows us to encrypt and decrypt messages using a constant key.
        """
        self.encryption_suite = AES.new(ENC_KEY, 1)

    def encrypt_message(self, original_message):
        """
        Encrypts a constant amount of the last bytes of a message according to the protocol.
        :param original_message: str, the message that needs to be encrypted
        :return: str, the encrypted message.
        """
        last_bytes = original_message[-BYTES_TO_ENCRYPT_NUM:]
        encrypted_last_bytes = self.encrypt_string(last_bytes)
        encrypted_message = original_message[:-BYTES_TO_ENCRYPT_NUM] + START_ENCRYPTION_SIGN + encrypted_last_bytes
        return encrypted_message

    def encrypt_string(self, original_str):
        """
        Fully encrypts a string.
        :param original_str: str, the string that needs to be encrypted.
        :return: str, the encrypted string.
        """
        original_str = original_str + PADDING_CHAR * (16 - len(original_str) % 16)
        encrypted_str = self.encryption_suite.encrypt(original_str)
        return encrypted_str

    def decrypt_message(self, encrypted_message):
        """
        Decrypts a constant amount of the last bytes of a message according to the protocol.
        :param encrypted_message: str, the message that needs to be decrypted.
        :return: str, the original message.
        """
        encrypted_last_bytes = encrypted_message[encrypted_message.find(START_ENCRYPTION_SIGN) + len(START_ENCRYPTION_SIGN):]
        decrypted_last_bytes = self.decrypt_string(encrypted_last_bytes)
        original_message = encrypted_message[:encrypted_message.find(START_ENCRYPTION_SIGN)] + decrypted_last_bytes
        return original_message

    def decrypt_string(self, encrypted_str):
        """
        Fully decrypts a string.
        :param encrypted_str: str, the string that needs to be decrypted.
        :return: str, the original string.
        """
        decrypted_str = self.encryption_suite.decrypt(encrypted_str)
        decrypted_str = decrypted_str.rstrip(PADDING_CHAR)
        return decrypted_str


class BasicCommunicator(object):
    """
    This class is responsible for handling basic communication between two connected entities
    using a more reliable protocol than a normal send/receive socket functions.
    The protocol makes sure that the whole message gets receives by the receiving side
    whenever a message is sent by first sending the message length and then the message itself.
    It also allows non-string objects to be sent.
    """
    def __init__(self):
        """
        Constructs a BasicCommunicator and starts its AES Cipher.
        """
        self.cipher = AESCipher()

    def receive_message_by_length(self, client_socket, message_length):
        """
        :param client_socket: socket - the socket which connects two entities.
        :param message_length: int - the length of the message that should be received.
        :returns: str - the full message with the given length.

        This function fully receives a message with an already known length.
        """
        message = ""
        while len(message) != message_length:
            message += client_socket.recv(message_length - len(message))
        return message

    def receive_full_message(self, client_socket):
        """
        :param client_socket: socket - the socket which connects two entities.
        :returns: any object, a full message which has an unknown length.

        This function receives a full message without needing to know anything about it in advance
        using the protocol described in the class documentation.
        """
        message_length = int(self.receive_message_by_length(client_socket, LEN_OF_LENGTH))
        message = self.receive_message_by_length(client_socket, message_length)
        message = self.cipher.decrypt_message(message)
        message = pickle.loads(message)
        return message

    def send_full_message(self, client_socket, message):
        """
        :param client_socket: socket - the socket which connects two entities.
        :param message: any object - the object that needs to be sent

        This function sends a full message to the other side using the protocol
        described in the class documentation.
        """
        message = pickle.dumps(message)
        encrypted_message = self.cipher.encrypt_message(message)
        client_socket.send(str(len(encrypted_message)).zfill(LEN_OF_LENGTH))
        client_socket.send(encrypted_message)


class CommunicationPortsPair(object):
    """
    This call contains a pair of ports that allow p2p communication between two users.
    Each pair of ports represents two ports that connect between two users and allows them to send
    and receive a specific type of data. The send_to_port of the first user is the receive_port of
    the second user and vice versa, and thus the users can transfer some kind of data through known
    addresses.
    """
    def __init__(self, send_to_port, receive_port):
        self.send_to_port = send_to_port
        self.receive_port = receive_port


class VoiceChatPeer(object):
    """
    Represents a peer in a p2p connection. Contains all the necessary information for
    starting a p2p connection.
    """
    def __init__(self, username, ip, voice_ports_pair, screen_ports_pair, camera_ports_pair, peer_encoded_picture_bytes):
        """
        *username - the username of the peer
        *ip - the ip of the peer
        *voice_ports_pair - PortsPair, a pair of ports to send and receive voice data.
        *screen_ports_pair - PortsPair, a pair of ports to send and receive screen data.
        *camera_ports_pair - PortsPair, a pair of ports to send and receive camera data.
        *peer_encoded_picture_bytes - str, the bytes of the peer's profile picture encoded in base64.
        """
        self.username = username
        self.ip = ip
        self.voice_ports_pair = voice_ports_pair
        self.screen_ports_pair = screen_ports_pair
        self.camera_ports_pair = camera_ports_pair
        self.peer_encoded_picture_bytes = peer_encoded_picture_bytes


class ContactInfo(object):
    """
    A data structure that contains information on a contact.
    """
    def __init__(self, contact_name, is_connected, encoded_picture_bytes):
        self.contact_name = contact_name
        self.is_connected = is_connected
        self.encoded_picture_bytes = encoded_picture_bytes


class InputValidator(object):
    """
    A common class for both the server and the client that contains functions that
    validate user input.
    """
    @staticmethod
    def validate_username(username):
        """
        Validates a username according to a few set rules:
        min/max length, allowed characters.
        :param username: str, the username which needs to be validated.
        :return: Bool, True if the username is valid, else False.
        """
        if len(username) < USERNAME_MIN_LENGTH or len(username) > USERNAME_MAX_LENGTH:
            return False
        for character in username:
            if character not in USERNAME_ALLOWED_CHARACTERS:
                return False
        return True

    @staticmethod
    def validate_password(password):
        """
        Validates a password according to a few set rules:
        min/max length, allowed characters.
        :param password: str, the password which needs to be validated.
        :return: Bool, True if the password is valid, else False.
        """
        if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
            return False
        for character in password:
            if character not in PASSWORD_ALLOWED_CHARACTERS:
                return False
        return True


#  ---------------------Message Objects----------------------#
class Message(object):
    """
    Represents an abstract empty message.
    Every message object will inherit this abstract characterization.
    """
    pass


class NewOpenPortsMessage(Message):
    """
    Informs the server about newly open ports of the client.
    """
    def __init__(self, new_open_ports):
        """
        :param new_open_ports: [int], list of new open ports.
        """
        self.new_open_ports = new_open_ports  # [PORT]


class DisconnectMessage(Message):
    """
    Informs the server about a client disconnect from it.
    """
    pass


class RequestUserInformationMessage(Message):
    """
    Requests the server for information about a specific user.
    """
    def __init__(self, username):
        """
        :param username: str, the user that the client wants information about.
        """
        self.username = username


class UserInformationMessage(Message):
    """
    Provides the client with information about a specific user who which has been requested beforehand.
    """
    def __init__(self, username, does_exist, is_online, encoded_picture_bytes):
        """
        :param username: str, the name of the user.
        :param does_exist: Bool, does the user exist in the database.
        :param is_online: Bool, is the user currently connected. None if the user doesnt exist.
        :param encoded_picture_bytes: str, the bytes of the user's profile picture encoded
        in base64. None if the user doesn't exist.
        """
        self.username = username
        self.does_exist = does_exist
        self.is_online = is_online
        self.encoded_picture_bytes = encoded_picture_bytes


class PopupMessage(Message):
    """
    A message that needs to pop up on the user's screen.
    """
    def __init__(self, message):
        """
        :param message: str, the message that will pop up.
        """
        self.message = message


class ChangePictureMessage(Message):
    """
    A general message that is sent by the client in order to change his profile picture.
    """
    def __init__(self, encoded_picture_bytes, in_call_participants):
        """
        :param encoded_picture_bytes: str, the bytes of the new picture encoded in base64.
        :param in_call_participants: [str], names of the participants who are in call with the client.
        """
        self.encoded_picture_bytes = encoded_picture_bytes
        self.in_call_participants = in_call_participants


# Contacts messages

class ContactMessage(Message):
    """
    Represents an abstract Contact message.
    All messages that have to do with contacts and contact adding process will inherit this characterization.
    """
    pass


class RequestAddContactMessage(ContactMessage):
    """
    Requests the server to ask a user to be contacts.
    """
    def __init__(self, request_username):
        """
        :param request_username: str, name of the user who will be asked to be contact.
        """
        self.request_username = request_username


class AskedToBeContactMessage(ContactMessage):
    """
    Informs a user that he was asked to be a contact.
    """
    def __init__(self, asked_by_username):
        """
        :param asked_by_username: str, the name of the user who asked to be contacts.
        """
        self.asked_by_username = asked_by_username


class AcceptContactMessage(ContactMessage):
    """
    Accepts a contact request.
    """
    def __init__(self, accept_requesting_username):
        """
        :param accept_requesting_username: str, the name of the user whose request was accepted.
        """
        self.requesting_username = accept_requesting_username


class RejectContactMessage(ContactMessage):
    """
    Rejects a contact request.
    """
    def __init__(self, reject_username):
        """
        :param reject_username: str, the name of the user whose request was rejected.
        """
        self.reject_username = reject_username


class AddContactsMessage(ContactMessage):
    """
    Tells a client to add a list of contacts.
    """
    def __init__(self, contact_info_list):
        """
        :param contact_info_list: [ContactInfo], a list of information objects about said contacts.
        """
        self.contacts_info_list = contact_info_list


class ContactWentOfflineMessage(ContactMessage):
    """
    Informs a user that his contact went offline.
    """
    def __init__(self, contact_name):
        """
        :param contact_name: str, name of the contact.
        """
        self.contact_name = contact_name


class ContactConnectedMessage(ContactMessage):
    """
    Informs a user that his contact went online.
    """
    def __init__(self, contact_name):
        """
        :param contact_name: str, name of contact.
        """
        self.contact_name = contact_name


class DeleteContactMessage(ContactMessage):
    """
    Tells a client to delete a contact.
    """
    def __init__(self, contact_name):
        """
        :param contact_name: str, name of the contact.
        """
        self.contact_name = contact_name


class ContactChangedPictureMessage(ContactMessage):
    """
    Informs a client that his contact changed his profile picture.
    """
    def __init__(self, contact_name, encoded_picture_bytes):
        """
        :param contact_name: str, name of the contact.
        :param encoded_picture_bytes: str, bytes of the new picture encoded in base64.
        """
        self.contact_name = contact_name
        self.encoded_picture_bytes = encoded_picture_bytes


# Call messages
class CallMessage(Message):
    """
    Represents an abstract Call message.
    All messages that are connected to the calling process will inherit this characterization.
    """
    pass


class RequestCallMessage(CallMessage):
    """
    Requests to start a call with a given username.
    If the requesting user is already in a call this will request to invite a user to this call.
    """
    def __init__(self, call_username, other_participants_names, call_group_name, host_name, not_in_call_members):
        """
        :param call_username: str, name of the user that will be called.
        :param other_participants_names: [str], names of the other participants who are aleady in call with the
        requesting user.
        :param call_group_name: str, name of the voice chat's group.
        :param host_name: str, name of the call host.
        :param not_in_call_members: [str], names of the group members who are not currently in the call.
        """
        self.call_username = call_username
        self.other_participants_names = other_participants_names  # [username (str)]
        self.call_group_name = call_group_name
        self.host_name = host_name
        self.not_in_call_members = not_in_call_members


class UpdateUserBeingCalledInformationMessage(CallMessage):
    """
    Informs the server about a change in the voice chat of a user who requested to call another user and
    requests the server to change the call information of said called user.
    """
    def __init__(self, called_username, new_other_participants_names, new_call_group_name, new_host_name, new_not_in_call_members):
        """
        :param called_username: str, name of the called user.
        :param new_other_participants_names: [str], names of the other participants who are aleady in call with the
        requesting user.
        :param new_call_group_name: str, name of the voice chat's group.
        :param new_host_name: str, name of the call host.
        :param new_not_in_call_members: [str], names of the group members who are not currently in the call.
        """
        self.called_username = called_username
        self.new_other_participants_names = new_other_participants_names
        self.new_call_group_name = new_call_group_name
        self.new_host_name = new_host_name
        self.new_not_in_call_members = new_not_in_call_members


class RequestJoinCallMessage(CallMessage):
    """
    Requests to join a call that the client is already part of (in group but not in call).
    """
    def __init__(self, call_name, host_name):
        """
        :param call_name: str, the name of the call's group.
        :param host_name: str, name of the call host.
        """
        self.call_name = call_name
        self.host_name = host_name


class GroupMemberRequestedJoinMessage(CallMessage):
    """
    Informs a client about a request to join the call by a group member.
    """
    def __init__(self, call_name, requesting_username):
        """
        :param call_name: str, name of the call's group.
        :param requesting_username: str, name of the requesting group member.
        """
        self.call_name = call_name
        self.requesting_username = requesting_username


class AllowCallJoinMessage(CallMessage):
    """
    Allows a requesting group member to join the call.
    Sent to the server by the call host
    """
    def __init__(self, call_name, requesting_username, other_participants_names):
        """
        :param call_name: str, name of the call.
        :param requesting_username: str, name of the requesting user.
        :param other_participants_names: [str], names of the other participants who are in the voice chat.
        """
        self.call_name = call_name
        self.requesting_username = requesting_username
        self.other_participants_names = other_participants_names


class CalledByMessage(CallMessage):
    """
    Informs a user about being called.
    """
    def __init__(self, called_by_names, call_name):
        self.called_by_names = called_by_names  # [str]
        self.call_name = call_name


class InvitedToCallMessage(CallMessage):
    """
    Informs a user that he was invited to a call that he is already part of it's call group.
    """
    def __init__(self, call_name, in_call_participants):
        self.in_call_participants = in_call_participants
        self.call_name = call_name


class AcceptCallMessage(CallMessage):
    """
    Accepts a call.
    """
    pass


class RejectCallMessage(CallMessage):
    """
    Rejects a call.
    """
    pass


class StartNewCallMessage(CallMessage):
    """
    Starts an entirely new call between users.
    Sent by the server to clients who need to start a new call after
    completing the calling process.
    """
    def __init__(self, voice_chat_peers_list, active_call_group_name):
        self.voice_chat_peers_list = voice_chat_peers_list  # [VoiceChatPeer]
        self.active_call_group_name = active_call_group_name


class AddParticipantToCallMessage(CallMessage):
    """
    Adds a participant to an existing call.
    Sent by the server to clients who just need to add a new
    user to the call and not start a new call entirely.
    """
    def __init__(self, voice_chat_peer, active_call_group_name):
        self.voice_chat_peer = voice_chat_peer
        self.active_call_group_name = active_call_group_name


class CallRejectedMessage(CallMessage):
    """
    Informs a user about a call reject.
    """
    def __init__(self):
        pass


class StopCallingMessage(CallMessage):
    """
    Stops calling a user.
    """
    def __init__(self, stop_calling_username):
        self.stop_calling_username = stop_calling_username


class StopBeingCalledMessage(CallMessage):
    """
    Informs a user about the fact that the user who was calling him stopped calling.
    """
    pass


class CallingFailedMessage(CallMessage):
    """
    Informs a user that his attempt to call failed.
    """
    def __init__(self, error_message):
        self.error_message = error_message


class ParticipantChangedPictureMessage(CallMessage):
    """
    Informs a user that a participant in his voice chat changed his profile pictrue.
    """
    def __init__(self, participant_username, encoded_picture_bytes):
        self.participant_username = participant_username
        self.encoded_picture_bytes = encoded_picture_bytes


# Group Messages
class CallGroupMessage(Message):
    """
    Represents an abstract Group message about a group with a given name.
    All messages that are connected to groups will inherit this characterization.
    """
    def __init__(self, call_name):
        self.call_name = call_name


class CreateNewCallGroupMessage(CallGroupMessage):
    """
    Creates a new group for clients.
    """
    def __init__(self, call_name, host_name):
        super(CreateNewCallGroupMessage, self).__init__(call_name)
        self.host_name = host_name


class AddCallGroupMembersMessage(CallGroupMessage):
    """
    Adds new members to an existing call group.
    """
    def __init__(self, call_name, members_names):
        super(AddCallGroupMembersMessage, self).__init__(call_name)
        self.members_names = members_names  # [names]


class CommandMembersToCloseGroup(CallGroupMessage):
    """
    Asks the server to tell all users in a group to delete said group after all its members left its voice chat.
    """
    def __init__(self, call_name, other_group_members_names):
        super(CommandMembersToCloseGroup, self).__init__(call_name)
        self.other_group_members_names = other_group_members_names  # [names]


class DeleteCallGroupMessage(CallGroupMessage):
    """
    Tells clients to close a certain group.
    """
    def __init__(self, call_name):
        super(DeleteCallGroupMessage, self).__init__(call_name)


class ChangeGroupHostMessage(CallGroupMessage):
    """
    Informs the client about a new host for a certain group.
    """
    def __init__(self, call_name, new_host_name):
        super(ChangeGroupHostMessage, self).__init__(call_name)
        self.new_host_name = new_host_name


class HostLeftVoiceChatMessage(CallGroupMessage):  # only the host should send this message
    """
    Asks the server to choose a new host for the group and tell all group members about it after the
    current host leaves the voice chat.
    """
    def __init__(self, call_name, other_participants_names, other_group_members_names, host_name):
        super(HostLeftVoiceChatMessage, self).__init__(call_name)
        self.other_participants_names = other_participants_names
        self.other_group_members_names = other_group_members_names
        self.host_name = host_name


class LeaveGroupMessage(CallGroupMessage):
    """
    Tells the server about a client wanting to leave a group in order to inform the other group members.
    """
    def __init__(self, call_name, other_group_members_names):
        super(LeaveGroupMessage, self).__init__(call_name)
        self.other_group_members_names = other_group_members_names


class RemoveGroupMemberMessage(CallGroupMessage):
    """
    Tells a group member to remove another member from the group after said member left the group.
    """
    def __init__(self, call_name, username):
        super(RemoveGroupMemberMessage, self).__init__(call_name)
        self.remove_username = username


# Chat Messages
class ChatMessage(object):
    """
    Represents a Chat message on a specific chat.
    every chat message is a part of one specific chat and are sent on a specific time.
    All messages that are part of the written chat protocol inherit this characterization.
    """
    def __init__(self, chat_name, send_time):
        """
        These are properties of all chat messages.
        :param chat_name: str, name of the chat.
        :param send_time: str, sending time of the chat message.
        """
        self.chat_name = chat_name
        self.send_time = send_time


class SendChatMessage(ChatMessage):
    """
    A chat message that is sent by the client to the server in order to let the server broadcast it
    to all the other chat participants.
    This class is not a specific message. All specific chat messages that are sent from the client will inherit this class.
    """
    def __init__(self, chat_name, chat_participants_list, send_time):
        """
        :param chat_participants_list: [str], names of all the other chat participants.
        """
        super(SendChatMessage, self).__init__(chat_name, send_time)
        self.chat_participants_list = chat_participants_list


class SendChatTextMessage(SendChatMessage):
    """
    A text message that is sent by the client to the server in order to be broadcasted.
    """
    def __init__(self, chat_name, chat_participants_list, send_time, message):
        super(SendChatTextMessage, self).__init__(chat_name, chat_participants_list, send_time)
        self.message = message


class SendChatPictureMessage(SendChatMessage):
    """
    A picture message that is sent by the client to the server in order to be broadcasted.
    the picture will be displayed in the chat.
    """
    def __init__(self, chat_name, chat_participants_list, send_time, encoded_picture_bytes):
        super(SendChatPictureMessage, self).__init__(chat_name, chat_participants_list, send_time)
        self.encoded_picture_bytes = encoded_picture_bytes


class DisplayableChatMessage(ChatMessage):
    """
    A chat message that is sent from the server to the chat participants in order to tell them to display a message
    in a specific chat. This class is not a specific message type. all specific message types that are
    sent by the server will inherit this class.
    """
    def __init__(self, chat_name, sender_username, send_time):
        """
        :param sender_username: str, name of the user who sent the original message.
        """
        super(DisplayableChatMessage, self).__init__(chat_name, send_time)
        self.sender_username = sender_username


class ChatTextMessage(DisplayableChatMessage):
    """
    A text message that should be displayed in the chat.
    """
    def __init__(self, chat_name, sender_username, send_time, message):
        super(ChatTextMessage, self).__init__(chat_name, sender_username, send_time)
        self.message = message


class ChatPictureMessage(DisplayableChatMessage):
    """
    A picture message that should be displayed in the chat.
    """
    def __init__(self, chat_name, sender_username, send_time, encoded_picture_bytes):
        super(ChatPictureMessage, self).__init__(chat_name, sender_username, send_time)
        self.encoded_picture_bytes = encoded_picture_bytes


# Login Process
class LoginMessage(Message):
    """
    Attempts to login to the server as an existing user.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password


class RegisterMessage(Message):
    """
    Attempts to register to the server as a new user.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password


class RegisterFailedMessage(Message):
    """
    Inform a user about a failed register attempt.
    """
    def __init__(self, message):
        self.message = message


class SuccessfulRegisterMessage(Message):
    """
    Inform a user about a successful register attempt.
    """
    pass


class SuccessfulLoginMessage(Message):
    """
    Inform a user about a successful login attempt.
    """
    def __init__(self, contacts_info_list, pending_contacts_list, user_encoded_picture_byes):
        self.contacts_info_list = contacts_info_list
        self.pending_contacts_list = pending_contacts_list
        self.user_encoded_picture_bytes = user_encoded_picture_byes


class LoginFailedMessage(Message):
    """
    Inform a user about a failed login attempt.
    """
    def __init__(self, message):
        self.message = message


# Voice Chat Message
class VoiceChatMessage(Message):
    """
    Represents an abstract Voice Chat message.
    All messages that have to do with an existing voice chat will inherit this characterization.
    These messages are sent through the server and not through the normal p2p connection of the voice chat
    because they are general messages (not raw data like the other voice chat data types) and thus have to be
    received fully, so they cannot be sent through an unreliable protocol like UDP.

    All voice chat messages are sent to the server in order to be immediately broadcasted to all the other
    voice chat participants. the server is a broker, it doesn't tamper with the messages data.
    """
    def __init__(self, participants_names_list):
        """
        All voice chat messages have these properties:
        :param participants_names_list: [str], names of the other voice chat participants.
        """
        self.participants_names_list = participants_names_list


class LeaveVoiceChatMessage(VoiceChatMessage):
    """
    A message that indicates that a user left the call.
    sent by the client to server in order to be broadcasted.
    """
    def __init__(self, participants_names_list):
        super(LeaveVoiceChatMessage, self).__init__(participants_names_list)


class StartedCameraShareMessage(VoiceChatMessage):
    """
    Indicates that a user started sharing his camera data.
    sent by the client to server in order to be broadcasted.
    """
    def __init__(self, participants_names_list):
        super(StartedCameraShareMessage, self).__init__(participants_names_list)


class StoppedCameraShareMessage(VoiceChatMessage):
    """
    Indicates that a user stopped sharing his camera data.
    sent by the client to server in order to be broadcasted.
    """
    def __init__(self, participants_names_list):
        super(StoppedCameraShareMessage, self).__init__(participants_names_list)


class StartedScreenShareMessage(VoiceChatMessage):
    """
    Indicates that a user started sharing his screen data.
    sent by the client to server in order to be broadcasted.
    """
    def __init__(self, participants_names_list):
        super(StartedScreenShareMessage, self).__init__(participants_names_list)


class StoppedScreenShareMessage(VoiceChatMessage):
    """
    Indicates that a user stopped sharing his screen data.
    """
    def __init__(self, participants_names_list):
        super(StoppedScreenShareMessage, self).__init__(participants_names_list)

# Voice Chat Messages - Messages that are sent from the server to the participants.


class ParticipantVoiceChatMessage(Message):
    """
    A message that is sent by the server to the participants of a voice chat in order
    to inform them about the actions of a different voice chat participant.
    This message is a general message that all participant voice chat messages inherit from.
    This message is a direct result of a VoiceChatMessage object - it is just a message that
    is broadcasted to all voice chat participants after a participant sends a VoiceChatMessage.
    """
    def __init__(self, sending_user):
        """
        All participant voice chat messages have these properties:
        :param sending_user: str, the name of the user who sent the original message.
        """
        self.sending_user = sending_user


class ParticipantLeaveVoiceChatMessage(ParticipantVoiceChatMessage):
    """
    Informs the participant that another participant has left the voice chat.
    """
    def __init__(self, sending_user):
        super(ParticipantLeaveVoiceChatMessage, self).__init__(sending_user)


class ParticipantStartedCameraShareMessage(ParticipantVoiceChatMessage):
    """
    Informs the participant that another participant started sharing his camera data.
    """
    def __init__(self, sending_user):
        super(ParticipantStartedCameraShareMessage, self).__init__(sending_user)


class ParticipantStoppedCameraShareMessage(ParticipantVoiceChatMessage):
    """
    Informs the participant that another participant stopped sharing his camera data.
    """
    def __init__(self, sending_user):
        super(ParticipantStoppedCameraShareMessage, self).__init__(sending_user)


class ParticipantStartedScreenShareMessage(ParticipantVoiceChatMessage):
    """
    Informs the participant that another participant started sharing his screen data.
    """
    def __init__(self, sending_user):
        super(ParticipantStartedScreenShareMessage, self).__init__(sending_user)


class ParticipantStoppedScreenShareMessage(ParticipantVoiceChatMessage):
    """
    Informs the participant that another participant stopped sharing his screen data.
    """
    def __init__(self, sending_user):
        super(ParticipantStoppedScreenShareMessage, self).__init__(sending_user)


