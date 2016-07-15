#calling script
import os


print "1:Port blocker\n2:L2 firewall\n",
foo = raw_input()

if foo=='1':
	print "Enter tcp port to block:\n",
	port = raw_input()
	print "t"
	os.system(" python pox.py log.level --DEBUG forwarding.l2_learning blocker_new --ports="+port)

elif foo=='2':
	print "Enter comma seperated mac addresses to blacklist\n",
	macadds = raw_input()
	os.system(" python pox.py log.level --DEBUG forwarding.l2_firewall_new --blacklist="+macadds)


else:
	print "existing"
	exit(0)



