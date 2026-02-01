/**
 * XRP Serial Drive
 *
 * This sketch implements a simple serial-controlled motor driver for the
 * SparkFun XRP robot platform. It supports two different command
 * protocols so you can control the motors from a Raspberry Pi or other
 * host using either simple single‑character commands or comma‑separated
 * numeric values.  Lines ending in a newline (\n) are parsed as
 * comma‑separated values in the format:
 *
 *   "<left speed>,<right speed>,<left dir>,<right dir>\n"
 *
 *  – left/right speed: integers from 0..100 (0 = stop, 100 = full power)
 *  – left/right dir: 0 = reverse, 1 = forward
 *
 * Alternatively, a single character command may be sent without a
 * newline.  The following commands are recognised:
 *
 *   'F' – drive forward (both motors forward at 100%)
 *   'B' – drive backward (both motors reverse at 100%)
 *   'L' – turn left (left motor reverse, right motor forward)
 *   'R' – turn right (left motor forward, right motor reverse)
 *   'S' – stop (both motors off)
 *
 * Speeds are automatically mapped to the PWM range of 0–255 with a
 * configurable minimum to ensure the motors actually spin.  You can
 * adjust the `min_speed` constant below to fine‑tune this threshold.
 *
 * License: 0BSD https://opensource.org/license/0bsd
 */

// -----------------------------------------------------------------------------
// User‑configurable settings
// -----------------------------------------------------------------------------

// Set this to 1 to print debug information over Serial
#define DEBUG 0

// Minimum PWM value when a non‑zero speed is requested.  Many DC motors do not
// move until a certain threshold; raising this value will ensure the robot
// doesn’t stall at low speeds.  Valid range: 0..254.
const int MIN_PWM = 90;

// Maximum number of characters we’ll buffer from a comma‑separated command.
constexpr int kMaxChars = 64;
// Maximum number of integer fields expected in a CSV line (l_speed,r_speed,l_dir,r_dir).
constexpr int kMaxVals = 4;

// -----------------------------------------------------------------------------
// Hardware pin assignments
// -----------------------------------------------------------------------------

const int MT_L_DIR_PIN = 6;
const int MT_L_PWM_PIN = 7;
const int MT_R_DIR_PIN = 14;
const int MT_R_PWM_PIN = 15;

// -----------------------------------------------------------------------------
// Internal buffers and state
// -----------------------------------------------------------------------------

char input_buf[kMaxChars];     // holds incoming serial text for CSV parsing
int vals[kMaxVals];            // parsed integer values
int buf_idx = 0;               // current write index into input_buf

// Forward declarations
void parse_csv_line(char* input);
void handle_simple_command(char cmd);
void set_motor(int pwm_pin, int dir_pin, bool dir, int speed);
void stop_motors();

void setup() {
  // initialise the serial port.  We use 115200 bps as our default because it
  // matches the sample Python code in this repository.  If you change this
  // value here you must update your host code accordingly.
  Serial.begin(115200);

  // configure motor driver pins
  pinMode(MT_L_DIR_PIN, OUTPUT);
  pinMode(MT_L_PWM_PIN, OUTPUT);
  pinMode(MT_R_DIR_PIN, OUTPUT);
  pinMode(MT_R_PWM_PIN, OUTPUT);

  // ensure the motors are off at start
  stop_motors();

  // initialise our vals array to zero
  memset(vals, 0, sizeof(vals));
}

void loop() {
  // Check for available serial data
  while (Serial.available() > 0) {
    char received = Serial.read();

    // If a single character command is received, handle immediately
    if (received == 'F' || received == 'B' || received == 'L' ||
        received == 'R' || received == 'S') {
      // clear any buffered CSV data as it may be stale
      buf_idx = 0;
      input_buf[0] = '\0';
      handle_simple_command(received);
      continue;
    }

    // accumulate characters until newline for CSV commands
    if (received == '\n') {
      input_buf[buf_idx] = '\0';
      parse_csv_line(input_buf);
      buf_idx = 0;
    } else if (received != '\r' && buf_idx < kMaxChars - 1) {
      input_buf[buf_idx++] = received;
    }
  }
}

/**
 * Parse a comma‑separated line of integers.  Expected format:
 *   l_speed,r_speed,l_dir,r_dir
 * Missing fields will default to zero.  Additional fields are ignored.
 */
void parse_csv_line(char* input) {
  uint8_t val_count = 0;

  // reset values
  for (int i = 0; i < kMaxVals; ++i) {
    vals[i] = 0;
  }

  // break string apart based on delimiter
  char* token = strtok(input, ",");

  // Save values and continue breaking apart string
  while (token != NULL && val_count < kMaxVals) {
    vals[val_count++] = atoi(token);
    // Next token, skip optional space after comma
    token = strtok(NULL, ", ");
  }

  // Debug the received message
#if DEBUG
  Serial.print("Parsed values: ");
  for (int i = 0; i < kMaxVals; i++) {
    Serial.print(vals[i]);
    if (i < kMaxVals - 1) Serial.print(", ");
  }
  Serial.println();
#endif

  // Compute motor directions; any positive value means forward, non‑positive reverse
  int l_dir = vals[2] > 0 ? 1 : 0;
  int r_dir = vals[3] > 0 ? 1 : 0;

  // Compute speeds (0..100).  Negative values treated as zero.
  int l_speed = vals[0] > 0 ? vals[0] : 0;
  int r_speed = vals[1] > 0 ? vals[1] : 0;

  // Drive the motors
  set_motor(MT_L_PWM_PIN, MT_L_DIR_PIN, l_dir, l_speed);
  set_motor(MT_R_PWM_PIN, MT_R_DIR_PIN, r_dir, r_speed);
}

/**
 * Handle single character commands.  Commands are case‑sensitive.
 */
void handle_simple_command(char cmd) {
#if DEBUG
  Serial.print("Received command: ");
  Serial.println(cmd);
#endif
  switch (cmd) {
    case 'F': // forward
      set_motor(MT_L_PWM_PIN, MT_L_DIR_PIN, 1, 100);
      set_motor(MT_R_PWM_PIN, MT_R_DIR_PIN, 1, 100);
      break;
    case 'B': // backward
      set_motor(MT_L_PWM_PIN, MT_L_DIR_PIN, 0, 100);
      set_motor(MT_R_PWM_PIN, MT_R_DIR_PIN, 0, 100);
      break;
    case 'L': // turn left
      set_motor(MT_L_PWM_PIN, MT_L_DIR_PIN, 0, 100);
      set_motor(MT_R_PWM_PIN, MT_R_DIR_PIN, 1, 100);
      break;
    case 'R': // turn right
      set_motor(MT_L_PWM_PIN, MT_L_DIR_PIN, 1, 100);
      set_motor(MT_R_PWM_PIN, MT_R_DIR_PIN, 0, 100);
      break;
    case 'S': // stop
    default:
      stop_motors();
      break;
  }
}

/**
 * Set a single motor’s direction and speed.  Speed values in the range
 * 0..100 are mapped to 0..255 PWM duty cycle with a minimum threshold.
 * Direction 1 drives the motor forward and 0 drives reverse.
 */
void set_motor(int pwm_pin, int dir_pin, bool dir, int speed) {
  digitalWrite(dir_pin, dir ? HIGH : LOW);

  // Map speed to PWM range; ensure that 0 stays at 0.  Values above 100 are clamped.
  int pwm_value = 0;
  if (speed > 0) {
    if (speed > 100) speed = 100;
    pwm_value = map(speed, 1, 100, MIN_PWM, 255);
  }
  analogWrite(pwm_pin, pwm_value);
}

/**
 * Immediately stop both motors.
 */
void stop_motors() {
  analogWrite(MT_L_PWM_PIN, 0);
  analogWrite(MT_R_PWM_PIN, 0);
}