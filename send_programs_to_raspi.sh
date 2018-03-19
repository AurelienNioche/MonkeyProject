rpi_ip_address=169.254.162.142

scp raspi/raspi_manager.py pi@${rpi_ip_address}:/home/pi/raspi_manager.py

scp raspi/raspi_manager.service pi@${rpi_ip_address}:/home/pi/raspi_manager.service

scp raspi/test_services.sh pi@${rpi_ip_address}:/home/pi/test_service.sh