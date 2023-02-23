import hashlib

class HashManager:
    """ Hash manager class """
    @classmethod
    def getSHA1file(cls, file):
        """ Get SHA1 hash of file 
        
        Args:
            file (File): File to hash

        Returns:
            str: SHA1 hash of file
        """
        BLOCKSIZE = 65536
        hasher = hashlib.sha1()
        buf = file.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
        return (hasher.hexdigest())