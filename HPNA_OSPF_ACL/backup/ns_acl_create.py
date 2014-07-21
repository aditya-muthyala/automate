import netscaler_ips_hpna
import settings
import sys
import re


def generateACLMap(vserver_ips):
  
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
      endloop = True
      while endloop:
        u_display = "Enter live or general " + vserverName + " " + ip + ": "
        u_input = raw_input(u_display)
        if re.search('live',u_input):
          live.append( { vserverName : ip } )
          endloop = False
        elif re.search('general',u_input):
          general.append( { vserverName : ip } )
          endloop = False
  
  aclMap['dr'] = dr
  aclMap['live'] = live
  aclMap['general'] = general
  return aclMap

def generateACL(aclMap, deviceIp):
  aclFile = 'acl_output_' + deviceIp
  try:
    outFile = open(aclFile, 'w')
    for vserverTagType, vserverList in aclMap.items():
      if len(vserverList) != 0:
        for vserver in vserverList:
          vserverName, vserverIp = vserver.popitem()
          remark = 'access-list ' + str(settings.aclNumber[vserverTagType]) + ' remark ##' + vserverName + '\n'
          permit = 'access-list ' + str(settings.aclNumber[vserverTagType]) + ' permit ' + vserverIp + '\n'
          outFile.write(remark)
          outFile.write(permit)
    
  except Exception as err:
    # readable error
    message = err[2]["error"]["message"]
    print message.replace("'", "")
    sys.exit(1)
  finally:
    outFile.close()

if __name__ == '__main__':  
  if len(sys.argv) < 2:
    print "Please specify device IP\nUsage: python ns_acl_create.py <deviceip>"
    sys.exit(1)
  
  deviceIp = sys.argv[1]
  
  vserver_ips = netscaler_ips_hpna.get_vserver_ip(deviceIp)
  
  if len(vserver_ips) == 0:
    print "Please check device %s has VIP and/or correct driver is applied in HPNA" % deviceIp
    sys.exit(1)
    
  aclMap = generateACLMap(vserver_ips)
  
  generateACL(aclMap, deviceIp)
  
    