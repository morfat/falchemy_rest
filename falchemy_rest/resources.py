import falcon 

from .pagination import Paginator

class BaseResource:

    login_required = True
    model = None
    serializer_class = None

    SEARCH_QUERY_PARAM_NAME = 'q'

    paginator_class = Paginator
  

    def get_queryset(self,**kwargs):
        return self.model.all()
        
    
    def get_serializer_class(self,**kwargs):
        return self.serializer_class
    

    def get_object(self,db,pk):
        queryset = self.get_queryset()

        
        results = db.objects( queryset ).filter( id__eq=pk).fetch()

        try:
            return results[0]
        except IndexError:
            return None
            

    def get_object_or_404(self,db,pk):
        obj = self.get_object(db,pk)

        if not obj:
            raise falcon.HTTPNotFound()
        return obj


    def get_db(self, req):
        return req.context['db']
    


    
    


#MIXINS


class RetrieveResourceMixin:

    def retrieve(self,req,resp,db,pk,**kwargs):
        result = self.get_object_or_404(db,pk)

        return result


class CreateResourceMixin:

    def create(self,req,resp,db,posted_data, **kwargs):

        created = db.objects( self.model.insert() ).create(**posted_data)

        #get created object
        
        created_object = db.objects( self.model.all() ).filter( id__eq = created.get("id") ).fetch()


        return created_object[0]



class DestroyResourceMixin:

    def destroy(self,req,resp,db,result,**kwargs):
       
        #destroy since it exists
        db.objects( self.model.delete() ).filter( id__eq= result.get("id")).delete()

        return result

class UpdateResourceMixin:

    def update(self,req,resp,db,result,data,**kwargs):
       
        db.objects( self.model.update() ).filter( id__eq= result.get("id")).update(**data)

        #get updated object
        
        updated_object = db.objects( self.model.all() ).filter( id__eq = result.get("id") ).fetch()

        return updated_object

class ListResourceMixin:

    filterable_fields = ()

    searchable_fields = ()

    """ List model and also filter and search  """


    def list(self,req,resp,db,**kwargs):

        query_params = req.params
        queryset = self.get_queryset()
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
        result = self.get_object_or_404(db,pk)

        write_serializer = self.get_serializer_class()(result)

        write_data = write_serializer.protect_data( protected_fields = write_serializer.Meta.write_protected_fields , data = new_data)

        updated = self.update(req,resp,db, result = result, data = write_data)
        
      
        read_serializer = self.get_serializer_class()(updated[0])


        resp.media = { "data": [ read_serializer.valid_read_data ] }
