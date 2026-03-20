#include <REGX52.H>
#include "Delay.h"
#include <Key.h>

/**
  * @brief  获取独立按键键码
  * @param  无
  * @retval 
  */
unsigned char Key()
{
	unsigned char KeyNumber=0;
	
	if(P3_1==0){Delay(20);while(P3_1==0);Delay(20);KeyNumber=1;}//k1
	if(P3_0==0){Delay(20);while(P3_0==0);Delay(20);KeyNumber=2;}//k2
	if(P3_2==0){Delay(20);while(P3_2==0);Delay(20);KeyNumber=3;}//k3
	if(P3_3==0){Delay(20);while(P3_3==0);Delay(20);KeyNumber=4;}//k4
	
	
	return KeyNumber;
}