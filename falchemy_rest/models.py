from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.declarative import has_inherited_table

from sqlalchemy import Column, Integer, String, Boolean,DateTime,ForeignKey,Numeric,UniqueConstraint


#define model fields

def CharField(max_length,*args,**kwargs):
    return Column(String(max_length),*args,**kwargs)

def DateTimeField(*args,**kwargs):
    return Column(DateTime,*args,**kwargs)
 
def BooleanField(*args,**kwargs):
    return Column(Boolean,*args,**kwargs)

def IntegerField(*args,**kwargs):
    return Column(Integer,*args,**kwargs)

def ForeignKeyField(references,*args,**kwargs):
    return CharField(50,ForeignKey(references),*args, **kwargs)

def TenantField(**kwargs):
    return CharField(50, nullable=False,**kwargs)

def DecimalField(max_digits,decimal_places,*args,**kwargs):
    return Column(Numeric(precision = max_digits, scale = decimal_places),*args,**kwargs)

def UniqueTogether(*args,**kwargs):
    return UniqueConstraint(*args,**kwargs)


import uuid

import datetime

def utc_now():
    return datetime.datetime.utcnow()

def utc_timestamp():
    t = utc_now().timestamp()
    return str(t).split('.')[0]

def hex_uuid():
    return uuid.uuid4().hex

def utc_pk():
    return utc_timestamp() + hex_uuid()



class CRUDMixin:
    #Column('deleted',Boolean,default = False)

 
    @classmethod
    def all(cls):
        return cls.__table__.select()
    
    @classmethod
    def insert(cls):
        return cls.__table__.insert()

    @classmethod
    def delete(cls):
        return cls.__table__.delete()
    
    @classmethod
    def update(cls):
        return cls.__table__.update()
    
    @classmethod
    def get(cls, pk):
        return cls.all().where(cls.id == pk)

        




    


class TimestampMixin:
    created_at = Column(DateTime,nullable = False,default = utc_now)
    updated_at = Column(DateTime,nullable = False,default = utc_now,onupdate = utc_now)
    

class BaseTable(CRUDMixin,TimestampMixin):
    @declared_attr
    def __tablename__(cls):
        name = cls.__make_name()
        return name.lower() + 's'
        
    id = Column(String(50), primary_key = True, default = utc_pk )


    @classmethod
    def __make_char(cls,index,char):
        if char.isupper() and index != 0:
            return '_' + char.lower()
        
        return char
    
    @classmethod
    def __make_name(cls):
        new_string_l = []
        current_name = cls.__name__

        if current_name.isupper():
            #this is one name that is upper all
            return current_name

        for index,char in enumerate(current_name):
            new_char = cls.__make_char(index,char)

            new_string_l.append(new_char)
        

        new_string = ''.join(new_string_l)

        return new_string
        






class HasTenantMixin:

    @declared_attr
    def tenant_id(cls):
        return Column(String(50), ForeignKey('tenants.id') , nullable = False)


Base = declarative_base(cls = BaseTable)
 









