import urllib2
import urllib
import json
import time
import datetime
from datetime import date
from datetime import datetime
import os
from StringIO import StringIO
import gzip
import time
from sets import Set
import sys
import yaml # pip install pyyaml
import tzlocal  # pip install tzlocal

# Global settings
g_debug = True # show additional information (debug mode)
g_offline_mode = False # use only cached data
g_eveserver = 'tranquility' # eveonline' server
#g_user_agent = 'http://gf-company.space/ Maintainer: Qandra Si qandra.si@gmail.com'
g_alliance_id = 99008697 # eveonline' alliance to generate video with team work
g_local_timezone = tzlocal.get_localzone()
#g_tmp_dir = 'c:/Workspace/eve'
g_tmp_dir = 't:/eve'
#g_tmp_dir = '/media/eve'


g_events = []
g_solar_systems = []
g_alliance_killmails = []
g_characters = []
#g_prev_get_json_type = int(0)
g_sde_uniq_names = []


def getDateStr(datetime_str):
    return datetime_str[:10]

def getTimestamp(datetime_str):
    dt = datetime.strptime(datetime_str,'%Y-%m-%dT%H:%M:%SZ')
    return int(time.mktime(dt.timetuple()))

def pushPlaintextEvent(datetime_str, text):
    g_events.append([getTimestamp(datetime_str),getDateStr(datetime_str),text])

def pushPlaintextEventTS(timestamp, text):
    g_events.append([int(timestamp),datetime.fromtimestamp(float(timestamp), g_local_timezone).strftime('%Y-%m-%d'),text])

def pushSolarSystem(id, name):
    g_solar_systems.append({"id":int(id),"name":name.replace('\\','/')})

def getSolarSystemName(id):
    for s in g_solar_systems:
        if int(id)==int(s["id"]):
            return s["name"]
    #return id
    print('Unknown solar system name {id}'.format(id=id))
    sys.stdout.flush()
    raise ValueError(id)

def pushAllianceKillmail(id, datetime_str, characters, solar_system_id, location_id):
    g_alliance_killmails.append({"id":int(id),"time":getTimestamp(datetime_str),"who":characters, "system":int(solar_system_id),"location":int(location_id)})

# type=0 : https://esi.evetech.net/
# type=1 : https://zkillboard.com/
def getJson(type,renew_cache,suburl):
    fdir = '{tmp}/{type}/{suburl}'.format(type=type,tmp=g_tmp_dir,suburl=suburl)
    fname = '{dir}/data.json'.format(dir=fdir)
    if not renew_cache and os.path.isfile(fname):
        lfr = open(fname,"rt")
        s = lfr.read()
        json_data = (json.loads(s))
        #if g_debug:
        #    print(s)
        #    print(json.dumps(json_data, indent=4, sort_keys=True))
        lfr.close()
    elif g_offline_mode:
        json_data = (json.loads('[]'))
    else: # online mode
        if type==0:
            url = 'https://esi.evetech.net/latest/{esi}/?datasource={server}'.format(esi=suburl,server=g_eveserver)
            #headers={'Content-Type': 'application/json'}
            #req.addheaders = [('Content-Type', 'application/json')]
        else:
            url = 'https://zkillboard.com/api/{api}/'.format(api=suburl)
            #req.addheaders = [('Content-Type', 'application/json')]
            #headers=[{'Content-Type': 'application/json'},{'Accept-Encoding': 'gzip'},{'Maintainer': 'Alexander alexander.bsrgin@yandex.ru'}]
        if g_debug:
            print(url)
            sys.stdout.flush()
        req = urllib2.Request(url)
        if type==0:
            req.add_header('Content-Type', 'application/json')
        else:
            req.add_header('Accept-Encoding', 'gzip')
            req.add_header('User-Agent', g_user_agent)
        f = urllib2.urlopen(req)
        if f.info().get('Content-Encoding') == 'gzip':
            buffer = StringIO(f.read())
            deflatedContent = gzip.GzipFile(fileobj=buffer)
            s = deflatedContent.read()
        else:
            s = f.read().decode('utf-8')
        f.close()
        json_data = (json.loads(s))
        #if g_debug:
        #    print(s)
        #    print(json.dumps(json_data, indent=4, sort_keys=True))
        if not os.path.isdir(fdir):
            os.makedirs(fdir)
        lfr = open(fname,"wt+")
        lfr.write(s)
        lfr.close()
        time.sleep(2) # Do not hammer the server with API requests. Be polite.
        #if int(g_prev_get_json_type) == int(type):
        #    time.sleep(10) # Do not hammer the server with API requests. Be polite.
        #else:
        #    time.sleep(5) # Do not hammer the server with API requests. Be polite.
        #    g_prev_get_json_type = type
    return json_data

# type=2 : unpacked SDE-yyyymmdd-TRANQUILITY.zip
def getYaml(type,suburl):
    fname = '{tmp}/{type}/{suburl}'.format(type=type,tmp=g_tmp_dir,suburl=suburl)
    f = open(fname,"rt")
    s = f.read()
    yaml_data = yaml.load(s, Loader=yaml.FullLoader)
    #if g_debug:
    #    print(s)
    #    print(yaml.dump(yaml_data))
    f.close()
    return yaml_data

def pushCharacter(id,name):
    g_characters.append({"id":int(id),"name":name})

def getCharacterName(id):
    for c in g_characters:
        if int(id)==int(c["id"]):
            return c["name"]
    # curl -X GET "https://esi.evetech.net/latest/characters/631632288/?datasource=tranquility" -H "accept: application/json"
    who = getJson(0,False,'characters/{who}'.format(who=id))
    if 'name' in who: # offline mode? and there are no data? (skip)
        pushCharacter(id,who["name"])
        return who["name"]
    else:
        return id

def getLocationName(id):
    for n in g_sde_uniq_names:
        if int(n[0]) == id:
            return n[1]
        elif int(n[0]) > id: # sorted
            return id
    return id



# curl -X GET "https://esi.evetech.net/latest/alliances/99008697/?datasource=tranquility" -H "accept: application/json"
alliance_details = getJson(0,False,'alliances/{alliance}'.format(alliance=g_alliance_id))
alliance_creator_id = int(alliance_details["creator_id"])

print("alliance_id = %d" % g_alliance_id)
print("  creator_id   = {} ({})".format(alliance_creator_id, getCharacterName(alliance_creator_id)))
print("  date_founded = %s" % alliance_details["date_founded"])
print("  name         = %s" % alliance_details["name"])
print("  ticker       = %s" % alliance_details["ticker"])
sys.stdout.flush()

pushPlaintextEvent(
    alliance_details["date_founded"],
    '{creator} created alliance {name}'.format(
        creator=getCharacterName(alliance_creator_id),
        name=alliance_details["name"])
)

now_ts = int(time.time())
now_year = date.today().year
now_month = date.today().month
founded_ts = getTimestamp(alliance_details["date_founded"])
founded_year = int(alliance_details["date_founded"][:4])
founded_month = int(alliance_details["date_founded"][5:7])
print('Fetching from {year}-{month} to {tyear}-{tmonth} ({now})'.format(year=founded_year,month=founded_month,tyear=now_year,tmonth=now_month,now=now_ts))
sys.stdout.flush()

def isAllianceExist(datetime_str):
    return founded_ts <= getTimestamp(datetime_str) < now_ts

# https://zkillboard.com/api/allianceID/99008697/endTime/20200131000000/startTime/20200130000000/
zkillmails_num = 0
for y in range(founded_year,now_year+1):
    if y==founded_year:
        m0 = founded_month
    else:
        m0 = 1
    if y==now_year:
        m1 = now_month
    else:
        m1 = 12
    for m in range(m0,m1+1):
        start = '{:04d}{:02d}01000000'.format(y,m)
        if m<12:
            end = '{:04d}{:02d}01000000'.format(y,m+1)
        else:
            end = '{:04d}0101000000'.format(y+1)
        page = 1
        if now_year == y and m == now_month:
            renew_cache = True # renew killmails by current month
        else:
            renew_cache = False
        while True:
            zkillmails = getJson(1,renew_cache,'allianceID/{alliance}/startTime/{start}/endTime/{end}/page/{page}'.format(alliance=g_alliance_id,start=start,end=end,page=page))
            zkillmails_num = zkillmails_num + len(zkillmails)
            #print(json.dumps(killmails, indent=4, sort_keys=False))
            for zkill in zkillmails:
                # https://zkillboard.com/api/killID/80970275/
                id = int(zkill["killmail_id"])
                zkillmail = getJson(1,False,'killID/{id}'.format(id=id))
                # curl -X GET "https://esi.evetech.net/latest/killmails/73216307/e015e69931dd8a22a10d0d439ca3ec45503498cc/?datasource=tranquility" -H "accept: application/json"
                killmail = getJson(0,False,'killmails/{id}/{hash}'.format(id=id,hash=zkill["zkb"]["hash"]))
                location_id = 0
                if 'locationID' in zkill["zkb"]:
                    location_id = zkill["zkb"]["locationID"]
                if not 'attackers' in killmail and not 'victim' in killmail:
                    break # offline mode? and there are no data? (skip)
                characters = []
                if 'attackers' in killmail:
                    for a in killmail["attackers"]:
                        if 'character_id' in a and 'alliance_id' in a and int(a["alliance_id"])==g_alliance_id:
                            characters.append(int(a["character_id"]))
                if 'victim' in killmail:
                    v = killmail["victim"]
                    if 'character_id' in v and 'alliance_id' in v and int(v["alliance_id"])==g_alliance_id:
                        characters.append(int(v["character_id"]))
                pushAllianceKillmail(id, killmail["killmail_time"], characters, killmail["solar_system_id"], location_id)
            if len(zkillmails)<200:
                break
            else:
                page = page + 1
print('Found {num} of {all} killmails of alliance'.format(num=len(g_alliance_killmails),all=zkillmails_num))
sys.stdout.flush()



#shafrak = getYaml(2,'sde/fsd/universe/eve/Aridia\Leseasesh\Shafrak/solarsystem.staticdata')
#print(shafrak)
print('Loading solar systems from filesystem...')
sys.stdout.flush()
sscnm = '{tmp}/solar_systems_cache.json'.format(tmp=g_tmp_dir)
if os.path.isfile(sscnm):
    sscr = open(sscnm,"rt")
    s = sscr.read()
    g_solar_systems = (json.loads(s))
    sscr.close()

else:
    print('  loading solar systems from Abyssal Depth...')
    sys.stdout.flush()
    sde_universe_path = '{tmp}/2/sde/fsd/universe/abyssal'.format(tmp=g_tmp_dir)
    for path, dirs, files in os.walk(sde_universe_path):
        for f in files:
            #if g_debug:
            #    print('{}/{}'.format(path,f))
            suburl = path.replace('{tmp}/2/'.format(tmp=g_tmp_dir),'')
            solar_system = getYaml(2,'{}/{}'.format(suburl,f))
            if 'solarSystemID' in solar_system:
                id = int(solar_system["solarSystemID"])
                nm = suburl.replace('sde/fsd/universe/abyssal','/abyssal/depth')[1:]
                #print('{} = {}'.format(nm,id))
                pushSolarSystem(id,nm)
    
    print('  loading solar systems from Wormholes...')
    sys.stdout.flush()
    sde_universe_path = '{tmp}/2/sde/fsd/universe/wormhole'.format(tmp=g_tmp_dir)
    for path, dirs, files in os.walk(sde_universe_path):
        for f in files:
            #if g_debug:
            #    print('{}/{}'.format(path,f))
            suburl = path.replace('{tmp}/2/'.format(tmp=g_tmp_dir),'')
            solar_system = getYaml(2,'{}/{}'.format(suburl,f))
            if 'solarSystemID' in solar_system:
                id = int(solar_system["solarSystemID"])
                nm = suburl.replace('sde/fsd/universe/wormhole','/worm/holes')[1:]
                #print('{} = {}'.format(nm,id))
                pushSolarSystem(id,nm)
    
    print('  loading solar systems from Universe...')
    sys.stdout.flush()
    sde_universe_path = '{tmp}/2/sde/fsd/universe/eve'.format(tmp=g_tmp_dir)
    for path, dirs, files in os.walk(sde_universe_path):
        for f in files:
            #if g_debug:
            #    print('{}/{}'.format(path,f))
            suburl = path.replace('{tmp}/2/'.format(tmp=g_tmp_dir),'')
            solar_system = getYaml(2,'{}/{}'.format(suburl,f))
            if 'solarSystemID' in solar_system:
                id = int(solar_system["solarSystemID"])
                nm = suburl.replace('sde/fsd/universe/eve','')[1:]
                #print('{} = {}'.format(nm,id))
                pushSolarSystem(id,nm)
    
    sscw = open(sscnm, "wt+")
    sscw.write(json.dumps(g_solar_systems, indent=1, sort_keys=False))
    sscw.close()
#if g_debug:
#    print(json.dumps(g_solar_systems, indent=1, sort_keys=False))
print('Found {num} solar systems in eve university'.format(num=len(g_solar_systems)))
sys.stdout.flush()



# curl -X GET "https://esi.evetech.net/latest/alliances/99008697/corporations/?datasource=tranquility" -H "accept: application/json"
alliance_corporations = getJson(0,False,'alliances/{alliance}/corporations'.format(alliance=g_alliance_id))
print('Found {num} corporations in alliance'.format(num=len(alliance_corporations)))
sys.stdout.flush()

for corporation_id in alliance_corporations:
    # curl -X GET "https://esi.evetech.net/latest/corporations/98550309/?datasource=tranquility" -H "accept: application/json"
    corp_details = getJson(0,False,'corporations/{corp}'.format(corp=corporation_id))
    print("corporation_id = %s" % corporation_id)
    #print("  ceo_id       = %s" % corp_details["ceo_id"])
    #print("  creator_id   = %s" % corp_details["creator_id"])
    #print("  date_founded = %s" % corp_details["date_founded"])
    #print("  name         = %s" % corp_details["name"])
    #print("  ticker       = %s" % corp_details["ticker"])
    sys.stdout.flush()
    
    # curl -X GET "https://esi.evetech.net/latest/corporations/98259632/alliancehistory/?datasource=tranquility" -H "accept: application/json"
    corp_history = getJson(0,False,'corporations/{corp}/alliancehistory'.format(corp=corporation_id))
    our_alliance = 0
    departed_from_out_alliance = ''
    for corp_event in corp_history:
        time_str = corp_event["start_date"]
        if isAllianceExist(time_str):
            #if 'alliance_id' in corp_event:
            #    print("    alliance_id  = %s" % corp_event["alliance_id"])
            #print("    start_date   = %s" % time_str)
            if 'alliance_id' in corp_event:
                our_alliance = int(corp_event["alliance_id"]) == g_alliance_id
                if our_alliance:
                    if departed_from_out_alliance:
                        pushPlaintextEvent(
                            departed_from_out_alliance,
                            'Goodbye {name}'.format(
                                name=corp_details["name"]
                            )
                        )
                    pushPlaintextEvent(
                        time_str,
                        'Hello {name} (founded {founded})'.format(
                            name=corp_details["name"],
                            founded=getDateStr(corp_details["date_founded"])
                        )
                    )
                else:
                    continue # another alliance
            else:
                departed_from_out_alliance = time_str



print('Loading names of locations...')
sys.stdout.flush()
un_yaml = getYaml(2,'sde/bsd/invUniqueNames.yaml')
g_sde_uniq_names = []
for n in un_yaml:
    g_sde_uniq_names.append([int(n["itemID"]),n["itemName"]])
un_yaml = []

g_sde_uniq_names.sort(key=lambda x: x[0])
jnw = open('{tmp}/unique_names_cache.json'.format(tmp=g_tmp_dir), "wt+")
jnw.write(json.dumps(g_sde_uniq_names, indent=1, sort_keys=False))
jnw.close()




print('Building killmails log...')
sys.stdout.flush()
virtual_unique_killid = 1
first_time_locations = []
first_time_characters = Set()
time_to_erase_systems = []
g_alliance_killmails.sort(key=lambda x: x["time"])
#print(g_alliance_killmails)
glf = open('{tmp}/git.log'.format(tmp=g_tmp_dir), "wt+")
for k in g_alliance_killmails:
    unix_timestamp = float(k["time"])
    id = 0
    system_id = int(k["system"])
    location_id = int(k["location"])
    system_name = getSolarSystemName(system_id)
    for c in k["who"]:
        if not c in first_time_characters:
            first_time_characters.add(c)
            #pushPlaintextEventTS(
            #    unix_timestamp,
            #    'Hi {}!'.format(getCharacterName(c))
            #)
        if id==0:
            id = int(k["id"])
        else:
            id = virtual_unique_killid
            virtual_unique_killid = virtual_unique_killid + 1
        glf.write('\n------------------------------------------------------------------------\nr{:08x} | '.format(id))
        glf.write('{name} | '.format(name=getCharacterName(c)))
        glf.write(datetime.fromtimestamp(unix_timestamp, g_local_timezone).strftime('%Y-%m-%d %H:%M:%S %z (%a, %m %b %Y %H:%M:%S %z)'))
        glf.write(' | x lines\nChanged paths:\n')
        sysloc0 = {"sys":int(system_id),"loc":0}
        sysloc = {"sys":int(system_id),"loc":int(location_id)}
        found = False
        for sl in first_time_locations:
            if sl["sys"] == system_id and sl["loc"] == location_id:
                found = True
                break;
        if not found:
            glf.write('A')
            if location_id>0:
                first_time_locations.append(sysloc)
                time_to_erase_systems.append({"sysloc":sysloc,"time":int(unix_timestamp)})
            first_time_locations.append(sysloc)
            time_to_erase_systems.append({"sysloc":sysloc0,"time":int(unix_timestamp)})
        else:
            glf.write('M')
            for ttes in time_to_erase_systems:
                if ttes["sysloc"]["sys"] == system_id and ttes["sysloc"]["loc"] == 0:
                    ttes["time"] = int(unix_timestamp)
            if location_id>0:
                for ttes in time_to_erase_systems:
                    if ttes["sysloc"]["sys"] == system_id and ttes["sysloc"]["loc"] == location_id:
                        ttes["time"] = int(unix_timestamp)
        glf.write('\t{system}'.format(system=system_name))
        if location_id > 0:
            glf.write('/{loc}'.format(loc=getLocationName(location_id)))
        glf.write('\n')
        
        repeat = True
        while repeat:
            repeat = False
            idxttes = 0
            for ttes in time_to_erase_systems:
                if (ttes["time"]+(3*24*60*60)) < unix_timestamp:
                    sid = int(ttes["sysloc"]["sys"])
                    lid = int(ttes["sysloc"]["loc"])
                    sl = {"sys":int(sid),"loc":int(lid)}
                    glf.write('D\t{system}'.format(system=getSolarSystemName(sid)))
                    if lid > 0:
                        glf.write('/{loc}'.format(loc=getLocationName(lid)))
                    glf.write('\n')
                    idxftl = 0
                    for ftl in first_time_locations:
                        if ftl["sys"] == sid and ftl["loc"] == lid:
                            del first_time_locations[idxftl]
                            break;
                        idxftl = idxftl + 1
                    del time_to_erase_systems[idxttes]
                    repeat = True
                    break
                idxttes = idxttes + 1
        glf.write('\n')
glf.close()



print('Building scenario...')
sys.stdout.flush()
g_events.sort(key=lambda x: x[0])
last_event_time = g_events[0][0]
last_event_txt = g_events[0][1]
stws = open('{tmp}/stw-scenario.txt'.format(tmp=g_tmp_dir), "wt+")
for e in g_events:
    if  (last_event_time+(3*24*60*60)) > e[0]:
        last_event_txt = '{} {}'.format(last_event_txt,e[2])
    else:
        stws.write('\n{}'.format(last_event_txt))
        last_event_time = e[0]
        last_event_txt = '{date} {txt}'.format(date=e[1],txt=e[2])
stws.write('\n{}'.format(last_event_txt))
stws.close()


#print(g_events)
#stws = open('{tmp}/stw-scenario.txt'.format(tmp=g_tmp_dir), "wt+")
#for e in g_events:
#    stws.write('\n{date} {txt}'.format(date=e[1],txt=e[2]))
#stws.close()
