#  !usr/bin/env python
import time
from gpiozero import CPUTemperature
from influxdb import InfluxDBClient
from typing import List, Dict
import speedtest
import logging
from threading import Thread

format= '%(asctime)s %(levelname)s  %(message)s'
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H%M%S")
cpu = CPUTemperature()
network = speedtest.Speedtest()
network.get_best_server()
db = InfluxDBClient('localhost', database="test")


def _write(db:InfluxDBClient, measurement:str, point:Dict):
	data=[{
		"measurement":measurement,
		"fields":point
		}
		]
	db.write_points(data)
	logging.info(f"{measurement} write succeeded")

def _temps(db:InfluxDBClient, cpu:object)->float:
	try:
		temp={"temp":cpu.temperature}
		_write(db=db, measurement="temps",point=temp)
	except Exception as e:
		logging.info(f"Temperature check failed with exception:{e}")

def _network(db:InfluxDBClient, network:object, threads:int):
	try:
		network.download(threads=threads)
		speed = round(network.results.dict().get('download')/1024**2,2)
		ping = network.results.dict()['ping']
		logging.info(f"Speed:{speed}, ping:{ping}")
		point= {"speed":speed,"ping":ping}
		_write(db=db,measurement="network",point=point)
	except Exception as e:
		logging.info(f"Network speed-test failed with reason {e}")

def temppr(frequency:int=10):
	while True:
		_temps(db=db,cpu=cpu)
		time.sleep(frequency)

def netwpr(frequency:int, threads:int=None):
	while True:
		_network(db=db, network=network, threads=threads)
		time.sleep(frequency)

if __name__ == "__main__":
	temps = Thread(target=temppr, args=(60,))
	netw = Thread(target=netwpr, args=(300,))
	temps.start()
	netw.start()
