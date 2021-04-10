"""
Fastly Tempo
"""
from collections import defaultdict
import json
import os
import sys
import time
import zlib
from traceback import print_exc
from threading import Thread, Lock
import requests

############## Environment Variables ##############

try:
    ACCOUNT_ID = os.environ['ACCOUNT_ID']
    INSERT_KEY = os.environ['INSERT_KEY']
    FASTLY_KEY = os.environ['FASTLY_KEY']
except:
    print('[!] Error: Please ensure you are providing the following ENV VARS: ACCOUNT_ID, INSERT_KEY, and FASTLY_KEY.')
    sys.stdout.flush()
    sys.exit(1)

# Setting the polling interval in seconds
try:
    INTERVAL = int(os.environ['INTERVAL'])
except KeyError:
    INTERVAL = 1

# Get Silent ENV to determine if info will be printed
try:
    SILENT = os.environ['SILENT'].upper() == 'TRUE'
except KeyError:
    SILENT = False

############# End Environment Variables #############

# Sets Default Dict values to 0 when logs are not present for a service
DEFAULT_DICT = {}
DEFAULT_DICT = defaultdict(lambda: 0, DEFAULT_DICT)

# Sets static variables for URLs and headers
INSIGHTS_URL = f'https://insights-collector.newrelic.com/v1/accounts/{ACCOUNT_ID}/events'
NR_HEADERS = {'content-encoding': 'deflate', 'X-Insert-Key': INSERT_KEY, 'Content-Type': 'application/json"'}
FASTLY_HEADERS = {'Content-Type': 'application/json', 'Fastly-Key': FASTLY_KEY}

class Service:
    """
    Fastly Service Class
    """
    def __init__(self):
        """
        Constructs all the necessary attributes for the Service object.

        Parameters
        ----------
            service_id : str - service_id of a Fastly service
            service_name : str - a friendly service name for a Fastly service
            display_name : str - the name to be displayed for a Fastly service in various functions
            timestamp : int - unix timestamp of a request to Fastly's API
            aggregated : dict - a structured dictionary of aggregated Fastly metrics for a service
            fastly_status : int - http status code from the Fastly API
            fastly_body : str - text response from the Fastly API (useful for debugging)
            message : dict - a structured dictionary of aggregated Fastly metrics to be sent to an endpoint
        """
        self.service_id = str
        self.service_name = str
        self.display_name = str
        self.timestamp = int
        self.aggregated_list = list
        self.fastly_status = int
        self.fastly_body = str
        self.message = DEFAULT_DICT

def get_services():
    """
    Gets a list of Fastly services to loop through and collect logs for.
    Returns a list[] containing dicts{} of Fastly service info
    """

    # Gets services from "SERVICES" env var
    try:
        list_of_services = [service_extractor(service_map) for service_map in os.environ['SERVICES'].split(" ")]
    except KeyError:
        print('[!] Error: No services provided. Provide services as environment variables...')
        print('Format: services=<NameOfService1>:<service_id1> <NameOfService2>:<service_id2>')
        print('This can easily be added via a docker .env file')
        sys.stdout.flush()
        sys.exit(1)

    # Sets max name length for print_output()
    global MAX_LEN 
    MAX_LEN = 0
    for idx, service in enumerate(list_of_services):
        if service.service_name:
            service.display_name = service.service_name
        else:
            service.display_name = service.service_id

        if len(service.display_name) > MAX_LEN:
            MAX_LEN = len(service.display_name)

        list_of_services[idx] = service

    return list_of_services

def poll_from_fastly(service):
    """
    Polls logs from the Fastly 'real-time' API

    :return:
    [aggregated_list] list of dicts of aggregated Fastly service data
    """

    # Polls Fastly's API
    fastly_url = f'https://rt.fastly.com/v1/channel/{service.service_id}/ts/{service.timestamp}'
    resp = requests.get(fastly_url, headers=FASTLY_HEADERS)
    data = resp.json()

    # Get imporant service (service) class object values and data
    service.timestamp = data['Timestamp']
    service.fastly_status = resp.status_code
    service.fastly_body = resp.text
    try:
        # If aggregated data is present, return it. Else, return None
        aggregated_list = data['Data']
        if len(aggregated_list) == 0:
            aggregated_list = None
    except IndexError:
        aggregated_list = None

    return aggregated_list

def batch(service, aggregated_list):
    """
    These are all the attributes that Fastly returns. I included every one; if there are any that are less interesting to you feel free to delete those.
    The Fastly API doesn't return an attribute if the value is 0. So instead of throwing an error, I'm just replacing missing attributes with 0.
    For more information on the Fastly API, see https://docs.fastly.com/api/

    If aggregated_list contains data -> returns aggregated message data
    If aggregated_list == None -> Then no metric data was recorded during the Fastly API call and all defaults of 0 are returned in the message data

    //imgopto = Fastly Image Optimizer (IO)

    :inputs:
    service - "service" class
    aggregated_list - list of all aggregated messages from Fastly at a 1 sec interval
    :returns: (technically no returns. just updates service class object in local scope)
    service - "service" class with updated message

    """

    if aggregated_list:

        for aggregate in aggregated_list:
            aggregate = aggregate['aggregated']

            service.message = {
                "eventType":                           "FastlyLogAggregate",
                "service":                             service.display_name,
                "num_requests":                        service.message['num_requests'] + aggregate.get('requests', 0),
                "num_tls":                             service.message['num_tls'] + aggregate.get('num_tls', 0),
                "num_http2":                           service.message['num_http2'] + aggregate.get('http2', 0),
                "num_logs":                            service.message['num_logs'] + aggregate.get('log', 0),
                "num_pci":                             service.message['num_pci'] + aggregate.get('pci', 0),
                "num_video":                           service.message['num_video'] + aggregate.get('video', 0),
                "ipv6":                                service.message['ipv6'] + aggregate.get('ipv6', 0),
                "pipe":                                service.message['pipe'] + aggregate.get('pipe', 0),
                "uncacheable":                         service.message['uncacheable'] + aggregate.get('uncacheable', 0),
                "shield":                              service.message['shield'] + aggregate.get('shield', 0),
                "shield_resp_header_bytes":            service.message['shield_resp_header_bytes'] + aggregate.get('shield_resp_header_bytes', 0),
                "shield_resp_body_bytes":              service.message['shield_resp_body_bytes'] + aggregate.get('shield_resp_body_bytes', 0),
                "otfp":                                service.message['otfp'] + aggregate.get('otfp', 0),
                "otfp_shield_time":                    service.message['otfp_shield_time'] + aggregate.get('otfp_shield_time', 0),
                "otfp_deliver_time":                   service.message['otfp_deliver_time'] + aggregate.get('otfp_deliver_time', 0),
                "otfp_manifests":                      service.message['otfp_manifests'] + aggregate.get('otfp_manifests', 0),
                "otfp_shield_resp_header_bytes":       service.message['otfp_shield_resp_header_bytes'] + aggregate.get('otfp_shield_resp_header_bytes', 0),
                "otfp_shield_resp_body_bytes":         service.message['otfp_shield_resp_body_bytes'] + aggregate.get('otfp_shield_resp_body_bytes', 0),
                "otfp_resp_header_bytes":              service.message['otfp_resp_header_bytes'] + aggregate.get('otfp_resp_header_bytes', 0),
                "otfp_resp_body_bytes":                service.message['otfp_resp_body_bytes'] + aggregate.get('otfp_resp_body_bytes', 0),
                "bandwidth":                           service.message['bandwidth'] + aggregate.get('bandwidth', 0),
                "resp_header_bytes":                   service.message['resp_header_bytes'] + aggregate.get('resp_header_bytes', 0),
                "header_size":                         service.message['header_size'] + aggregate.get('header_size', 0),
                "resp_body_bytes":                     service.message['resp_body_bytes'] + aggregate.get('resp_body_bytes', 0),
                "body_size":                           service.message['body_size'] + aggregate.get('body_size', 0),
                "req_body_bytes":                      service.message['req_body_bytes'] + aggregate.get('req_body_bytes', 0),
                "req_header_bytes":                    service.message['req_header_bytes'] + aggregate.get('req_header_bytes', 0),
                "bereq_header_bytes":                  service.message['bereq_header_bytes'] + aggregate.get('bereq_header_bytes', 0),
                "bereq_body_bytes":                    service.message['bereq_body_bytes'] + aggregate.get('bereq_body_bytes', 0),
                "billed_header_bytes":                 service.message['billed_header_bytes'] + aggregate.get('billed_header_bytes', 0),
                "billed_body_bytes":                   service.message['billed_body_bytes'] + aggregate.get('billed_body_bytes', 0),
                "status_2xx":                          service.message['status_2xx'] + aggregate.get('status_2xx', 0),
                "status_3xx":                          service.message['status_3xx'] + aggregate.get('status_3xx', 0),
                "status_4xx":                          service.message['status_4xx'] + aggregate.get('status_4xx', 0),
                "status_5xx":                          service.message['status_5xx'] + aggregate.get('status_5xx', 0),
                "status_200":                          service.message['status_200'] + aggregate.get('status_200', 0),
                "status_204":                          service.message['status_204'] + aggregate.get('status_204', 0),
                "status_301":                          service.message['status_301'] + aggregate.get('status_301', 0),
                "status_304":                          service.message['status_304'] + aggregate.get('status_304', 0),
                "status_400":                          service.message['status_400'] + aggregate.get('status_400', 0),
                "status_401":                          service.message['status_401'] + aggregate.get('status_401', 0),
                "status_403":                          service.message['status_403'] + aggregate.get('status_403', 0),
                "status_404":                          service.message['status_404'] + aggregate.get('status_404', 0),
                "status_500":                          service.message['status_500'] + aggregate.get('status_500', 0),
                "status_501":                          service.message['status_501'] + aggregate.get('status_501', 0),
                "status_502":                          service.message['status_502'] + aggregate.get('status_502', 0),
                "status_503":                          service.message['status_503'] + aggregate.get('status_503', 0),
                "status_504":                          service.message['status_504'] + aggregate.get('status_504', 0),
                "status_505":                          service.message['status_505'] + aggregate.get('status_505', 0),
                "status_1xx":                          service.message['status_1xx'] + aggregate.get('status_1xx', 0),
                "waf_logged":                          service.message['waf_logged'] + aggregate.get('waf_logged', 0),
                "waf_blocked":                         service.message['waf_blocked'] + aggregate.get('waf_blocked', 0),
                "waf_passed":                          service.message['waf_passed'] + aggregate.get('waf_passed', 0),
                "attack_req_body_bytes":               service.message['attack_req_body_bytes'] + aggregate.get('attack_req_body_bytes', 0),
                "attack_req_header_bytes":             service.message['attack_req_header_bytes'] + aggregate.get('attack_req_header_bytes', 0),
                "attack_logged_req_body_bytes":        service.message['attack_logged_req_body_bytes'] + aggregate.get('attack_logged_req_body_bytes', 0),
                "attack_logged_req_header_bytes":      service.message['attack_logged_req_header_bytes'] + aggregate.get('attack_logged_req_header_bytes', 0),
                "attack_blocked_req_body_bytes":       service.message['attack_blocked_req_body_bytes'] + aggregate.get('attack_blocked_req_body_bytes', 0),
                "attack_blocked_req_header_bytes":     service.message['attack_blocked_req_header_bytes'] + aggregate.get('attack_blocked_req_header_bytes', 0),
                "attack_passed_req_body_bytes":        service.message['attack_passed_req_body_bytes'] + aggregate.get('attack_passed_req_body_bytes', 0),
                "attack_passed_req_header_bytes":      service.message['attack_passed_req_header_bytes'] + aggregate.get('attack_passed_req_header_bytes', 0),
                "attack_resp_synth_bytes":             service.message['attack_resp_synth_bytes'] + aggregate.get('attack_resp_synth_bytes', 0),
                "hits":                                service.message['hits'] + aggregate.get('hits', 0),
                "hit_ratio":                           service.message['hit_ratio'] + aggregate.get('hit_ratio', 0),
                "miss":                                service.message['miss'] + aggregate.get('miss', 0),
                "pass":                                service.message['pass'] + aggregate.get('cache_pass', 0),
                "pass_time":                           service.message['pass_time'] + aggregate.get('pass_time', 0),
                "synth":                               service.message['synth'] + aggregate.get('synth', 0),
                "errors":                              service.message['errors'] + aggregate.get('errors', 0),
                "restarts":                            service.message['restarts'] + aggregate.get('restarts', 0),
                "hits_time":                           service.message['hits_time'] + aggregate.get('hits_time', 0),
                "miss_time":                           service.message['miss_time'] + aggregate.get('miss_time', 0),
                "tls":                                 service.message['tls'] + aggregate.get('tls', 0),
                "tls_v10":                             service.message['tls_v10'] + aggregate.get('tls_v10', 0),
                "tls_v11":                             service.message['tls_v11'] + aggregate.get('tls_v11', 0),
                "tls_v12":                             service.message['tls_v12'] + aggregate.get('tls_v12', 0),
                "tls_v13":                             service.message['tls_v13'] + aggregate.get('tls_v13', 0),
                "imgopto":                             service.message['imgopto'] + aggregate.get('imgopto', 0),
                "imgopto_resp_body_bytes":             service.message['imgopto_resp_body_bytes'] + aggregate.get('imgopto_resp_body_bytes', 0),
                "imgopto_resp_header_bytes":           service.message['imgopto_resp_header_bytes'] + aggregate.get('imgopto_resp_header_bytes', 0),
                "imgopto_shield_resp_body_bytes":      service.message['imgopto_shield_resp_body_bytes'] + aggregate.get('imgopto_shield_resp_body_bytes', 0),
                "imgopto_shield_resp_header_bytes":    service.message['imgopto_shield_resp_header_bytes'] + aggregate.get('imgopto_shield_resp_header_bytes', 0),
                "object_size_1k":                      service.message['object_size_1k'] + aggregate.get('object_size_1k', 0),
                "object_size_10k":                     service.message['object_size_10k'] + aggregate.get('object_size_10k', 0),
                "object_size_100k":                    service.message['object_size_100k'] + aggregate.get('object_size_100k', 0),
                "object_size_1m":                      service.message['object_size_1m'] + aggregate.get('object_size_1m', 0),
                "object_size_10m":                     service.message['object_size_10m'] + aggregate.get('object_size_10m', 0),
                "object_size_100m":                    service.message['object_size_100m'] + aggregate.get('object_size_100m', 0),
                "object_size_1g":                      service.message['object_size_1g'] + aggregate.get('object_size_1g', 0),
                "recv_sub_time":                       service.message['recv_sub_time'] + aggregate.get('recv_sub_time', 0),
                "recv_sub_count":                      service.message['recv_sub_count'] + aggregate.get('recv_sub_count', 0),
                "hash_sub_time":                       service.message['hash_sub_time'] + aggregate.get('hash_sub_time', 0),
                "hash_sub_count":                      service.message['hash_sub_count'] + aggregate.get('hash_sub_count', 0),
                "deliver_sub_time":                    service.message['deliver_sub_time'] + aggregate.get('deliver_sub_time', 0),
                "deliver_sub_count":                   service.message['deliver_sub_count'] + aggregate.get('deliver_sub_count', 0),
                "hit_sub_time":                        service.message['hit_sub_time'] + aggregate.get('hit_sub_time', 0),
                "hit_sub_count":                       service.message['hit_sub_count'] + aggregate.get('hit_sub_count', 0),
                "prehash_sub_time":                    service.message['prehash_sub_time'] + aggregate.get('prehash_sub_time', 0),
                "prehash_sub_count":                   service.message['prehash_sub_count'] + aggregate.get('prehash_sub_count', 0),
                "predeliver_sub_time":                 service.message['predeliver_sub_time'] + aggregate.get('predeliver_sub_time', 0),
                "predeliver_sub_count":                service.message['predeliver_sub_count'] + aggregate.get('predeliver_sub_count', 0)
            }

def service_extractor(service_map):
    """
    Extracts the service_name and service_id and saves each to its own variable

    All returns are updating values in the Service class object "service".

    If the ServiceName:ServiceId format is used:
    :return:
    [service_name] The Fastly service_name
    [service_id] The Fastly service_id

    If the ServiceId format is used:
    :return:
    [service_name] - Always False
    [service_id] The Fastly service_id
    """

    service = Service()

    try:
        # ServiceName:ServiceId format extraction
        service_map_split = service_map.split(':')
        service.service_name = service_map_split[0]
        service.service_id = service_map_split[1]
    except IndexError:
        # ServiceId format only extraction
        service.service_name = False
        service.service_id = service_map

    # Sets the initial timestamp to 0 (now)
    service.timestamp = 0

    return service

def send_to_insights(service):
    """
    Sends a POST request with aggregated data to New Relic Insights
    If the request fails, it is printed out and returns 'False'
    - NRstatus ~ New Relic HTTP status code
    """

    try:
        data = zlib.compress(json.dumps(service.message).encode('utf-8'))
        resp = requests.post(INSIGHTS_URL, headers=NR_HEADERS, data=data)
        print_output(service, resp.status_code, 'NRstatus')
        return True
    except:
        print_exc()
        return False

def print_output(service, status_code, friendly_output_name):
    """
    Used for printing the output of POST requests to monitoring services.
    About: If the env var "SILENT" is set to "False", this will print to stdout with a few values
    Example Output: [#] Service: TestService [12a34b56] | Fstatus: 200 | NRstatus: 200 | Timestamp: 1234567890
    Where Fstatus = Fastly and NRstatus = {service} variable set as a function param
    - Fstatus ~ Fastly API HTTP status code
    - Freq ~ Aggregated HTTP requests to a Fastly Service
    - friendly_output_name ~ the name of an external service used and its friendly name to output | Ex: New Relic, Datadog, etc
    """

    if not SILENT and service.fastly_status == 200:
        print(f'[#] Service: {service.display_name:.<{MAX_LEN}} [{service.service_id}] | Fstatus: {service.fastly_status} | {friendly_output_name}: {status_code} | Timestamp: {service.timestamp} | Freqs: {service.message["num_requests"]:0>10}')

        sys.stdout.flush()

    elif service.fastly_status != 200:
        print(f'[!] Error | Service: {service.display_name} | Fastly Status: {service.fastly_status} | {service.fastly_body}')

def main():
    """
    Main App Function - Polls Fastly Metrics and sends to New Relic
    """

    if not SILENT:
        print("""

        ############################################################
        [#] Starting: FASTLY TEMPO 
        ############################################################
        
        """)
        sys.stdout.flush()

    list_of_services = get_services()

    threads = []
    lock = Lock()

    while True:

        for idx, service in enumerate(list_of_services):

            try:
                t = Thread(target=main_thread, args=[service, idx, lock, list_of_services])
                threads.append(t)
                t.start()

            except:
                print_exc()
                continue

        for thread in threads:
            thread.join()

        # Optional Sleep
        time.sleep(INTERVAL)

def main_thread(service, idx, lock, list_of_services):
    """
    Main Thread which does the processing for each service
    All code runs in parallel and applies a "lock" to the list_of_services list
    """
    # Polls Fastly's API for aggregated metrics
    aggregated_list = poll_from_fastly(service)

    # Creates a batch dict of aggregated values
    batch(service, aggregated_list)

    ############ SEND Metrics Data ############
    send_to_insights(service)
    ###########################################

    # Clear message after send
    service.message = DEFAULT_DICT

    # Updates list_of_services list with new values
    with lock:
        list_of_services[idx] = service

if __name__ == "__main__":
    main()
