import os
import requests
import zlib
iport json
import time
import sys
from traceback import print_exc

# Sets API keys and account IDs for GET/POST requests
try:
    ACCOUNT_ID = os.environ['ACCOUNT_ID']
    INSERT_KEY = os.environ['INSERT_KEY']
    FASTLY_KEY = os.environ['FASTLY_KEY']
except:
    print('[!] Error: Please ensure you are providing the following ENV VARS: ACCOUNT_ID, INSERT_KEY, and FASTLY_KEY.')
    sys.stdout.flush()
    sys.exit(1)

# Sets static variables for URLs and headers
insights_url = f'https://insights-collector.newrelic.com/v1/accounts/{ACCOUNT_ID}/events'
nr_headers = {'content-encoding': 'deflate', 'X-Insert-Key': INSERT_KEY, 'Content-Type': 'application/json"'}
fastly_headers = {'Content-Type': 'application/json', 'Fastly-Key': FASTLY_KEY}

# This will create 1440 events per day for each service, or 10080 events per week. Interval is in seconds.
try:
    INTERVAL = int(os.environ['INTERVAL'])
except KeyError:
    INTERVAL = 60
try:
    SILENT = os.environ['SILENT']
except KeyError:
    SILENT = False

if SILENT == 'True':
    SILENT = True
else:
    SILENT = False

# A limitation of Fastly is that you have to query one service at a time. I chose to create an array of my service ids, and loop through them.
try:
    LIST_OF_SERVICES = os.environ['SERVICES'].split(" ")
except KeyError:
    print('[!] Error: No services provided. To use this app please provide services to this docker container as environment variables in the following format:\nservices=<NameOfService1>:<ServiceId1> <NameOfService2>:<ServiceId2>\nThis can easily be added via a docker .env file')
    sys.stdout.flush()
    sys.exit(1)

class Log:
    def __init__(self):
        self.num_requests = 0
        self.num_tls = 0
        self.num_http2 = 0
        self.num_logs = 0
        self.num_pci = 0
        self.num_video = 0
        self.ipv6 = 0
        self.pipe = 0
        self.uncacheable = 0
        self.shield = 0
        self.shield_resp_header_bytes = 0
        self.shield_resp_body_bytes = 0
        self.otfp = 0
        self.otfp_shield_time = 0
        self.otfp_deliver_time = 0
        self.otfp_shield_resp_header_bytes = 0
        self.otfp_shield_resp_body_bytes = 0
        self.otfp_resp_header_bytes = 0
        self.otfp_resp_body_bytes = 0
        self.bandwidth = 0
        self.resp_header_bytes = 0
        self.header_size = 0
        self.resp_body_bytes = 0
        self.body_size = 0
        self.req_header_bytes = 0
        self.req_body_bytes = 0
        self.bereq_header_bytes = 0
        self.bereq_body_bytes = 0
        self.billed_header_bytes = 0
        self.billed_body_bytes = 0
        self.status_2xx = 0
        self.status_3xx = 0
        self.status_4xx = 0
        self.status_5xx = 0
        self.status_200 = 0
        self.status_204 = 0
        self.status_301 = 0
        self.status_304 = 0
        self.status_400 = 0
        self.status_401 = 0
        self.status_403 = 0
        self.status_404 = 0
        self.status_500 = 0
        self.status_501 = 0
        self.status_502 = 0
        self.status_503 = 0
        self.status_504 = 0
        self.status_505 = 0
        self.status_1xx = 0
        self.waf_logged = 0
        self.waf_blocked = 0
        self.waf_passed = 0
        self.attack_req_body_bytes = 0
        self.attack_req_header_bytes = 0
        self.attack_logged_req_body_bytes = 0
        self.attack_logged_req_header_bytes = 0
        self.attack_blocked_req_body_bytes = 0
        self.attack_blocked_req_header_bytes = 0
        self.attack_passed_req_body_bytes = 0
        self.attack_passed_req_header_bytes = 0
        self.attack_resp_synth_bytes = 0
        self.hits = 0
        self.hit_ratio = 0
        self.miss = 0
        self.cache_pass = 0
        self.pass_time = 0
        self.synth = 0
        self.errors = 0
        self.restarts = 0
        self.hits_time = 0
        self.miss_time = 0
        self.tls = 0
        self.tls_v10 = 0
        self.tls_v11 = 0
        self.tls_v12 = 0
        self.tls_v13 = 0
        self.imgopto = 0
        self.imgopto_resp_body_bytes = 0
        self.imgopto_resp_header_bytes = 0
        self.imgopto_shield_resp_body_bytes = 0
        self.imgopto_shield_resp_header_bytes = 0
        self.object_size_1k = 0
        self.object_size_10k = 0
        self.object_size_100k = 0
        self.object_size_1m = 0
        self.object_size_10m = 0
        self.object_size_100m = 0
        self.object_size_1g = 0
        self.recv_sub_time = 0
        self.hash_sub_time = 0
        self.hash_sub_count = 0
        self.deliver_sub_time = 0
        self.deliver_sub_count = 0
        self.hit_sub_time = 0
        self.hit_sub_count = 0
        self.prehash_sub_time = 0
        self.prehash_sub_count = 0
        self.predeliver_sub_time = 0
        self.predeliver_sub_count = 0
        self.otfp_manifests = 0
        self.recv_sub_count = 0

def main():

    if not SILENT:
        print('''

        ############################################################
        [#] Starting the Fastly -> New Relic Insights Log Aggregator
        ############################################################
        
        ''')
        sys.stdout.flush()

    while True:
        try:
            for service_map in LIST_OF_SERVICES:

                serviceName, serviceId = serviceExtractor(service_map)

                aggregated, timestamp, fastly_status = pollFromFastly(serviceId)
                if serviceName: message = batch(aggregated, serviceName)
                else: message = batch(aggregated, serviceId)
                nr_status = sendToInsights(message)

                if not SILENT:

                    if serviceName:
                        print(f'[#] Service: {serviceName} [{serviceId}] | Fstatus: {fastly_status} | NRstatus: {nr_status} | Timestamp: {timestamp}')
                    else:
                        print(f'[#] Service: {serviceId} | Fstatus: {fastly_status} | NRstatus: {nr_status} | Timestamp: {timestamp}')
                    
                    sys.stdout.flush()

            time.sleep(INTERVAL)
        except:
            print_exc()

def pollFromFastly(serviceId):
    global timestamp
    timestamp = 0

    fastly_url = f'https://rt.fastly.com/v1/channel/{serviceId}/ts/{timestamp}'
    r = requests.get(fastly_url, headers=fastly_headers)

    data = r.json()

    timestamp = data['Timestamp']

    try:
        # If no metrics were recorded, None types are returned except for the timestamp
        aggregated = data['Data'][0]['aggregated']
    except IndexError:
        return None, timestamp, None

    return aggregated, timestamp, r.status_code

def batch(aggregated, service_name):
    '''
    These are all the attributes that Fastly returns. I included every one; if there are any that are less interesting to you feel free to delete those. 
    The Fastly API doesn't return an attribute if the value is 0. So instead of throwing an error, I'm just replacing missing attributes with 0. 
    For more information on the Fastly API, see https://docs.fastly.com/api/

    If aggregated contains data -> returns message data
    If aggregated == None -> Then no metric data was recorded during the Fastly API call and all defaults of 0 are returned in the message data

    //imgopto = Fastly Image Optimizer
    '''

    l = Log()

    if aggregated != None:

        try: l.num_requests = aggregated['requests']
        except KeyError: pass
        try: l.num_tls = aggregated['num_tls']
        except KeyError: pass
        try: l.num_http2 = aggregated['http2']
        except KeyError: pass    
        try: l.num_logs = aggregated['log']
        except KeyError: pass    
        try: l.num_pci = aggregated['pci']
        except KeyError: pass    
        try: l.num_video = aggregated['video']
        except KeyError: pass    
        try: l.ipv6 = aggregated['ipv6']
        except KeyError: pass    
        try: l.pipe = aggregated['pipe']
        except KeyError: pass    
        try: l.uncacheable = aggregated['uncacheable']
        except KeyError: pass    
        try: l.shield = aggregated['shield']
        except KeyError: pass    
        try: l.shield_resp_header_bytes = aggregated['shield_resp_header_bytes']
        except KeyError: pass    
        try: l.shield_resp_body_bytes = aggregated['shield_resp_body_bytes']
        except KeyError: pass    
        try: l.otfp = aggregated['otfp']
        except KeyError: pass    
        try: l.otfp_shield_time = aggregated['otfp_shield_time'][0]
        except KeyError: pass    
        try: l.otfp_deliver_time = aggregated['otfp_deliver_time'][0]
        except KeyError: pass    
        try: l.otfp_manifests = aggregated['otfp_manifests'][0]
        except KeyError: pass    
        try: l.otfp_shield_resp_header_bytes = aggregated['otfp_shield_resp_header_bytes']
        except KeyError: pass    
        try: l.otfp_shield_resp_body_bytes = aggregated['otfp_shield_resp_body_bytes']
        except KeyError: pass    
        try: l.otfp_resp_header_bytes = aggregated['otfp_resp_header_bytes']
        except KeyError: pass    
        try: l.otfp_resp_body_bytes = aggregated['otfp_resp_body_bytes']
        except KeyError: pass    
        try: l.bandwidth = aggregated['bandwidth']
        except KeyError: pass    
        try: l.resp_header_bytes = aggregated['resp_header_bytes']
        except KeyError: pass    
        try: l.header_size = aggregated['header_size']
        except KeyError: pass    
        try: l.resp_body_bytes = aggregated['resp_body_bytes']
        except KeyError: pass    
        try: l.body_size = aggregated['body_size']
        except KeyError: pass    
        try: l.req_body_bytes = aggregated['req_body_bytes']
        except KeyError: pass    
        try: l.req_header_bytes = aggregated['req_header_bytes']
        except KeyError: pass    
        try: l.bereq_header_bytes = aggregated['bereq_header_bytes']
        except KeyError: pass    
        try: l.bereq_body_bytes = aggregated['bereq_body_bytes']
        except KeyError: pass    
        try: l.billed_header_bytes = aggregated['billed_header_bytes']
        except KeyError: pass    
        try: l.billed_body_bytes = aggregated['billed_body_bytes']
        except KeyError: pass    
        try: l.status_2xx = aggregated['status_2xx']
        except KeyError: pass    
        try: l.status_3xx = aggregated['status_3xx']
        except KeyError: pass    
        try: l.status_4xx = aggregated['status_4xx']
        except KeyError: pass    
        try: l.status_5xx = aggregated['status_5xx']
        except KeyError: pass    
        try: l.status_200 = aggregated['status_200']
        except KeyError: pass    
        try: l.status_204 = aggregated['status_204']
        except KeyError: pass    
        try: l.status_301 = aggregated['status_301']
        except KeyError: pass    
        try: l.status_304 = aggregated['status_304']
        except KeyError: pass    
        try: l.status_400 = aggregated['status_400']
        except KeyError: pass    
        try: l.status_401 = aggregated['status_401']
        except KeyError: pass    
        try: l.status_403 = aggregated['status_403']
        except KeyError: pass    
        try: l.status_404 = aggregated['status_404']
        except KeyError: pass    
        try: l.status_500 = aggregated['status_500']
        except KeyError: pass    
        try: l.status_501 = aggregated['status_501']
        except KeyError: pass    
        try: l.status_502 = aggregated['status_502']
        except KeyError: pass    
        try: l.status_503 = aggregated['status_503']
        except KeyError: pass    
        try: l.status_504 = aggregated['status_504']
        except KeyError: pass    
        try: l.status_505 = aggregated['status_505']
        except KeyError: pass    
        try: l.status_1xx = aggregated['status_1xx']
        except KeyError: pass    
        try: l.waf_logged = aggregated['waf_logged']
        except KeyError: pass    
        try: l.waf_blocked = aggregated['waf_blocked']
        except KeyError: pass    
        try: l.waf_passed = aggregated['waf_passed']
        except KeyError: pass    
        try: l.attack_req_body_bytes = aggregated['attack_req_body_bytes']
        except KeyError: pass    
        try: l.attack_req_header_bytes = aggregated['attack_req_header_bytes']
        except KeyError: pass    
        try: l.attack_logged_req_body_bytes = aggregated['attack_logged_req_body_bytes']
        except KeyError: pass    
        try: l.attack_logged_req_header_bytes = aggregated['attack_logged_req_header_bytes']
        except KeyError: pass    
        try: l.attack_blocked_req_body_bytes = aggregated['attack_blocked_req_body_bytes']
        except KeyError: pass    
        try: l.attack_blocked_req_header_bytes = aggregated['attack_blocked_req_header_bytes']
        except KeyError: pass    
        try: l.attack_passed_req_body_bytes = aggregated['attack_passed_req_body_bytes']
        except KeyError: pass    
        try: l.attack_passed_req_header_bytes = aggregated['attack_passed_req_header_bytes']
        except KeyError: pass    
        try: l.attack_resp_synth_bytes = aggregated['attack_resp_synth_bytes']
        except KeyError: pass    
        try: l.hits = aggregated['hits']
        except KeyError: pass    
        try: l.hit_ratio = aggregated['hit_ratio']
        except KeyError: pass    
        try: l.miss = aggregated['miss']
        except KeyError: pass    
        try: l.cache_pass = aggregated['pass']
        except KeyError: pass    
        try: l.pass_time = aggregated['pass_time']
        except KeyError: pass    
        try: l.synth = aggregated['synth']
        except KeyError: pass    
        try: l.errors = aggregated['errors']
        except KeyError: pass    
        try: l.restarts = aggregated['restarts']
        except KeyError: pass    
        try: l.hits_time = aggregated['hits_time']
        except KeyError: pass    
        try: l.miss_time = aggregated['miss_time']
        except KeyError: pass    
        try: l.tls = aggregated['tls']
        except KeyError: pass    
        try: l.tls_v10 = aggregated['tls_v10']
        except KeyError: pass    
        try: l.tls_v11 = aggregated['tls_v11']
        except KeyError: pass    
        try: l.tls_v12 = aggregated['tls_v12']
        except KeyError: pass    
        try: l.tls_v13 = aggregated['tls_v13']
        except KeyError: pass    
        try: l.imgopto = aggregated['imgopto']
        except KeyError: pass    
        try: l.imgopto_resp_body_byte = aggregated['imgopto_resp_body_bytes']
        except KeyError: pass    
        try: l.imgopto_resp_header_bytes = aggregated['imgopto_resp_header_bytes']
        except KeyError: pass    
        try: l.imgopto_shield_resp_body_bytes = aggregated['imgopto_shield_resp_body_bytes']
        except KeyError: pass    
        try: l.imgopto_shield_resp_header_bytes = aggregated['imgopto_shield_resp_header_bytes']
        except KeyError: pass    
        try: l.object_size_1k = aggregated['object_size_1k']
        except KeyError: pass    
        try: l.object_size_10k = aggregated['object_size_10k']
        except KeyError: pass    
        try: l.object_size_100k = aggregated['object_size_100k']
        except KeyError: pass    
        try: l.object_size_1m = aggregated['object_size_1m']
        except KeyError: pass    
        try: l.object_size_10m = aggregated['object_size_10m']
        except KeyError: pass    
        try: l.object_size_100m = aggregated['object_size_100m']
        except KeyError: pass    
        try: l.object_size_1g = aggregated['object_size_1g']
        except KeyError: pass    
        try: l.recv_sub_time = aggregated['recv_sub_time']
        except KeyError: pass    
        try: l.recv_sub_count = aggregated['recv_sub_count']
        except KeyError: pass    
        try: l.hash_sub_time = aggregated['hash_sub_time']
        except KeyError: pass    
        try: l.hash_sub_count = aggregated['hash_sub_count']
        except KeyError: pass    
        try: l.deliver_sub_time = aggregated['deliver_sub_time']
        except KeyError: pass    
        try: l.deliver_sub_count = aggregated['deliver_sub_count']
        except KeyError: pass    
        try: l.hit_sub_time = aggregated['hit_sub_time']
        except KeyError: pass    
        try: l.hit_sub_count = aggregated['hit_sub_count']
        except KeyError: pass    
        try: l.prehash_sub_time = aggregated['prehash_sub_time']
        except KeyError: pass    
        try: l.prehash_sub_count = aggregated['prehash_sub_count']
        except KeyError: pass    
        try: l.predeliver_sub_time = aggregated['predeliver_sub_time']
        except KeyError: pass    
        try: l.predeliver_sub_count = aggregated['predeliver_sub_count']
        except KeyError: pass

    message  = {
        "eventType":                           "LogAggregate",
        "service":                             service_name,
        "num_requests":                        l.num_requests,
        "num_tls":                             l.num_tls,
        "num_http2":                           l.num_http2,
        "num_logs":                            l.num_logs,
        "num_pci":                             l.num_pci,
        "num_video":                           l.num_video,
        "ipv6":                                l.ipv6,
        "pipe":                                l.pipe,
        "uncacheable":                         l.uncacheable,
        "shield":                              l.shield,
        "shield_resp_header_bytes":            l.shield_resp_header_bytes,
        "shield_resp_body_bytes":              l.shield_resp_body_bytes,
        "otfp":                                l.otfp,
        "otfp_shield_time":                    l.otfp_shield_time,
        "otfp_deliver_time":                   l.otfp_deliver_time,
        "otfp_manifests":                      l.otfp_manifests,
        "otfp_shield_resp_header_bytes":       l.otfp_shield_resp_header_bytes,
        "otfp_shield_resp_body_bytes":         l.otfp_shield_resp_body_bytes,
        "otfp_resp_header_bytes":              l.otfp_resp_header_bytes,
        "otfp_resp_body_bytes":                l.otfp_resp_body_bytes,
        "bandwidth":                           l.bandwidth,
        "resp_header_bytes":                   l.resp_header_bytes,
        "header_size":                         l.header_size,
        "resp_body_bytes":                     l.resp_body_bytes,
        "body_size":                           l.body_size,
        "req_body_bytes":                      l.req_body_bytes,
        "req_header_bytes":                    l.req_header_bytes,
        "bereq_header_bytes":                  l.bereq_header_bytes,
        "bereq_body_bytes":                    l.bereq_body_bytes,
        "billed_header_bytes":                 l.billed_header_bytes,
        "billed_body_bytes":                   l.billed_body_bytes,
        "status_2xx":                          l.status_2xx,
        "status_3xx":                          l.status_3xx,
        "status_4xx":                          l.status_4xx,
        "status_5xx":                          l.status_5xx,
        "status_200":                          l.status_200,
        "status_204":                          l.status_204,
        "status_301":                          l.status_301,
        "status_304":                          l.status_304,
        "status_400":                          l.status_400,
        "status_401":                          l.status_401,
        "status_403":                          l.status_403,
        "status_404":                          l.status_404,
        "status_500":                          l.status_500,
        "status_501":                          l.status_501,
        "status_502":                          l.status_502,
        "status_503":                          l.status_503,
        "status_504":                          l.status_504,
        "status_505":                          l.status_505,
        "status_1xx":                          l.status_1xx,
        "waf_logged":                          l.waf_logged,
        "waf_blocked":                         l.waf_blocked,
        "waf_passed":                          l.waf_passed,
        "attack_req_body_bytes":               l.attack_req_body_bytes,
        "attack_req_header_bytes":             l.attack_req_header_bytes,
        "attack_logged_req_body_bytes":        l.attack_logged_req_body_bytes,
        "attack_logged_req_header_bytes":      l.attack_logged_req_header_bytes,
        "attack_blocked_req_body_bytes":       l.attack_blocked_req_body_bytes,
        "attack_blocked_req_header_bytes":     l.attack_blocked_req_header_bytes,
        "attack_passed_req_body_bytes":        l.attack_passed_req_body_bytes,
        "attack_passed_req_header_bytes":      l.attack_passed_req_header_bytes,
        "attack_resp_synth_bytes":             l.attack_resp_synth_bytes,
        "hits":                                l.hits,
        "hit_ratio":                           l.hit_ratio,
        "miss":                                l.miss,
        "pass":                                l.cache_pass,
        "pass_time":                           l.pass_time,
        "synth":                               l.synth,
        "errors":                              l.errors,
        "restarts":                            l.restarts,
        "hits_time":                           l.hits_time,
        "miss_time":                           l.miss_time,
        "tls":                                 l.tls,
        "tls_v10":                             l.tls_v10,
        "tls_v11":                             l.tls_v11,
        "tls_v12":                             l.tls_v12,
        "tls_v13":                             l.tls_v13,
        "imgopto":                             l.imgopto,
        "imgopto_resp_body_bytes":             l.imgopto_resp_body_bytes,
        "imgopto_resp_header_bytes":           l.imgopto_resp_header_bytes,
        "imgopto_shield_resp_body_bytes":      l.imgopto_shield_resp_body_bytes,
        "imgopto_shield_resp_header_bytes":    l.imgopto_shield_resp_header_bytes,
        "object_size_1k":                      l.object_size_1k,
        "object_size_10k":                     l.object_size_10k ,
        "object_size_100k":                    l.object_size_100k,
        "object_size_1m":                      l.object_size_1m ,
        "object_size_10m":                     l.object_size_10m,
        "object_size_100m":                    l.object_size_100m,
        "object_size_1g":                      l.object_size_1g,
        "recv_sub_time":                       l.recv_sub_time,
        "recv_sub_count":                      l.recv_sub_count,
        "hash_sub_time":                       l.hash_sub_time,
        "hash_sub_count":                      l.hash_sub_count,
        "deliver_sub_time":                    l.deliver_sub_time,
        "deliver_sub_count":                   l.deliver_sub_count,
        "hit_sub_time":                        l.hit_sub_time,
        "hit_sub_count":                       l.hit_sub_count,
        "prehash_sub_time":                    l.prehash_sub_time,
        "prehash_sub_count":                   l.prehash_sub_count,
        "predeliver_sub_time":                 l.predeliver_sub_time,
        "predeliver_sub_count":                l.predeliver_sub_count
    }

    return message

def serviceExtractor(service_map):
    try:
        service_map_split = service_map.split(':')
        serviceName = service_map_split[0]
        serviceId = service_map_split[1]
    except:
        serviceName = False
        serviceId = service_map
    return serviceName, serviceId

def sendToInsights(message):
    '''
    Sends a POST request with aggregated data to New Relic Insights
    If the request fails, it is printed out and returns "failed"
    '''

    data = zlib.compress(json.dumps(message).encode('utf-8'))
    r = requests.post(insights_url, headers=nr_headers, data=data)
    return r.status_code

if __name__ == "__main__":
    main()