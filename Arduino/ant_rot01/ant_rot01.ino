/*  ------------------------
    Tilt Compensated Compass
    ------------------------
    "tilt_comp_compass.ino"
    Code by LINGIB
    https://www.instructables.com/member/lingib/instructables/
    Last update 10 May 2019

    The default compass heading is Magnetic North.

    Uncomment the Geographic North code in the main "loop()"
    if you require True North ... you will also have to
    enter the magnetic declination for your location

    The MPU-9250 contains an MPU-9250 gyro/accelerometer
    and an AK8963 magnetometer within the same package.

    +----------+         +-----------+
    |          +--Pitch->+           |
    | MPU-6050 |         |           |
    |          +--Roll-->+           |
    +----------+         |           |
                         |  Compass  |
    +----------+         |           |
    |          +----X--->+           |
    | AK8963   +----Y--->+           |
    |          +----Z--->+           |
    +----------+         +-----------+

   The pitch and roll code for this compass is modelled on
   the MPU-6050 IMU (Inertial Management Unit) described
   by Joop Brokking, http://www.brokking.net/imu.html.

   The algorithm for calibrating the magnetometer is
   described in the following article by Kris Winer:
   https://github.com/kriswiner/MPU6050/wiki/Simple-and-Effective-Magnetometer-Calibration

   The remaining code, including the AK8963 magnetometer code, is by LINGIB
   https://www.instructables.com/member/lingib/instructables/

   -------------
   TERMS OF USE:
   -------------
   The software is provided "AS IS", without any warranty of any kind, express or implied,
   including but not limited to the warranties of mechantability, fitness for a particular
   purpose and noninfringement. In no event shall the authors or copyright holders be liable
   for any claim, damages or other liability, whether in an action of contract, tort or
   otherwise, arising from, out of or in connection with the software or the use or other
   dealings in the software.

   -------------
   WARNING:
   -------------
   Do NOT use this compass in situations involving safety to life such as navigation at sea.
*/

// ----- Libraries
#include <Wire.h>
#include <Servo.h>

Servo servo1;
#define SERV_MIN 544
#define SERV_MAX 2400
#define SERV_MAP 1023

// Serial Buffer values
int servoList[2][2] = {{0, 950}, {0, 950}}; // {{val, in_val_1},{servo2,..}}
int in_val_1 	= 0;
int in_val_0 	= -99;
int packet_flag 	= -1;
bool run_servo_adj, init_ok, lock_trigger, align_acc = false;
// temp values
int serv_slowmv_val_buffer;
int heading_buffer, flag_1;
//int dir_flag 		= -1;
float H_buffer 		= 0;
long serv_slowmv_timer_buffer = micros();
// ----- Adjust Servo Angle
#define ADJUST false
float serv_max_angle = 216;
// ----- globals
float serv_min_angle, serv_N_angle, serv_N_ms;
int LOOP_counter = 5;	// Start with INIT
//Serial Read Buffer
String inString, outString  = "";    // string to hold input, String to hold output
// ----- Gyro
#define MPU9250_I2C_address 0x68                                        // I2C address for MPU9250 
#define MPU9250_I2C_master_enable 0x6A                                  // USER_CTRL[5] = I2C_MST_EN
#define MPU9250_Interface_bypass_mux_enable 0x37                        // INT_PIN_CFG[1]= BYPASS_EN

#define Frequency 125                                                   // 8mS sample interval 
#define Sensitivity 62.5                                                // Gyro sensitivity (see data sheet)

#define Sensor_to_deg 1/(Sensitivity*Frequency)                         // Convert sensor reading to degrees
#define Sensor_to_rad Sensor_to_deg*DEG_TO_RAD                          // Convert sensor reading to radians

#define Loop_time 1000000/Frequency                                     // Loop time (uS)
long    Loop_start;                                                     // Loop start time (uS)

int     Gyro_x,     Gyro_y,     Gyro_z;
long    Gyro_x_cal, Gyro_y_cal, Gyro_z_cal;
float   Gyro_pitch, Gyro_roll, Gyro_yaw;
float   Gyro_pitch_output, Gyro_roll_output;

// ----- Accelerometer
long    Accel_x,      Accel_y,      Accel_z,    Accel_total_vector;
float   Accel_pitch,  Accel_roll;
float   Cal_Accel_pitch, Cal_Accel_roll = -.0f;

// ----- Magnetometer
#define AK8963_I2C_address 0x0C                                             // I2C address for AK8963
#define AK8963_cntrl_reg_1 0x0A                                             // CNTL[4]=#bits, CNTL[3:0]=mode
#define AK8963_status_reg_1 0x02                                            // ST1[0]=data ready
#define AK8963_data_ready_mask 0b00000001                                   // Data ready mask
#define AK8963_overflow_mask 0b00001000                                     // Magnetic sensor overflow mask
#define AK8963_data 0x03                                                    // Start address of XYZ data                                                                
#define AK8963_fuse_ROM 0x10                                                // X,Y,Z fuse ROM

// ----- Compass heading
/*
  The magnetic declination for Lower Hutt, New Zealand is +22.5833 degrees
  Obtain your magnetic declination from http://www.magnetic-declination.com/
  Uncomment the declination code within the main loop() if you want True North.
*/
// float   Declination = +3.36667;                                             //  Degrees ... replace this declination with yours
float     Heading;

int     Mag_x,                Mag_y,                Mag_z;                  // Raw magnetometer readings
float   Mag_x_dampened,       Mag_y_dampened,       Mag_z_dampened;
float   Mag_x_hor, Mag_y_hor;
float   Mag_pitch, Mag_roll;

// ----- Record compass offsets, scale factors, & ASA values
/*
   These values seldom change ... an occasional check is sufficient
   (1) Open your Arduino "Serial Monitor
   (2) Set "Record_data=true;" then upload & run program.
   (3) Replace the values below with the values that appear on the Serial Monitor.
   (4) Set "Record_data = false;" then upload & rerun program.
*/
bool    Record_data = false ;
int     Mag_x_offset = -71,      Mag_y_offset = 203,     Mag_z_offset = 134;   // Hard-iron offsets
float   Mag_x_scale = 0.8,     Mag_y_scale = 0.7,     Mag_z_scale = 3.19;    // Soft-iron scale factors
float   ASAX = 1.18,            ASAY = 1.18,            ASAZ = 1.14;           // (A)sahi (S)ensitivity (A)djustment fuse ROM values.

// ----- LED
const int LED = 13;                     // Status LED

// ----- Flags
bool Gyro_synchronised = false;
bool Flag = false;

// ----- Debug
//#define Switch A0                       // Connect an SPST switch between A0 and GND to enable/disable tilt stabilazation
#define Poti A1
long Loop_start_time;
long Debug_start_time;

// -----------------
//  Setup
// -----------------
void setup()
{
  // ----- Serial communication
  Serial.begin(115200);                                 //Use only for debugging
  // ----- Start-up message
  Serial.println("");
  Serial.println("BSTRT");								//Restart Trigger for Python						
  Wire.begin();                                         //Start I2C as master
  Wire.setClock(400000);
  
  servo1.attach(3);
  serv_N_angle 	 	 = float(SERV_MAP / serv_max_angle * 360);
  serv_N_ms		 	 = float((SERV_MAX - SERV_MIN) / serv_max_angle * 360);

  serv_min_angle 	 = 180 - serv_max_angle / 2;
  serv_max_angle 	 = serv_min_angle + serv_max_angle;
  
  // ----- Status LED
  pinMode(LED, OUTPUT);                                 // Set LED (pin 13) as output
  digitalWrite(LED, HIGH);                               // Turn LED off

  
  // ----- Configure the magnetometer
  configure_magnetometer();
  // ----- Calibrate the magnetometer
  /*
     Calibrate only needs to be done occasionally.
     Enter the magnetometer values into the "header"
     then set "Record_data = false".
  */
  if (Record_data == true)
  {
    calibrate_magnetometer();
  }

  // ----- Configure the gyro & magnetometer
  config_gyro();
  calibrate_gyro();

  Debug_start_time = micros();                          // Controls data display rate to Serial Monitor
  Loop_start_time  = micros();                          // Controls the Gyro refresh rate
  digitalWrite(LED, LOW);
}

// ----------------------------
// Main loop
// ----------------------------
void loop()
{
	// ----- Main Loop - Get Serial - Adj Servo ...
	loop_contol();
	// ----- Loop control		
	/*
		Adjust the loop count for a yaw reading of 360 degrees
		when the MPU-9250 is rotated exactly 360 degrees.
		(Compensates for any 16 MHz Xtal oscillator error)
	*/
	if((micros() - Loop_start_time) >= 8400) {
		main_loop();		
		Loop_start_time = micros();
	}
}
// ----------------------------
//  Main : Get and calc Parameters
// ----------------------------
void main_loop() {
	  ////////////////////////////////////////////
	  //        PITCH & ROLL CALCULATIONS       //
	  ////////////////////////////////////////////

	  /*
		 --------------------
		 MPU-9250 Orientation
		 --------------------
		 Component side up
		 X-axis facing forward
	  */

	  // ----- read the raw accelerometer and gyro data
	  read_mpu_6050_data();                                             // Read the raw acc and gyro data from the MPU-6050

	  // ----- Adjust for offsets
	  Gyro_x -= Gyro_x_cal;                                             // Subtract the offset from the raw gyro_x value
	  Gyro_y -= Gyro_y_cal;                                             // Subtract the offset from the raw gyro_y value
	  Gyro_z -= Gyro_z_cal;                                             // Subtract the offset from the raw gyro_z value

	  // ----- Calculate travelled angles
	  /*
		---------------------------
		Adjust Gyro_xyz signs for:
		---------------------------
		Pitch (Nose - up) = +ve reading
		Roll (Right - wing down) = +ve reading
		Yaw (Clock - wise rotation)  = +ve reading
	  */
	  Gyro_pitch += -Gyro_y * Sensor_to_deg;                            // Integrate the raw Gyro_y readings
	  Gyro_roll += Gyro_x * Sensor_to_deg;                              // Integrate the raw Gyro_x readings
	  Gyro_yaw += -Gyro_z * Sensor_to_deg;                              // Integrate the raw Gyro_x readings

	  // ----- Compensate pitch and roll for gyro yaw
	  Gyro_pitch += Gyro_roll * sin(Gyro_z * Sensor_to_rad);            // Transfer the roll angle to the pitch angle if the Z-axis has yawed
	  Gyro_roll -= Gyro_pitch * sin(Gyro_z * Sensor_to_rad);            // Transfer the pitch angle to the roll angle if the Z-axis has yawed

	  // ----- Accelerometer angle calculations
	  Accel_total_vector = sqrt((Accel_x * Accel_x) + (Accel_y * Accel_y) + (Accel_z * Accel_z));   // Calculate the total (3D) vector
	  Accel_pitch = asin((float)Accel_x / Accel_total_vector) * RAD_TO_DEG;                         //Calculate the pitch angle
	  Accel_roll = asin((float)Accel_y / Accel_total_vector) * RAD_TO_DEG;                         //Calculate the roll angle

	  // ----- Zero any residual accelerometer readings
	  /*
		 Place the accelerometer on a level surface
		 Adjust the following two values until the pitch and roll readings are zero
	  */
	  //Accel_pitch -= -0.2f;                                             //Accelerometer calibration value for pitch
	  Accel_pitch -= Cal_Accel_pitch;                                             //Accelerometer calibration value for pitch
	  //Accel_roll -= 1.1f;                                               //Accelerometer calibration value for roll
	  Accel_roll -= Cal_Accel_roll;                                              //Accelerometer calibration value for roll

	  // ----- Correct for any gyro drift
	  if (Gyro_synchronised)
	  {
		// ----- Gyro & accel have been synchronised
		Gyro_pitch = Gyro_pitch * 0.9996 + Accel_pitch * 0.0004;        //Correct the drift of the gyro pitch angle with the accelerometer pitch angle
		Gyro_roll = Gyro_roll * 0.9996 + Accel_roll * 0.0004;           //Correct the drift of the gyro roll angle with the accelerometer roll angle
	  }
	  else
	  {
		// ----- Synchronise gyro & accel
		Gyro_pitch = Accel_pitch;                                       //Set the gyro pitch angle equal to the accelerometer pitch angle
		Gyro_roll = Accel_roll;                                         //Set the gyro roll angle equal to the accelerometer roll angle
		Gyro_synchronised = true;                                             //Set the IMU started flag
	  }

	  // ----- Dampen the pitch and roll angles
	  Gyro_pitch_output = Gyro_pitch_output * 0.9 + Gyro_pitch * 0.1;   //Take 90% of the output pitch value and add 10% of the raw pitch value
	  Gyro_roll_output = Gyro_roll_output * 0.9 + Gyro_roll * 0.1;      //Take 90% of the output roll value and add 10% of the raw roll value

	  ////////////////////////////////////////////
	  //        MAGNETOMETER CALCULATIONS       //
	  ////////////////////////////////////////////
	  /*
		 --------------------------------
		 Instructions for first time use
		 --------------------------------
		 Calibrate the compass for Hard-iron and Soft-iron
		 distortion by temporarily setting the header to read
		 bool    Record_data = true;

		 Turn on your Serial Monitor before uploading the code.

		 Slowly tumble the compass in all directions until a
		 set of readings appears in the Serial Monitor.

		 Copy these values into the appropriate header locations.

		 Edit the header to read
		 bool    Record_data = false;

		 Upload the above code changes to your Arduino.

		 This step only needs to be done occasionally as the
		 values are reasonably stable.
	  */

	  // ----- Read the magnetometer
	  read_magnetometer();

	  // ----- Fix the pitch, roll, & signs
	  /*
		 MPU-9250 gyro and AK8963 magnetometer XY axes are orientated 90 degrees to each other
		 which means that Mag_pitch equates to the Gyro_roll and Mag_roll equates to the Gryro_pitch

		 The MPU-9520 and AK8963 Z axes point in opposite directions
		 which means that the sign for Mag_pitch must be negative to compensate.
	  */
	  Mag_pitch = -Gyro_roll_output * DEG_TO_RAD;
	  Mag_roll = Gyro_pitch_output * DEG_TO_RAD;

	  // ----- Apply the standard tilt formulas
	  Mag_x_hor = Mag_x * cos(Mag_pitch) + Mag_y * sin(Mag_roll) * sin(Mag_pitch) - Mag_z * cos(Mag_roll) * sin(Mag_pitch);
	  Mag_y_hor = Mag_y * cos(Mag_roll) + Mag_z * sin(Mag_roll);

	  // ----- Dampen any data fluctuations
	  Mag_x_dampened = Mag_x_dampened * 0.9 + Mag_x_hor * 0.1;
	  Mag_y_dampened = Mag_y_dampened * 0.9 + Mag_y_hor * 0.1;

	  // ----- Calculate the heading
	  Heading = atan2(Mag_x_dampened, Mag_y_dampened) * RAD_TO_DEG;  // Magnetic North
	  // ----- Correct for True North
	  // Heading += Declination;                                   // Geographic North
	  // ----- Allow for under/overflow
	  Heading = heading_overflow(Heading);
}

// ----------------------------
//  Configure magnetometer
// ----------------------------
void configure_magnetometer()
{
  /*
     The MPU-9250 contains an AK8963 magnetometer and an
     MPU-6050 gyro/accelerometer within the same package.

     To access the AK8963 magnetometer chip The MPU-9250 I2C bus
     must be changed to pass-though mode. To do this we must:
      - disable the MPU-9250 slave I2C and
      - enable the MPU-9250 interface bypass mux
  */
  // ----- Disable MPU9250 I2C master interface
  Wire.beginTransmission(MPU9250_I2C_address);                      // Open session with MPU9250
  Wire.write(MPU9250_I2C_master_enable);                            // Point USER_CTRL[5] = I2C_MST_EN
  Wire.write(0x00);                                                 // Disable the I2C master interface
  Wire.endTransmission();

  // ----- Enable MPU9250 interface bypass mux
  Wire.beginTransmission(MPU9250_I2C_address);                      // Open session with MPU9250
  Wire.write(MPU9250_Interface_bypass_mux_enable);                  // Point to INT_PIN_CFG[1] = BYPASS_EN
  Wire.write(0x02);                                                 // Enable the bypass mux
  Wire.endTransmission();

  // ----- Access AK8963 fuse ROM
  /* The factory sensitivity readings for the XYZ axes are stored in a fuse ROM.
     To access this data we must change the AK9863 operating mode.
  */
  Wire.beginTransmission(AK8963_I2C_address);                       // Open session with AK8963
  Wire.write(AK8963_cntrl_reg_1);                                   // CNTL[3:0] mode bits
  Wire.write(0b00011111);                                           // Output data=16-bits; Access fuse ROM
  Wire.endTransmission();
  delay(100);                                                       // Wait for mode change

  // ----- Get factory XYZ sensitivity adjustment values from fuse ROM
  /* There is a formula on page 53 of "MPU-9250, Register Map and Decriptions, Revision 1.4":
      Hadj = H*(((ASA-128)*0.5)/128)+1 where
      H    = measurement data output from data register
      ASA  = sensitivity adjustment value (from fuse ROM)
      Hadj = adjusted measurement data (after applying
  */
  Wire.beginTransmission(AK8963_I2C_address);                       // Open session with AK8963
  Wire.write(AK8963_fuse_ROM);                                      // Point to AK8963 fuse ROM
  Wire.endTransmission();
  Wire.requestFrom(AK8963_I2C_address, 3);                          // Request 3 bytes of data
  while (Wire.available() < 3);                                     // Wait for the data
  ASAX = (Wire.read() - 128) * 0.5 / 128 + 1;                       // Adjust data
  ASAY = (Wire.read() - 128) * 0.5 / 128 + 1;
  ASAZ = (Wire.read() - 128) * 0.5 / 128 + 1;

  // ----- Power down AK8963 while the mode is changed
  /*
     This wasn't necessary for the first mode change as the chip was already powered down
  */
  Wire.beginTransmission(AK8963_I2C_address);                       // Open session with AK8963
  Wire.write(AK8963_cntrl_reg_1);                                   // Point to mode control register
  Wire.write(0b00000000);                                           // Set mode to power down
  Wire.endTransmission();
  delay(100);                                                       // Wait for mode change

  // ----- Set output to mode 2 (16-bit, 100Hz continuous)
  Wire.beginTransmission(AK8963_I2C_address);                       // Open session with AK8963
  Wire.write(AK8963_cntrl_reg_1);                                   // Point to mode control register
  Wire.write(0b00010110);                                           // Output=16-bits; Measurements = 100Hz continuous
  Wire.endTransmission();
  delay(100);                                                       // Wait for mode change
}

// -------------------------------
//  Calibrate magnetometer
// -------------------------------
void calibrate_magnetometer(){
	// send ACK
	while(outString.length() != 0) send_Serial();
	// ----- Locals
	int mag_x, mag_y, mag_z;
	int status_reg_2;                                               // ST2 status register

	int mag_x_min =  32767;                                         // Raw data extremes
	int mag_y_min =  32767;
	int mag_z_min =  32767;
	int mag_x_max = -32768;
	int mag_y_max = -32768;
	int mag_z_max = -32768;

	float chord_x,  chord_y,  chord_z;                              // Used for calculating scale factors
	float chord_average;

	// ----- Display calibration message
	digitalWrite(LED, HIGH);                              //Turn LED on ... indicates startup

	Serial.println("Rotate Compass");

	// ----- Record min/max XYZ compass readings
	// 128 sec. 32000 * 4 / 1000
	for (int counter = 0; counter < 32000 ; counter ++) {             // Run this code 16000 times

		Loop_start = micros();                                        // Start loop timer
		if (counter % 1000 == 0) Serial.println(".");                 // Print a dot on the LCD every 1000 readings

		// ----- Point to status register 1
		Wire.beginTransmission(AK8963_I2C_address);                   // Open session with AK8963
		Wire.write(AK8963_status_reg_1);                              // Point to ST1[0] status bit
		Wire.endTransmission();
		Wire.requestFrom(AK8963_I2C_address, 1);                      // Request 1 data byte
		while (Wire.available() < 1);                                 // Wait for the data
		if (Wire.read() & AK8963_data_ready_mask) {                    // Check data ready bit
    
			// ----- Read data from each axis (LSB,MSB)
			Wire.requestFrom(AK8963_I2C_address, 7);                    // Request 7 data bytes
			while (Wire.available() < 7);                               // Wait for the data
			mag_x = (Wire.read() | Wire.read() << 8) * ASAX;            // Combine LSB,MSB X-axis, apply ASA corrections
			mag_y = (Wire.read() | Wire.read() << 8) * ASAY;            // Combine LSB,MSB Y-axis, apply ASA corrections
			mag_z = (Wire.read() | Wire.read() << 8) * ASAZ;            // Combine LSB,MSB Z-axis, apply ASA corrections
			status_reg_2 = Wire.read();                                 // Read status and signal data read

			// ----- Validate data
			if (!(status_reg_2 & AK8963_overflow_mask)) {         // Check HOFL flag in ST2[3]
				// ----- Find max/min xyz values
				mag_x_min = min(mag_x, mag_x_min);
				mag_x_max = max(mag_x, mag_x_max);
				mag_y_min = min(mag_y, mag_y_min);
				mag_y_max = max(mag_y, mag_y_max);
				mag_z_min = min(mag_z, mag_z_min);
				mag_z_max = max(mag_z, mag_z_max);
			}
		}
		delay(4);                                                     // Time interval between magnetometer readings
	}

	// ----- Calculate hard-iron offsets
	Mag_x_offset = (mag_x_max + mag_x_min) / 2;                     // Get average magnetic bias in counts
	Mag_y_offset = (mag_y_max + mag_y_min) / 2;
	Mag_z_offset = (mag_z_max + mag_z_min) / 2;

	// ----- Calculate soft-iron scale factors
	chord_x = ((float)(mag_x_max - mag_x_min)) / 2;                 // Get average max chord length in counts
	chord_y = ((float)(mag_y_max - mag_y_min)) / 2;
	chord_z = ((float)(mag_z_max - mag_z_min)) / 2;

	chord_average = (chord_x + chord_y + chord_z) / 3;              // Calculate average chord length

	Mag_x_scale = chord_average / chord_x;                          // Calculate X scale factor
	Mag_y_scale = chord_average / chord_y;                          // Calculate Y scale factor
	Mag_z_scale = chord_average / chord_z;                          // Calculate Z scale factor

	// ----- Record magnetometer offsets
	/*
	 When active this feature sends the magnetometer data
	 to the Serial Monitor then halts the program.
	*/
	if (Record_data == true) {
		// ----- Display data extremes
		Serial.println("");
		Serial.println("");
		Serial.print("XYZ Max/Min: ");
		Serial.print(mag_x_min); Serial.print("\t");
		Serial.print(mag_x_max); Serial.print("\t");
		Serial.print(mag_y_min); Serial.print("\t");
		Serial.print(mag_y_max); Serial.print("\t");
		Serial.print(mag_z_min); Serial.print("\t");
		Serial.println(mag_z_max);
		Serial.println("");

		// ----- Display hard-iron offsets
		Serial.print("Hard-iron: ");
		Serial.print(Mag_x_offset); Serial.print("\t");
		Serial.print(Mag_y_offset); Serial.print("\t");
		Serial.println(Mag_z_offset);
		Serial.println("");

		// ----- Display soft-iron scale factors
		Serial.print("Soft-iron: ");
		Serial.print(Mag_x_scale); Serial.print("\t");
		Serial.print(Mag_y_scale); Serial.print("\t");
		Serial.println(Mag_z_scale);
		Serial.println("");

		// ----- Display fuse ROM values
		Serial.print("ASA: ");
		Serial.print(ASAX); Serial.print("\t");
		Serial.print(ASAY); Serial.print("\t");
		Serial.println(ASAZ);

		// ----- Halt program    
		digitalWrite(LED, LOW);                             //Turn LED on ... indicates startup
		while (true);                                       // Wheelspin ... program halt
	}else{
		send_busy(0);
		send_mag_param();
	}
	digitalWrite(LED, LOW);                             //Turn LED on ... indicates startup
}

// -------------------------------
//  Read magnetometer
// -------------------------------
void read_magnetometer()
{
  // ----- Locals
  int mag_x, mag_y, mag_z;
  int status_reg_2;

  // ----- Point to status register 1
  Wire.beginTransmission(AK8963_I2C_address);                   // Open session with AK8963
  Wire.write(AK8963_status_reg_1);                              // Point to ST1[0] status bit
  Wire.endTransmission();
  Wire.requestFrom(AK8963_I2C_address, 1);                      // Request 1 data byte
  while (Wire.available() < 1);                                 // Wait for the data
  if (Wire.read() & AK8963_data_ready_mask)                     // Check data ready bit
  {
    // ----- Read data from each axis (LSB,MSB)
    Wire.requestFrom(AK8963_I2C_address, 7);                    // Request 7 data bytes
    while (Wire.available() < 7);                               // Wait for the data
    mag_x = (Wire.read() | Wire.read() << 8) * ASAX;            // Combine LSB,MSB X-axis, apply ASA corrections
    mag_y = (Wire.read() | Wire.read() << 8) * ASAY;            // Combine LSB,MSB Y-axis, apply ASA corrections
    mag_z = (Wire.read() | Wire.read() << 8) * ASAZ;            // Combine LSB,MSB Z-axis, apply ASA corrections
    status_reg_2 = Wire.read();                                 // Read status and signal data read

    // ----- Validate data
    if (!(status_reg_2 & AK8963_overflow_mask))                 // Check HOFL flag in ST2[3]
    {
      Mag_x = (mag_x - Mag_x_offset) * Mag_x_scale;
      Mag_y = (mag_y - Mag_y_offset) * Mag_y_scale;
      Mag_z = (mag_z - Mag_z_offset) * Mag_z_scale;
    }
  }
}

// -----------------------------------
//  Configure the gyro & accelerometer
// -----------------------------------
void config_gyro()
{
  // ----- Activate the MPU-6050
  Wire.beginTransmission(0x68);                         //Open session with the MPU-6050
  Wire.write(0x6B);                                     //Point to power management register
  Wire.write(0x00);                                     //Use internal 20MHz clock
  Wire.endTransmission();                               //End the transmission

  // ----- Configure the accelerometer (+/-8g)
  Wire.beginTransmission(0x68);                         //Open session with the MPU-6050
  Wire.write(0x1C);                                     //Point to accelerometer configuration reg
  Wire.write(0x10);                                     //Select +/-8g full-scale
  Wire.endTransmission();                               //End the transmission

  // ----- Configure the gyro (500dps full scale)
  Wire.beginTransmission(0x68);                         //Open session with the MPU-6050
  Wire.write(0x1B);                                     //Point to gyroscope configuration
  Wire.write(0x08);                                     //Select 500dps full-scale
  Wire.endTransmission();                               //End the transmission
}

// -----------------------------------
//  Calibrate gyro
// -----------------------------------
void calibrate_gyro()
{
  // ----- Display calibration message
  Serial.println("Calibrating Gyro");

  // ----- LED Status (ON = calibration start)
  digitalWrite(LED, HIGH);                              //Turn LED on ... indicates startup

  // ----- Calibrate gyro
  for (int counter = 0; counter < 2000 ; counter ++)    //Run this code 2000 times
  {
    Loop_start = micros();
    if (counter % 125 == 0)Serial.println(".");           //Print a dot on the LCD every 125 readings
    read_mpu_6050_data();                               //Read the raw acc and gyro data from the MPU-6050
    Gyro_x_cal += Gyro_x;                               //Add the gyro x-axis offset to the gyro_x_cal variable
    Gyro_y_cal += Gyro_y;                               //Add the gyro y-axis offset to the gyro_y_cal variable
    Gyro_z_cal += Gyro_z;                               //Add the gyro z-axis offset to the gyro_z_cal variable
    while (micros() - Loop_start < Loop_time);           // Wait until "Loop_time" microseconds have elapsed
  }  
  Gyro_x_cal /= 2000;                                   //Divide the gyro_x_cal variable by 2000 to get the average offset
  Gyro_y_cal /= 2000;                                   //Divide the gyro_y_cal variable by 2000 to get the average offset
  Gyro_z_cal /= 2000;                                   //Divide the gyro_z_cal variable by 2000 to get the average offset

  // ----- Status LED
  Serial.println("");
  digitalWrite(LED, LOW);                               // Turn LED off ... calibration complete
}

// --------------------
//  Read MPU 6050 data
// --------------------
void read_mpu_6050_data()
{
  /*
    Subroutine for reading the raw gyro and accelerometer data
  */

  // ----- Locals
  int     temperature;                                  // Needed when reading the MPU-6050 data ... not used

  // ----- Point to data
  Wire.beginTransmission(0x68);                         // Start communicating with the MPU-6050
  Wire.write(0x3B);                                     // Point to start of data
  Wire.endTransmission();                               // End the transmission

  // ----- Read the data
  Wire.requestFrom(0x68, 14);                           // Request 14 bytes from the MPU-6050
  while (Wire.available() < 14);                        // Wait until all the bytes are received
  Accel_x = Wire.read() << 8 | Wire.read();             // Combine MSB,LSB Accel_x variable
  Accel_y = Wire.read() << 8 | Wire.read();             // Combine MSB,LSB Accel_y variable
  Accel_z = Wire.read() << 8 | Wire.read();             // Combine MSB,LSB Accel_z variable
  temperature = Wire.read() << 8 | Wire.read();         // Combine MSB,LSB temperature variable
  Gyro_x = Wire.read() << 8 | Wire.read();              // Combine MSB,LSB Gyro_x variable
  Gyro_y = Wire.read() << 8 | Wire.read();              // Combine MSB,LSB Gyro_x variable
  Gyro_z = Wire.read() << 8 | Wire.read();              // Combine MSB,LSB Gyro_x variable
}
// ----- Allow for under/overflow
float heading_overflow(float h_in) {	
	if (h_in >= 360) h_in -= 360;    	
	if (h_in < 0)    h_in += 360;		
	return h_in;
}
// -------------------------------
//  Adjust Servos
// -------------------------------
void adjust_servos() {	
	if(ADJUST) {
		serv_max_angle = map(analogRead(Poti), 50, 1000, 200, 280 );
		serv_min_angle = 180 - serv_max_angle / 2;
		serv_max_angle = serv_min_angle + serv_max_angle;
	}	
	
	float temp_head = (Heading - H_buffer + serv_min_angle);
	temp_head = map(temp_head, -360, 360, -serv_N_ms, serv_N_ms);
	int map_val = int(temp_head + serv_slowmv_val_buffer) % int(serv_N_ms);
	map_val		= max(map_val, SERV_MIN);  
	map_val		= min(map_val, SERV_MAX);  
	servo1.writeMicroseconds(map_val);	
}

// --------------------------
//  Send ACK end of received msg
// --------------------------
void send_ack() {
	addTo_outString("ACK" + (String)packet_flag);
	inString 	= "";
	packet_flag = -1;
	in_val_0	= -99;
	in_val_1	= -99;
}
// --------------------------
//  Send outString byte per byte 
// --------------------------
void send_Serial() {
	if(outString.length() != 0) {
		Serial.print(outString.charAt(0));
		outString.remove(0, 1);
	}
	if(outString.length() > 10) LOOP_counter = 1; // prevent jaming outString
}
// --------------------------
//  add Strin to outString 
// --------------------------
void addTo_outString(String in_p) {
	outString += in_p;
	outString += '\n';
}
// --------------------------
//  Send busy Flag if Ardu cant receive packets ( mag cal ) 
// --------------------------
void send_busy(int in_p) {
	addTo_outString("BSY" + (String)in_p);
}
// --------------------------
//  add Strin to outString 
// --------------------------
void serv_in_pos_ack() {
	addTo_outString("SAC");
	servoList[0][1] = 1;
}
// --------------------------
//  Alinge accelerometer pitch & roll
// --------------------------
void align_accel(){
	Cal_Accel_pitch = Accel_pitch;
	Cal_Accel_roll  = Accel_roll;
}
// --------------------------
//  Send magnetometer calculation parameter
// --------------------------
void send_mag_param() {
	// Flag
	String out_s = "CM";
	// Hard-iron
	out_s += (String)Mag_x_offset;
	out_s += "a";
	out_s += (String)Mag_y_offset;
	out_s += "b";
	out_s += (String)Mag_z_offset;
	out_s += "c";
	// Soft-iron
	out_s += (String)Mag_x_scale;
	out_s += "d";
	out_s += (String)Mag_y_scale;
	out_s += "e";
	out_s += (String)Mag_z_scale;
	out_s += "f";
	// ASA
	out_s += (String)ASAX;
	out_s += "g";
	out_s += (String)ASAY;
	out_s += "h";
	out_s += (String)ASAZ;
	out_s += "i";
	// Out
	addTo_outString(out_s);
}
// --------------------------
//  Slow move servo
// --------------------------
/*
void slow_mv_servo() {
	int soll = servoList[0][0];
	int ist  = serv_slowmv_val_buffer;
	if(soll == ist) {
		dir_flag = -1;
		serv_in_pos_ack();
	}else{
		Serial.println("init");
		Serial.println("ist  " + (String)ist);
		Serial.println("soll " + (String)soll);
		if(dir_flag == -1) {
			if(soll > ist) {
				Serial.println("0");
				int res_1 = serv_N_ms - soll + ist;
				int res_2 = soll - ist;
				if(res_1 < res_2) {
					Serial.println("-");
					dir_flag = 1;
				}else{
					Serial.println("+");
					dir_flag = 0;
				}				
			}else{
				Serial.println("1");
				int res_1 = -serv_N_ms - soll + ist;
				int res_2 = soll - ist;
				if(abs(res_1) < abs(res_2)) {
					Serial.println("+");
					dir_flag = 1;
				}else{
					Serial.println("-");
					dir_flag = 0;
				}
			}
		}else{
			Serial.println("");
			Serial.println("ist  " + (String)ist);
			Serial.println("soll " + (String)soll);
			switch (dir_flag) {
				case 0 : serv_slowmv_val_buffer -= 1; break;
				case 1 : serv_slowmv_val_buffer += 1; break;
			}
		}
	}
}
*/
// --------------------------
//  Main Loop - Get Serial - Adj Servo ...
// --------------------------
void loop_contol() {
	
 /*
	Subroutine for updating the LCD display.
	In order to reduce the refresh time only one
	digit is updated each time around the main loop.
 */

LOOP_counter++;
// Adjust Servos each iritation
if(run_servo_adj) adjust_servos();


switch (LOOP_counter) {		
		
	////////////////////// Heading /////////////////////////
	case 1: // ----- Send Heading if change
		flag_1 = round(Heading);
		if(flag_1 != heading_buffer) {
			heading_buffer 	= flag_1; 	
			addTo_outString("$" + (String)Heading);
			//addTo_outString("P " + (String)Accel_pitch + " R " + (String)Accel_roll);
			if(ADJUST) addTo_outString("ADJ: " + (String)serv_max_angle);
		}		
		break;
	
	////////////////////// send Serial /////////////////////////
	case 2:
		send_Serial();
    break;

	/////////////////////// get Serial ///////////////////////////
	// in_val_0, in_val_1, servo()
	case 3: // ----- write Serial if available and Buffer free to Buffer
		if(Serial.available() > 0) {
			int stri = Serial.read();
			if(packet_flag == -1) {			
				packet_flag = ((String)stri).toInt();
			}else{
				// convert the incoming byte to a char and add it to the string:
				inString += (char)stri;			
			}
			switch(packet_flag) {
				
				case 73:	// "I"	get Init ok
					if(stri == '\n') {
						if(inString.toInt() == 1) {
							init_ok = true;	
							send_ack();
							H_buffer = Heading;
							addTo_outString("LH" + (String)H_buffer);	//gimbal lock heading
						}
					}
				break;				
				case 65: 	// "A"	Servo Adjust on/off
					if(stri == '\n') {
						if(inString.toInt() == 1) {
							run_servo_adj = true;						
						}else{
							run_servo_adj = false;
						}
						send_ack();	
					}
				break;
				case 66:	// "B"	Set H_buffer if not set in case 83
					if(stri == '\n') {
						H_buffer = Heading;						
						send_ack();
						addTo_outString("LH" + (String)H_buffer);	//gimbal lock heading
					}
				break;
				case 67: 	// "C" Level accelerometer & calibrate magnetometer
					if(in_val_0 == -99) {
						switch (stri) {
							case 'A': in_val_0 = 0; break;	// accelerometer
							// CA for Auto
							// CA2.55P1.45R
							case 'M': in_val_0 = 1;	break;  // magnetometer
							// CM new calibration
							// CM40a-236b147c1.01d0.98e1.01f1.18g1.18h1.14i
							case 'P': in_val_0 = 2; break; 	// magnetometer parameter
							// CP send magnetometer Parameter
						}
						inString = "";
					}else{
						if(stri == '\n') {													
							switch (in_val_0) {
								case 0:  send_ack(); align_acc = true;  		break;	// accelerometer
								case 1:  send_busy(1); 
										 send_ack(); calibrate_magnetometer();  break;	// magnetometer
								case 2:  send_ack(); send_mag_param();		   	break;	// send magnetometer parameter without calibration
								default: send_ack();							break;
							}
						}else{
							switch(in_val_0) {
								case 0:
									switch (stri) {
										case 'P': 
											Cal_Accel_pitch = inString.toFloat();
											inString 		= "";
										break;
										case 'R':
											Cal_Accel_roll  = inString.toFloat();
											inString 		= "";
											in_val_0		= -1;
										break;
									}
									break;
								case 1:
									switch (stri) {
										// Hard-iron
										case 'a':
											Mag_x_offset  	= inString.toInt();
											inString 		= "";
										break;
										case 'b':
											Mag_y_offset  	= inString.toInt();
											inString 		= "";
										break;
										case 'c':
											Mag_z_offset  	= inString.toInt();
											inString 		= "";
										break;
										// Soft-iron
										case 'd':
											Mag_x_scale  	= inString.toFloat();
											inString 		= "";
										break;
										case 'e':
											Mag_y_scale  	= inString.toFloat();
											inString 		= "";
										break;
										case 'f':
											Mag_z_scale  	= inString.toFloat();
											inString 		= "";
										break;
										// ASA
										case 'g':
											ASAX  			= inString.toFloat();
											inString 		= "";
										break;
										case 'h':
											ASAY  			= inString.toFloat();
											inString 		= "";
										break;
										case 'i':
											ASAZ  			= inString.toFloat();
											inString 		= "";
											in_val_0		= -1;
										break;
									}
								break;
							}
						}
							
					}
				break;
				case 83:	// "S"  Servo Parameter	
					if (stri == 'L') { // Set Gimbal Lock
						lock_trigger = true;
						inString = "";
					}				
					if (stri == ',') { // value
						in_val_0 = map((inString.toInt() - 2000), -serv_N_angle, serv_N_angle, -serv_N_ms, serv_N_ms);				
						inString = "";
					}
					if (stri == ':') { // speed
						in_val_1 = inString.toInt();			
						inString = "";
					}					
					if (stri == '\n') {	// servo number
						int serv = (inString.toInt() - 1);						
						servoList[serv][1] = in_val_1;
						servoList[serv][0] = in_val_0;
						if(lock_trigger) {
							H_buffer = Heading;	
							addTo_outString("LH" + (String)H_buffer);
							lock_trigger = false;
						}
						if(in_val_1 == 1) {
							serv_slowmv_val_buffer = in_val_0;
							LOOP_counter = 0;
						}
						send_ack();									
					}
				break;
				default:
					if(stri == '\n') {	// ACK -1 .. fail	
						send_ack();
					}
				break;
			}			
		}	
		if(!init_ok) LOOP_counter = 1;
		break;
		
	////////////////////// Servo slow move /////////////////////////

	case 4:		
		if(servoList[0][1] != 1) {			
			if(servoList[0][0] != serv_slowmv_val_buffer) {
				if((micros() - serv_slowmv_timer_buffer) > pow(servoList[0][1], 2) ) {
					
					if(servoList[0][0] > serv_slowmv_val_buffer) {					
						serv_slowmv_val_buffer += 1;
					}else{				
						serv_slowmv_val_buffer -= 1;						
					}	
					
					//slow_mv_servo();
					serv_slowmv_timer_buffer = micros();
				}
			}else{
				serv_in_pos_ack();
			}			
		}
		if(!align_acc) LOOP_counter = 0;
		break;
	case 5:
		if(round(Accel_pitch) != 0 || round(Accel_roll) != 0 )	{
			align_accel();
		}else{
			align_acc = false;
			addTo_outString("CA" + (String)Cal_Accel_pitch + "P" + (String)Cal_Accel_roll + "R" ) ;
		}
		LOOP_counter = 0;
		break;
	////////////////////// Init /////////////////////////
	case 6:
		addTo_outString("INITMIN" + (String)round(serv_min_angle) + "INITMAX"+ (String)round(serv_max_angle) + "HDG" + (String)Heading);
		LOOP_counter = 1;
		break;
	}
}
