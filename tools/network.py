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

def scan_network(start,end,method='subprocess',timeout='method',scan_and_break=False):
    if timeout == 'method':
        if method == 'subprocess':
            timeout = 0.014
        elif method == 'requests':
            timeout = 0.036
        elif type(timeout) == float or type(timeout) == int:
            timeout = float(timeout)
        else:
            raise ValueError('timeout input not recoqnized')
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
                            if method == 'subprocess':
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