class ValidationServerNotResponded(Exception):
    '''Called if the validation server did not responded'''

class IncorrectRKSOKRequest(Exception):
    '''Called if the client`s request doesn`t meet to rksok`s standart'''