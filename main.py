from server import ServerCow
import multiprocessing, sys

def create_server(name, port):
	s = ServerCow(name, port)

if __name__ == '__main__':
	ports = [16540, 16541, 16542, 16543, 16544]
	names = ['Alford', 'Ball','Hamilton','Holiday','Welsh']
	srv_directory = {'Alford': 16540, 'Ball': 16541,'Hamilton':16542,'Holiday': 16543,'Welsh': 16544}

	# starts all the processes
	if len(sys.argv) == 1:
		processes = [multiprocessing.Process(target=create_server, args=(n, p,)) for (n, p) in zip(names, ports)]
	# starts one of the processes
	elif len(sys.argv) == 2:
		server = sys.argv[1]
		processes = [multiprocessing.Process(target=create_server, args=(server, srv_directory[server],))]
	else:
		sys.exit("Invalid number of args")

	for p in processes:
		p.start()
	for p in processes:
		p.join()