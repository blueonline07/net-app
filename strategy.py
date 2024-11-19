import heapq

class TitOrTat:
    def __init__(self):
        self.downloaded_from= dict() # keep track of how much you have downloaded from each peer

    def init_downloaded_from(self, ip):
        self.downloaded_from[ip] = 0
    
    def get_unchoke_peers(self, num_peers):
        l = heapq.nlargest(num_peers, self.downloaded_from.items(), key=lambda x: x[1])
        return [peer for peer, _ in l]
    
    def inc_peer_downloaded(self, ip):
        self.downloaded_from[ip] += 1

    def test_init_downloaded_from(self):
        self.downloaded_from = {
            '172.18.0.2' : 8, #docker containers ip
            '172.18.0.3' : 7,
            '172.18.0.4' : 3,
            '172.18.0.5' : 4,
            '172.18.0.6' : 2
        }