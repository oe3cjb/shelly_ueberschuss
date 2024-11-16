# Ueberschussladen V1.1
#
# Import some modules
import json, requests, time, datetime, threading
from decimal import Decimal
from flask import Flask, render_template, request

# Variable declaration
device = 'tasmota' #set to 'shelly' if want to use Shelly devices


power_consumption_form = 450
power_consumption = 4500
charge_pwr_keep = 50
state_string = 'empty state_string'
load_pwr_avg = 0
grid_pwr_avg = 0
battery_pwr_avg = 0
pv_pwr_avg = 0
switch_onoff = 0
battery_soc = 0
battery_power_min = 4000
battery_soc_min = 60
battery_soc_full_load = 80
secsavg = 15
switch_mode = 0
switch_mode1 = "SWITCH OFF"
# 0 = Stop, 1 = Auto, 2 = Fixed

url_pv     = 'http://192.168.29.211/solar_api/v1/GetPowerFlowRealtimeData.fcgi'
if device == 'shelly':
   url_shelly = 'http://192.168.29.223/relay/0'           # get switch state Shelly
else:
   url_shelly = 'http://192.168.29.214/cm?cmnd=Power%20' # get switch state Tasmota


def get_pv_data():
	global state_string
	error = True
	while (error):
		try:
			pv_intern = json.loads(requests.get(url_pv).text)
#			time.sleep(5)
		except:
			now = datetime.datetime.now()
			state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " PV IP Error"
			print(state_string)
			time.sleep(15)
		else:
			error = False
	return pv_intern

def get_switch_state():
	global state_string
	error = True
	while (error):
		try:
			switch_intern = json.loads(requests.get(url_shelly).text)
		except:
			now = datetime.datetime.now()
			state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " Shelly IP Error"
			print(state_string)
			time.sleep(15)
		else:
			error = False
	return int(round(Decimal(switch_intern['ison'])))

def set_switch(sw):
	global state_string
	if (sw == True):
		error = True
		while (error):
			try:
				if device == 'shelly':
					requests.post(url_shelly+"?turn=on")
				else:
					requests.post(url_shelly+"On")
			except:
				now = datetime.datetime.now()
				state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " Shelly IP Error"
				print(state_string)
				time.sleep(15)
			else:
				error = False
	else:
		error = True
		while (error):
			try:
				if device == 'shelly':
					requests.post(url_shelly+"?turn=off")
				else:
					requests.post(url_shelly+"Off")
			except:
				now = datetime.datetime.now()
				state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " Shelly IP Error"
				print(state_string)
				time.sleep(15)
			else:
				error = False

def load():
        P_Load = (data['Body']['Data']['Site']['P_Load'])
        if P_Load != None:
                return int(round(Decimal(P_Load)))
        else:
                return 0

def grid():
        P_Grid = (data['Body']['Data']['Site']['P_Grid'])
        if P_Grid != None:
                return int(round(Decimal(P_Grid)))
        else:
                return 0

def battery():
        P_Battery = (data['Body']['Data']['Site']['P_Akku'])
        if P_Battery != None:
                return int(round(Decimal(P_Battery)))
        else:
                return 0

def pv():
        P_PV = (data['Body']['Data']['Site']['P_PV'])
        if P_PV != None:
                return int(round(Decimal(P_PV)))
        else:
                return 0

def soc():
        SOC = (data['Body']['Data']['Inverters']['1']['SOC'])
        if SOC != None:
                return int(SOC)
        else:
                return 0

flask_app = Flask(__name__)

@flask_app.route("/", methods=['GET', 'POST'])
def view_ueberschuss():
	global switch_mode1
	global state_string
	global power_consumption_form
	global switch_mode

	if request.method == 'POST':
		if request.form.get('auto') == 'AUTO':
			switch_mode = 1
			switch_mode1 = "SWITCH SURPLUS"
			power_consumption_form = int(request.form.get('power_consumption'))
		elif  request.form.get('stop') == 'OFF':
			switch_mode = 0
			switch_mode1 = "SWITCH OFF"
		elif  request.form.get('fixed') == 'ON':
			switch_mode = 2
			switch_mode1 = "SWITCH ON"
		else:
			pass # unknown
	elif request.method == 'GET':
		return render_template('index.html', state_string = state_string, switch_mode1 = switch_mode1)

	return render_template('index.html', state_string = state_string, switch_mode1 = switch_mode1)

def run_ueberschuss():
	global switch_onoff
	global state_string
	global data
	global switch_mode1
	global switch_mode
	global power_consumption_form
	global power_consumption

	while True:
		if (switch_mode < 0) or (switch_mode > 2): switch_mode = 0
		while (switch_mode == 0):
			switch_onoff = 0
			set_switch(False)
			now = datetime.datetime.now()
			state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " switched off"
			print(state_string)
			time.sleep(20)

		while (switch_mode == 2):
			switch_onoff = 1
			set_switch(True)
			now = datetime.datetime.now()
			state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " switched on"
			print(state_string)
			time.sleep(20)

		while (switch_mode == 1):
			set_switch(False)
			now = datetime.datetime.now()
			state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " start switch surplus mode"
			print(state_string)
			power_consumption = power_consumption_form
			time.sleep(20)

			while ((switch_onoff == 0) & (switch_mode == 1)):
				set_switch(False)

		#		grid_pwr_avg, load_pwr_avg, battery_pwr_avg = one_minute_avg()
				i = 0
				load_pwr_avg = 0
				grid_pwr_avg = 0
				pv_pwr_avg = 0
				battery_pwr_avg = 0
				while (i<secsavg):
					i += 1
					data = get_pv_data()
					grid_pwr_avg = grid()/secsavg + grid_pwr_avg
					grid_pwr_avg = int(grid_pwr_avg)
					load_pwr_avg = load()/secsavg + load_pwr_avg
					load_pwr_avg = int(load_pwr_avg)
					battery_pwr_avg = battery()/secsavg + battery_pwr_avg
					battery_pwr_avg = int(battery_pwr_avg)
					pv_pwr_avg = pv()/secsavg + pv_pwr_avg
					pv_pwr_avg = int(pv_pwr_avg)
					time.sleep(1)

				battery_soc = soc()

				surplus_power = grid_pwr_avg
				if (battery_soc >= battery_soc_min):
					if (battery_soc >= battery_soc_full_load):
						if (battery_pwr_avg > 100):
							surplus_power = grid_pwr_avg + battery_pwr_avg
						elif (battery_pwr_avg < -1000):
							surplus_power = grid_pwr_avg - 500
					else:
						if (battery_pwr_avg > 100):
							surplus_power = grid_pwr_avg + battery_pwr_avg

					if (surplus_power < (-power_consumption)):
						switch_onoff = 1
						set_switch(True)
						now = datetime.datetime.now()
						state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " EINSCHALTEN"
						print(state_string)
				now = datetime.datetime.now()
				state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " GP:" + str(grid_pwr_avg).rjust(5) + " LP:" + str(load_pwr_avg).rjust(5) + " PV:" + str(pv_pwr_avg).rjust(5) + " BP:" + str(battery_pwr_avg).rjust(5) + " UE:" + str(surplus_power).rjust(5) + " SOC:" + str(battery_soc).rjust(3) + " Act:" + str(switch_onoff)
				print(state_string)

			while ((switch_onoff == 1) & (switch_mode == 1)):
				i = 0
				load_pwr_avg = 0
				grid_pwr_avg = 0
				battery_pwr_avg = 0
				pv_pwr_avg = 0
				while (i<secsavg):
					i += 1
					data = get_pv_data()
					grid_pwr_avg = grid()/secsavg + grid_pwr_avg
					grid_pwr_avg = int(grid_pwr_avg)
					load_pwr_avg = load()/secsavg + load_pwr_avg
					load_pwr_avg = int(load_pwr_avg)
					battery_pwr_avg = battery()/secsavg + battery_pwr_avg
					battery_pwr_avg = int(battery_pwr_avg)
					pv_pwr_avg = pv()/secsavg + pv_pwr_avg
					pv_pwr_avg = int(pv_pwr_avg)
					time.sleep(1)
				battery_soc = soc()

				surplus_power = grid_pwr_avg
				if (battery_soc >= battery_soc_min):
					if (battery_soc >= battery_soc_full_load):
						if (battery_pwr_avg > 100):
							surplus_power = grid_pwr_avg + battery_pwr_avg
						elif (battery_pwr_avg < -1000):
							surplus_power = grid_pwr_avg - 500
					else:
						if (battery_pwr_avg > 100):
							surplus_power = grid_pwr_avg + battery_pwr_avg

				now = datetime.datetime.now()
				state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " GP:" + str(grid_pwr_avg).rjust(5) + " LP:" + str(load_pwr_avg).rjust(5) + " PV:" + str(pv_pwr_avg).rjust(5) + " BP:" + str(battery_pwr_avg).rjust(5) + " UE:" + str(surplus_power).rjust(5) + " SOC:" + str(battery_soc).rjust(3) + " Act:" + str(switch_onoff)
				print(state_string)

				if (surplus_power >= -(power_consumption)):
					if (surplus_power > charge_pwr_keep):
						switch_onoff = 0
						set_switch(False)
						now = datetime.datetime.now()
						state_string = now.strftime("%m/%d/%Y, %H:%M:%S") + " AUSSCHALTEN"
						print(state_string)


if __name__ == '__main__':
    # Start a background thread to control/update the LCD
    # You'll also want to devise a graceful way to shutdown your whole app
    # by providing a kill signal to your threads, for example (beyond the scope of this answer)
    thread_ueberschuss = threading.Thread(target=run_ueberschuss, name='run_ueberschuss')
    thread_ueberschuss.start()
    # Now run the flask web server in the main thread
    # debug=False to avoid Flask printing duplicate info to the console
    flask_app.run(debug=False, host='0.0.0.0', port=5001)
