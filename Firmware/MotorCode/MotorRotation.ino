#include "soc/gpio_struct.h"
#include "driver/pcnt.h"

// Motor 1 (left)
#define ENA 18
#define IN1 19
#define IN2 21
#define ENCODER_A1 22

// Motor 2 (right)
#define ENB 25
#define IN3 13
#define IN4 14
#define ENCODER_A2 26

#define LEDC_FREQ 1000
#define LEDC_RES 8

const int COUNTS_PER_REV = 746;

const int COUNTS_PER_10IN = 590;

// PID gains - start with just P, we'll tune from here
float kP = 0.5;
float kI = 0.005;
float kD = 0.0;

const float M1_TARGET = 13; // for 150 PWM 47.0;
const float M2_TARGET = 13; // for 150 PWM 43.0; 

// Motor 1 PID state
float m1_integral = 0;
float m1_lastError = 0;
int m1_pwm = 55; //150 starting place

// Motor 2 PID state
float m2_integral = 0;
float m2_lastError = 0;
int m2_pwm = 55; // 150 starting place 

// Previous encoder counts
int16_t m1_lastCount = 0;
int16_t m2_lastCount = 0;

unsigned long lastPIDTime = 0;
const int PID_INTERVAL = 10; // ms

void setupPCNT(pcnt_unit_t unit, int pin) {
  pcnt_config_t config = {
    .pulse_gpio_num = pin,
    .ctrl_gpio_num = PCNT_PIN_NOT_USED,
    .lctrl_mode = PCNT_MODE_KEEP,
    .hctrl_mode = PCNT_MODE_KEEP,
    .pos_mode = PCNT_COUNT_INC,
    .neg_mode = PCNT_COUNT_INC,
    .counter_h_lim = 32767,
    .counter_l_lim = -32768,
    .unit = unit,
    .channel = PCNT_CHANNEL_0,
  };
  pcnt_unit_config(&config);
  pcnt_filter_disable(unit);
  pcnt_counter_pause(unit);
  pcnt_counter_clear(unit);
  pcnt_counter_resume(unit);
}

void updatePID() {
  // Read current counts
  int16_t m1_count, m2_count;
  pcnt_get_counter_value(PCNT_UNIT_0, &m1_count);
  pcnt_get_counter_value(PCNT_UNIT_1, &m2_count);

  // Handle overflow for motor 1
  int16_t m1_delta = m1_count - m1_lastCount;
  if(abs(m1_count) > 30000) {
    pcnt_counter_clear(PCNT_UNIT_0);
    m1_lastCount = 0;
  } else {
    m1_lastCount = m1_count;
  }

  // Handle overflow for motor 2
  int16_t m2_delta = m2_count - m2_lastCount;
  if(abs(m2_count) > 30000) {
    pcnt_counter_clear(PCNT_UNIT_1);
    m2_lastCount = 0;
  } else {
    m2_lastCount = m2_count;
  }

  // Calculate speed as counts since last update
  float m1_speed = abs(m1_delta);
  float m2_speed = abs(m2_delta);

  // Calculate errors
  float m1_error = M1_TARGET - m1_speed;
  float m2_error = M2_TARGET - m2_speed;

  // Update integrals
  m1_integral += m1_error;
  m2_integral += m2_error;

  // Clamp integrals to prevent windup
  m1_integral = constrain(m1_integral, -50, 50);
  m2_integral = constrain(m2_integral, -50, 50);

  // Calculate derivatives
  float m1_derivative = m1_error - m1_lastError;
  float m2_derivative = m2_error - m2_lastError;
  m1_lastError = m1_error;
  m2_lastError = m2_error;

  // Calculate PID output
  m1_pwm += kP * m1_error + kI * m1_integral + kD * m1_derivative;
  m2_pwm += kP * m2_error + kI * m2_integral + kD * m2_derivative;

  // Clamp PWM values
  m1_pwm = constrain(m1_pwm, 30, 255);
  m2_pwm = constrain(m2_pwm, 30, 255);

  // Apply to motors
  ledcWrite(ENA, m1_pwm);
  ledcWrite(ENB, m2_pwm);

  // Debug output
  Serial.print("M1 speed: "); Serial.print(m1_speed);
  Serial.print(" PWM: "); Serial.print(m1_pwm);
  Serial.print(" | M2 speed: "); Serial.print(m2_speed);
  Serial.print(" PWM: "); Serial.println(m2_pwm);
}

void setup() {
  Serial.begin(115200);

  // Motor 1
  ledcAttach(ENA, LEDC_FREQ, LEDC_RES);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENCODER_A1, INPUT_PULLUP);
  setupPCNT(PCNT_UNIT_0, ENCODER_A1);

  // Motor 2
  ledcAttach(ENB, LEDC_FREQ, LEDC_RES);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENCODER_A2, INPUT_PULLUP);
  setupPCNT(PCNT_UNIT_1, ENCODER_A2);

  // Set motor directions
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  Serial.println("Starting velocity PID...");
  lastPIDTime = millis();
}

void loop() {
  pcnt_counter_clear(PCNT_UNIT_0);
  pcnt_counter_clear(PCNT_UNIT_1);

  Serial.println("Roll the mouse 10 inches then stop.");
  Serial.println("Press reset when done to see final counts.");

  while(true) {
    int16_t m1_count, m2_count;
    pcnt_get_counter_value(PCNT_UNIT_0, &m1_count);
    pcnt_get_counter_value(PCNT_UNIT_1, &m2_count);
    Serial.print("M1: "); Serial.print(m1_count);
    Serial.print(" | M2: "); Serial.println(m2_count);
    delay(100);
  }
}

// void loop() {
//   unsigned long runStart = millis();

//   while(millis() - runStart < 1500) {
//     if(millis() - lastPIDTime >= PID_INTERVAL) {
//       lastPIDTime = millis();
//       updatePID();
//     }
//   }

//   // Stop both motors
//   ledcWrite(ENA, 0);
//   ledcWrite(ENB, 0);
//   digitalWrite(IN1, LOW);
//   digitalWrite(IN2, LOW);
//   digitalWrite(IN3, LOW);
//   digitalWrite(IN4, LOW);

//   Serial.println("Run complete.");
//   while(true);
// }