#The hpfeeds module is written by  Mark Schloesser, refer to https://github.com/rep/hpfeeds/blob/master/cli/hpfeeds-client
import sys
import optparse
import datetime
import logging
import string
logging.basicConfig(level=logging.CRITICAL)

import hpfeeds

def log(msg):
    print '[feedcli] {0}'.format(msg)

def main(opts, action, pubdata=None):
    outfd = None
    if opts.output:
        try: outfd = open(opts.output, 'a')
        except:
            log('could not open output file for message log.')
            return 1
    else:
        outfd = sys.stdout

    try: hpc = hpfeeds.new(opts.host, opts.port, opts.ident, opts.secret)
    except hpfeeds.FeedException, e:
        log('Error: {0}'.format(e))
        return 1
    
    log('connected to {0}'.format(hpc.brokername))

    if action == 'subscribe':
        def on_message(ident, chan, payload):
            if [i for i in payload[:20] if i not in string.printable]:
                log('publish to {0} by {1}: {2}'.format(chan, ident, payload[:20].encode('hex') + '...'))
            else:
                log('publish to {0} by {1}: {2}'.format(chan, ident, payload))

        def on_error(payload):
            log('Error message from broker: {0}'.format(payload))
            hpc.stop()

        hpc.subscribe(opts.channels)
        try: hpc.run(on_message, on_error)
        except hpfeeds.FeedException, e:
            log('Error: {0}'.format(e))
            return 1

    elif action == 'publish':
        hpc.publish(opts.channels, pubdata)

    elif action == 'sendfile':
        pubfile = open(pubdata, 'rb').read()
        hpc.publish(opts.channels, pubfile)

    log('closing connection.')
    hpc.close()

    return 0

def opts():
    usage = "usage: %prog -i ident -s secret --host host -p port -c channel1 [-c channel2, ...] <action> [<data>]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--chan",
        action="append", dest='channels', nargs=1, type='string',
        help="channel (can be used multiple times)")
    parser.add_option("-i", "--ident",
        action="store", dest='ident', nargs=1, type='string',
        help="authkey identifier")
    parser.add_option("-s", "--secret",
        action="store", dest='secret', nargs=1, type='string',
        help="authkey secret")
    parser.add_option("--host",
        action="store", dest='host', nargs=1, type='string',
        help="broker host")
    parser.add_option("-p", "--port",
        action="store", dest='port', nargs=1, type='int',
        help="broker port")
    parser.add_option("-o", "--output",
        action="store", dest='output', nargs=1, type='string',
        help="publish log filename")

    options, args = parser.parse_args()

    if len(args) < 1:
        parser.error('You need to give "subscribe" or "publish" as <action>.')
    if args[0] not in ['subscribe', 'publish', 'sendfile']:
        parser.error('You need to give "subscribe" or "publish" as <action>.')

    action = args[0]
    data = None
    if action == 'publish':
        data = ' '.join(args[1:])
    elif action == 'sendfile':
        data = ' '.join(args[1:])

    return options, action, data

if __name__ == '__main__':
    options, action, data = opts()
    try:
        sys.exit(main(options, action, pubdata=data))
    except KeyboardInterrupt:
        sys.exit(0)
