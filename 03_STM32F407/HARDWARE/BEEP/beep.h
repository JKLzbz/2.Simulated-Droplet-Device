#ifndef __BEEP_H
#define __BEEP_H	 
#include "sys.h" 

void TIM13_PWM_Init(void);
void set_pwm(uint16_t period, uint16_t pulse);

#endif

















