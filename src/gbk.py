import btree

class GBKFont:
    def __init__(self):
        try:
            self.f = open('gbk16x16.btree', 'rb') #打开文件
            self.fontDB = btree.open(self.f)  #打开数据库
        except OSError:
            self.f=None 
            self.fontDB=None
            print('Failed to load the fontDB!')
    
    def deinit(self):
        if self.fontDB is not  None:
            self.fontDB.close()
            self.f.close()
    
    def get(self, ch):
        if self.fontDB is None:       
            return 0, 0, bytearray()
        else:        
            bm = bytearray(self.fontDB.get(ch[0].encode(), self.fontDB[b"*"]))   #在数据库内查找文字点阵图 
            w = len(bm) // 2       
            return w, 16, bm #返回字符信息