from tracemalloc import start
import requests #0.036
import subprocess #0.013
import time

def progress_bar(ratio,length=18,start_str='[',end_str=']',progress_str='=',empty_str=' ',percentages=True):
    if length < 5:
        length=5
    if ratio < 0:
        ratio = 0 
    elif ratio > 1:
        ratio = 1
    if ratio == 0.5:
        ratio = 0.501
    prt_str = start_str+round(ratio*length)*progress_str
    prt_str = prt_str+(1+length-len(prt_str))*empty_str+end_str
    if percentages:
        perc_str = str(round(ratio*100))+'%'
        prt_str = prt_str[0:int(length/2)-1]+perc_str+prt_str[int(length/2)+len(perc_str)-1:]
    return(prt_str)

def scan_network(start,end,method='ping',timeout='method',scan_and_break=False):
    if timeout == 'method':
        if method == 'ping':
            timeout = 0.014
        elif method == 'requests':
            timeout = 0.036
        elif method == 'nmap':
            #requires linux OS and nmap
            timeout = 'NA'
        elif method == 'arp':
            timeout = 'NA'        
        elif type(timeout) == float or type(timeout) == int:
            timeout = float(timeout)
        else:
            raise ValueError('timeout input not recoqnized')
    print('Using method: '+method+' with timeout of '+str(timeout)+' seconds')
    if method == 'nmap':
        #only for use on raspbien with nmap installed
        end = start.split('.')[0]+'.'+start.split('.')[1]+'.'+start.split('.')[2]+'.255'
        start = start.split('.')[0]+'.'+start.split('.')[1]+'.'+start.split('.')[2]+'.0'
        print('Using nmap for scanning the subnet only, eg. '+start+' to '+end)
        hosts = []
        r = subprocess.check_output("nmap -sn "+start+"/24 -oG - | awk '/Up$/{print $2}'",shell=True).decode('utf-8')
        for line in r.split('\n'):
            if line != '':
                hosts.append(line)
                print('\n'+line+'\n')
        return hosts, hosts[-1]
    if method == 'arp':
        #only for use on raspbian
        print('Using arp to give all currently connected hosts in the arp table. List can be completed by running nmap or ping scan first.')
        hosts = []
        r = subprocess.check_output("arp -a | awk '{print $2}' | tr -d '()'",shell=True).decode('utf-8')
        for line in r.split('\n'):
            if line != '':
                hosts.append(line)
                print('\n'+line+'\n')
        return hosts, hosts[-1]
    a,b,c,d = start.split('.')
    a2,b2,c2,d2 = end.split('.')
    number_of_ips = (int(a2)-int(a)+1)*(int(b2)-int(b)+1)*(int(c2)-int(c)+1)*(int(d2)-int(d)+1)
    count = 0
    hosts = []
    end_statement = False
    print('\n')
    print(str(count)+' out of '+str(number_of_ips)+' '+progress_bar(0),end='\r')
    try:
        for i in range(int(a),256):
            if end_statement:
                break
            for j in range(int(b),256):
                if end_statement:
                    break
                for k in range(int(c),256):
                    if end_statement:
                        break
                    for l in range(int(d),256):
                        ip = str(i)+'.'+str(j)+'.'+str(k)+'.'+str(l)
                        count +=1
                        print(str(count)+' out of '+str(number_of_ips)+' '+progress_bar(count/number_of_ips),end='\r')
                        try:
                            if method == 'ping':
                                r = subprocess.check_output("ping -c 1 -W 1 "+ip+" >/dev/null 2>&1",shell=True,timeout=timeout)
                            elif method == 'requests':
                                r = requests.get('http://'+ip,timeout=timeout)
                            else:
                                r = subprocess.check_output("ping -c 1 -W 1 "+ip+" >/dev/null 2>&1",shell=True,timeout=timeout)                                
                            hosts.append(ip)
                            print('\n'+ip+'\n')
                            if ip == end or scan_and_break:
                                end_statement = True
                                break
                        except subprocess.TimeoutExpired:
                            #print(ip,' did not answer')
                            if ip == end:
                                end_statement = True
                                break
                            continue
                        except requests.exceptions.Timeout:
                            #print(ip,' did not answer')
                            if ip == end:
                                end_statement = True
                                break
                            continue
    except KeyboardInterrupt:
        print('\nInterrupted at '+ip)
    return hosts, ip

def fast_scan_network(group = '192.168.1.0'):
    """Extract all MAC addresses from ARP table using subprocess"""
    try:
        cache = subprocess.check_output("nmap -sn "+group+"/24",shell=True).decode('utf-8')
    except:
        print('Failed using nmap. The following list may be incomplete. Try "sudo apt install nmap" to install nmap on linux systems.')
    r = subprocess.check_output("arp -a", shell=True).decode('utf-8')
    ip_addresses = []
    mac_addresses = []
    for line in r.split('\n'):
        # Parse each line of arp output
        parts = line.split(' ')
        for part in parts:
            if '.' in part and len(part.split('.')) == 4:
                if '(' in part or ')' in part:
                    ip_addresses.append(part.strip('()'))
                else:
                    ip_addresses.append(part)
            elif ':' in part and len(part.split(':')) == 6:
                mac_addresses.append(part)
    return ip_addresses,mac_addresses
