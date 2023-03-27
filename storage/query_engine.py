from redis import Redis
from redis.commands.search.query import Query

"""Interface to query similar images against indexed vectors in the redis db.
"""

class QueryEngine():
    def __init__(self):
        self.r = Redis(host = 'localhost', port = 6379)
        self.ef_runtime = 10
        self.product_image_vector_field = 'product_image_vector'
        self.item_field_name = "item_name"
        self.dim = 512


    def query(self, query_vector, count):
        # Build query
        q = Query(f'*=>[KNN {count} @{self.product_image_vector_field} $vec_param EF_RUNTIME {self.ef_runtime} AS vector_score]').sort_by('vector_score').paging(0, count).return_fields('vector_score','item_name').dialect(2)
        params_dict = {"vec_param": query_vector}

        # Run Query and return documents
        docs = self.r.ft().search(q, params_dict).docs
        return docs