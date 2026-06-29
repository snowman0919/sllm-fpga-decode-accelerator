package qk

object UartPacketProtocol {
  val ReqMagic0 = 0xa5
  val ReqMagic1 = 0x5a
  val RespMagic0 = 0x5a
  val RespMagic1 = 0xa5

  val CmdPing = 0x01
  val CmdReset = 0x02
  val CmdMatVec = 0x10

  val RspPingAck = 0x81
  val RspResetAck = 0x82
  val RspMatVecResult = 0x90

  val StatusOk = 0x00
  val StatusBadPacket = 0x01
  val StatusBadShape = 0x02
  val StatusBadCommand = 0x03
}
