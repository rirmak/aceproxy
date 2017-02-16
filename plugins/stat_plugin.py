'''
Simple statistics plugin

To use it, go to http://127.0.0.1:8000/stat
'''
from modules.PluginInterface import AceProxyPlugin
import time
import json
import plugins.modules.ipaddr as ipaddr
import urllib2

localnetranges = (
        '192.168.0.0/16',
        '10.0.0.0/8',
        '172.16.0.0/12',
        '224.0.0.0/4',
        '240.0.0.0/5',
        '127.0.0.0/8',
        )

class Stat(AceProxyPlugin):
    handlers = ('stat', 'favicon.ico')

    def __init__(self, AceConfig, AceStuff):
        self.config = AceConfig
        self.stuff = AceStuff

    def geo_ip_lookup(self, ip_address):
        """
         Look up the geo information based on the IP address passed in
        """
        GEOIP_LOOKUP_URL = 'http://api.2ip.ua/geo.json?ip=%s'
        lookup_url = GEOIP_LOOKUP_URL % ip_address
        req = urllib2.Request(lookup_url, headers={'User-Agent' : "Magic Browser"})
        response = json.loads(urllib2.urlopen(req, timeout=10).read())
        
        return {'country_code' : response['country_code'],
                'country'      : response['country'],
                'region'       : response['region'],
                'city'         : response['city'],
                }

    def handle(self, connection, headers_only=False):
        current_time = time.time()

        if connection.reqtype == 'favicon.ico':
            connection.send_response(404)
            return
        
        connection.send_response(200)
        connection.send_header('Content-type', 'text/html; charset=utf-8')
        connection.end_headers()
        
        if headers_only:
            return
        
        connection.wfile.write(
            '<meta http-equiv="Refresh" content="60" />'
            '<html><body><h4>Connected clients: ' + str(self.stuff.clientcounter.total) + '</h4>')
        connection.wfile.write(
            '<h5>Concurrent connections limit: ' + str(self.config.maxconns) + '</h5><table  border="1" cellspacing="0" cellpadding="3">')
        for i in self.stuff.clientcounter.clients:
            for c in self.stuff.clientcounter.clients[i]:
                connection.wfile.write('<tr><td>')
                if c.channelIcon:
                    connection.wfile.write('<img src="' + c.channelIcon + '" width="40" height="16" />&nbsp;')
                if c.channelName:
                    connection.wfile.write(c.channelName.encode('UTF8'))
                else:
                    connection.wfile.write(i)

                connection.wfile.write('</td><td>' + c.handler.clientip + '</td>')
                clientinrange = any(map(lambda i: ipaddr.IPAddress(c.handler.clientip) in ipaddr.IPNetwork(i),localnetranges))

                if clientinrange: 
                   connection.wfile.write('<td>' + 'Local IP adress' + '</td>')
                else:
                   geo_ip_info = self.geo_ip_lookup(c.handler.clientip)
                   connection.wfile.write('<td>' + geo_ip_info.get('country') + ', ' + geo_ip_info.get('city') + '</td>')

                connection.wfile.write('<td>' + time.strftime('%c', time.localtime(c.connectionTime)) + '</td>')
                connection.wfile.write('<td>' + time.strftime("%H:%M:%S",  time.gmtime(current_time-c.connectionTime)) + '</td></tr>')
        connection.wfile.write('</table></body></html>')
