import heapq

num_peers = 4

class TitOrTat:
    def __init__(self, peers):
        self.peer_downloads = dict() # keep track of how much you have downloaded from each peer
        for peer in peers:
            self.peer_downloads[peer['peer_id']] = 0
    
    def get_unchoke_peers(self, num_peers):
        return heapq.nlargest(num_peers, self.peer_downloads, key=self.peer_downloads.get)
    
    def inc_peer_downloaded(self, peer_id):
        self.peer_downloads[peer_id] += 1