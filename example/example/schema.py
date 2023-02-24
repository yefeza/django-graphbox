import graphene
#prueba
import prueba.schema

class Query(
    prueba.schema.query,
    prueba.schema.session_query,
    graphene.ObjectType
    ):
    pass

class Mutation(
    prueba.schema.mutation,
    prueba.schema.session_mutation,
    graphene.ObjectType
    ):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)