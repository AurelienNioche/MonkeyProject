rpi_ip_address=10.24.12.48
scp raspi/grip_manager.py pi@${rpi_ip_address}:/home/pi/grip_manager.py
scp raspi/pump_manager.py pi@${rpi_ip_address}:/home/pi/pump_manager.py
scp raspi/pump_manager.service pi@${rpi_ip_address}:/home/pi/pump_manager.service
scp raspi/grip_manager.service pi@${rpi_ip_address}:/home/pi/grip_manager.service
scp raspi/create_services.sh pi@${rpi_ip_address}:/home/pi/create_services.sh
scp raspi/test_services.sh pi@${rpi_ip_address}:/home/pi/test_services.sh