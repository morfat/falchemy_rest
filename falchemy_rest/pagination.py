from .urls import replace_query_param,remove_query_param


class Paginator:
    """

    Handles cursor based pagination. 

    """

    MAX_PAGE_SIZE = 1000
    DEFAULT_PAGE_SIZE = 20
    PAGE_SIZE_QUERY_PARAM = 'limit'
    AFTER_CURSOR_QUERY_PARAM = 'after'
    BEFORE_CURSOR_QUERY_PARAM = 'before'
    PAGE_QUERY_PARAM = 'page'




    def get_page_size(self,params):
        page_size = int ( params.get(self.PAGE_SIZE_QUERY_PARAM, self.DEFAULT_PAGE_SIZE) )

        if page_size > self.MAX_PAGE_SIZE:
            page_size = self.MAX_PAGE_SIZE
        
        return page_size

    
        
    def paginate(self,url,url_query_params,queryset_object):

        pk_column_name = 'id'
       
        page_size = self.get_page_size(url_query_params)
        before = url_query_params.get(self.BEFORE_CURSOR_QUERY_PARAM)
        after = url_query_params.get(self.AFTER_CURSOR_QUERY_PARAM)
        page_number = url_query_params.get(self.PAGE_QUERY_PARAM,1)
        page_number  = int(page_number)
        
        
        
        ordered_queryset_object = queryset_object

        if after:
            #get records after the cursor value

            ordered_queryset_object = queryset_object.filter( id__lt = after).order_by_desc( pk_column_name )

        elif before and page_number == 1:

            ordered_queryset_object = queryset_object.order_by_asc( pk_column_name )

        elif before:

            ordered_queryset_object = queryset_object.filter( id__gt = before).order_by_asc( pk_column_name )

        else:
            ordered_queryset_object = queryset_object.order_by_desc( pk_column_name )
     
        #apply limit and fetch

        results = ordered_queryset_object.fetch( page_size )
        
        #build next/previous urls.

        pagination = self.get_pagination(url,results,before,after,page_number,page_size,pk_column_name)
        
        return results ,  pagination 


    
    
               
    
    
    def get_pagination(self,url,results,before,after,page_number,page_size,pk_column_name):

        total_results = len(results)

        next_url = self.get_next_link(url,results,total_results,before,after,page_number,page_size,pk_column_name)

        prev_url = self.get_previous_link(url,results,total_results,before,after,page_number,page_size,pk_column_name)

        return {self.PAGE_SIZE_QUERY_PARAM: page_size,"next_url": next_url,"current_page": page_number, "count": total_results,  "previous_url": prev_url,}
    

    def get_next_link(self,url,results,total_results,before,after,page_number,page_size,pk_column_name):
        last_seen = {}
        page_number = page_number + 1

        if total_results >= page_size:
            if before and page_number == 2:
                last_seen = results[-1:][0]

            elif before:
                last_seen = results[:1][0]
            else:
                last_seen = results[-1:][0]

        last_seen_cursor = None

        if last_seen:
            last_seen_cursor = last_seen.get(pk_column_name)

        if not last_seen_cursor:
            return None

        url = replace_query_param(url, self.AFTER_CURSOR_QUERY_PARAM, last_seen_cursor)
        url = replace_query_param(url, self.PAGE_QUERY_PARAM, page_number)
        url = remove_query_param(url,self.BEFORE_CURSOR_QUERY_PARAM)
       
        return url


    def get_previous_link(self,url,results,total_results,before,after,page_number,page_size,pk_column_name):
        last_seen = {}
        page_number = page_number - 1
        if page_number == 0:
            return None


        if after:
            if total_results >= 1:
                last_seen =  results[:1][0]
        elif before:
            last_seen =  results[-1:][0]
        else:
            return None

        last_seen_cursor = None

        if not last_seen:
            if not before:
                return None
            last_seen_cursor = before

        else:
            last_seen_cursor = last_seen.get(pk_column_name)


        if not last_seen_cursor:
            return None
        
        url = replace_query_param(url, self.PAGE_QUERY_PARAM, page_number)
        url = replace_query_param(url, self.BEFORE_CURSOR_QUERY_PARAM, last_seen_cursor)  
        url = remove_query_param(url,self.AFTER_CURSOR_QUERY_PARAM)

        return url
