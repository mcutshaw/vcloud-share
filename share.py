from search_db import ialab_db
from vcloud_rest import vcloud
import configparser

def validateMember(member, db):
    return db.checkIalabUserExists(member)

config = configparser.ConfigParser()
config.read('search-db.conf')
db = ialab_db(config)
vcloud = vcloud(config)

Num = config['Share']['Num']
base = 'Team'
vapp_base = '_vapp'

for x in range(1,int(Num)+1):
    teamList = config['Share'][base+str(x)].split(',')
    vapp_name = config['Share'][base+str(x)+vapp_base]
    vapp = vcloud._getvapp(vapp_name)
    for member in teamList:
        if not validateMember(member,db):
                print('Member not in db:', member)
        else:
                member_href = db.getIalabHref(member)
                vcloud.addUserToVapp(vapp, member, member_href)
