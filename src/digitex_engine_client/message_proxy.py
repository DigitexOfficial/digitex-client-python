from . import messages_pb2

class MessageProxy:
    def __getattr__(self, name):
        field_name = name + '_msg'
        try:
            field = messages_pb2._MESSAGE.fields_by_name[field_name]
        except KeyError:
            raise AttributeError()
        desc = field.message_type

        def make_message(**kwargs):
            concrete_msg_fields = {}
            for arg in desc.fields:
                if arg.name in kwargs:
                    concrete_msg_fields[arg.name] = kwargs[arg.name]
                    del kwargs[arg.name]
            message_class = getattr(messages_pb2, desc.name)
            assert(message_class.DESCRIPTOR is desc)
            message_content = message_class(**concrete_msg_fields)
            message = messages_pb2.Message(**{field_name: message_content}, **kwargs)
            return message

        return make_message
