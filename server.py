import asyncio
import time, re, json
import multiprocessing

class ServerCow:
	def __init__(self, name, port):
		log = open("{}-log.txt".format(name), "w")
		log.write("Starting server {} on port {}\n".format(name, port))
		log.close()

		self.name = name
		self.port = port
		# clientID: [server, difftimestamp, coordinates, posixtime]
		self.messages = {}
		self.msgDirectory = {"IAMAT": self.handle_IAMAT,  "WHATSAT": self.handle_WHATSAT, "AT": self.handle_AT}
		self.srvDirectory = {"Alford": [("Hamilton", 16542), ("Welsh", 16544)], 
							"Ball": [("Holiday", 16543), ("Welsh", 16544)], 
							"Hamilton": [("Holiday", 16543)],
							"Welsh": [("Alford", 16540), ("Ball", 16541)],
							"Holiday": [("Ball", 16541), ("Hamilton", 16542)]
		}


		loop = asyncio.get_event_loop()
		coro = asyncio.start_server(self.handle_connection, '127.0.0.1', port, loop=loop)
		server = loop.run_until_complete(coro)
		loop.run_forever()

	@asyncio.coroutine
	def propagate(self, msg, name, port, loop):
		try:
			reader, writer = yield from asyncio.open_connection('127.0.0.1', port=port, loop=loop)
			writer.write(msg)
			writer.close()

			# log that intended propagation succeeded
			with open("{}-log.txt".format(self.name), "a") as log:
				log.write("***{} propogated place location {} to {}\n".format(self.name, msg, name))
		except Exception:
			# log that intended propagation failed
			with open("{}-log.txt".format(self.name), "a") as log:
				log.write("***{} could not propagate place location to {}\n".format(self.name, name))

	# TODO: fix connection error here
	@asyncio.coroutine
	def get_location_info(self, info, loop, cwriter, msg):

		API_KEY = 'AIzaSyANIjgTHYogHJIt4N9e3_QV714vImOtN00'
		client = info[1]
		lat, long = re.match(r'([\+\-]?\d*\.?\d*)([\+\-]?\d*\.?\d*)', self.messages[client][2]).group(1, 2)
		radius = int(info[2]) * 1000
		upper_bound = int(info[3])
		directory = '/maps/api/place/nearbysearch/json?location={},{}&radius={}&key={}'.format(lat, long, radius, API_KEY)

		HTTP_req = 'GET {} HTTP/1.1\r\nHost: maps.googleapis.com\r\nConnection: close\r\n\r\n'.format(directory).encode('utf-8')
		reader, writer = yield from asyncio.open_connection('maps.googleapis.com', port=443, loop=loop, ssl=True)
		writer.write(HTTP_req)

		# log that server sent a HTTP request
		with open("{}-log.txt".format(self.name), "a") as log:
			log.write("***{} sent a HTTP request to the Google API: {}\n".format(self.name, HTTP_req))

		json_msg = ""
		# gets rid of header
		while True:
			header = yield from reader.readline()
			if not header or header == b'\r\n':
				break

		while True:
			d = yield from reader.readline()
			if not d:
				break
			json_msg += d.decode('utf-8')

		json_dict = json.loads(json_msg)
		json_dict["results"] = json_dict["results"][:upper_bound]
		json_msg = json.dumps(json_dict, indent=2, sort_keys=True)

		writer.close()
		response = "{}{}".format(msg, json_msg).encode('utf-8')
		cwriter.write(response)
		cwriter.close()

		# log that server sent a response to WHATSAT
		with open("{}-log.txt".format(self.name), "a") as log:
			log.write("***{} sent a WHATSAT response back to client\n".format(self.name))
		
	def relay_messages(self, msg):
		if (self.name in self.srvDirectory):
			for (name, port) in self.srvDirectory[self.name]:
				loop = asyncio.get_event_loop()
				asyncio.ensure_future(self.propagate(msg, name, port, loop))

	def handle_IAMAT(self, writer, info, date):
		# check if it's a valid string
		orig = " ".join(info).strip()
		m = re.match(r'^IAMAT (\S+) ([\+\-]\d+\.\d+)([\+\-]\d+\.\d+) (\d+\.\d+)$', orig, re.M|re.I|re.S)
		if m == None:
			# no match
			raise ValueError("Invalid IAMAT command string: " + orig)

		# check if it's a valid timestamp
		if (info[1] in self.messages and float(self.messages[info[1]][3]) > float(info[3])):
			i = self.messages[info[1]]
			msg = 'AT {} {} {} {} {}\n'.format(i[0],
												i[1],
												info[1],
												i[2],
												i[3]).encode('utf-8')
			writer.write(msg)
			writer.close()
			return

		timestamp =  "+" + str(date - float(info[3])) if (date - float(info[3])) >= 0 else str(date - float(info[3])) 
		self.messages[info[1]] = [self.name, timestamp, info[2], info[3]]
		msg = 'AT {} {} {} {} {}\n'.format(self.name, timestamp, info[1], info[2], info[3]).encode('utf-8')

		# log that server received IAMAT msg
		with open("{}-log.txt".format(self.name), "a") as log:
			log.write("***{} received an IAMAT message: {} {} {} {}\n".format(self.name, info[0], info[1], info[2], info[3]))

		writer.write(msg)
		writer.close()
		# log that server wrote AT msg to client
		with open("{}-log.txt".format(self.name), "a") as log:
			log.write("***{} sent an AT message to client ({}): {}\n".format(self.name,info[1], msg))

		self.relay_messages(msg)

	def handle_WHATSAT(self, writer, info, date):
		# check if it's a valid string
		orig = " ".join(info).strip()
		m = re.match(r'^WHATSAT (\S+) (\d+) (\d+)$', orig, re.M|re.I|re.S)
		if m == None:
			raise ValueError('Invalid WHATSAT command string: ' + orig)
		if int(info[2]) > 50 or int(info[2]) < 0 or int(info[3]) > 20 or int(info[3]) < 0:
			raise ValueError('Invalid radius value.')
		msg = 'AT {} {} {} {} {}\n'.format(self.messages[info[1]][0],
						 					self.messages[info[1]][1],
						 					info[1],
											self.messages[info[1]][2],
											self.messages[info[1]][3])

		# log that server received WHATSAT msg
		with open("{}-log.txt".format(self.name), "a") as log:
			log.write("***{} received a WHATSAT message from {}: {} {} {} {}\n".format(self.name, info[1] ,info[0], info[1], info[2], info[3]))

		loop = asyncio.get_event_loop()
		asyncio.ensure_future(self.get_location_info(info, loop, writer, msg))

	def handle_AT(self, writer, info, date):
		if info[3] in self.messages and self.messages[info[3]] == [info[1], info[2], info[4], info[5]]:
			pass
		elif info[3] in self.messages and float(self.messages[info[3]][3]) > float(info[5]):
			pass
		else:
			self.messages[info[3]] = [info[1], info[2], info[4], info[5]]
			msg = '{} {} {} {} {} {}\n'.format(info[0], info[1], info[2], info[3], info[4], info[5]).encode('utf-8')

			# logs that server received AT message
			with open("{}-log.txt".format(self.name), "a") as log:
				log.write("***{} received an AT message: {}\n".format(self.name, msg))

			self.relay_messages(msg)
			writer.close()


# write regular expressions to reject invalid inputs

	@asyncio.coroutine
	def handle_connection(self, reader, writer):
		date = time.time()
		addr = writer.get_extra_info('peername')
		data = (yield from reader.readline()).decode("utf-8")
		info = data.split()

		try:
			self.msgDirectory[info[0]](writer, info, date)
		except Exception:
			writer.write('? {}'.format(data).encode('utf-8'))

			# log that server received an invalid message
			with open("{}-log.txt".format(self.name), "a") as log:
				log.write("***{} received an invalid message: {}\n".format(self.name, data))

			yield from writer.drain()
			writer.close()
