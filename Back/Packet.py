
messageTypes = {
    'CONNECT': b'\x10',
    'CONNACK': b'\x20',
    'PUBLISH': b'\x30',
    'PUBACK': b'\x40',
    'PUBREC': b'\x50',
    'PUBREL': b'\x60',
    'PUBCOMP': b'\x70',
    'SUBSCRIBE': b'\x80',
    'SUBACK': b'\x90',
    'UNSUBSCRIBE': b'\xA0',
    'UNSUBACK': b'\xB0',
    'PINGREQ': b'\xC0',
    'PINGRESP': b'\D0',
    'DISCONNECT': b'\xE0',
    'AUTH': b'\xF0'
}

class Connect(object):
    def __init__(self, _id, _username, _password, _keepAlive, _cleanSession, _lastWillTopic, _lastWillMessage, _lastWillQos, _lastWillRetain):
        self.__id = _id
        self.__username = _username
        self.__password = _password
        self.__keepAlive= _keepAlive
        self.__cleanSession = _cleanSession
        self.__lastWillTopic= _lastWillTopic
        self.__lastWillMessage = _lastWillMessage
        self.__lastWillQos= _lastWillQos
        self.__lastWillRetain = _lastWillRetain

        self.willFlag = None
        if (_lastWillMessage != None):
            self.willFlag = 1

        if (_lastWillQos != None):
            Qo2B0 = (self.__lastWillQos & 1)
            if (Qo2B0 == 0):
                Qo2B0 = None

            Qo2B1 = ((self.__lastWillQos >> 1) & 1)
            if (Qo2B1 == 0):
                Qo2B1 = None
        else:
            Qo2B0 = None
            Qo2B1 = None

        #facem o lista cu valorile ce ar putea aparea in payload, ne ajuta la determinarea flagului
        self.mapConnParam = [_username, _password, _lastWillRetain, Qo2B1, Qo2B0, self.willFlag, _cleanSession, None]

    #scoatem valoarea flagului care indica ce valori avem in payload
    def getFlagValue(self):
        putere = 7
        flagValue = 0
        for value in self.mapConnParam:
            if value != None:
                flagValue = flagValue + 2 ** putere
            putere = putere - 1

        return (flagValue).to_bytes(1, byteorder='big')

    def makePacket (self):
        #Variable header
        variableHeader = b'\x00'
        variableHeader += b'\x04' #length mqtt string
        variableHeader += ('MQTT').encode ('UTF-8') #protocol name
        variableHeader += b'\x04' #version of mqtt
        variableHeader += self.getFlagValue() #flag
        variableHeader += (self.__keepAlive).to_bytes (1, byteorder='big') #keep alive

        #payload
        #set Id
        payload = (len (str(self.__id))).to_bytes (2, byteorder='big')
        payload += str(self.__id).encode ('UTF-8')

        if (self.willFlag != None):
            payload += (len (self.__lastWillTopic)).to_bytes (2, byteorder='big')
            payload += self.__lastWillTopic.encode ('UTF-8')

            payload += (len (self.__lastWillMessage)).to_bytes (2, byteorder='big')
            payload += self.__lastWillMessage.encode ('UTF-8')

        if (self.__username != None):
            payload += (len (self.__username)).to_bytes (2, byteorder='big')
            payload += self.__username.encode ('UTF-8')


        if (self.__password):
            payload += (len (self.__password)).to_bytes (2, byteorder='big')
            payload += self.__password.encode ('UTF-8')

        stringConcat = variableHeader + '!'.encode('UTF-8') + payload

        finalPacket = messageTypes['CONNECT']
        finalPacket += len(stringConcat).to_bytes(1, byteorder='big')
        finalPacket += stringConcat
        return finalPacket

class Disconnect (object):
    def makePacket (self):
        packet = bytearray ()
        packet += messageTypes['DISCONNECT']

        packet += b'\x00'

        return packet

class PingReq (object):
    def makePacket (self):
        packet = bytearray ()
        packet += messageTypes['PINGREQ']

        packet += b'\x00'

        return packet

class Publish (object):
    def __init__ (self, _topicName, _message, _Qos, _packetIdentifier):
        self.__topicName = _topicName
        self.__message = _message
        self.__Qos = _Qos
        self.__packetIdentifier = _packetIdentifier

        self.Qo2B0 = (self.__Qos & 1)
        if (self.Qo2B0 == 0):
            self.Qo2B0 = None

        self.Qo2B1 = ((self.__Qos >> 1) & 1)
        if (self.Qo2B1 == 0):
            self.Qo2B1 = None

    def makePacket (self):
        finalPacket = messageTypes['PUBLISH']

        #make variable header
        variableHeader = (self.__packetIdentifier).to_bytes (1, byteorder='big')
        variableHeader += (len (self.__topicName)).to_bytes(1, byteorder='big')
        variableHeader += (self.__topicName).encode('UTF-8')

        payload = (len(self.__message)).to_bytes(1, byteorder='big')
        payload += (self.__message).encode ('UTF-8')

        stringConcat = variableHeader +  payload
        finalPacket += stringConcat

        return finalPacket