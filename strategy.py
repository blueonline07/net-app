import heapq

num_peers = 4

class TitOrTat:
    def __init__(self, peers):
        self.peer_downloads = [] # keep track of how much you have downloaded from each peer
        for peer in peers:
            self.peer_downloads.append({'peer_id': peer['peer_id'],'ip':peer['ip'], 'port':peer['port'], 'downloaded': 0})
    
    def get_unchoke_peers(self, num_peers):
        return heapq.nlargest(num_peers, self.peer_downloads, key=lambda x: (x['downloaded'], x['peer_id']))
    
    def inc_peer_downloaded(self, peer_id):
        for peer in self.peer_downloads:
            if peer['peer_id'] == peer_id:
                peer['downloaded'] += 1
                break