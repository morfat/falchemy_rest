import falcon 

from .pagination import Paginator

class BaseResource:

    login_required = True
    model = None
    serializer_class = None

    SEARCH_QUERY_PARAM_NAME = 'q'

    paginator_class = Paginator
    multitenant = True

  

    def get_queryset(self,req,**kwargs):
        if self.multitenant:
            return self.model.all().where( self.model.tenant_id == self.get_auth_tenant_id(req) )

        return self.model.all()

        
        
    def get_serializer_class(self,**kwargs):
        return self.serializer_class
    

    def get_object(self,req,db,pk):
        queryset = self.get_queryset(req)

        
        results = db.objects( queryset ).filter( id__eq=pk).fetch()

        try:
            return results[0]
        except IndexError:
            return None
            

    def get_object_or_404(self,req,db,pk):
        obj = self.get_object(req,db,pk)

        if not obj:
            raise falcon.HTTPNotFound( title = "Not Found", description = "Record with key {pk} does not exist".format(pk = pk))
        return obj


    def get_db(self, req):
        return req.context['db']
    
    def get_auth_data(self,req):
        try:
            return req.context['auth']
        except KeyError:
            raise falcon.HTTPBadRequest(title="Tenant Identification Failed", 
                                        description="You need to provide access token or Client-ID as header value for unauthenticated requests."
                                        )

    
    def get_auth_tenant_id(self,req):
        auth = self.get_auth_data(req)
        return auth.get("tenant_id")

    

    
#MIXINS

class RetrieveResourceMixin:

    def retrieve(self,req,resp,db,pk,**kwargs):
        result = self.get_object_or_404(req,db,pk)

        return result


class CreateResourceMixin:

    def perform_create(self,req,db,posted_data):
        if self.multitenant:
            posted_data.update({"tenant_id": self.get_auth_tenant_id(req)} )

        return db.objects( self.model.insert() ).create(**posted_data)

    def create(self,req,resp,db,posted_data, **kwargs):

        created = self.perform_create(req,db,posted_data)

        #get created object
        
        pk = created.get("id")

        return self.get_object(req,db,pk) #db.objects( self.get_queryset(req) ).filter( id__eq = created.get("id") ).fetch()

       



class DestroyResourceMixin:

    def destroy(self,req,resp,db,result,**kwargs):
        #destroy since it exists
        if self.multitenant:
            db.objects( self.model.delete() ).filter( id__eq= result.get("id") , tenant_id__eq = self.get_auth_tenant_id(req) ).delete()
        else:
            db.objects( self.model.delete() ).filter( id__eq= result.get("id")).delete()
        return result

class UpdateResourceMixin:

    def update(self,req,resp,db,result,data,**kwargs):
        pk = result.get("id")
        db.objects( self.model.update() ).filter( id__eq= pk ).update(**data)

        #get updated object
        
        #updated_object = db.objects( self.model.all() ).filter( id__eq = result.get("id") ).fetch()

        #return updated_object
         
        return self.get_object(req,db,pk)

class ListResourceMixin:

    filterable_fields = ()

    searchable_fields = ()

    """ List model and also filter and search  """


    def list(self,req,resp,db,**kwargs):

        query_params = req.params
        queryset = self.get_queryset(req)
        queryset_object = db.objects( queryset )

        #1.filter
        filtered_queryset_object = self.filter_queryset(queryset_object, filter_params = query_params)

        #2. paginate and get results

        results, pagination = self.paginator_class().paginate(
                                          url = req.uri,
                                          url_query_params = query_params,
                                          queryset_object = queryset_object
                                          )

        #3. read db/ execute

        #results = filtered_queryset_object.fetch()

        return results, pagination
    
    def filter_queryset(self, queryset_object,filter_params):
        filter_params = dict(filter_params) #since we donot want to inteferere with global query_params

        """ for the filter params we expect example dict:
           { 'name__startswith': ' mosoti' , 'age': 20, 'gender__ne':'M' } e.t.c.

           for search, we apply or

        """

        search_text =  filter_params.pop(self.SEARCH_QUERY_PARAM_NAME , None )
        

        if search_text:
            #filter queryset with or
            search_params = {}
            for field in self.searchable_fields:
                field__condition = "{field}__contains".format(field = field)

                search_params.update({ field__condition: search_text })

            
            queryset_object = queryset_object.or_filter( **search_params )
        
        
        filter_params_copy = dict(filter_params)

        for field_and_condition, field_value in filter_params_copy.items():
            field_name = field_and_condition.split("__")[0]
            
            if field_name not in self.filterable_fields:
                #remove the fiilter as is not allowed

                del filter_params[field_name]
        
        #apply AND filter
        queryset_object = queryset_object.filter( **filter_params )

        return queryset_object


#VIEWS / RESOURCES classes


class ListResource(ListResourceMixin , BaseResource):

    def on_get(self,req, resp):
        db = self.get_db(req)
        query_params = req.params 

        results, pagination = self.list(req,resp,db)

        serializer = self.get_serializer_class()(results, many = True)


        resp.media = {"data": serializer.valid_read_data, "pagination": pagination}


class RetrieveResource(RetrieveResourceMixin , BaseResource):

    def on_get(self,req, resp,pk):
        db = self.get_db(req)
        result = self.retrieve(req,resp,db,pk)

        serializer = self.get_serializer_class()(result)
       
        resp.media = {"data": [serializer.valid_read_data] }


        



class DestroyResource(DestroyResourceMixin , BaseResource):

    def on_delete(self,req, resp,pk):
        db = self.get_db(req)
        result = self.get_object_or_404(db,pk)

        self.destroy(req,resp,db,result)

        #no content reply

        resp.status = falcon.HTTP_NO_CONTENT


class CreateResource(CreateResourceMixin , BaseResource):

    def on_post(self,req, resp):
        db = self.get_db(req)
        posted_data = req.media

        serializer = self.get_serializer_class()(posted_data)
        created_data = self.create(req,resp,db,posted_data = serializer.valid_write_data )

        serializer = self.get_serializer_class()(created_data)
        read_data = serializer.valid_read_data

        resp.media = { "data": [ read_data ] }

        resp.status = falcon.HTTP_CREATED




class UpdateResource(UpdateResourceMixin , BaseResource):

    def on_patch(self,req, resp,pk):

        db = self.get_db(req)
        new_data = req.media
        result = self.get_object_or_404(req,db,pk)

        write_serializer = self.get_serializer_class()(result)

        write_data = write_serializer.protect_data( protected_fields = write_serializer.Meta.write_protected_fields , data = new_data)

        updated = self.update(req,resp,db, result = result, data = write_data)
        
      
        read_serializer = self.get_serializer_class()(updated)


        resp.media = { "data": [ read_serializer.valid_read_data ] }

#Grouped generic resource views

class ListCreateResource(ListResource,CreateResource):
    pass

class RetrieveUpdateResource(RetrieveResource,UpdateResource):
    pass

class RetrieveUpdateDestroyResource(RetrieveResource,UpdateResource,DestroyResource):
    pass
    