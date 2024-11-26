from abc import ABC, abstractmethod

class Message(ABC):
  @abstractmethod
  def encode(self):
    pass

  @staticmethod
  def decode(data):
    if data[0] == 19:
      return HandshakeMessage(data[1:20].decode('ascii'), data[28:48], data[48:].decode('ascii'))
    elif data[0] == 0:
      return ChokeMessage()
    elif data[0] == 1:
      return UnchokeMessage()
    elif data[0] == 2:
      return InterestedMessage()
    elif data[0] == 3:
      return NotInterestedMessage()
    elif data[0] == 4:
      return HaveMessage(int.from_bytes(data[1:], 'big'))
    elif data[0] == 5:
      return BitfieldMessage(data[1:])
    elif data[0] == 6:
      return RequestMessage(int.from_bytes(data[1:5], 'big'), int.from_bytes(data[5:9], 'big'), int.from_bytes(data[9:], 'big'))
    elif data[0] == 7:
      return PieceMessage(int.from_bytes(data[1:5], 'big'), int.from_bytes(data[5:9], 'big'), data[9:])
    else:
      raise ValueError("Invalid message type")

class HandshakeMessage(Message):
  def __init__(self, protocol_name, info_hash, peer_id):
    self.protocol_name = protocol_name
    self.info_hash = info_hash
    self.peer_id = peer_id

  def __repr__(self):
    return f"Hanshake msg - protocol_name: {self.protocol_name}, info_hash: {self.info_hash}, peer_id: {self.peer_id}"

  def encode(self):
    return len(self.protocol_name).to_bytes(1, 'big') + self.protocol_name.encode('ascii') + b'\x00' * 8 + self.info_hash + self.peer_id.encode('ascii')
  
class InterestedMessage(Message):
  def encode(self):
    return b'\x00\x00\x00\x01\x02'
  
class NotInterestedMessage(Message):
  def encode(self):
    return b'\x00\x00\x00\x01\x03'
  
class ChokeMessage(Message):
  def encode(self):
    return b'\x00\x00\x00\x01\x00'

class UnchokeMessage(Message):
  def encode(self):
    return b'\x00\x00\x00\x01\x01'
  
class HaveMessage(Message):
  def __init__(self, piece_index):
    self.piece_index = piece_index

  def encode(self):
    return b'\x00\x00\x00\x05\x04' +  self.piece_index.to_bytes(4, 'big')
  
class BitfieldMessage(Message):
  def __init__(self, bitfield):
    self.bitfield = bitfield

  def __repr__(self):
    return f"Bitfield: {self.bitfield}"
  
  def encode(self):
    return (len(self.bitfield) + 1).to_bytes(4, 'big') + b'\x05' + self.bitfield
  
class RequestMessage(Message):
  def __init__(self, index, begin, length):
    self.index = index
    self.begin = begin
    self.length = length
  
  def __repr__(self):
    return f"Request msg - index: {self.index}, begin: {self.begin}, length: {self.length}"
  
  def encode(self):
    return b'\x00\x00\x00\r\x06' + self.index.to_bytes(4, 'big') + self.begin.to_bytes(4, 'big') + self.length.to_bytes(4, 'big')
  
class PieceMessage(Message):
  def __init__(self, index, begin, block):
    self.index = index
    self.begin = begin
    self.block = block
  
  def __repr__(self):
    return f"Piece msg - index: {self.index}, begin: {self.begin}, block: {self.block}"
  
  def encode(self):
    return (9+len(self.block)).to_bytes(4, 'big') + b'\x07' + self.index.to_bytes(4, 'big') + self.begin.to_bytes(4, 'big') + self.block