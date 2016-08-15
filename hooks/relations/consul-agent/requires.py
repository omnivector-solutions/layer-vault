from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes
from charms.reactive import is_state


class ConsulClient(RelationBase):
    scope = scopes.UNIT
    auto_accessors = ['address', 'port']

    @hook('{requires:consul-agent}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')
        data = {
            'address': self.address(),
            'port': self.port(),
        }
        if all(data.values()):
            self.set_state('{relation_name}.available')

    @hook('{requires:consul-agent}-relation-{broken,departed}')
    def broken(self):
        if(is_state('{relation_name}.available')):
            self.remove_state('{relation_name}.available')
