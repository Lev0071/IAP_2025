
#!/usr/bin/env python3
import flask 
import smbus2 as smbus
import time
import sys
import threading
#import pygame.mixer
#import RPi.GPIO as GPIO
import gpiod
import random
import argparse
import os
import threading
import sys
from threading import Lock


I2Cbus = smbus.SMBus(1)
beepfile = '/server/beep-02.wav'
Solenoid4Pin = 8
Solenoid3Pin = 10
Solenoid2Pin = 12
Solenoid1Pin = 16
HELLO_SIGNAL = 0xFF
Solenoid4Line = 14
Solenoid3Line = 15
Solenoid2Line = 18
Solenoid1Line = 23

SolSec = 8
IntervalTime= 13

RANDOM = 1
COOP = 2
TOGGLE = 3

OFF = 0
SOLID = 1
BlINK = 2
ROTATE = 3

SOUND_OFF = 0
SOUND_2500 = 1
SOUND_5000 = 2
SOUND_7500 = 3

SOUNDWITHLED = 0

currentGameThread = None
currentGameMode = 0

should_continue = True
slave_data_lock = Lock()
game_active = False  # Global flag to indicate coop game mode
coop_game_thread = None  # Global variable for coop game thread
buttons = [] # empty list of buttons to start with
chosen_button = None
hose_state = False
hose_over = False

#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(Solenoid1Pin, GPIO.OUT)
#GPIO.output(Solenoid1Pin, GPIO.HIGH)

#GPIO.setup(Solenoid2Pin, GPIO.OUT)
#GPIO.output(Solenoid2Pin, GPIO.HIGH)

I2C_addresses = range ( 0x8, 0x19 )
app = flask.Flask(__name__)
"""
INITALISE ALL REQUIRED GLOBAL INFORMATION
"""


"""
BEGINNING OF THE ELECTRONICS CODE - CODE THAT DOESN'T REQUIRE FLASK ROUTING/CALLING
"""

class Button:
    
    def __init__ ( self, address, bus ):
        self.status= True # is the button contactable or not
        self.address = address # I2C address of this button
        self.LEDstatus = 0 # LED is on or off
        self.LEDtype = ROTATE # type of light, 0 = normal, 1 = blink, 2 = circle pattern
        self.soundfreq = SOUND_2500
        self.soundstatus = 0
        self.buttonstatus = False # button pressed or unpressed
        self.bus = bus
        self.override = False # button has been overridden to a fixed value temporarily (hopefully)
        self.update = True # LED data needs updating
        self.state = 0 # Variable I'm adding for interaction with the web server.

        
        
    def __eq__ (self, o ):
        if self.address == o.address:
            return True
        else:
            return False
        

    def checkbuttonstatus ( self ):
        
        if not self.override: # don't check if override is set        
            try:
                current_button_state = self.bus.read_byte(self.address)
                if current_button_state != self.buttonstatus:
                    self.buttonstatus = current_button_state

                    if current_button_state == 1:  # Button is pressed
                        print(f"pressed {hex(self.address)}")
                    else:
                        print(f"unpressed {hex(self.address)}")
                        
            except Exception as e:
                if self.address is not None:
                    self.status = False # can't contact this button, mark for removal
                    print(f"Error reading button state from Arduino at address {hex(self.address)}: {e}")
                else:
                    print(f"Error: {e}")
    
    
    def press ( self, t ):
        # simulate a button press for t seconds
        self.override = True
        self.buttonstatus = 1
        print (f"pressed {hex(self.address)}")
        time.sleep ( t )
        self.override = False   
                    

    def setLED ( self, onoff, blinktype ):
        self.LEDstatus = onoff
        self.LEDtype = blinktype
        if SOUNDWITHLED == 1:
            self.soundstatus = onoff
        self.update = True
        
        
    def updateLED ( self ):
        try:
            self.bus.write_byte ( self.address, (self.LEDstatus * self.LEDtype) + 4 * (self.soundstatus * self.soundfreq))
        except Exception as e:
            print (f"Error writing LED state to Button at address {hex(self.address)}: {e}")
            self.status = False # mark for removal
        
        
    def toggleLED ( self ):
        if self.LEDstatus == 0:
            self.LEDstatus = 1
        else:
            self.LEDstatus = 0
        
        if SOUNDWITHLED == 1:
            self.soundstatus = self.LEDstatus
            
        self.update = True


def list_buttons ():

    for b in buttons:
        print(f"{b.address} {b.LEDstatus} {b.LEDtype} {b.buttonstatus}")
    
    print(f"Hose state: {hose_state}")
    print(f"Hose override: {hose_over}")


# def suppress_pygame_message(): #function to clear the pygame premble. Replace function call with pygame.mixer.init() if issues persist
#     sys.stdout = open(os.devnull, 'w')
#     pygame.mixer.init()
#     sys.stdout = sys.__stdout__

# Arduino control functions
def is_arduino_on(address, bus):
    try:
        bus.write_byte(address, HELLO_SIGNAL)
        time.sleep(0.05)
        data = bus.read_byte(address)
        return True
    except Exception as e:
        #print(f"Error on address {address}: {e}")
        return False


# def buzz():
#     #pygame.mixer.init()
#     suppress_pygame_message()
#     beep_sound = pygame.mixer.Sound(beepfile)
#     beep_sound.play()

def SolenoidSpray(line):
    global hose_state
    hose_state = True
    time.sleep(SolSec)
    hose_state = False
    
def button_loop():
    global should_continue, buttons

    while should_continue:
        
        for b in buttons:
            if b.update: # only update if there is a reason to
                b.update = False
                b.updateLED()
            time.sleep ( 0.05 )
            b.checkbuttonstatus()
            time.sleep ( 0.05 )
            if b.status== False:
                # something went wrong with the read, button is now OFF, so remove it from list
                buttons.remove(b)
                
        # now check hose
        if hose_state or hose_over:
            hoseLine.set_value ( Solenoid1Line, gpiod.line.Value.INACTIVE )
            # GPIO.output(Solenoid1Pin, GPIO.LOW)
        else:
            hoseLine.set_value ( Solenoid1Line, gpiod.line.Value.ACTIVE )
            # GPIO.output(Solenoid1Pin. GPIO.HIGH)
            

#APP-ROUTE WRITTEN
def reset_arduino():
    global powerLine, server_data

    print("Turning off power")
    sys.stdout.flush()
#    GPIO.output(Solenoid2Pin, GPIO.HIGH)
    powerLine.set_value ( Solenoid2Line, gpiod.line.Value.ACTIVE )
    time.sleep(2)
    print("Turning on power")
    sys.stdout.flush()
#    GPIO.output(Solenoid2Pin, GPIO.LOW)
    server_data["logging_message"]="reset_arduno function executed, calling from line 217"
    
    powerLine.set_value ( Solenoid2Line, gpiod.line.Value.INACTIVE)
    perform_scan()
    return  flask.render_template('homepage_iteration_three.html',serverdata=server_data)
    
def perform_scan():
    global buttons, currentGameThread, currentGameMode, game_active

    if currentGameThread != None:
        print("Stopping current game")
        server_data['game_status']=False
        game_active = False
        currentGameThread.join()
        currentGameThread = None
        currentGameMode = 0

    server_data['buttons']=[0,0,0,0]

    buttons = [] # reset all buttons
    detected_addresses = []
    print(I2C_addresses)
    #Get some index to keep the tracking between internal data and server data consistent
    index=0
    for address in I2C_addresses:
        print(address)
        if is_arduino_on(address, I2Cbus):
            b = Button(address, I2Cbus)
            print("Detected address at" + str(address))
            b.update = True
            b.state=1
            buttons.append(b)
            server_data['buttons'][index]=b
            detected_addresses.append ( address )
            index+=1
            print(address)
            

    # Print detected addresses in the desired format, only once after scanning
    if detected_addresses:
        print("scan", ','.join(map(str, detected_addresses)))
    else:
        print("scan")  # Print "scan" alone if no addresses are detected
    sys.stdout.flush()

                
def process_led_command(line):
    global buttons, chosen_button, currentGameMode
    address = line
    
    print ("Button command")
    
    for b in buttons:
        if b.address == address:
            print (f"Address: {address}")
            print ( f"Mode: {currentGameMode}")
            if currentGameMode == RANDOM:
                print (f"Changing chosen light to {address}")
                chosen_button.setLED ( 0,3 )
                chosen_button = b
                b.setLED ( 1, 3 )
                break
            elif currentGameMode == COOP:
                pass
            else:
                b.toggleLED()


def update_hose_time(line):
    global SolSec, hose_over
    parts = line.split()  # Split the command into parts
    if len(parts) == 2:
        if parts[1] == "over_on":
            print ("Hose override on")
            hose_over = True
        elif parts[1] == "over_off":
            print ("Hose override off")
            hose_over = False
        else:
            try:
                SolSec = int(parts[1])  # Convert the second part to integer
                print(f"Hose time updated to {SolSec} seconds")
            except ValueError:
                print("Invalid hose time value")
    else:
        print("Invalid hose_time command format")

def start_random_game(line):
    global random_game_thread, IntervalTime, currentGameThread, game_active, currentGameMode, server_data
    
    if currentGameThread != None:
        print ("Game is already running,let's stop it")
        game_active = False ;
        currentGameThread.join()
        currentGameThread = None
        currentGameMode = 0
        print ("Game stopped")
    
    parts = line.split()  # Split the command into parts
    if len(parts) == 3:
        try:
            IntervalTime = int(parts[2])  # Convert the second part to integer
            # Start random game here
            random_game_thread = threading.Thread(target=random_game)
            currentGameThread = random_game_thread

            currentGameMode = RANDOM
            server_data['game_status']=True
            random_game_thread.start()

        except ValueError:
            print("Invalid Interval time")
    else:
        print("Invalid Interval Time format")
        
        
def stop_random_game ():
    global currentGameThread, game_active, currentGameMode, chosen_button

    
    if currentGameThread != None:
        server_data['game_status']=False
        print ("Stopping current game" )
        game_active = False ;
        currentGameThread.join()
        currentGameThread = None
        currentGameMode = 0
    else:
        print ("No current game active!")


def buttonspressed ( buttons ):
    
    count = 0
    
    for b in buttons:
        if b.buttonstatus:
            count = count + 1
            
    return count


def random_game():
    global buttons, should_continue, IntervalTime, currentGameThread, game_active, currentGameMode, chosen_button, server_data

    game_active = True
    while should_continue and game_active:

        if len(buttons) > 0:

            # turn all lights off            
            for b in buttons:
                b.setLED ( 0, 3 )

            if buttonspressed ( buttons ) > 0:
                print (f"Waiting for all buttons to be unpressed")
                while buttonspressed ( buttons ) > 0:
                    time.sleep ( 0.1 )

            chosen_button = random.choice(buttons)
            chosen_button.setLED ( 1, 3 )
            chosen_button.state=2
#Visually display the correct button
            index=0

            print(f"Random game: LED turned on for Arduino at {hex(chosen_button.address)}")

            # Wait for button press in check_button_press function
        
            # now wait for that button to be pressed
            
            while buttonspressed ( buttons ) == 0 and should_continue and game_active:
                time.sleep(0.01)

            # After button press
            if chosen_button.buttonstatus == 1:
                print(f"Random game: correct button pressed, moving to next after {IntervalTime} seconds")
                server_data['logging_message']="Correct Button Pressed"
                chosen_button.setLED ( 0, 3 ) # turn LED off
                chosen_button.state=1
                # activate hose and sound
                solenoid_thread = threading.Thread(target=SolenoidSpray, args=(hoseLine,))
                solenoid_thread.start()
                time.sleep(IntervalTime)
            elif should_continue and game_active:
                chosen_button.state=1
                print(f"Random game: incorrect button pressed, resetting game to start again")
                server_data['logging_message']="Wrong button pressed"
                for b in buttons:
                    b.setLED( 0, 3)
                time.sleep ( 5 ) # wait 5 seconds to start again
            else:
                print(f"Random game is over")
           

        else:
            print("No connected Arduinos left for random game")
            break
            
    for b in buttons:
        b.setLED( 0, 3 )
    
        
    currentGameThread = None
    currentGameMode = 0


def coop_game(num_buttons, timeout_timer):
    global buttons, should_continue, game_active, currentGameThread, currentGameMode
    game_active = True
    chosen_buttons = []
    pressed_buttons = []
    timer_started = False
    start_time = 0

    while should_continue and game_active:

        if len(buttons) < num_buttons:
                print(f"Not enough available Arduinos for {num_buttons}-button game")
                game_active = False
                currentGameThread= None
                return
    
        while len(chosen_buttons) < num_buttons:
            found = False
            chosen_button = random.choice(buttons)
            for b in chosen_buttons:
                if b == chosen_button:
                    found = True
            if not found:
                chosen_buttons.append ( chosen_button )
                chosen_button.setLED ( 1, 3 )
        
    
        print("Cooperative game started, waiting for button presses...")
        
        count = 0
        while should_continue and game_active and count < num_buttons:
    
            count = 0
            for b in chosen_buttons:
                if b.buttonstatus == True:
                    b.setLED( 0, 3 )
                    count = count + 1
                else:
                    b.setLED( 1, 3 )

            time.sleep(0.1)


        if count == num_buttons:
            print("All buttons pressed, activating solenoid")
            SolenoidSpray(hoseLine)
            # delay for a few seconds to start again
            time.sleep ( IntervalTime )
       

    for b in buttons:
        b.setLED( 0, 3 )
        
    currentGameThread = None
    currentGameMode = 0


def press_button ( line ):
    global buttons
    
    parts = line.split()
    if len(parts) > 1:
        try:
            address = int ( parts[1],16)
            if len(parts)>2:
                t = int( parts[2] )
            else:
                t = 1
                
            for b in buttons:
                if b.address == address:
                    print(f"Pressing button at {address} for {t} seconds")
                    b.press(t)
        except ValueError:
            print ( "Invalid address or time")
                    


def process_commands():
    global should_continue, game_active, currentGameThread, currentGameMode
    while should_continue:
        for line in sys.stdin:
            line = line.strip()
            if line == "reset_arduino":
                reset_arduino()
            elif line == "scan":
                perform_scan()
            elif line == "list":
                list_buttons()
            elif line.startswith("0x"):
                process_led_command(line)
            elif line.startswith("press"):
                press_button ( line )
            elif line.startswith("hose_time"):
                update_hose_time(line)
            elif line.startswith("random"):
                start_random_game(line)
            elif line == "stop random":
                stop_random_game()
            elif line.startswith("coop"):
                parts = line.split()
                if len(parts) == 3:
                    try:
                        num_buttons = int(parts[1])
                        timeout_timer = int(parts[2])
                        if currentGameThread is not None:
                            print("Stopping current Co-Op game")
                            game_active = False
                            currentGameThread.join()  # Wait for the current game to stop
                            currentGameThread= None

                        print("Starting new Co-Op game")
                        game_active = True
                        currentGameThread = threading.Thread(target=coop_game, args=(num_buttons,timeout_timer,))
                        currentGameMode = COOP
                        currentGameThread.start()
                    except ValueError:
                        print("Invalid number of buttons for coop game")
                else:
                    print("Invalid coop command format")

            elif line == "stop coop":
                if currentGameThread is not None:
                    print("Stopping Co-Op game")
                    game_active = False
                    currentGameThread.join()  # Wait for the game to stop
                else:
                    print("No Co-Op game is currently running")
            else:
                print("Unknown Command")




def main(args):
    global should_continue, currentGameThread, powerLine, hoseLine
    
    #initialise random seed
    random.seed()
    print ("Initialised random seed")
    print ("Setting up GPIO")
    if gpiod.is_gpiochip_device ( "/dev/gpiochip4" ):
        # this is a pi5, so use this
        chiptype = "/dev/gpiochip4"
    else:
        # older pi
        chiptype = "/dev/gpiochip0"
        
    chip = gpiod.Chip(chiptype)
    powerLine = chip.request_lines ( consumer="dolphingame", config={Solenoid2Line: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT, output_value=gpiod.line.Value.ACTIVE)},)
    #powerLine.request(consumer="power", type=gpiod.LINE_REQ_DIR_OUT)

    hoseLine = chip.request_lines ( consumer="dolphingame", config={Solenoid1Line: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT, output_value=gpiod.line.Value.ACTIVE)},)
    
    # GPIO.output(Solenoid2Pin, GPIO.LOW) #turn on power to the board
    hoseLine.set_value ( Solenoid1Line, gpiod.line.Value.ACTIVE ) # turn hose OFF for now
    print ("Turning on arduinos..")
    powerLine.set_value ( Solenoid2Line, gpiod.line.Value.INACTIVE  )
    time.sleep ( 5 ) # give time for arduinos to power up

    print ("Boards turned on")

    perform_scan()
    print ( "Scan for devices done")

    currentGameThread = None

    button_thread = threading.Thread(target=button_loop, daemon=True)
    command_thread = threading.Thread(target=process_commands, daemon=True)

    button_thread.start()
    command_thread.start()
    
    #start_random_game( f"random {IntervalTime} {IntervalTime}")

    
    try:
        # Here, you can add any main loop logic if needed.
         app.run(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
    except Exception as e:
        print("EXCEPTION:")
        print(e)

    # Cleanup code after main loop
    # GPIO.output(Solenoid2Pin, GPIO.HIGH) # turn all arduinos OFF
    powerLine.set_value ( Solenoid2Line, gpiod.line.Value.ACTIVE )
        

    sys.exit()




server_data={
            #Definition of button states, 0 means nothing conected. 1 means connected. 2 means chosen in game. More to come?

			 'logging_message':"",
             'buttons':[],
			 "hose_override":False,
			 "game_status":False,
			 "game_time":8,
			 "hose_time":8,
			 "coop_button_time":5,
			 "coop_game_status":False}
             

@app.route('/')
def index():
    global server_data
    return flask.render_template('homepage_iteration_three.html',serverdata=server_data)
    
@app.route('/reset_buttons_pressed')
def reset_buttons_flask_route():
    global server_data
    server_data['logging_message']='Resetting'


    #time.sleep(4)
    #Reseting the arduino is tied to a user input so return it with function
    return reset_arduino()
@app.route('/shutdown_system')
def shutdown_system_flask_route():
    global server_data
	#Write code for shutting things down <- I don't think this was represented in the original code so it's prbably in node-red connected directly to the pi
    os.system('sudo shutdown --r now')
    return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/reboot_rasberry_pi')
def reboot_rasberry_pi_flask_route():
    global server_data
	#Write code for shutting down the pi <- Probably the same thing as shutdown_system_flask_route
    server_data['logging_message']="Reboot resberry pi button pushed"
    os.system('sudo reboot')
    return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/restart_program')
def restart_program_flask_route():
	#Write code for restarting the program <- Probably the same thing as reboot and shutdown flask routes
	global server_data
	server_data['logging_message']="Restart program button pushed"
    
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/change_hose_time/',methods=['POST'])
def change_hose_time_flask_route():
	global server_data	
	global SolSec
	new_hose_time=flask.request.form.get('hose_time')
	server_data['hose_time']=new_hose_time
	server_data['logging_message']="New hose time is " + str(new_hose_time) + " Seconds"
	SolSec=new_hose_time
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)


@app.route('/set_new_interval_time/<int:new_interval_time>',methods=['POST'])
def set_new_interval_time(new_interval_time):
	global server_data
	global IntervalTime
	IntervalTime=new_interval_time
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/start_random_game')
def start_random_game_flask_route():
    global server_data, buttons
    for button in buttons:
        button.state=1
    start_random_game(f"random {server_data['game_time']} {server_data['game_time']}")
    server_data['logging_message']="Starting random game"
    server_data['game_status']=True
    return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/stop_random_game')
def stop_random_game_flask_route():
    global server_data, buttons
    for button in buttons:
        button.state=1
    stop_random_game()
    server_data['logging_message']="Stopping random game"
    server_data['game_status']=False
    server_data['logging_message']="Stopping random game"
    return flask.render_template('homepage_iteration_three.html', serverdata=server_data)    

@app.route('/change_coop_button_time',methods=['POST'])
def change_coop_button_time():
	global server_data	
	#global SolSec
	new_button_time=flask.request.form.get('coop_button_time')
	server_data['coop_button_time']=new_button_time
	server_data['logging_message']="New co-op button time time is " + str(new_button_time) + " Seconds"
	#SolSec=new_button_time
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)
    

@app.route('/start_coop_game')
def start_coop_game():
	global server_data
	server_data['logging_message']="Start coop random game"
	server_data['coop_game_status']=True
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/stop_coop_game')
def stop_coop_game():
	global server_data
	server_data['logging_message']="Stop coop random game"
	server_data['coop_game_status']=False
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)

@app.route('/scan_button_pressed')
def scan_button_pressed_flask():
	global server_data	
    #Perform scan isn't tied to a route so we don't need to return a function.
	perform_scan()
	return flask.render_template('homepage_iteration_three.html',serverdata=server_data)
    
    
#This occurs when a user clicks a button on the user interface. General idea is that button_id acts as an index that points to the same position as the internal button array aswell as th
@app.route('/button_click_server/<int:button_id>',methods=['POST'])
def button_click_server(button_id):
    global server_data, buttons
    
    #Placeholder code to show the route is called.

    server_data['logging_message']="button "+str(button_id+1) + " Pressed"
    
    #Check to ensure that the game is running, if it is do nothing. If it isn't then change the selected button and reload the screen. See if Brayden's implementation of this can be found.

    #Case 1 - Random Game - change the selected button to the new button
    if server_data['game_status']==True:
        try:
            for button in buttons:
                if button.state==2:
                    button.state=1
                buttons[button_id].state=2
                process_led_command(buttons[button_id].address)
            server_data['buttons'][button_id].state=2
            process_led_command(buttons[button_id].address)
        except:
            pass
        
    else:
        try:
            #Case 2 - No Game - Toggle the LED on or off
            if buttons[button_id].state==1:
                buttons[button_id].state=2
            else:
                buttons[button_id].state=1
            process_led_command(buttons[button_id].address)
        except:
            pass
    return flask.render_template('homepage_iteration_three.html',serverdata=server_data)
    
    
    
    
    
@app.route('/toggle_override',methods=['POST'])
def toggle_override():
    global server_data, hose_over 
    hose_over= not hose_over 
    server_data['logging_message']="Hose override toggeled" 
    server_data['hose_override']=not server_data['hose_override']
    return flask.render_template('homepage_iteration_three.html',serverdata=server_data)


@app.route('/stream')
def stream_logging_data():
    def generate():
        while True:
            time.sleep(1)
            yield f"data: Latest logging message: " + server_data['logging_message'] +  "\n\n"
    return flask.Response(generate(),mimetype="text/event-stream")



@app.route('/update_button_colour/<button_id>', methods=['POST','GET'])
def update_colour(button_id):
    global server_data
    button_number=int(button_id[len(button_id)-1])-1
    try:
        if server_data['buttons'][button_number].state==1:
            return flask.jsonify(new_color="green")
        elif server_data['buttons'][button_number].state==2:
            return flask.jsonify(new_color="yellow")
    except:
        return flask.jsonify(new_color="red")




@app.route('/start_simulate_press/<button_id>', methods=['POST'])
def start_stimulating_button(button_id):
    global button_status, buttons
	
    button_number=int(button_id[len(button_id)-1])-1
    
    print(buttons)

    buttons[button_number].press(3)
    
    print("Button status updated to:")  # For debugging purposes
    return "Button status is now: "

@app.route('/stop_simulate_press/<button_id>', methods=['POST'])
def stop_simulating_button(button_id):
    global button_status, buttons
	
    button_number=int(button_id[len(button_id)-1])-1
    print(buttons[button_number].address)

    
    print("Button status updated to:")  # For debugging purposes
    return "Button status is now: "



if __name__ == '__main__':
		#Initalise the provided code for electronics


	#Initalise the flask server code.
    main(sys.argv)
    
