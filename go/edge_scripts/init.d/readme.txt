Instructions for use:

1. Copy command-adapter.etc.default file into /etc/default, name the file "command-adapter"
2. Modify the values of the variables defined in the /etc/default/command-adapter file to match your system
3. Copy command-adapter.etc.initd file into /etc/init.d, name the file "command-adapter"
4. From a terminal prompt, execute the following commands:
	3a. chmod 755 /etc/init.d/command-adapter
	3b. chown root:root /etc/init.d/command-adapter
	3c. update-rc.d command-adapter defaults 85

If you wish to start the adapter, rather than reboot, issue the following command from a terminal prompt:

	/etc/init.d/command-adapter start