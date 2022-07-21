class dec:
    def __init__(self,  num) -> None:
        self.num = num
        
    def __call__(self, func):
        print(f"__call___ | {id(self.num)} | {self.num}")
        return func(self, self.num)
    
    
class chair:
    
    @dec(200)
    def process(self, item):
        print (f"process({item})")
        

c = chair()

c.process(5)