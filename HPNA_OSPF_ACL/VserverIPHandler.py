import settings
import sys
import re
import getpass
import socket
from HPNA import HPNA 

class VserverIPHandler:

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
	for vserverName, ip in vserver_ips.items():
		if settings.tagMatchGeneral.search(vserverName) is not None:
			general.append( { vserverName : ip } )
		elif settings.tagMatchDR.search(vserverName) is not None:
			dr.append( { vserverName : ip } )
		else:
			live.append( { vserverName : ip } )
	
	aclMap['dr'] = dr
	aclMap['live'] = live
	aclMap['general'] = general
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
  
    