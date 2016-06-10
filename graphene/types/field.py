import inspect

from graphql.type import GraphQLField, GraphQLInputObjectField
from graphql.utils.assert_valid_name import assert_valid_name

from ..utils.orderedtype import OrderedType
from ..utils.str_converters import to_camel_case
from .argument import to_arguments


class AbstractField(object):
    @property
    def name(self):
        return self._name or self.attname and to_camel_case(self.attname)

    @name.setter
    def name(self, name):
        if name is not None:
            assert_valid_name(name)
        self._name = name

    @property
    def type(self):
        from ..utils.get_graphql_type import get_graphql_type
        from .structures import NonNull
        if inspect.isfunction(self._type):
            _type = self._type()
        else:
            _type = self._type

        if self.required:
            return NonNull(_type)
        return get_graphql_type(_type)

    @type.setter
    def type(self, type):
        self._type = type


class Field(AbstractField, GraphQLField, OrderedType):

    def __init__(self, type, args=None, resolver=None, source=None, deprecation_reason=None, name=None, description=None, required=False, _creation_counter=None, **extra_args):
        self.name = name
        self.attname = None
        self.parent = None
        self.type = type
        self.args = to_arguments(args, extra_args)
        assert not (source and resolver), ('You cannot have a source '
                                           'and a resolver at the same time')

        self.resolver = resolver
        self.source = source
        self.required = required
        self.deprecation_reason = deprecation_reason
        self.description = description
        OrderedType.__init__(self, _creation_counter=_creation_counter)

    def mount_error_message(self, where):
        return 'Field "{}" can only be mounted in ObjectType or Interface, received {}.'.format(
            self,
            where.__name__
        )

    def mount(self, parent, attname=None):
        from .objecttype import ObjectType
        from .interface import Interface
        assert issubclass(parent, (ObjectType, Interface)), self.mount_error_message(parent)

        self.attname = attname
        self.parent = parent

    def default_resolver(self, root, args, context, info):
        return getattr(root, self.source or self.attname, None)

    @property
    def resolver(self):
        from .objecttype import ObjectType
        from .interface import GrapheneInterfaceType

        resolver = getattr(self.parent, 'resolve_{}'.format(self.attname), None)

        # We try to get the resolver from the interfaces
        # This is not needed anymore as Interfaces could be extended now with Python syntax
        # if not resolver and issubclass(self.parent, ObjectType):
        #     graphql_type = self.parent._meta.graphql_type
        #     interfaces = graphql_type._provided_interfaces or []
        #     for interface in interfaces:
        #         if not isinstance(interface, GrapheneInterfaceType):
        #             continue
        #         fields = interface.get_fields()
        #         if self.attname in fields:
        #             resolver = getattr(interface.graphene_type, 'resolve_{}'.format(self.attname), None)
        #             if resolver:
        #                 # We remove the bounding to the method
        #                 resolver = resolver #.__func__
        #                 break

        if resolver:
            resolver = resolver.__func__
        else:
            resolver = self.default_resolver

        # def resolver_wrapper(root, *args, **kwargs):
        #     if not isinstance(root, self.parent):
        #         root = self.parent()
        #     return resolver(root, *args, **kwargs)

        return self._resolver or resolver # resolver_wrapper

    @resolver.setter
    def resolver(self, resolver):
        self._resolver = resolver

    def __copy__(self):
        field = self.__class__(
            type=self._type,
            args=self.args,
            resolver=self._resolver,
            source=self.source,
            deprecation_reason=self.deprecation_reason,
            name=self._name,
            required=self.required,
            description=self.description,
            _creation_counter=self.creation_counter,
        )
        field.attname = self.attname
        field.parent = self.parent
        return field

    def __str__(self):
        if not self.parent:
            return 'Not bounded field'
        return "{}.{}".format(self.parent._meta.graphql_type, self.attname)


class InputField(AbstractField, GraphQLInputObjectField, OrderedType):

    def __init__(self, type, default_value=None, description=None, name=None, required=False, _creation_counter=None):
        self.name = name
        self.type = type
        self.default_value = default_value
        self.description = description
        self.required = required
        self.attname = None
        self.parent = None
        OrderedType.__init__(self, _creation_counter=_creation_counter)

    def mount_error_message(self, where):
        return 'InputField {} can only be mounted in InputObjectType classes, received {}.'.format(
            self,
            where.__name__
        )

    def mount(self, parent, attname):
        from .inputobjecttype import InputObjectType

        assert issubclass(parent, (InputObjectType)), self.mount_error_message(parent)
        self.attname = attname
        self.parent = parent

    def __copy__(self):
        field = self.__class__(
            type=self._type,
            name=self._name,
            required=self.required,
            default_value=self.default_value,
            description=self.description,
        )
        field.attname = self.attname
        field.parent = self.parent
        return field
