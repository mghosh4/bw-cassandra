import ConfigParser

__author__ = 'Daniel'


class BaseProfile(object):
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        pass


class BlueWatersProfile(BaseProfile):
    def __init__(self):
        BaseProfile.__init__(self)
        self.config.read('bw-config.ini')

    # Get host names in .crayccm file
    def get_hosts(self):
        hosts = set()
        for fn in os.listdir('/u/sciteam/shin1/.crayccm/'):
            f = open('/u/sciteam/shin1/.crayccm/%s' % fn)
            lines = f.read().splitlines()
            for line in lines:
                host = line
                hosts.add(host)

            break  # Break after first file
        return list(hosts)


class EmulabProfile(BaseProfile):
    def __init__(self):
        BaseProfile.__init__(self)
        self.config.read('emulab-config.ini')

    def get_hosts(self):
        hosts = set()
        f = open('/etc/hosts')
        lines = f.read().splitlines()
        for line in lines:
            tokens = line.split()
            if len(tokens) < 4:
                continue
            elif tokens[3].find('node') == -1:
                continue
            else:
                host = tokens[3]
                hosts.add(host)
        return list(hosts)