import settings
import sys
import re
import getpass
import socket
from HPNA import HPNA 

class VserverIPHandler:

  #Example for portAddress_str [Address[172.29.3.69], Mask[255.255.255.255], Type[3]]
  def extract_ip(self, portAddress_str):
	address_str = portAddress_str.split(',')[0]
	match_set = re.search('\d+.\d+.\d+.\d+', address_str)
	if match_set is not None:
		portAddress = match_set.group(0)
		return portAddress
	else:
		return 'Empty'
  #
  def extract_wildcard(self, portAddress_str):
	'''
	First extract the mask from the string [Address[172.29.3.69], Mask[255.255.255.255], Type[3]]
	'''
	mask_str = portAddress_str.split(',')[1]
	match_set = re.search('\d+.\d+.\d+.\d+', mask_str)
	if match_set is not None:
		portMask = match_set.group(0)
		maskList = portMask.split('.')
		wildcardList = []
		for octect in maskList:
			wildcardList.append( str(255 - int(octect)) )
		wildCard = '.'.join(wildcardList)
		return wildCard
	else:
		return 'Empty'

  def generateACLMap(self, vserver_ips):
	'''
	Generates a map for intermediate processing
	acl map returned by this method
	{
	'live': [ List of live vserverName : vserverIP key value pairs]
	'dr': [ List of dr vserverName : vserverIP key value pairs]
	'general': [ List of vserverName : vserverIP key value pairs]
	}
	'''
	aclMap = {}
	live = []
	dr = []
	general = []
	vlan = []
	for vserverName, ip in vserver_ips.items():
		ipaddress = self.extract_ip(ip)
		if settings.tagMatchGeneral.search(vserverName) is not None:
			general.append( { vserverName : ipaddress } )
		elif settings.tagMatchDR.search(vserverName) is not None:
			dr.append( { vserverName : ipaddress } )
		elif settings.tagMatchVlan.search(vserverName) is not None:
			#print "%s : %s" % vserverName, ipaddress
			wildCard = self.extract_wildcard(ip)
			vlan.append( { vserverName : (ipaddress, wildCard) } )
		else:
			live.append( { vserverName : ipaddress } )
	
	aclMap['dr'] = dr
	aclMap['live'] = live
	aclMap['general'] = general
	aclMap['vlan'] = vlan
	return aclMap

  def generateACL(self, aclMap, deviceIp):
	'''
	Uses the ACL map produced by the function generateACLMap and print the netscaler vtysh commands
	to add the ACLs
	'''
	hostname = socket.gethostbyaddr(deviceIp)[0]
	dc = hostname.split('.')[1].upper()
	if len(dc) > 3:
		u_display = "Please enter Datacenter name in Upper Case[" + dc + "] "
		u_input = raw_input(u_display)
		dc = u_input
	aclFile = dc + '/acl_output_' + hostname + '.txt'
	try:
		outFile = open(aclFile, 'w')
		for vserverTagType, vserverList in aclMap.items():
			if len(vserverList) != 0:
				remark = 'access-list ' + str(settings.aclNumber[vserverTagType]) + ' remark #######' + vserverTagType + '\n'
				outFile.write(remark)
				for vserver in vserverList:
					vserverName, vserverIp = vserver.popitem()
					if settings.tagMatchVlan.search(vserverName) is not None:
						permit = 'access-list ' + str(settings.aclNumber[vserverTagType]) + ' permit ' + vserverIp[0] + ' ' + vserverIp[1] + '\n'
					else:
						permit = 'access-list ' + str(settings.aclNumber[vserverTagType]) + ' permit ' + vserverIp + '\n'
					outFile.write(permit)
		
	except Exception as err:
		# readable error
		print sys.exc_info()[0:2]
		sys.exit(1)
	finally:
		outFile.close()

if __name__ == '__main__':  
  if len(sys.argv) < 2:
    print "Please specify device IP\nUsage: python ns_acl_create.py <deviceip>"
    sys.exit(1)
  
  deviceIp = sys.argv[1]
  
  aclh = VserverIPHandler()
  hpna = HPNA()
  vserver_ips = hpna.get_vserver_ip(deviceIp)
  
  if len(vserver_ips) == 0:
    print "Please check device %s has VIP and/or correct driver is applied in HPNA" % deviceIp
    sys.exit(1)
    
  aclMap = aclh.generateACLMap(vserver_ips)
  
  aclh.generateACL(aclMap, deviceIp)
  
    