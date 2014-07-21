import settings
import sys
import re
import getpass
from HPNA import HPNA 

class VserverIPHandler:

  def generateWildCard(self, address_mask):
  	wildCard = [0,0,0,0]
  	mask = int(address_mask)
  	wildBits = 32 - mask
  	while wildBits > 0:
  		wildCard[wildBits/8 - 1] = pow(2, wildBits) - 1
  		wildBits = wildBits - 8
  	wildCard.reverse()
  	return '.'.join(wildCard)

  def generateACLMap(self, vserver_ips):
	'''
	Generates a map for intermediate processing
	acl map returned by this method has the below skeleton
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
	aclFile = 'acl_output_' + deviceIp
	try:
		outFile = open(aclFile, 'w')
		'''
		vserverTagType is either 'live' or 'dr' or 'general' see details of aclMap in 
		generateACLMap method of this class
		'''
		for vserverTagType, vserverList in aclMap.items():
			if len(vserverList) != 0:
				remark = 'access-list ' + str(settings.aclNumber[vserverTagType]) + ' remark ## ' + vserverTagType + '\n'
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
  
    