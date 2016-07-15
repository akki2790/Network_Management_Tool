#
from Tkinter import *
from ttk import *
import os

root=Tk()
canvas=Canvas(root, width=600, height=480)

class SDNgui(object):
	
	def __init__(self):
		self.canvas = canvas
		clicked=False
		self.clicked=clicked

	
	def createButton(self,btn_side,btn_expand,btn_fill,btn_text,btn_cmd):
		self.root=root
		self.mybutton = Button(self.root,text=btn_text,highlightcolor="blue",command=btn_cmd)
		self.mybutton.pack(side=btn_side, expand=btn_expand, fill=btn_fill) 

	
	def onClickBlock(self,event,hostname=""):
		global clicked

		if not if_clicked[hostname]:
			self.canvas.itemconfigure(host_map[hostname], fill='blue')
			block_list.append(hostname)
			if_clicked[hostname]=True

		else:
			self.canvas.itemconfigure(host_map[hostname], fill='black')
			block_list.remove(hostname)
			if_clicked[hostname]=False

			


	def createTopoBlock(self, x1, y1, x2, y2,blockname):
		
		self.currentobject = self.canvas.create_rectangle(x1,y1,x2,y2)
		self.text = self.canvas.create_text(round((x1+x2)/2), round((y1+y2)/2), text=blockname)
		host_map[blockname] = self.text

		#self.canvas.tag_bind(self.currentobject, "<Button-1>", lambda event: self.onClickBlock(self.currentobject,event,blockname))
		self.canvas.tag_bind(self.text, "<Button-1>", lambda event: self.onClickBlock(event,blockname))
	

host_map={}
if_clicked={"h1":False,"h2":False,"h3":False,"h4":False,"h5":False,"h6":False,"h7":False,"h8":False}
block_list=[]
host_to_mac={"h1":"00:00:00:00:00:11",
			"h2":"00:00:00:00:00:12",
			"h3":"00:00:00:00:00:13",
			"h4":"00:00:00:00:00:14",
			"h5":"00:00:00:00:00:15",
			"h6":"00:00:00:00:00:16",
			"h7":"00:00:00:00:00:17",
			"h8":"00:00:00:00:00:18"
			}

#create instance
sdngui=SDNgui()

def topo1():
	sdngui.createTopoBlock(275, 100, 325, 135,"c1")


	switch_x1=100
	switch_x2=150
	host_x1=40
	host_x2=90

	switches=["s1","s2","s3","s4"]
	hosts=["h1","h2","h3","h4","h5","h6","h7","h8"]
	switch_points=[]

#create 4 switches 
	for sw in switches:
		sdngui.createTopoBlock(switch_x1, 200, switch_x2, 235,sw)
		canvas.create_line(round((switch_x1+switch_x2)/2),200,300,135)
		switch_points.append(round((switch_x1+switch_x2)/2))
		switch_points.append(round((switch_x1+switch_x2)/2))
		switch_x1+=125
		switch_x2+=125


#create 8 hosts
	for i in xrange(0,8):
		sdngui.createTopoBlock(host_x1, 300, host_x2, 335,hosts[i])
		canvas.create_line(round((host_x1+host_x2)/2),300,switch_points[i],235)
		host_x1+=70
		host_x2+=70

def topo2():
	sdngui.createTopoBlock(275, 100, 325, 135,"c1")
	sdngui.createTopoBlock(275, 175, 325, 215,"s1")
	canvas.create_line(300,135,300,175)


	
	host_x1=40
	host_x2=90

	
	hosts=["h1","h2","h3","h4","h5","h6","h7","h8"]
	
#create 1 switch & 8 hosts
	for i in xrange(0,8):
		sdngui.createTopoBlock(host_x1, 300, host_x2, 335,hosts[i])
		canvas.create_line(round((host_x1+host_x2)/2),300,300,215)
		host_x1+=70
		host_x2+=70
	 

topo1()


#========ttk starts=====
#create a tabbed interface

note = Notebook(root)


tab1 = Frame(note)
tab2 = Frame(note)
tab3 = Frame(note)
tab4 = Frame(note)

#display topo according to current tab
def tabChangedEvent(event):
	if event.widget.tab(event.widget.index("current"),'text')== "IP Loadbalancer":
		canvas.delete(ALL)
		topo2()

	else:
		canvas.delete(ALL)
		topo1()



#button actions
def onFire():
	 
	block_string=""
	for item in block_list:
		block_string+=host_to_mac[item]+","
	block_string = block_string[:-1]
	 
	os.system(" python pox.py log.level --DEBUG forwarding.l2_firewall_new --blacklist="+block_string)
	
	 

def onPort():
	port_no=port_fld.get()
	os.system("python pox.py log.level --DEBUG forwarding.l2_learning blocker_new --ports="+port_no)



def onUnblock():
	os.system("python pox.py log.level --DEBUG forwarding.l2_learning")

 



def onLoadbal():
	svc_ip=service_ip.get()
	svr_ip=server_ip.get()
	os.system("python pox.py log.level --DEBUG misc.ip_loadbalancer_new --ip="+svc_ip+" --servers="+svr_ip)


def onLinklat1():
	os.system("python pox.py log.level --DEBUG forwarding.l2_learning")
	latency_script = open("link_lat.py", 'w')
#create a py script to test latency & write to file
	for i in xrange(1,8):
		for j in xrange(i+1,9):
			line1="print \"h"+str(i)+" ----------------------> h"+str(j)+"\""
			latency_script.write(line1)
			latency_script.write("\n")

			line2="h"+str(i)+".cmdPrint( \'ping -i 1 -c 5 \' + h"+str(j)+".IP() +\'|grep rtt\' )"
			latency_script.write(line2)
			latency_script.write("\n")

			latency_script.write("\n")

	latency_script.close()








port_fld = StringVar()
service_ip=StringVar()
server_ip=StringVar()

#Link latency
Button(tab1, text='Test latency',command=onLinklat1).pack()




#Firewall
Label(tab2,text='Select the hosts to be blocked:').pack()
Button(tab2, text='Block hosts',command=onFire).pack() 

#Port blocker
Label(tab3,text='Enter port number to blocked:').pack()
Entry(tab3,width=5,textvariable=port_fld).pack()
Button(tab3, text='Block ports',command=onPort).pack()
Button(tab3, text='Unblock ports',command=onUnblock).pack()

#IP Loadbalancer
Label(tab4,text='Enter main service IP:').pack()
Entry(tab4,width=10,textvariable=service_ip).pack()
Label(tab4,text='Enter comma sperated list of server IP\'s: ').pack()
Entry(tab4,width=10,textvariable=server_ip).pack()
Button(tab4, text='Go',command=onLoadbal).pack()



note.add(tab1, text = "Link latency" )
note.add(tab2, text = "Firewall")
note.add(tab3, text = "Port blocker")
note.add(tab4, text = "IP Loadbalancer")
note.bind_all("<<NotebookTabChanged>>", tabChangedEvent)
note.pack()





canvas.pack()

mainloop()

