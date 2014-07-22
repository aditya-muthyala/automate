# Simple script to generate flat config files for a security POC
import sys
import getpass
import re
import json

try:
  import SOAPpy
except:
  print "Install SOAPpy from https://pypi.python.org/pypi/SOAPpy"
  sys.exit(1)
    
class HPNA:

  def login(self):
  	'''
  	Returns SOAP client and session id to the calling function
  	return client, session_id
  	'''    
	username = getpass.getuser()
	u_display = "HPNA.Username: [" + username + "] "
	u_input = raw_input(u_display)
	if len(u_input) > 0:
		username = u_input
		password = getpass.getpass()

	service_url = 'https://hpna.ops.expertcity.com/soap'
	namespace = 'http://opsware.com/nas/90'

	client = SOAPpy.SOAPProxy(service_url, namespace, simplify_objects=True)

	try:
		credentials = client.login(username=username, password=password)
		session_id = credentials["Text"]
		return client, session_id
	except Exception as err:
		# readable error
		message = err[2]["error"]["message"]
		print message.replace("'", "")
		sys.exit(1)

 
  #Example for portAddress_str [Address[172.29.3.69], Mask[255.255.255.255], Type[3]]
  def extract_ip(self, portAddress_str):
	address_str = portAddress_str.split(',')[0]
	match_set = re.search('\d+.\d+.\d+.\d+', address_str)
	if match_set is not None:
		portAddress = match_set.group(0)
		return portAddress
	else:
		return 'Empty'

  def get_vserver_ip(self, devip):
    client, session_id = self.login()

    port_map = client.list_port(sessionid=session_id, deviceip=devip)
    '''
	port_map 
	{'Status': '200', 'ResultSet': []}
	list_port returns empty set if the device is not found
	
	Each Element in the Result list contains the following fields
	associatedChannelID
	associatedChannelName
	associatedVlanID
	comments
	configuredDuplex
	configuredSpeed
	description
	deviceID
	devicePortID
	ipAddresses		--> THIS IS WHAT WE ARE INTERESTED IN. IT IS A STRING OF THE FORMAT
								[Address[1.1.1.1], Mask[255.255.255.255], Type[3]]	
	lastModifiedDate
	macAddress
	nativeVlan
	negotiatedDuplex
	negotiatedSpeed
	portAllows
	portCustom1
	portCustom2
	portCustom3
	portCustom4
	portCustom5
	portCustom6
	portName			--> CONTAINS THE NAME OF THE INTERFACE. WE ARE INTERESTED IN 
					EXTRACTING THE VSERVER NAMES. FIELD "portType" IS USED TO VERIFY
					IF ITS A VIP 
	portState
	portStatus
	portType			--> THIS IS SET TO "VIP" IN THE DRIVER WHICH PARSES THE CONFIG IN HPNA
	slotNumber
	temporaryVlanName
	'''
  
    vserver_ip = {}
    try:
      ports = port_map['ResultSet']
      
      for port in ports:
        portname = port['portName']
        portType = port['portType']
        portAddress_str = port['ipAddresses']

        '''
        if condition checks to see if the port type is a VIP and has 
        an IP address assign to it
        '''
        portTypeMatch = re.compile('VIP|VLAN')
        
        if portTypeMatch.search(portType) is not None and portAddress_str:
          '''
          extract_ip() is used to parse the ipAddress field
          see above for the format
          '''
          #portAddress = self.extract_ip(portAddress_str)
          vserver_ip[portname] = portAddress_str
          #print "%s : %s" % (portname, portAddress)
      
    except KeyError:
      print sys.exc_info()[0:2]
    finally:
      client.logout(sessionid=session_id)
      return vserver_ip

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Please specify device IP\nUsage: python netscaler_ips_hpna <deviceip>"
    sys.exit(1)
    
  devip = sys.argv[1]
  hpna = HPNA()
  vserver_ip = hpna.get_vserver_ip(devip)

  if vserver_ip.keys():
    for key in vserver_ip.keys():
      print "%s : %s" % (key, vserver_ip[key])
  else:
    print "Please check device %s has VIP and/or correct driver is applied in HPNA" % devip