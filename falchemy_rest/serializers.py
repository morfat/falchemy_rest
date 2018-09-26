import serpy

import falcon
import json

class DictField(serpy.Field):
    def to_value(self,value):
        try:
            return json.loads(value)
        except TypeError:
            return json.dumps(value)


class BaseSerializer(serpy.DictSerializer):

    id = serpy.StrField( required = False)
    created_at = serpy.StrField( required = False)
    updated_at = serpy.StrField( required = False)

    class Meta:
        read_protected_fields = ()
        write_protected_fields = ('id','created_at','updated_at')
    
    def __is_valid(self,internal = False):
        try:
            self.data #this raises exception if data required is not given
            return True
        except KeyError as ke:
            if internal:
                raise KeyError
            raise falcon.HTTPBadRequest(title = "Missing Request Parameters", description = "{field} is a required field".format( field = ke) )
    
        
 
   
    def __remove_from_data(self,fields, data):
        for k in list(data.keys()):
            if k in fields:
                del data[k]
        
        return data
    
    def protect_data(self, protected_fields, data):
        try:
            #clean remove read protextect fields
            self.__remove_from_data( fields = protected_fields,data = data)

        except AttributeError:
            #probably data is list of dicts
            for d in data:
                self.__remove_from_data( fields = protected_fields ,data = d)
        
        return data


    @property
    def valid_read_data(self):
        if self.__is_valid():
            valid_data =  self.protect_data( protected_fields = self.Meta.read_protected_fields, data = self.data )
            return valid_data

    @property
    def valid_write_data(self):
       if self.__is_valid():
            valid_data =  self.protect_data( protected_fields = self.Meta.write_protected_fields, data = self.data )
            return valid_data