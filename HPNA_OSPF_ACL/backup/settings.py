import re

'''
Add to 'generalTag' list the regular expression to tag the respective VIPs
as general with tag 595. the dictionary tagMap contains the regex
used by VserverIPHandler to add the VIPs to respective ACL number
'''
generalTag = ['VLAN',
			'login',
			'dns',
			'builds',
			'devices.col',
			'-ats.',
			'joing2',
			'launch',
			'logging',
			'authentication',
			'oauthsvc',
			'commmom',
			'commsession',
			'commadmin',
			'queue',
			'depo',
			'mdm',
			'probe',
			'vip',
			'auth.*443'
			]

tagMap = {}

tagMap['dr'] = '-dr-'
tagMap['general'] = '|'.join(generalTag)

tagMatchDR = re.compile(tagMap['dr'])
tagMatchGeneral = re.compile(tagMap['general'])

aclNumber = {
            'live' : 10,
            'dr' : 20,
            'general' : 30,
            'vlan' : 30,
           }
           
gitcheckin = 'http://ciserver1.qai.expertcity.com:7990/'