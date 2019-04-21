from taObject import TAObject
from canopen.objectdictionary import Variable, DOMAIN

class TAODVariable(Variable):
    def __init__(self, obj: TAObject, name: str = "Unnamed"):
        self.__obj = obj
        super().__init__(name, obj.idx, obj.subIdx)
        self.value = self.__obj.data
        self.data_type = DOMAIN
        self.access_type = "ro"