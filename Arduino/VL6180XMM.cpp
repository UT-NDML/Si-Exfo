#include <VL6180X.h>

class VL6180XMM : public VL6180X {
  public:
  uint16_t VL6180XMM::readRangeContinuousRaw()
{
  uint16_t millis_start = millis();
  while ((readReg(RESULT__INTERRUPT_STATUS_GPIO) & 0x04) == 0)
  {
    if (io_timeout > 0 && ((uint16_t)millis() - millis_start) > io_timeout)
    {
      did_timeout = true;
      return 255;
    }
  }

  uint16_t range = readReg16Bit(RESULT__RANGE_RETURN_RATE);
  writeReg(SYSTEM__INTERRUPT_CLEAR, 0x01);

  return range;
}
uint16_t VL6180XMM::readRangeSingleRaw()
{
  writeReg(SYSRANGE__START, 0x01);
  return readRangeContinuousRaw();
}
  
};
