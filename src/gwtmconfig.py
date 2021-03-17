from numpy import genfromtxt


class Config():
    def __init__(self, directory, _file):
        self.directory = directory
        self.file = _file
    
    def run(self):
        data=genfromtxt(self.directory+self.file,str)
        gg={}
        for i in data:
            try:
                gg[i[0]]=eval(i[1])
            except:
                gg[i[0]]=i[1]
        return gg
